"""Copia a datos/publicados/ los datos que lee la aplicación.

Streamlit Community Cloud no ejecuta la cadena de descarga, preparación y
detección: la aplicación publicada lee esta copia. Junto a ella se escribe
publicacion.json, que identifica de dónde sale: fecha de generación, último
mes de datos, commit y huellas SHA-256 de los originales y de cada archivo.

Se detiene si alertas.csv es anterior a los datos procesados, si los
resultados de la validación son anteriores a alertas.csv o si los originales
no son la versión revisada que fija src/descargar_datos.py.
"""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

from descargar_datos import FUENTES


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
PUBLICADOS = RAIZ / "datos" / "publicados"

# Solo lo que lee la aplicación (src/datos_app.py).
ALERTAS = RAIZ / "resultados" / "alertas.csv"
PROCESADOS = [
    RAIZ / "datos" / "procesados" / "paro_edad_mensual.csv",
    RAIZ / "datos" / "procesados" / "contratos_mensuales.csv",
]
MAPA = RAIZ / "datos" / "procesados" / "municipios_mapa.geojson"

# Resultados de la validación que muestra la aplicación: pestaña «¿Cómo
# sabemos que funciona?», etiqueta local/regional y otros métodos de la ficha
# (src/validar_detector.py, src/comparar_metodos.py y docs/validacion.md).
VALIDACION = RAIZ / "resultados" / "validacion"
ARCHIVOS_VALIDACION = [
    VALIDACION / "validacion_mensual.csv",
    VALIDACION / "potencia.csv",
    VALIDACION / "resumen_metodos.csv",
    VALIDACION / "curvas_metodos.csv",
    VALIDACION / "clasificacion_local_regional.csv",
    VALIDACION / "otros_metodos.csv",
]
ARCHIVOS = [ALERTAS, *PROCESADOS, MAPA, *ARCHIVOS_VALIDACION]

# Scripts que generan los datos. Si tienen cambios sin commit, el commit
# anotado en publicacion.json no basta para reproducir la copia.
CADENA = [
    "src/descargar_datos.py",
    "src/comprobar_datos.py",
    "src/preparar_datos.py",
    "src/detectar_alertas.py",
    "src/preparar_mapa.py",
    "src/validar_detector.py",
    "src/comparar_metodos.py",
]

# Atribución exigida por la licencia CC BY 4.0 de los datos del portal
# (docs/fuentes_datos.md). Se repite en publicacion.json porque esta copia
# redistribuye datos derivados.
PAGINAS = {
    "paro_edad_municipio.csv": "https://datos.comunidad.madrid/dataset/paro_registrado_edad_municipio",
    "contratos_municipio.csv": "https://datos.comunidad.madrid/dataset/contratos_trabajo_municipio",
    "municipios_comunidad_madrid.csv": "https://datos.comunidad.madrid/dataset/municipio_comunidad_madrid",
    "limites_municipales_idem.csv": (
        "https://idem.comunidad.madrid/catalogocartografia/srv/spa/catalog.search"
        "#/metadata/spacm_divisionesadmin"
    ),
}
ATRIBUCION = {
    "fuente": (
        "Comunidad de Madrid. Portal de Datos Abiertos (datos.comunidad.madrid). "
        "Fuente de los datos: D. G. del Servicio Público de Empleo. Límites "
        "municipales: Información geográfica de la Comunidad de Madrid (Geoportal IDEM)."
    ),
    "licencia": "CC BY 4.0",
    "url_licencia": "https://creativecommons.org/licenses/by/4.0/legalcode.es",
    "modificaciones": (
        "Datos transformados por Pulso Laboral Madrid: series mensuales, nombres "
        "de municipio armonizados, alertas experimentales calculadas y límites "
        "municipales simplificados."
    ),
}


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def filas(ruta):
    """Filas de datos de un CSV o entidades de un GeoJSON."""
    if ruta.suffix == ".geojson":
        return len(json.loads(ruta.read_text(encoding="utf-8"))["features"])
    with ruta.open("rb") as archivo:
        return sum(1 for _ in archivo) - 1


