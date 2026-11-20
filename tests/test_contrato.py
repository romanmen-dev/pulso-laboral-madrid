"""datos/publicados/alertas.csv cumple docs/contrato_alertas.md.

Es la tabla que lee la aplicación publicada. La referencia de municipios y
meses es paro_edad_mensual.csv, también publicada.
"""

import pandas as pd

from detectar_alertas import (
    COLUMNAS,
    ESTADOS_NO_EVALUABLES,
    MUNICIPIOS_ESPERADOS,
    comprobar_reglas,
)


ESTADOS = {"alerta_experimental", "sin_alerta", *ESTADOS_NO_EVALUABLES}


def test_columnas_en_el_orden_del_contrato(alertas_texto, columnas_del_contrato):
    assert columnas_del_contrato == COLUMNAS
    assert list(alertas_texto.columns) == columnas_del_contrato


def test_regla_1_los_179_municipios_y_todos_los_meses(alertas, paro_edad):
    municipios = set(alertas["municipio"])
    assert len(municipios) == MUNICIPIOS_ESPERADOS
    assert municipios == set(paro_edad["municipio"])

    meses = pd.date_range(paro_edad["fecha"].min(), paro_edad["fecha"].max(), freq="MS")
    esperados = pd.MultiIndex.from_product([sorted(municipios), meses])
    presentes = pd.MultiIndex.from_frame(alertas[["municipio", "fecha"]])
    assert len(esperados.difference(presentes)) == 0, "Faltan pares municipio-mes"
    assert len(presentes.difference(esperados)) == 0, "Sobran pares municipio-mes"


def test_regla_2_claves_unicas(alertas):
    repetidos = alertas.loc[alertas.duplicated(["municipio", "fecha"], keep=False)]
    assert repetidos.empty, repetidos[["municipio", "fecha"]].head().to_string()


def test_estados_y_alerta_con_valores_del_contrato(alertas_texto):
    assert set(alertas_texto["estado_detector"]) <= ESTADOS
    assert set(alertas_texto["alerta_experimental"]) <= {"True", "False", ""}


def test_regla_3_alerta_vacia_si_y_solo_si_no_evaluable(alertas):
    no_evaluable = alertas["estado_detector"].isin(ESTADOS_NO_EVALUABLES)
    alerta_vacia = alertas["alerta_experimental"].isna()
    assert alerta_vacia.eq(no_evaluable).all()


def test_regla_4_alerta_si_y_solo_si_estado_alerta(alertas):
    es_alerta = alertas["alerta_experimental"].eq(True).fillna(False)
    estado_alerta = alertas["estado_detector"].eq("alerta_experimental")
    assert es_alerta.eq(estado_alerta).all()


def test_regla_5_toda_alerta_sube_y_supera_el_limite(alertas):
    con_alerta = alertas.loc[alertas["alerta_experimental"].eq(True).fillna(False)]
    assert len(con_alerta) > 0
    # fillna(False): un cambio o un límite vacío hace fallar la prueba.
    assert con_alerta["cambio_mensual"].gt(0).fillna(False).all()
    assert con_alerta["cambio_mensual"].gt(con_alerta["limite_superior"]).fillna(False).all()


def test_las_comprobaciones_del_script_aceptan_el_archivo(alertas, paro_edad):
    # La misma comprobación que hace detectar_alertas.py antes de escribir.
    comprobar_reglas(alertas, paro_edad[["municipio", "fecha"]].drop_duplicates())
