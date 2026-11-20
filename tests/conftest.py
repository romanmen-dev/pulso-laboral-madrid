"""Datos compartidos por las pruebas.

Las pruebas no necesitan los originales del portal: leen la copia versionada
de datos/publicados/ o construyen series sintéticas.
"""

import json
from pathlib import Path

import pandas as pd
import pytest


RAIZ = Path(__file__).resolve().parents[1]
PUBLICADOS = RAIZ / "datos" / "publicados"


@pytest.fixture(scope="session")
def alertas_texto():
    """alertas.csv tal como está escrito: todo texto y las celdas vacías como ''."""
    return pd.read_csv(
        PUBLICADOS / "alertas.csv",
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )


@pytest.fixture(scope="session")
def alertas():
    """alertas.csv con los tipos del contrato: enteros y booleanos con vacíos."""
    return pd.read_csv(
        PUBLICADOS / "alertas.csv",
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
        dtype={
            "paro_mes_anterior": "Int64",
            "cambio_mensual": "Int64",
            "alerta_experimental": "boolean",
        },
    )


@pytest.fixture(scope="session")
def paro_edad():
    return pd.read_csv(
        PUBLICADOS / "paro_edad_mensual.csv",
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
    )


@pytest.fixture(scope="session")
def mapa():
    return json.loads((PUBLICADOS / "municipios_mapa.geojson").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def columnas_del_contrato():
    """Columnas de la tabla de docs/contrato_alertas.md, en su orden."""
    texto = (RAIZ / "docs" / "contrato_alertas.md").read_text(encoding="utf-8")
    seccion = texto.split("## Columnas, en este orden", 1)[1].split("\n## ", 1)[0]
    return [
        linea.split("`")[1]
        for linea in seccion.splitlines()
        if linea.startswith("| `")
    ]
