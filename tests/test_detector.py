"""El detector de src/detectar_alertas.py con series sintéticas."""

import numpy as np
import pandas as pd
import pytest

from detectar_alertas import (
    ESTADOS_NO_EVALUABLES,
    GRUPOS_EDAD,
    anadir_grupo_edad_principal,
    aplicar_detector,
    preparar_salida,
)


ESTADOS = {"alerta_experimental", "sin_alerta", *ESTADOS_NO_EVALUABLES}


# Caso conocido: cambios de septiembre a octubre del paro de Madrid
# (README, «Cómo funciona»).
CAMBIOS_OCTUBRE_MADRID = {
    2021: -5_282,
    2022: -91,
    2023: 61,
    2024: 233,
    2025: 1_495,
    2026: 2_130,
}


def serie_con_cambios_en_octubre(cambios, paro_inicial=150_000):
    """Paro mensual de un municipio que solo cambia en octubre."""
    fechas = pd.date_range("2021-09-01", "2026-10-01", freq="MS")
    cambio = [cambios[f.year] if f.month == 10 else 0 for f in fechas]
    return pd.DataFrame(
        {
            "municipio": "Madrid",
            "fecha": fechas,
            "paro_total": paro_inicial + np.cumsum(cambio),
        }
    )


def test_caso_conocido_madrid_octubre_2026():
    resultado = aplicar_detector(serie_con_cambios_en_octubre(CAMBIOS_OCTUBRE_MADRID))
    octubre = resultado.loc[resultado["fecha"].eq("2026-10-01")]
    assert len(octubre) == 1
    fila = octubre.iloc[0]

    assert fila["cambio_mensual"] == 2_130
    assert fila["n_historico"] == 5
    assert fila["referencia_cambio"] == 61
    assert fila["mad_cambio"] == 172
    assert fila["limite_superior"] == pytest.approx(826.0, abs=0.05)
    assert fila["puntuacion_robusta"] == pytest.approx(8.11, abs=0.005)
    assert octubre["alerta_experimental"].tolist() == [True]
    assert fila["estado_detector"] == "alerta_experimental"


# Sin información futura ---------------------------------------------------

def panel_sintetico(semilla):
    """Paro por grupo de edad de tres municipios, de 2005 a 2014.

    «Grande» y «Mediano» son paseos aleatorios; «Grande» tiene subidas
    bruscas que dan alertas. «Constante» no cambia nunca: dispersión cero.
    """
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range("2005-01-01", "2014-12-01", freq="MS")
    subidas = {pd.Timestamp("2010-10-01"), pd.Timestamp("2012-03-01"), pd.Timestamp("2013-09-01")}

    filas = []
    for municipio, nivel, ruido in [("Grande", 20_000, 300), ("Mediano", 2_000, 30), ("Constante", 3, 0)]:
        for grupo in GRUPOS_EDAD:
            cambios = rng.normal(0, ruido, len(fechas)).round()
            if municipio == "Grande":
                cambios += [3_000 if f in subidas else 0 for f in fechas]
            paro = np.maximum(nivel + np.cumsum(cambios), 0).astype(int)
            filas.append(pd.DataFrame({"municipio": municipio, "fecha": fechas, "grupo_edad": grupo, "paro": paro}))
    return pd.concat(filas, ignore_index=True)


def alterar_despues_de(paro_edad, corte, semilla):
    """Cambia todos los valores posteriores al mes de corte."""
    rng = np.random.default_rng(semilla)
    alterado = paro_edad.copy()
    futuro = alterado["fecha"].gt(corte)
    factor = rng.uniform(0.3, 3.0, futuro.sum())
    alterado.loc[futuro, "paro"] = (alterado.loc[futuro, "paro"] * factor).round().astype(int) + 7
    return alterado


def detectar(paro_edad):
    """La misma secuencia que detectar_alertas.main(), sin leer ni escribir archivos."""
    paro = (
        paro_edad.groupby(["municipio", "fecha"], as_index=False)["paro"]
        .sum()
        .rename(columns={"paro": "paro_total"})
        .sort_values(["municipio", "fecha"])
        .reset_index(drop=True)
    )
    resultado = aplicar_detector(paro)
    resultado = anadir_grupo_edad_principal(resultado, paro_edad)
    return preparar_salida(resultado)


def hasta(tabla, corte):
    return tabla.loc[tabla["fecha"].le(corte)].reset_index(drop=True)


def despues(tabla, corte):
    return tabla.loc[tabla["fecha"].gt(corte)].reset_index(drop=True)


@pytest.mark.parametrize("corte", ["2011-06-01", "2012-12-01", "2014-01-01"])
def test_sin_informacion_futura(corte):
    original = panel_sintetico(semilla=2026)
    alterado = alterar_despues_de(original, corte, semilla=1)

    base = detectar(original)
    con_futuro_cambiado = detectar(alterado)

    # La prueba tiene sentido: hay meses de todos los estados antes del
    # corte y el cambio sí altera los resultados posteriores.
    assert set(hasta(base, corte)["estado_detector"]) == ESTADOS
    assert not despues(base, corte).equals(despues(con_futuro_cambiado, corte))

    pd.testing.assert_frame_equal(hasta(base, corte), hasta(con_futuro_cambiado, corte))
