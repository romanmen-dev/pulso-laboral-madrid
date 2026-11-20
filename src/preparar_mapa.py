"""Prepara la geometría simplificada de los municipios para el mapa de la app.

Cruza los límites del Geoportal IDEM con los municipios del paro por código
municipal, no por nombre: la tabla municipios_comunidad_madrid.csv del portal
traduce cada nombre del paro a su código INE. Se detiene si algún municipio
no tiene exactamente un término municipal en los límites.

Los enclaves se unen a su municipio. Las comunidades jurisdiccionales
(territorios compartidos por dos municipios) no se incluyen. La geometría se
simplifica sin dejar huecos entre municipios vecinos (shapely.coverage_simplify)
y se guarda en datos/procesados/municipios_mapa.geojson.
"""

import json
import re

import pandas as pd
import shapely
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
PROCESADOS = RAIZ / "datos" / "procesados"

RUTA_MUNICIPIOS = ORIGINALES / "municipios_comunidad_madrid.csv"
RUTA_LIMITES = ORIGINALES / "limites_municipales_idem.csv"
RUTA_PARO = PROCESADOS / "paro_total_mensual.csv"
RUTA_SALIDA = PROCESADOS / "municipios_mapa.geojson"

# Simplificación: tolerancia en grados (0,001° son unos 85-110 m, menos de un
# píxel a la escala del mapa) y precisión de las coordenadas guardadas
# (0,0001°, unos 10 m). Con estos valores ningún municipio cambia más de un
# 0,6 % de superficie y el archivo ocupa unos 260 KB.
TOLERANCIA = 0.001
REJILLA = 0.0001

# Tipos de entidad de la capa IDEM_CM_UNID_ADMIN que forman cada municipio.
TERMINO = "Término Municipal"
ENCLAVE = "Enclave"
# Las «Comunidad Jurisdiccional de …» son territorios compartidos: se excluyen.
COMUNIDAD = "Comunidad Jurisdiccional"

# Nombres de la tabla de municipios que difieren de los del paro, una vez
# pasado el artículo al final («Acebeda (La)» -> «Acebeda, La»).
NOMBRES_TABLA_A_PARO = {
    "Alamo, El": "Álamo, El",
    "Berzosa del Lozoya": "Berzosa de Lozoya",
    "Fuente el Saz de Jarama": "Fuente el Saz del Jarama",
    "Navarredonda y San Mamés": "Navaredonda",
    "Paracuellos de Jarama": "Paracuellos del Jarama",
    "Piñuecar-Gandullas": "Piñuécar-Gandullas",
    "San Agustín del Guadalix": "San Agustín de Guadalix",
    "Villavieja del Lozoya": "Villavieja de Lozoya",
}


def comprobar_archivos():
    for ruta in (RUTA_MUNICIPIOS, RUTA_LIMITES, RUTA_PARO):
        if not ruta.is_file():
            raise FileNotFoundError(
                f"No se encuentra {ruta.relative_to(RAIZ)}. Ejecuta antes "
                "src/descargar_datos.py y src/preparar_datos.py."
            )


def nombre_formato_paro(nombre):
    nombre = re.sub(r"^(.*) \((La|El|Los|Las)\)$", r"\1, \2", nombre.strip())
    return NOMBRES_TABLA_A_PARO.get(nombre, nombre)


def leer_correspondencia():
    """Nombre del paro -> código INE de 5 cifras, comprobando que es biunívoca."""
    tabla = pd.read_csv(RUTA_MUNICIPIOS, sep=";", encoding="latin-1", dtype=str)
    tabla["municipio"] = tabla["municipio_nombre"].map(nombre_formato_paro)
    tabla["codigo_ine"] = tabla["municipio_codigo_ine"].str[:5]

    for columna in ("municipio", "codigo_ine"):
        if not tabla[columna].is_unique:
            repetidos = sorted(tabla.loc[tabla[columna].duplicated(), columna])
            raise ValueError(f"La tabla de municipios repite {columna}: {repetidos}")

    paro = set(pd.read_csv(RUTA_PARO, sep=";", encoding="utf-8-sig", usecols=["municipio"])["municipio"])
    tabla_nombres = set(tabla["municipio"])
    if paro != tabla_nombres:
        raise ValueError(
            "Los nombres de la tabla de municipios no casan con los del paro. "
            f"Solo en el paro: {sorted(paro - tabla_nombres)}. "
            f"Solo en la tabla: {sorted(tabla_nombres - paro)}."
        )
    return tabla[["municipio", "codigo_ine"]]