def git(*argumentos):
    try:
        resultado = subprocess.run(
            ["git", *argumentos], cwd=RAIZ, capture_output=True, text=True, check=True
        )
        return resultado.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def comprobar_entradas():
    faltan = [ruta for ruta in ARCHIVOS if not ruta.is_file()]
    if faltan:
        raise FileNotFoundError(
            "Faltan archivos: "
            + ", ".join(str(r.relative_to(RAIZ)) for r in faltan)
            + ". Ejecuta antes preparar_datos.py, detectar_alertas.py, "
            "validar_detector.py y comparar_metodos.py."
        )

    recientes = [r for r in PROCESADOS if r.stat().st_mtime > ALERTAS.stat().st_mtime]
    if recientes:
        raise ValueError(
            "resultados/alertas.csv es anterior a "
            + ", ".join(r.name for r in recientes)
            + ". Ejecuta de nuevo src/detectar_alertas.py antes de publicar."
        )

    antiguos = [r for r in ARCHIVOS_VALIDACION if r.stat().st_mtime < ALERTAS.stat().st_mtime]
    if antiguos:
        raise ValueError(
            ", ".join(r.name for r in antiguos)
            + " es anterior a resultados/alertas.csv. Ejecuta de nuevo "
            "src/validar_detector.py y src/comparar_metodos.py antes de publicar."
        )


def comprobar_originales():
    originales = []
    for fuente in FUENTES:
        ruta = ORIGINALES / fuente["archivo"]
        if not ruta.is_file():
            raise FileNotFoundError(
                f"No se encuentra {ruta.relative_to(RAIZ)}: hace falta para "
                "registrar de qué versión salen los datos publicados."
            )
        firma = huella(ruta)
        if firma != fuente["sha256"]:
            raise ValueError(
                f"{fuente['archivo']} no es la versión revisada que fija "
                "src/descargar_datos.py. No se publica."
            )
        originales.append(
            {
                "archivo": fuente["archivo"],
                "sha256": firma,
                "pagina": PAGINAS[fuente["archivo"]],
                "url": fuente["url"],
            }
        )
    return originales


def main():
    comprobar_entradas()
    originales = comprobar_originales()

    PUBLICADOS.mkdir(parents=True, exist_ok=True)

    archivos = []
    for origen in ARCHIVOS:
        destino = PUBLICADOS / origen.name
        shutil.copy2(origen, destino)
        archivos.append(
            {
                "archivo": destino.name,
                "origen": origen.relative_to(RAIZ).as_posix(),
                "bytes": destino.stat().st_size,
                "filas": filas(destino),
                "sha256": huella(destino),
            }
        )

    fechas = pd.read_csv(ALERTAS, sep=";", encoding="utf-8-sig", usecols=["fecha"])["fecha"]
    estado_cadena = git("status", "--porcelain", "--", *CADENA)

    publicacion = {
        "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
        "datos_desde": fechas.min()[:7],
        "datos_hasta": fechas.max()[:7],
        "commit": git("rev-parse", "HEAD"),
        "cadena_con_cambios_sin_commit": (
            bool(estado_cadena) if estado_cadena is not None else None
        ),
        "atribucion": ATRIBUCION,
        "originales": originales,
        "archivos": archivos,
    }
    (PUBLICADOS / "publicacion.json").write_text(
        json.dumps(publicacion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    total = sum(a["bytes"] for a in archivos)
    for a in archivos:
        print(f"Publicado: {a['archivo']} | {a['bytes'] / 1e6:.1f} MB | {a['filas']:,} filas".replace(",", "."))
    print(f"Total: {total / 1e6:.1f} MB en datos/publicados/")
    print(f"Datos de {publicacion['datos_desde']} a {publicacion['datos_hasta']}. Commit: {publicacion['commit']}")
    if publicacion["cadena_con_cambios_sin_commit"]:
        print("Aviso: la cadena de datos tiene cambios sin commit; el commit anotado no los incluye.")


if __name__ == "__main__":
    main()
