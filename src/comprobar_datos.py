from pathlib import Path
import hashlib

import pandas as pd


# Localiza el proyecto a partir de la ubicación de este script.
RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
RESULTADOS = RAIZ / "resultados"

ARCHIVOS = {
    "paro_edad_municipio.csv": "Municipio",
    "contratos_municipio.csv": "Territorio",
}


def comprobar_archivo(nombre, columna_territorio):
    ruta = ORIGINALES / nombre

    if not ruta.exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {ruta}")

    # Primero probamos UTF-8. Algunos CSV de Windows usan CP1252.
    try:
        datos = pd.read_csv(
            ruta, sep=";", encoding="utf-8-sig",
            dtype="string", keep_default_na=False
        )
        codificacion = "utf-8-sig"
    except UnicodeDecodeError:
        datos = pd.read_csv(
            ruta, sep=";", encoding="cp1252",
            dtype="string", keep_default_na=False
        )
        codificacion = "cp1252"

    necesarias = {
        "Año", "Periodo", columna_territorio,
        "Indicador", "Valor", "Unidad", "Estado dato"
    }
    if nombre == "paro_edad_municipio.csv":
        necesarias.add("Edad")

    faltan = necesarias - set(datos.columns)
    if faltan:
        raise ValueError(f"{nombre}: faltan columnas: {sorted(faltan)}")

    informe = []

    def anotar(texto):
        informe.append(str(texto))

    anotar(f"ARCHIVO: {nombre}")
    anotar(f"Codificación utilizada: {codificacion}")
    anotar(f"SHA-256: {hashlib.sha256(ruta.read_bytes()).hexdigest()}")
    anotar(f"Filas: {len(datos):,}".replace(",", "."))
    anotar(f"Columnas: {list(datos.columns)}")

    anotar("\nPRIMERAS FILAS")
    anotar(datos.head(5).to_string(index=False))

    anotar("\nAÑOS PRESENTES")
    anotar(sorted(datos["Año"].unique().tolist()))

    anotar("\nPERIODOS PRESENTES")
    anotar(sorted(datos["Periodo"].unique().tolist()))

    anotar("\nCOMBINACIONES DE AÑO Y PERIODO")
    periodos = datos[["Año", "Periodo"]].drop_duplicates()
    periodos = periodos.sort_values(["Año", "Periodo"])
    anotar(periodos.to_string(index=False))

    territorios = datos[columna_territorio].str.strip()
    territorios = territorios[territorios.ne("")]
    anotar(f"\nEtiquetas territoriales distintas: {territorios.nunique()}")
    anotar("Pueden incluir agregados; aún no es un recuento de municipios.")
    anotar(sorted(territorios.unique().tolist()))

    if "Edad" in datos.columns:
        anotar("\nGRUPOS DE EDAD")
        anotar(datos["Edad"].drop_duplicates().tolist())

    anotar("\nINDICADORES Y UNIDADES: NÚMERO DE FILAS")
    anotar(
        datos.groupby(["Indicador", "Unidad"], dropna=False)
        .size()
        .to_string()
    )

    anotar("\nCAMPOS VACÍOS POR COLUMNA")
    vacios = datos.apply(lambda columna: columna.str.strip().eq("").sum())
    anotar(vacios.to_string())

    anotar("\nESTADOS DEL DATO")
    anotar(datos["Estado dato"].value_counts(dropna=False).to_string())

    anotar(f"\nFilas completamente duplicadas: {datos.duplicated().sum()}")

    # Comprueba la conversión sin reemplazar la columna original.
    valores = datos["Valor"].str.strip()
    numeros = pd.to_numeric(valores, errors="coerce")
    no_numericos = valores.ne("") & numeros.isna()

    anotar(f"\nValores no vacíos que no se convierten a número: {no_numericos.sum()}")
    if no_numericos.any():
        anotar(valores[no_numericos].value_counts().head(10).to_string())

    anotar("\nComprobación terminada. Los originales no se han modificado.")
    return "\n".join(informe)


def main():
    RESULTADOS.mkdir(parents=True, exist_ok=True)

    for nombre, columna_territorio in ARCHIVOS.items():
        informe = comprobar_archivo(nombre, columna_territorio)
        salida = RESULTADOS / f"comprobacion_{Path(nombre).stem}.txt"
        salida.write_text(informe, encoding="utf-8")

        print(f"\nArchivo leído correctamente: {nombre}")
        print(f"Informe guardado en: {salida}")


if __name__ == "__main__":
    main()