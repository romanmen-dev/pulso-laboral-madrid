"""Los métodos alternativos de src/comparar_metodos.py.

Usan series sintéticas (las de test_detector.py) y la copia de
datos/publicados/: no necesitan los datos originales ni matplotlib. La prueba
con statsmodels se salta si no está instalado (solo está en requirements-dev.txt).
"""

import numpy as np
import pandas as pd
import pytest

import comparar_metodos as cm
import detectar_alertas as detector
from test_detector import alterar_despues_de, panel_sintetico
from validar_detector import alerta_con_subida, mismas_alertas, serie_con_subidas, simular_normal, subida_en_personas


# Para estas pruebas el valor del umbral de C no importa: no se calibra.
UMBRALES_FIJOS = {n: 3.0 for n in range(cm.MIN_CAMBIOS_C, len(cm.DESFASES_ANUALES) + 1)}

METODOS = {
    "C": lambda paro: cm.metodo_c(paro, UMBRALES_FIJOS),
    "Cc": lambda paro: cm.metodo_c_centrado(paro, 3.0),
    "A": cm.metodo_a,
    "B": cm.metodo_b,
}


def paro_total(paro_edad):
    return (
        paro_edad.groupby(["municipio", "fecha"], as_index=False)["paro"]
        .sum()
        .rename(columns={"paro": "paro_total"})
        .sort_values(["municipio", "fecha"])
        .reset_index(drop=True)
    )


@pytest.fixture(scope="module")
def paro_sintetico():
    return paro_total(panel_sintetico(semilla=2026))


# Sin información futura ---------------------------------------------------

@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("corte", ["2011-06-01", "2012-12-01", "2014-01-01"])
def test_sin_informacion_futura(metodo, corte):
    original = panel_sintetico(semilla=2026)
    alterado = alterar_despues_de(original, corte, semilla=1)

    columnas = ["municipio", "fecha", "evaluacion", "limite_cambio", "alerta"]
    base = cm.con_alertas(METODOS[metodo](paro_total(original)))[columnas]
    con_futuro_cambiado = cm.con_alertas(METODOS[metodo](paro_total(alterado)))[columnas]

    hasta = base["fecha"].le(corte)
    # La prueba tiene sentido: hay meses evaluables antes del corte y el
    # cambio sí altera los resultados posteriores.
    assert base.loc[hasta, "evaluacion"].eq(cm.EVALUABLE).sum() > 20
    assert not base.loc[~hasta].equals(con_futuro_cambiado.loc[~hasta])

    pd.testing.assert_frame_equal(base.loc[hasta], con_futuro_cambiado.loc[hasta])


# Subida sintética enorme --------------------------------------------------

@pytest.mark.parametrize("metodo", METODOS)
def test_subida_enorme_se_detecta_siempre(metodo, paro_sintetico):
    resultado = METODOS[metodo](paro_sintetico)
    evaluable = cm.es_evaluable(resultado)
    assert evaluable.sum() > 100

    alerta = cm.alertas_metodo(resultado, subida=10**9)

    assert alerta[evaluable].eq(True).all()
    assert alerta[~evaluable].isna().all()


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("municipio, fecha", [("Grande", "2013-05-01"), ("Mediano", "2011-01-01")])
def test_subida_enorme_con_el_metodo_ejecutado_sobre_la_serie_alterada(metodo, municipio, fecha, paro_sintetico):
    """Ejecutar el método sobre la serie con la subida da alerta en ese mes y
    no cambia su límite: la inyección rápida es exacta."""
    mes = paro_sintetico["municipio"].eq(municipio) & paro_sintetico["fecha"].eq(fecha)
    subida = pd.Series(np.where(mes, 10**6, 0), index=paro_sintetico.index)

    original = cm.con_alertas(METODOS[metodo](paro_sintetico))
    alterado = cm.con_alertas(METODOS[metodo](serie_con_subidas(paro_sintetico, subida)))

    assert original.loc[mes, "evaluacion"].eq(cm.EVALUABLE).all()
    assert alterado.loc[mes, "alerta"].eq(True).all()
    np.testing.assert_allclose(alterado.loc[mes, "limite_cambio"], original.loc[mes, "limite_cambio"], rtol=1e-12)
    assert mismas_alertas(
        cm.alertas_metodo(METODOS[metodo](paro_sintetico), subida.to_numpy())[mes],
        alterado.loc[mes, "alerta"],
    )


# Umbral calibrado ---------------------------------------------------------

@pytest.mark.parametrize("n", [5, 15])
def test_umbral_calibrado_da_0135_con_datos_normales(n):
    umbral = cm.calibrar_umbral(n, repeticiones=1_000_000, semilla=11)
    # Simulaciones independientes de las de la calibración.
    puntuaciones = cm.simular_puntuaciones(n, 1_000_000, semilla=12)
    tasa = np.mean(puntuaciones > umbral)

    assert tasa == pytest.approx(cm.P_OBJETIVO, abs=0.00025)
    # Con umbral 3, en cambio, la tasa es mucho mayor.
    assert np.mean(puntuaciones > 3) > 10 * cm.P_OBJETIVO