def leer_limites(codigos):
    """Una geometría por código municipal: término municipal más sus enclaves."""
    limites = pd.read_csv(RUTA_LIMITES, dtype=str, encoding="utf-8")
    tipo = limites["DS_DESCRIPCION"].fillna("")

    excluidas = limites.loc[tipo.str.startswith(COMUNIDAD), "DS_NOMBRE"].tolist()
    desconocidos = sorted(set(tipo) - {TERMINO, ENCLAVE} - set(tipo[tipo.str.startswith(COMUNIDAD)]))
    if desconocidos:
        raise ValueError(f"Tipos de entidad inesperados en los límites: {desconocidos}")

    terminos = limites[tipo.eq(TERMINO)]
    enclaves = limites[tipo.eq(ENCLAVE)]

    cuenta = terminos["CD_INE"].value_counts()
    sin_geometria = sorted(set(codigos) - set(cuenta.index))
    repetidos = sorted(cuenta.index[cuenta > 1])
    sobrantes = sorted(set(cuenta.index) - set(codigos))
    huerfanos = sorted(set(enclaves["CD_INE"]) - set(codigos))
    if sin_geometria or repetidos or sobrantes or huerfanos:
        raise ValueError(
            "Cada municipio debe tener exactamente un término municipal. "
            f"Sin geometría: {sin_geometria}. Con varias: {repetidos}. "
            f"Términos sin municipio: {sobrantes}. Enclaves sin municipio: {huerfanos}."
        )

    partes = pd.concat([terminos, enclaves])
    partes = partes.assign(geometria=shapely.make_valid(shapely.from_wkt(partes["GEOMETRY1"].to_numpy())))
    unidas = partes.groupby("CD_INE")["geometria"].agg(lambda g: shapely.union_all(g.to_numpy()))
    return unidas, len(enclaves), excluidas


def simplificar(geometrias):
    simplificadas = shapely.coverage_simplify(geometrias, tolerance=TOLERANCIA)
    simplificadas = shapely.set_precision(simplificadas, grid_size=REJILLA)

    if not shapely.is_valid(simplificadas).all() or shapely.is_empty(simplificadas).any():
        raise ValueError("La simplificación ha producido geometrías vacías o no válidas.")
    if not shapely.coverage_is_valid(simplificadas):
        raise ValueError("La simplificación ha creado solapes entre municipios vecinos.")

    cociente = shapely.area(simplificadas) / shapely.area(geometrias)
    return simplificadas, float(abs(cociente - 1).max())


def main():
    comprobar_archivos()
    correspondencia = leer_correspondencia()
    unidas, n_enclaves, excluidas = leer_limites(correspondencia["codigo_ine"].tolist())

    correspondencia = correspondencia.sort_values("codigo_ine").reset_index(drop=True)
    geometrias = unidas.loc[correspondencia["codigo_ine"]].to_numpy()
    simplificadas, desviacion = simplificar(geometrias)

    vertices = (int(shapely.get_num_coordinates(geometrias).sum()),
                int(shapely.get_num_coordinates(simplificadas).sum()))

    entidades = [
        {
            "type": "Feature",
            "id": fila.codigo_ine,
            "properties": {"codigo_ine": fila.codigo_ine, "municipio": fila.municipio},
            "geometry": json.loads(shapely.to_geojson(geometria)),
        }
        for fila, geometria in zip(correspondencia.itertuples(), simplificadas)
    ]
    PROCESADOS.mkdir(parents=True, exist_ok=True)
    RUTA_SALIDA.write_bytes(
        json.dumps(
            {"type": "FeatureCollection", "features": entidades},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    print(f"Municipios: {len(entidades)} (con {n_enclaves} enclaves unidos a su municipio)")
    print(f"Excluidas por ser territorio compartido: {', '.join(excluidas)}")
    print(f"Vértices: {vertices[0]:,} -> {vertices[1]:,}".replace(",", "."))
    print(f"Mayor cambio de superficie de un municipio al simplificar: {100 * desviacion:.2f} %")
    print(f"Generado: {RUTA_SALIDA.relative_to(RAIZ)} | {RUTA_SALIDA.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
