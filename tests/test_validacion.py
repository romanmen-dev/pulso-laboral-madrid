"""La inyección sintética de src/validar_detector.py.

Usa la copia de datos/publicados/alertas.csv: no necesita los datos originales
ni matplotlib.
"""

import numpy as np
import pandas as pd
import pytest

import detectar_alertas as detector
from validar_detector import (
    EVALUABLES,
    alerta_con_subida,
    aplicar_variante,
    mismas_alertas,
    parametros_detector,
    serie_con_subidas,
    subida_en_personas,
)


def test_subida_nula_da_las_alertas_oficiales(alertas):
    subida = subida_en_personas(alertas["paro_mes_anterior"], 0.0)
    assert subida.dropna().eq(0).all()

    resultado = alerta_con_subida(alertas, subida)

    assert mismas_alertas(resultado, alertas["alerta_experimental"])


def test_subida_enorme_se_detecta_siempre(alertas):
    evaluable = alertas["estado_detector"].isin(EVALUABLES)
    assert evaluable.sum() > 30_000

    resultado = alerta_con_subida(alertas, 10**9)

    assert resultado[evaluable].eq(True).all()
    # Los meses no evaluables siguen sin evaluar: no pasan a ser alertas.
    assert resultado[~evaluable].isna().all()


def test_subida_redondeada_a_personas():
    paro_mes_anterior = pd.Series([0, 49, 50, 149, 150, None], dtype="Int64")

    subida = subida_en_personas(paro_mes_anterior, 0.01)

    assert subida.iloc[:5].tolist() == [0, 0, 1, 1, 2]
    assert np.isnan(subida.iloc[5])


MUNICIPIOS = ["Madrid", "Getafe", "Aranjuez", "Acebeda, La"]


@pytest.mark.parametrize("ano", [2015, 2019])
@pytest.mark.parametrize("proporcion", [0.01, 0.05, 0.10])
def test_inyeccion_igual_que_el_detector_sobre_la_serie_alterada(alertas, ano, proporcion):
    """Sumar la subida al cambio da lo mismo que ejecutar el detector sobre la
    serie con la subida: la referencia y el límite del mes no cambian."""
    paro = (
        alertas.loc[alertas["municipio"].isin(MUNICIPIOS), ["municipio", "fecha", "paro_total"]]
        .sort_values(["municipio", "fecha"])
        .reset_index(drop=True)
    )
    oficial = aplicar_variante(paro, detector.VENTANA_ANOS, detector.UMBRAL)

    en_ano = oficial["fecha"].dt.year.eq(ano)
    subida = subida_en_personas(oficial["paro_mes_anterior"], proporcion).where(en_ano, 0)
    completo = aplicar_variante(serie_con_subidas(paro, subida), detector.VENTANA_ANOS, detector.UMBRAL)

    # El mes de la subida cambia en esas personas y los demás no cambian.
    diferencia = completo["cambio_mensual"] - oficial["cambio_mensual"]
    assert diferencia[en_ano].eq(subida[en_ano]).all()
    assert diferencia[~en_ano].fillna(0).eq(0).all()

    # Mismo límite y mismas alertas en el año de la subida.
    for columna in ["referencia_cambio", "escala_robusta", "limite_superior"]:
        pd.testing.assert_series_equal(oficial.loc[en_ano, columna], completo.loc[en_ano, columna])
    assert mismas_alertas(alerta_con_subida(oficial, subida)[en_ano], completo.loc[en_ano, "alerta_experimental"])


def test_parametros_detector_se_restauran():
    originales = (detector.VENTANA_ANOS, detector.MIN_OBSERVACIONES, detector.UMBRAL)

    with pytest.raises(RuntimeError):
        with parametros_detector(7, 2.5):
            assert (detector.VENTANA_ANOS, detector.MIN_OBSERVACIONES, detector.UMBRAL) == (7, 7, 2.5)
            raise RuntimeError

    assert (detector.VENTANA_ANOS, detector.MIN_OBSERVACIONES, detector.UMBRAL) == originales
