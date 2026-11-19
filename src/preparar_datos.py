from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
PROCESADOS = RAIZ / "datos" / "procesados"

EDADES = {
    "Menor de 25 años",
    "De 25 a 44 años",
    "Mayor de 44 años",
}

# Nombres de contratos que se traducen a los de paro, que es la serie principal.
NOMBRES_CONTRATOS_A_PARO = {
    "Berzosa del Lozoya": "Berzosa de Lozoya",
    "Fuente el Saz de Jarama": "Fuente el Saz del Jarama",
    "Horcajo de la Sierra": "Horcajo de la Sierra-Aoslos",
    "Mejorada del campo": "Mejorada del Campo",
    "Navarredonda": "Navaredonda",
    "San Lorenzo del Escorial": "San Lorenzo de El Escorial",
}


def leer_serie(nombre, territorio, unidad):
    datos = pd.read_csv(
        ORIGINALES / nombre,
        sep=";",
        encoding="utf-8-sig",
        dtype="string",
        keep_default_na=False,
    )

    # Solo seleccionamos recuentos, excluyendo medias y tasas.
    datos = datos.loc[datos["Indicador"].eq("Serie")].copy()

    if datos.empty:
        raise ValueError(f"{nombre}: no hay filas de Serie.")

    if not datos["Unidad"].eq(unidad).all():
        raise ValueError(f"{nombre}: hay unidades inesperadas.")

    if not datos["Periodo"].str.fullmatch(r"M(0[1-9]|1[0-2])").all():
        raise ValueError(f"{nombre}: hay periodos mensuales incorrectos.")

    datos["fecha"] = pd.to_datetime(
        datos["Año"] + "-" + datos["Periodo"].str[1:] + "-01",
        format="%Y-%m-%d",
        errors="raise",
    )

    valores = pd.to_numeric(datos["Valor"], errors="raise")

    if valores.isna().any() or (valores < 0).any() or (valores % 1 != 0).any():
        raise ValueError(f"{nombre}: hay recuentos no válidos.")

    datos["valor"] = valores.astype("int64")
    datos = datos.rename(
        columns={
            territorio: "municipio",
            "Edad": "grupo_edad",
            "Estado dato": "estado_dato",
        }
    )

    columnas = ["municipio", "fecha", "valor", "estado_dato"]
    if "grupo_edad" in datos.columns:
        columnas.insert(2, "grupo_edad")

    return datos[columnas]


def comprobar_continuidad(datos, grupos):
    claves = grupos + ["fecha"]

    if datos.duplicated(claves).any():
        raise ValueError(f"Hay claves duplicadas: {claves}")

    meses = pd.date_range(
        datos["fecha"].min(), datos["fecha"].max(), freq="MS"
    )

    for nombre, grupo in datos.groupby(grupos):
        ausentes = meses.difference(grupo["fecha"])
        if len(ausentes):
            raise ValueError(f"Faltan {len(ausentes)} meses en {nombre}.")


def guardar(datos, nombre, orden):
    ruta = PROCESADOS / nombre
    datos.sort_values(orden).to_csv(
        ruta,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )
    filas = f"{len(datos):,}".replace(",", ".")
    print(f"Generado: {nombre} | Filas: {filas}")

def main():
    paro = leer_serie(
        "paro_edad_municipio.csv", "Municipio", "Número de parados"
    )
    contratos = leer_serie(
        "contratos_municipio.csv", "Territorio", "Contratos"
    )

    contratos["municipio"] = contratos["municipio"].replace(
        NOMBRES_CONTRATOS_A_PARO
    )

    municipios_paro = set(paro["municipio"])
    municipios_contratos = set(contratos["municipio"])

    if municipios_paro != municipios_contratos:
        raise ValueError(
            "Los municipios de paro y contratos no coinciden. "
            f"Solo en paro: {sorted(municipios_paro - municipios_contratos)}. "
            f"Solo en contratos: {sorted(municipios_contratos - municipios_paro)}."
        )

    comprobar_continuidad(paro, ["municipio", "grupo_edad"])
    comprobar_continuidad(contratos, ["municipio"])

    for (municipio, fecha), grupo in paro.groupby(["municipio", "fecha"]):
        edades_presentes = set(grupo["grupo_edad"].tolist())

        if edades_presentes != EDADES:
            raise ValueError(
                f"{municipio}, {fecha:%Y-%m}: "
                f"grupos de edad inesperados: {edades_presentes}"
            )

    paro_total = (
        paro.groupby(["municipio", "fecha"], as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "paro_total"})
    )

    paro = paro.rename(columns={"valor": "paro"})
    contratos = contratos.rename(columns={"valor": "contratos"})

    PROCESADOS.mkdir(parents=True, exist_ok=True)

    guardar(
        paro,
        "paro_edad_mensual.csv",
        ["municipio", "fecha", "grupo_edad"],
    )
    guardar(
        paro_total,
        "paro_total_mensual.csv",
        ["municipio", "fecha"],
    )
    guardar(
        contratos,
        "contratos_mensuales.csv",
        ["municipio", "fecha"],
    )

    print("\nPreparación terminada. Los originales no se han modificado.")


if __name__ == "__main__":
    main()
