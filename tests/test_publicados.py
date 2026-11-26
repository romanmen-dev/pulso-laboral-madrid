"""La copia de datos/publicados/ que lee la aplicación es coherente.

Huellas de publicacion.json y resultados de la validación (src/validar_detector.py
y src/comparar_metodos.py) frente a alertas.csv.
"""

import hashlib
import json

import pandas as pd
import pytest

from conftest import PUBLICADOS


def leer(nombre, **opciones):
    return pd.read_csv(PUBLICADOS / nombre, sep=";", encoding="utf-8-sig", **opciones)


@pytest.fixture(scope="module")
def publicacion():
    return json.loads((PUBLICADOS / "publicacion.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def clasificacion():
    return leer("clasificacion_local_regional.csv", parse_dates=["fecha"])


@pytest.fixture(scope="module")
def otros_metodos():
    tabla = leer("otros_metodos.csv", parse_dates=["fecha"])
    for columna in ["c_centrado", "c_ampliado", "farrington", "local_b"]:
        tabla[columna] = tabla[columna].astype("Int64")
    return tabla


def test_las_huellas_de_publicacion_json_coinciden(publicacion):
    publicados = {a["archivo"]: a for a in publicacion["archivos"]}
    esperados = {
        "alertas.csv",
        "paro_edad_mensual.csv",
        "contratos_mensuales.csv",
        "municipios_mapa.geojson",
        "validacion_mensual.csv",
        "potencia.csv",
        "resumen_metodos.csv",
        "curvas_metodos.csv",
        "clasificacion_local_regional.csv",
        "otros_metodos.csv",
    }
    assert set(publicados) == esperados

    for nombre, datos in publicados.items():
        contenido = (PUBLICADOS / nombre).read_bytes()
        assert hashlib.sha256(contenido).hexdigest() == datos["sha256"], nombre
        assert len(contenido) == datos["bytes"], nombre


def claves(tabla):
    return pd.MultiIndex.from_frame(tabla[["municipio", "fecha"]])


def test_la_clasificacion_cubre_todas_las_alertas_oficiales(alertas, clasificacion):
    oficiales = alertas.loc[alertas["alerta_experimental"].eq(True).fillna(False)]
    assert claves(clasificacion).sort_values().equals(claves(oficiales).sort_values())
    assert set(clasificacion["clasificacion"]) <= {"local", "regional", "sin clasificar (B no evaluable)"}


def test_otros_metodos_tiene_una_fila_por_municipio_y_mes(alertas, otros_metodos):
    assert claves(otros_metodos).equals(claves(alertas))
    for columna in ["c_centrado", "c_ampliado", "farrington", "local_b"]:
        assert set(otros_metodos[columna].dropna()) <= {0, 1}, columna


def test_local_si_y_solo_si_b_marca_el_mes(clasificacion, otros_metodos):
    tabla = clasificacion.merge(otros_metodos, on=["municipio", "fecha"], how="left", validate="one_to_one")
    assert tabla["local_b"].eq(1).fillna(False).eq(tabla["clasificacion"].eq("local")).all()


def test_las_alertas_por_mes_coinciden_con_alertas_csv(alertas):
    mensual = leer("validacion_mensual.csv", parse_dates=["fecha"]).set_index("fecha")
    periodo = alertas.loc[alertas["fecha"].ge(mensual.index.min())]
    estados = periodo.assign(
        con_alerta=periodo["estado_detector"].eq("alerta_experimental"),
        evaluables=periodo["estado_detector"].isin(["alerta_experimental", "sin_alerta"]),
    )
    por_mes = estados.groupby("fecha")[["con_alerta", "evaluables"]].sum()

    assert por_mes.index.equals(mensual.index)
    assert (por_mes["con_alerta"].to_numpy() == mensual["con_alerta"].to_numpy()).all()
    assert (por_mes["evaluables"].to_numpy() == mensual["evaluables"].to_numpy()).all()