def test_umbral_calibrado_de_c_centrado_da_0135_con_datos_normales():
    umbral = cm.calibrar_umbral_centrado(repeticiones=1_000_000, semilla=11)
    puntuaciones = cm.simular_puntuaciones_centrado(1_000_000, semilla=12)

    assert np.mean(puntuaciones > umbral) == pytest.approx(cm.P_OBJETIVO, abs=0.00025)


# C centrado ---------------------------------------------------------------

def test_c_centrado_usa_la_referencia_oficial(paro_sintetico):
    """La referencia de C centrado es la mediana del mismo mes, como el oficial;
    solo cambia la escala."""
    centrado = cm.metodo_c_centrado(paro_sintetico, 3.0).tabla
    oficial = detector.aplicar_detector(paro_sintetico)
    evaluable = centrado["evaluacion"].eq(cm.EVALUABLE)
    assert evaluable.sum() > 100

    np.testing.assert_array_equal(
        centrado.loc[evaluable, "referencia_cambio"].to_numpy(),
        oficial.loc[evaluable, "referencia_cambio"].to_numpy(),
    )


def test_c_centrado_quita_la_diferencia_entre_meses():
    """Si los meses contiguos solo difieren en su nivel habitual, centrar
    devuelve la misma escala que si no difirieran."""
    rng = np.random.default_rng(5)
    historicos = rng.normal(0, 10, size=(200, 5, 3))
    desplazados = historicos + np.array([-500.0, 0.0, 800.0])

    _, escala = cm.referencia_y_escala_centradas(historicos)
    _, escala_desplazada = cm.referencia_y_escala_centradas(desplazados)

    np.testing.assert_allclose(escala_desplazada, escala)


# Umbral fuera de muestra --------------------------------------------------

@pytest.mark.parametrize("metodo", ["C", "Cc"])
def test_umbral_fuera_de_muestra_solo_usa_los_anos_de_seleccion(metodo):
    anos = [2011, 2012]
    original = panel_sintetico(semilla=2026)
    alterado = alterar_despues_de(original, "2012-12-01", semilla=1)

    resultado = METODOS[metodo](paro_total(original))
    umbral = cm.umbral_fuera_de_muestra(resultado, 10.0, anos)
    umbral_con_futuro_cambiado = cm.umbral_fuera_de_muestra(METODOS[metodo](paro_total(alterado)), 10.0, anos)

    assert umbral == umbral_con_futuro_cambiado
    # Da la mayor tasa que no pasa del objetivo en los años de selección.
    pct, evaluables, alertas = cm.tasa_alertas(resultado, anos, umbral)
    assert 0 < pct <= 10.0
    assert alertas == int(np.floor(0.10 * evaluables + 1e-9))


def test_calibrado_reutiliza_la_simulacion_de_la_validacion():
    _, directa = simular_normal(5, 3.0, repeticiones=1_000, semilla=[7, 5, 0])
    por_bloques = cm.simular_puntuaciones(5, 1_000, semilla=7)
    np.testing.assert_array_equal(directa, por_bloques)


# Oficial ------------------------------------------------------------------

def test_oficial_reproduce_alertas_y_la_inyeccion_de_la_validacion(alertas):
    oficial = cm.metodo_oficial(alertas)
    assert mismas_alertas(cm.alertas_metodo(oficial), alertas["alerta_experimental"])

    subida = subida_en_personas(alertas["paro_mes_anterior"], 0.05).fillna(0)
    assert mismas_alertas(cm.alertas_metodo(oficial, subida.to_numpy()), alerta_con_subida(alertas, subida))


# A: ajuste de Poisson -----------------------------------------------------

def test_ajuste_quasi_poisson_igual_que_statsmodels():
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(3)
    tiempo = -np.asarray(cm.DESFASES_ANUALES) / 12
    casos = [
        rng.poisson(np.exp(3 + 0.2 * tiempo)),
        rng.negative_binomial(5, 5 / (5 + np.exp(6 - 0.1 * tiempo))),
        np.array([0, 1, 0, 2, 1, 0, 3, 1, 0, 1, 2, 0, 1, 0, 4]),
    ]

    a, b, phi_bruto, covarianza_00, converge = cm.ajustar_quasi_poisson(np.vstack(casos), tiempo)

    assert converge.all()
    X = np.column_stack([np.ones_like(tiempo), tiempo])
    for k, y in enumerate(casos):
        ajuste = sm.GLM(y, X, family=sm.families.Poisson()).fit(scale="X2")
        np.testing.assert_allclose([a[k], b[k]], ajuste.params, rtol=1e-6, atol=1e-8)
        np.testing.assert_allclose(phi_bruto[k], ajuste.scale, rtol=1e-6)
        np.testing.assert_allclose(phi_bruto[k] * covarianza_00[k], ajuste.bse[0] ** 2, rtol=1e-6)


def test_limite_farrington_equivale_a_la_puntuacion():
    """y > U si y solo si la puntuación de Farrington con potencia 2/3 supera z."""
    mu0, phi, tau, z = 40.0, 2.5, 0.01, 3.0
    limite = cm.limite_farrington(mu0, phi, tau, z)
    puntuacion = lambda y: (y ** (2 / 3) - mu0 ** (2 / 3)) / ((2 / 3) * mu0 ** (1 / 6) * np.sqrt(phi + mu0 * tau))
    assert puntuacion(limite) == pytest.approx(z)
    assert puntuacion(limite + 0.01) > z > puntuacion(limite - 0.01)
