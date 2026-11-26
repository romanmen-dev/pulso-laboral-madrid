"""Prepara la población de 15 a 64 años por municipio y año.

Es el denominador del indicador de contexto de la ficha: paro registrado por
cada 1.000 habitantes de 15 a 64 años. No interviene en el detector.

Fuente: «Población censada por edad, nacionalidad y sexo. Censo anual.
Municipios» (Censo de Población Anual del INE, a 1 de enero de cada año,
2021-2025). Los grupos de edad son quinquenales, por eso se usa 15-64 y no
16-64. Se suman los diez grupos de 15-19 a 60-64, con nacionalidad y sexo
«Total».

Se cruza por código INE con la tabla de municipios del portal (la misma
correspondencia nombre-código que usa el mapa) y se detiene si a algún
municipio del paro le falta la población de algún año.

Salida: datos/procesados/poblacion_15_64.csv (municipio, codigo_ine, anio,
poblacion_15_64).
"""

from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
PROCESADOS = RAIZ / "datos" / "procesados"

RUTA_CENSO = ORIGINALES / "poblacion_censo_anual_edad.csv"
RUTA_SALIDA = PROCESADOS / "poblacion_15_64.csv"

GRUPOS_15_64 = [f"De {inicio}-{inicio + 4} años" for inicio in range(15, 65, 5)]
COLUMNAS = ["anio", "tipo", "codigo", "territorio", "edad", "nacionalidad", "sexo", "valor"]


def leer_censo(ruta=RUTA_CENSO):
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encuentra {ruta.relative_to(RAIZ)}. Ejecuta antes src/descargar_datos.py."
        )
    censo = pd.read_csv(ruta, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    censo = censo.iloc[:, : len(COLUMNAS)]
    censo.columns = COLUMNAS

    municipios = censo[
        censo["tipo"].eq("Municipios")
        & censo["nacionalidad"].eq("Total")
        & censo["sexo"].eq("Total")
    ].copy()

    faltan_grupos = sorted(set(GRUPOS_15_64) - set(municipios["edad"]))
    if faltan_grupos:
        raise ValueError(f"El censo no trae los grupos de edad {faltan_grupos}.")

    municipios = municipios[municipios["edad"].isin(GRUPOS_15_64)]
    if not municipios["codigo"].str.fullmatch(r"\d{4}").all():
        raise ValueError("Hay códigos municipales del censo que no tienen 4 cifras.")
    valores = pd.to_numeric(municipios["valor"], errors="raise")
    if valores.isna().any() or (valores < 0).any() or (valores % 1 != 0).any():
        raise ValueError("Hay recuentos de población no válidos en el censo.")

    municipios["valor"] = valores.astype("int64")
    # Código del portal: 3 cifras del municipio y dígito de control. El INE
    # de 5 cifras es «28» más las 3 primeras.
    municipios["codigo_ine"] = "28" + municipios["codigo"].str[:3]
    municipios["anio"] = municipios["anio"].astype(int)

    cuenta = municipios.groupby(["codigo_ine", "anio"])["edad"].nunique()
    incompletos = cuenta[cuenta != len(GRUPOS_15_64)]
    if not incompletos.empty:
        raise ValueError(f"Municipios sin los diez grupos de 15 a 64 años: {incompletos.index.tolist()}")

    return (
        municipios.groupby(["codigo_ine", "anio"], as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "poblacion_15_64"})
    )


def cruzar(poblacion, correspondencia):
    """Añade el nombre del paro; se detiene si falta algún municipio o año."""
    anios = sorted(poblacion["anio"].unique())
    tabla = correspondencia.merge(poblacion, on="codigo_ine", how="left", validate="one_to_many")

    sin_poblacion = sorted(tabla.loc[tabla["poblacion_15_64"].isna(), "municipio"])
    if sin_poblacion:
        raise ValueError(f"Municipios sin población en el censo: {sin_poblacion}")

    cuenta = tabla.groupby("municipio")["anio"].nunique()
    incompletos = sorted(cuenta.index[cuenta != len(anios)])
    if incompletos:
        raise ValueError(f"Municipios a los que les falta algún año ({anios}): {incompletos}")

    sobrantes = sorted(set(poblacion["codigo_ine"]) - set(correspondencia["codigo_ine"]))
    if sobrantes:
        raise ValueError(f"Códigos del censo que no están entre los municipios del paro: {sobrantes}")

    tabla["poblacion_15_64"] = tabla["poblacion_15_64"].astype("int64")
    return tabla[["municipio", "codigo_ine", "anio", "poblacion_15_64"]]


def main():
    # Misma correspondencia nombre-código que el mapa. Se importa aquí para
    # que las pruebas de cruzar() no necesiten shapely.
    from preparar_mapa import leer_correspondencia

    tabla = cruzar(leer_censo(), leer_correspondencia())
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    tabla.sort_values(["municipio", "anio"]).to_csv(
        RUTA_SALIDA, sep=";", index=False, encoding="utf-8-sig"
    )
    anios = sorted(tabla["anio"].unique())
    print(
        f"Guardado: {RUTA_SALIDA.relative_to(RAIZ)} | {tabla['municipio'].nunique()} municipios | "
        f"años {anios[0]}-{anios[-1]} | {len(tabla)} filas"
    )


if __name__ == "__main__":
    main()
