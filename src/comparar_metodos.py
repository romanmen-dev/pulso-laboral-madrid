"""Comparación del detector oficial con métodos alternativos.

Métodos (docs/validacion.md, «Comparación con métodos alternativos»):

- oficial: src/detectar_alertas.py. Mediana y MAD de los cambios del mismo mes
  en los 5 años anteriores (5 cambios), umbral 3.
- C5: el oficial con el umbral calibrado para 5 cambios.
- C: robusto ampliado y calibrado. Misma regla con los cambios del mismo mes y
  de los meses contiguos (±1) en los 5 años anteriores, hasta 15 cambios, y el
  umbral calibrado para cada número de cambios.
- Cc: C centrado. Referencia: la mediana del propio mes, como el oficial.
  Escala: los 15 cambios centrados cada uno en la mediana de su mes
  calendario, para no mezclar estacionalidades. Umbral calibrado.
- A: quasi-Poisson tipo Farrington sobre el nivel de paro.
- B: anomalía local. Cambio del municipio frente al del resto de la Comunidad.
- C_fm y Cc_fm: C y Cc con el umbral elegido fuera de muestra, en 2012-2016,
  para dar la misma tasa de alertas que el oficial con umbral 3 en esos años.
  Se evalúan en 2017-2019 y en 2020.

Reutiliza el banco de pruebas de src/validar_detector.py (lectura, quintiles y
subidas sintéticas) y escribe en resultados/validacion/. No modifica el
detector oficial ni resultados/alertas.csv.

Ningún método usa información futura: la referencia de cada mes sale solo de
meses anteriores. B usa además el cambio del resto de la Comunidad en el mismo
mes, que se publica a la vez que el del municipio.
"""

import math
import time
import warnings
from dataclasses import dataclass, replace
from typing import Callable

import numpy as np
import pandas as pd

import detectar_alertas as detector
import validar_detector as val


EVALUABLE = "evaluable"

# «3» con n infinito: P(Z > 3) con normalidad, 0,135 %.
P_OBJETIVO = 0.5 * math.erfc(3 / math.sqrt(2))

# C y A: el mismo mes y los contiguos (±1) de los 5 años anteriores, como
# desfases en meses: 11, 12, 13, 23, 24, 25, ..., 59, 60, 61.
DESFASES_ANUALES = [12 * k + j for k in range(1, 6) for j in (-1, 0, 1)]
MIN_CAMBIOS_C = 5
REPETICIONES_CALIBRADO = 2_000_000
REPETICIONES_COMPROBACION = 1_000_000
BLOQUE_SIMULACION = 250_000

# A: límite superior de predicción con z = 3 (cuantil del 99,865 %, el mismo
# 0,135 % que C).
Z_FARRINGTON = 3.0

# B: los 60 meses anteriores (5 años) y umbral de 3 escalas robustas.
MESES_B = 60
UMBRAL_B = 3.0

# Umbral fuera de muestra: se elige en 2012-2016 y se evalúa en 2017-2019 y
# en 2020.
ANOS_SELECCION = [2012, 2013, 2014, 2015, 2016]

# Potencia: 2015-2019 (como en la validación) y 2017-2019 (evaluación fuera
# de muestra, sin los años con los que se elige el umbral).
PERIODOS_INYECCION = {"2015-2019": "inyeccion", "2017-2019": "inyeccion_2017_2019"}

MUNICIPIO_CASO = "Madrid"
FECHA_CASO = pd.Timestamp("2026-10-01")
FECHA_CLASIFICACION = pd.Timestamp("2026-10-01")

AMARILLO = "#eda100"
MAGENTA = "#e87ba4"


@dataclass
class Resultado:
    """Resultado de un método: una fila por municipio y mes.

    `tabla` tiene municipio, fecha, paro_total, paro_mes_anterior,
    cambio_mensual y evaluacion («evaluable» o el motivo por el que no lo es).
    `limite(u)` da el límite superior del cambio mensual con el umbral u: hay
    alerta si el mes es evaluable, el paro sube y el cambio supera el límite.
    """

    clave: str
    nombre: str
    tabla: pd.DataFrame
    umbral: object
    limite: Callable
    segundos: float = 0.0


# Utilidades -----------------------------------------------------------------

def a_matrices(paro):
    """Claves y matrices municipio × mes de niveles y cambios mensuales."""
    tabla = paro.pivot(index="municipio", columns="fecha", values="paro_total").sort_index()
    if tabla.isna().any().any():
        raise ValueError("Todos los municipios deben tener los mismos meses.")

    claves = pd.MultiIndex.from_product(
        [tabla.index, tabla.columns], names=["municipio", "fecha"]
    ).to_frame(index=False)
    niveles = tabla.to_numpy(dtype=float)
    cambios = np.full_like(niveles, np.nan)
    cambios[:, 1:] = np.diff(niveles, axis=1)
    return claves, niveles, cambios


def tabla_base(claves, niveles, cambios):
    anterior = np.full_like(niveles, np.nan)
    anterior[:, 1:] = niveles[:, :-1]
    return claves.assign(
        paro_total=niveles.ravel(),
        paro_mes_anterior=anterior.ravel(),
        cambio_mensual=cambios.ravel(),
    )


def ventanas(matriz, desfases):
    """Valores de matriz[:, t - d] para cada mes t y desfase d; NaN si t - d < 0."""
    desfases = np.asarray(desfases)
    indices = np.arange(matriz.shape[1])[:, None] - desfases[None, :]
    resultado = matriz[:, np.clip(indices, 0, None)]
    resultado[:, indices < 0] = np.nan
    return resultado


def es_evaluable(resultado):
    return resultado.tabla["evaluacion"].eq(EVALUABLE).to_numpy()


def alertas_metodo(resultado, subida=0.0, umbral=None):
    """Alertas del método, con `subida` personas sumadas al cambio del mes.

    Solo cambia el mes evaluado: el límite de cada método depende de meses
    anteriores (y, en B, del resto de la Comunidad), así que no varía.
    Vacía si el mes no es evaluable.
    """
    umbral = resultado.umbral if umbral is None else umbral
    tabla = resultado.tabla
    evaluable = es_evaluable(resultado)
    cambio = tabla["cambio_mensual"].to_numpy(dtype=float) + np.asarray(subida, dtype=float)
    with np.errstate(invalid="ignore"):
        alerta = (cambio > 0) & (cambio > np.asarray(resultado.limite(umbral), dtype=float))

    serie = pd.Series(pd.NA, index=tabla.index, dtype="boolean")
    serie[evaluable] = alerta[evaluable]
    return serie


def con_alertas(resultado):
    """La tabla del método con su límite y su alerta con el umbral por defecto."""
    return resultado.tabla.assign(
        limite_cambio=np.where(es_evaluable(resultado), resultado.limite(resultado.umbral), np.nan),
        alerta=alertas_metodo(resultado),
    )


# Umbral calibrado (C y C5) -------------------------------------------------

def simular_puntuaciones(n, repeticiones, semilla):
    """Puntuaciones del detector con n cambios normales (val.simular_normal por bloques)."""
    bloques = []
    for i, inicio in enumerate(range(0, repeticiones, BLOQUE_SIMULACION)):
        tamano = min(BLOQUE_SIMULACION, repeticiones - inicio)
        _, puntuacion = val.simular_normal(n, 3.0, repeticiones=tamano, semilla=[semilla, n, i])
        bloques.append(puntuacion)
    return np.concatenate(bloques)


def calibrar_umbral(n, probabilidad=P_OBJETIVO, repeticiones=REPETICIONES_CALIBRADO, semilla=val.SEMILLA):
    """Umbral u_n con el que P(puntuación > u_n) = probabilidad si los n cambios
    históricos y el nuevo son normales e independientes."""
    puntuaciones = simular_puntuaciones(n, repeticiones, semilla)
    return float(np.quantile(puntuaciones, 1 - probabilidad))


def referencia_y_escala_centradas(historicos):
    """Referencia y escala de C centrado.

    `historicos` tiene forma (..., 5 años, 3 meses), con los meses en el orden
    de DESFASES_ANUALES: siguiente, mismo y anterior al evaluado. Cada cambio se
    centra en la mediana de su mes calendario. La referencia es la mediana del
    mismo mes (la del oficial) y la escala, 1,4826 × MAD de los 15 residuos.
    """
    mediana_mes = np.median(historicos, axis=-2)
    residuos = historicos - mediana_mes[..., None, :]
    residuos = residuos.reshape(*residuos.shape[:-2], -1)
    mad = np.median(np.abs(residuos - np.median(residuos, axis=-1, keepdims=True)), axis=-1)
    return mediana_mes[..., 1], detector.FACTOR_ESCALA * mad


def simular_puntuaciones_centrado(repeticiones, semilla):
    """Puntuaciones de C centrado con datos normales: 3 meses × 5 años y un
    cambio nuevo del mismo mes. La media de cada mes no influye (se centra)."""
    bloques = []
    for i, inicio in enumerate(range(0, repeticiones, BLOQUE_SIMULACION)):
        tamano = min(BLOQUE_SIMULACION, repeticiones - inicio)
        rng = np.random.default_rng([semilla, 0, i])
        historicos = rng.standard_normal((tamano, 5, 3))
        nuevo = rng.standard_normal(tamano)
        referencia, escala = referencia_y_escala_centradas(historicos)
        bloques.append((nuevo - referencia) / escala)
    return np.concatenate(bloques)


def calibrar_umbral_centrado(probabilidad=P_OBJETIVO, repeticiones=REPETICIONES_CALIBRADO, semilla=val.SEMILLA):
    puntuaciones = simular_puntuaciones_centrado(repeticiones, semilla)
    return float(np.quantile(puntuaciones, 1 - probabilidad))


def tabla_umbrales_calibrados(valores_n=range(MIN_CAMBIOS_C, len(DESFASES_ANUALES) + 1)):
    filas = []
    for n in valores_n:
        umbral = calibrar_umbral(n)
        # Comprobación con simulaciones independientes (otra semilla).
        comprobacion = simular_puntuaciones(n, REPETICIONES_COMPROBACION, semilla=val.SEMILLA + 1)
        filas.append(
            {
                "metodo": "C",
                "n_cambios": n,
                "umbral_calibrado": umbral,
                "pct_simulado_con_umbral_3": 100 * float(np.mean(comprobacion > 3)),
                "pct_simulado_con_umbral_calibrado": 100 * float(np.mean(comprobacion > umbral)),
                "pct_objetivo": 100 * P_OBJETIVO,
            }
        )

    umbral = calibrar_umbral_centrado()
    comprobacion = simular_puntuaciones_centrado(REPETICIONES_COMPROBACION, semilla=val.SEMILLA + 1)
    filas.append(
        {
            "metodo": "Cc",
            "n_cambios": len(DESFASES_ANUALES),
            "umbral_calibrado": umbral,
            "pct_simulado_con_umbral_3": 100 * float(np.mean(comprobacion > 3)),
            "pct_simulado_con_umbral_calibrado": 100 * float(np.mean(comprobacion > umbral)),
            "pct_objetivo": 100 * P_OBJETIVO,
        }
    )
    return pd.DataFrame(filas)


# Oficial y C5 ---------------------------------------------------------------

def metodo_oficial(alertas, umbral=None, clave="oficial", nombre="Oficial: 5 cambios, umbral 3"):
    """El detector oficial leído de alertas.csv, con otro umbral si se indica."""
    tabla = alertas[["municipio", "fecha", "paro_total"]].assign(
        paro_total=alertas["paro_total"].astype(float),
        paro_mes_anterior=alertas["paro_mes_anterior"].astype(float),
        cambio_mensual=alertas["cambio_mensual"].astype(float),
        evaluacion=alertas["estado_detector"].where(
            ~alertas["estado_detector"].isin(val.EVALUABLES), EVALUABLE
        ),
        referencia_cambio=alertas["referencia_cambio"].astype(float),
        escala_robusta=alertas["escala_robusta"].astype(float),
    )
    referencia = alertas["referencia_cambio"].to_numpy(dtype=float)
    escala = alertas["escala_robusta"].to_numpy(dtype=float)
    return Resultado(
        clave=clave,
        nombre=nombre,
        tabla=tabla.reset_index(drop=True),
        umbral=val.UMBRAL_OFICIAL if umbral is None else umbral,
        limite=lambda u: referencia + np.asarray(u) * escala,
    )


# C. Robusto ampliado y calibrado --------------------------------------------

def metodo_c(paro, umbrales_n):
    """Mediana y MAD de hasta 15 cambios: mismo mes y contiguos de 5 años.

    El umbral depende del número de cambios disponibles (umbrales_n). Con menos
    de 5 cambios el mes no es evaluable, como en el oficial.
    """
    inicio = time.perf_counter()
    claves, niveles, cambios = a_matrices(paro)
    historicos = ventanas(cambios, DESFASES_ANUALES)
    n = (~np.isnan(historicos)).sum(axis=2)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mediana = np.nanmedian(historicos, axis=2)
        mad = np.nanmedian(np.abs(historicos - mediana[..., None]), axis=2)
    escala = detector.FACTOR_ESCALA * mad

    umbral = np.full(n.shape, np.nan)
    for valor_n, valor_u in umbrales_n.items():
        umbral[n == valor_n] = valor_u

    evaluacion = np.where(
        (n < MIN_CAMBIOS_C) | np.isnan(cambios),
        "historial_insuficiente",
        np.where(escala > 0, EVALUABLE, "dispersion_cero"),
    )

    tabla = tabla_base(claves, niveles, cambios).assign(
        evaluacion=evaluacion.ravel(),
        n_cambios=n.ravel(),
        referencia_cambio=mediana.ravel(),
        escala_robusta=escala.ravel(),
        umbral=umbral.ravel(),
    )
    referencia = tabla["referencia_cambio"].to_numpy()
    escala_plana = tabla["escala_robusta"].to_numpy()
    return Resultado(
        clave="C",
        nombre="C. Robusto ampliado (hasta 15 cambios) y umbral calibrado",
        tabla=tabla,
        umbral=tabla["umbral"].to_numpy(),
        limite=lambda u: referencia + np.asarray(u) * escala_plana,
        segundos=time.perf_counter() - inicio,
    )


# C centrado -----------------------------------------------------------------

def metodo_c_centrado(paro, umbral):
    """C sin mezclar estacionalidades.

    Usa los mismos 15 cambios que C (mismo mes y contiguos de los 5 años
    anteriores), pero centra cada uno en la mediana de su mes calendario dentro
    de la ventana. La referencia es la mediana del mismo mes, como en el
    oficial; la escala, 1,4826 × MAD de los 15 residuos. Exige los 15 cambios.
    """
    inicio = time.perf_counter()
    claves, niveles, cambios = a_matrices(paro)
    historicos = ventanas(cambios, DESFASES_ANUALES)
    forma = niveles.shape
    completo = ~np.isnan(historicos).any(axis=2)

    referencia, escala = referencia_y_escala_centradas(historicos.reshape(*forma, 5, 3))

    evaluacion = np.where(
        ~completo | np.isnan(cambios),
        "historial_insuficiente",
        np.where(escala > 0, EVALUABLE, "dispersion_cero"),
    )

    tabla = tabla_base(claves, niveles, cambios).assign(
        evaluacion=evaluacion.ravel(),
        referencia_cambio=np.where(completo, referencia, np.nan).ravel(),
        escala_robusta=np.where(completo, escala, np.nan).ravel(),
    )
    referencia_plana = tabla["referencia_cambio"].to_numpy()
    escala_plana = tabla["escala_robusta"].to_numpy()
    return Resultado(
        clave="Cc",
        nombre="Cc. C centrado en la mediana de cada mes, umbral calibrado",
        tabla=tabla,
        umbral=umbral,
        limite=lambda u: referencia_plana + np.asarray(u) * escala_plana,
        segundos=time.perf_counter() - inicio,
    )


# Umbral fuera de muestra ----------------------------------------------------

def tasa_alertas(resultado, anos, umbral=None):
    """% de alertas entre los meses evaluables de esos años."""
    filtro = resultado.tabla["fecha"].dt.year.isin(anos).to_numpy() & es_evaluable(resultado)
    alerta = alertas_metodo(resultado, 0, umbral).fillna(False).to_numpy(dtype=bool)
    return val.porcentaje((filtro & alerta).sum(), filtro.sum()), int(filtro.sum()), int((filtro & alerta).sum())


def umbral_fuera_de_muestra(resultado, tasa_objetivo_pct, anos=ANOS_SELECCION):
    """Umbral con el que el método da, en `anos`, la mayor tasa de alertas que
    no pasa de la tasa objetivo. Usa solo los meses de esos años.

    Para métodos con referencia y escala (oficial, C, Cc): hay alerta si el
    paro sube y la puntuación (cambio − referencia) / escala supera el umbral.
    Con k = ⌊objetivo · N⌋, el umbral es el punto medio entre la k-ésima y la
    (k+1)-ésima puntuación más alta, para no quedar justo en un valor observado.
    """
    tabla = resultado.tabla
    seleccion = tabla["fecha"].dt.year.isin(anos).to_numpy() & es_evaluable(resultado)
    cambio = tabla["cambio_mensual"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        puntuacion = (cambio - tabla["referencia_cambio"].to_numpy(dtype=float)) / tabla["escala_robusta"].to_numpy(
            dtype=float
        )
    efectiva = np.sort(np.where(cambio > 0, puntuacion, -np.inf)[seleccion])[::-1]
    k = int(np.floor(tasa_objetivo_pct / 100 * len(efectiva) + 1e-9))
    if k == 0:
        return float(efectiva[0]) + 1.0
    return float((efectiva[k - 1] + efectiva[k]) / 2)


def con_umbral_fuera_de_muestra(resultado, tasa_objetivo_pct, clave, nombre, anos=ANOS_SELECCION):
    umbral = umbral_fuera_de_muestra(resultado, tasa_objetivo_pct, anos)
    return replace(resultado, clave=clave, nombre=nombre, umbral=umbral)


# A. Quasi-Poisson tipo Farrington -------------------------------------------

def ajustar_quasi_poisson(y, tiempo, iteraciones=100, tolerancia=1e-9):
    """Regresión de Poisson log(mu) = a + b · tiempo para muchas series a la vez.

    `y` tiene una fila por ajuste. Newton-Raphson (IRLS) vectorizado, con el
    paso limitado a 1 en escala logarítmica. Devuelve a, b, la sobredispersión
    sin truncar (X² de Pearson / (n - 2)), el elemento (0, 0) de la inversa de
    la matriz de información y si ha convergido.
    """
    y = np.asarray(y, dtype=float)
    tiempo = np.asarray(tiempo, dtype=float)[None, :]
    a = np.log(y.mean(axis=1))
    b = np.zeros(len(y))
    paso = np.full(len(y), np.inf)

    for _ in range(iteraciones):
        mu = np.exp(a[:, None] + b[:, None] * tiempo)
        residuo = y - mu
        u0 = residuo.sum(axis=1)
        u1 = (residuo * tiempo).sum(axis=1)
        i00 = mu.sum(axis=1)
        i01 = (mu * tiempo).sum(axis=1)
        i11 = (mu * tiempo**2).sum(axis=1)
        determinante = i00 * i11 - i01**2
        da = np.clip((i11 * u0 - i01 * u1) / determinante, -1, 1)
        db = np.clip((i00 * u1 - i01 * u0) / determinante, -1, 1)
        a, b = a + da, b + db
        paso = np.maximum(np.abs(da), np.abs(db))
        if np.all(paso < tolerancia):
            break

    mu = np.exp(a[:, None] + b[:, None] * tiempo)
    i00 = mu.sum(axis=1)
    i01 = (mu * tiempo).sum(axis=1)
    i11 = (mu * tiempo**2).sum(axis=1)
    covarianza_00 = i11 / (i00 * i11 - i01**2)
    phi_bruto = ((y - mu) ** 2 / mu).sum(axis=1) / (y.shape[1] - 2)
    converge = (paso < tolerancia) & np.isfinite(a) & np.isfinite(b) & np.isfinite(covarianza_00)
    return a, b, phi_bruto, covarianza_00, converge


def limite_farrington(mu0, phi, tau, z):
    """Límite superior de predicción de Farrington et al. (1996).

    Con la transformación de potencia 2/3:
    U = mu0 · (1 + (2/3) · z · ((phi · mu0 + Var(mu0)) / mu0²)^(1/2))^(3/2),
    con Var(mu0) = mu0² · tau.
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        return mu0 * (1 + (2 / 3) * np.asarray(z) * np.sqrt(phi / mu0 + tau)) ** 1.5


def metodo_a(paro, z=Z_FARRINGTON):
    """Quasi-Poisson con tendencia lineal sobre el nivel de paro (solo pasado).

    Para cada municipio y mes ajusta el paro del mismo mes y los contiguos de
    los 5 años anteriores (15 meses) y predice el mes evaluado. Hay alerta si el
    paro supera el límite y además sube respecto al mes anterior.
    """
    inicio = time.perf_counter()
    claves, niveles, cambios = a_matrices(paro)
    historicos = ventanas(niveles, DESFASES_ANUALES)
    tiempo = -np.asarray(DESFASES_ANUALES) / 12  # años respecto al mes evaluado

    completo = ~np.isnan(historicos).any(axis=2)
    ajustable = completo & (np.nansum(historicos, axis=2) > 0) & ~np.isnan(cambios)

    forma = niveles.shape
    mu0 = np.full(forma, np.nan)
    phi = np.full(forma, np.nan)
    tau = np.full(forma, np.nan)
    pendiente = np.full(forma, np.nan)
    converge = np.zeros(forma, dtype=bool)

    a, b, phi_bruto, covarianza_00, ok = ajustar_quasi_poisson(historicos[ajustable], tiempo)
    phi_ajuste = np.maximum(1.0, phi_bruto)
    mu0[ajustable] = np.exp(a)
    phi[ajustable] = phi_ajuste
    tau[ajustable] = phi_ajuste * covarianza_00
    pendiente[ajustable] = b
    converge[ajustable] = ok

    evaluacion = np.where(
        ~completo | np.isnan(cambios),
        "historial_insuficiente",
        np.where(~ajustable, "sin_paro_en_la_referencia", np.where(converge, EVALUABLE, "ajuste_no_converge")),
    )

    tabla = tabla_base(claves, niveles, cambios).assign(
        evaluacion=evaluacion.ravel(),
        prediccion_paro=mu0.ravel(),
        sobredispersion=phi.ravel(),
        varianza_predictor=tau.ravel(),
        tendencia_anual_log=pendiente.ravel(),
    )
    mu0_plano = tabla["prediccion_paro"].to_numpy()
    phi_plano = tabla["sobredispersion"].to_numpy()
    tau_plano = tabla["varianza_predictor"].to_numpy()
    anterior = tabla["paro_mes_anterior"].to_numpy()
    return Resultado(
        clave="A",
        nombre="A. Quasi-Poisson tipo Farrington sobre el nivel",
        tabla=tabla,
        umbral=z,
        # El paro supera U si y solo si el cambio supera U - paro del mes anterior.
        limite=lambda u: limite_farrington(mu0_plano, phi_plano, tau_plano, u) - anterior,
        segundos=time.perf_counter() - inicio,
    )


# B. Anomalía local frente al resto de la Comunidad --------------------------

def metodo_b(paro, umbral=UMBRAL_B):
    """Cambio del municipio frente al del resto de la Comunidad.

    Con los 60 meses anteriores estima la recta cambio_municipio = a + b ·
    cambio_resto por Theil-Sen (mediana de las pendientes entre pares) y la
    escala robusta de sus residuos (1,4826 × MAD). El resto excluye al propio
    municipio, para que Madrid no se explique a sí mismo. Hay alerta si el
    residuo del mes supera `umbral` escalas y el paro sube.
    """
    inicio = time.perf_counter()
    claves, niveles, cambios = a_matrices(paro)
    resto = cambios.sum(axis=0)[None, :] - cambios
    desfases = np.arange(1, MESES_B + 1)
    y_historico = ventanas(cambios, desfases)
    x_historico = ventanas(resto, desfases)
    completo = ~(np.isnan(y_historico).any(axis=2) | np.isnan(x_historico).any(axis=2))

    forma = niveles.shape
    ordenada = np.full(forma, np.nan)
    pendiente = np.full(forma, np.nan)
    mad = np.full(forma, np.nan)
    i, j = np.triu_indices(MESES_B, k=1)

    for m in range(forma[0]):
        meses = np.flatnonzero(completo[m])
        if not len(meses):
            continue
        y = y_historico[m, meses]
        x = x_historico[m, meses]
        dx = x[:, j] - x[:, i]
        with np.errstate(divide="ignore", invalid="ignore"):
            pendientes = np.where(dx != 0, (y[:, j] - y[:, i]) / dx, np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            b = np.nanmedian(pendientes, axis=1)
        a = np.median(y - b[:, None] * x, axis=1)
        residuos = y - a[:, None] - b[:, None] * x
        mad[m, meses] = np.median(np.abs(residuos - np.median(residuos, axis=1)[:, None]), axis=1)
        ordenada[m, meses] = a
        pendiente[m, meses] = b

    escala = detector.FACTOR_ESCALA * mad
    prediccion = ordenada + pendiente * resto
    evaluacion = np.where(
        ~completo | np.isnan(cambios),
        "historial_insuficiente",
        np.where(np.isnan(prediccion), "sin_ajuste", np.where(escala > 0, EVALUABLE, "dispersion_cero")),
    )

    tabla = tabla_base(claves, niveles, cambios).assign(
        evaluacion=evaluacion.ravel(),
        cambio_resto_comunidad=resto.ravel(),
        ordenada_b=ordenada.ravel(),
        pendiente_b=pendiente.ravel(),
        prediccion_cambio=prediccion.ravel(),
        escala_robusta=escala.ravel(),
    )
    prediccion_plana = tabla["prediccion_cambio"].to_numpy()
    escala_plana = tabla["escala_robusta"].to_numpy()
    return Resultado(
        clave="B",
        nombre="B. Anomalía local frente al resto de la Comunidad",
        tabla=tabla,
        umbral=umbral,
        limite=lambda u: prediccion_plana + np.asarray(u) * escala_plana,
        segundos=time.perf_counter() - inicio,
    )


# Métricas -------------------------------------------------------------------

def mascaras_periodos(tabla):
    ano = tabla["fecha"].dt.year
    mes = tabla["fecha"].dt.month
    return {
        "calma": ano.isin(val.ANOS_CALMA).to_numpy(),
        "mar_jun_2020": (ano.eq(val.ANO_EPISODIO) & mes.isin(val.MESES_EPISODIO)).to_numpy(),
        "abril_2020": (ano.eq(val.ANO_EPISODIO) & mes.eq(4)).to_numpy(),
        "inyeccion": ano.isin(val.ANOS_INYECCION).to_numpy(),
        "inyeccion_2017_2019": ano.isin(val.ANOS_CALMA).to_numpy(),
        "historico": tabla["fecha"].ge(val.INICIO).to_numpy(),
    }


def sufijo_periodo(periodo):
    return "" if periodo == "2015-2019" else "_" + periodo.replace("-", "_")


def deteccion_con_subidas(resultado, quintil_fila, umbral=None, subidas=val.SUBIDAS):
    """Tasa de detección de cada subida en los meses evaluables de 2015-2019 y
    de 2017-2019."""
    tabla = resultado.tabla
    mascaras = mascaras_periodos(tabla)
    evaluable = es_evaluable(resultado)
    filas = []
    for proporcion in subidas:
        subida = val.subida_en_personas(tabla["paro_mes_anterior"], proporcion).fillna(0).to_numpy()
        detectado = alertas_metodo(resultado, subida, umbral).fillna(False).to_numpy(dtype=bool)
        for periodo, mascara in PERIODOS_INYECCION.items():
            seleccion = mascaras[mascara] & evaluable
            for nombre in ["Todos"] + val.QUINTILES:
                filtro = seleccion if nombre == "Todos" else seleccion & (quintil_fila == nombre)
                filas.append(
                    {
                        "metodo": resultado.clave,
                        "periodo_inyeccion": periodo,
                        "subida_pct": 100 * proporcion,
                        "quintil": nombre,
                        "meses_evaluables": int(filtro.sum()),
                        "detectados": int((filtro & detectado).sum()),
                        "tasa_deteccion_pct": val.porcentaje((filtro & detectado).sum(), filtro.sum()),
                    }
                )
    return pd.DataFrame(filas)


def umbral_principal(resultado):
    """El umbral del método; para C, que lo calibra por n, el de 15 cambios."""
    umbral = np.asarray(resultado.umbral, dtype=float)
    if umbral.ndim == 0:
        return float(umbral)
    return float(np.nanmedian(umbral))


def resumen_metodo(resultado, quintil_fila, potencia):
    tabla = resultado.tabla
    periodos = mascaras_periodos(tabla)
    evaluable = es_evaluable(resultado)
    alerta = alertas_metodo(resultado).fillna(False).to_numpy(dtype=bool)
    paro = tabla["paro_total"].to_numpy()
    abril = periodos["abril_2020"]

    fila = {
        "metodo": resultado.clave,
        "descripcion": resultado.nombre,
        "umbral": umbral_principal(resultado),
        "segundos_calculo": resultado.segundos,
        "evaluables_calma": int((periodos["calma"] & evaluable).sum()),
        "alertas_calma": int((periodos["calma"] & alerta).sum()),
        "pct_alertas_calma": val.porcentaje((periodos["calma"] & alerta).sum(), (periodos["calma"] & evaluable).sum()),
        "alertas_mar_jun_2020": int((periodos["mar_jun_2020"] & alerta).sum()),
        "pct_alertas_mar_jun_2020": val.porcentaje(
            (periodos["mar_jun_2020"] & alerta).sum(), (periodos["mar_jun_2020"] & evaluable).sum()
        ),
        "alertas_abril_2020": int((abril & alerta).sum()),
        "evaluables_abril_2020": int((abril & evaluable).sum()),
        "pct_alertas_abril_2020": val.porcentaje((abril & alerta).sum(), (abril & evaluable).sum()),
        "pct_paro_comunidad_en_alerta_abril_2020": val.porcentaje(paro[abril & alerta].sum(), paro[abril].sum()),
    }

    for _, fila_potencia in potencia.loc[potencia["metodo"].eq(resultado.clave)].iterrows():
        sufijo = sufijo_periodo(fila_potencia["periodo_inyeccion"])
        if fila_potencia["quintil"] != "Todos":
            sufijo += f"_{fila_potencia['quintil']}"
        fila[f"potencia_{fila_potencia['subida_pct']:g}pct{sufijo}"] = fila_potencia["tasa_deteccion_pct"]

    historico = periodos["historico"]
    fila["pct_no_evaluables"] = val.porcentaje((historico & ~evaluable).sum(), historico.sum())
    for q in val.QUINTILES:
        filtro = historico & (quintil_fila == q)
        fila[f"pct_no_evaluables_{q}"] = val.porcentaje((filtro & ~evaluable).sum(), filtro.sum())

    caso = (tabla["municipio"].eq(MUNICIPIO_CASO) & tabla["fecha"].eq(FECHA_CASO)).to_numpy()
    limite = np.asarray(resultado.limite(resultado.umbral), dtype=float)
    limite = np.broadcast_to(limite, caso.shape)
    fila["madrid_oct_2026_cambio"] = float(tabla.loc[caso, "cambio_mensual"].iloc[0])
    fila["madrid_oct_2026_limite_cambio"] = float(limite[caso][0]) if evaluable[caso][0] else np.nan
    fila["madrid_oct_2026_alerta"] = alertas_metodo(resultado)[caso].iloc[0]
    return fila


def tabla_coincidencia(resultados):
    """Jaccard y kappa de Cohen entre pares de métodos, febrero de 2010 a octubre de 2026,
    en los municipio-mes evaluables por los dos."""
    filas = []
    for i, primero in enumerate(resultados):
        for segundo in resultados[i + 1 :]:
            comun = (
                mascaras_periodos(primero.tabla)["historico"]
                & es_evaluable(primero)
                & es_evaluable(segundo)
            )
            a = alertas_metodo(primero).fillna(False).to_numpy(dtype=bool)[comun]
            b = alertas_metodo(segundo).fillna(False).to_numpy(dtype=bool)[comun]
            n = len(a)
            ambos, solo_a, solo_b = int((a & b).sum()), int((a & ~b).sum()), int((~a & b).sum())
            ninguno = n - ambos - solo_a - solo_b
            observado = (ambos + ninguno) / n
            esperado = ((ambos + solo_a) * (ambos + solo_b) + (ninguno + solo_b) * (ninguno + solo_a)) / n**2
            filas.append(
                {
                    "metodo_1": primero.clave,
                    "metodo_2": segundo.clave,
                    "meses_evaluables_ambos": n,
                    "alertas_ambos": ambos,
                    "solo_metodo_1": solo_a,
                    "solo_metodo_2": solo_b,
                    "jaccard": ambos / (ambos + solo_a + solo_b) if (ambos + solo_a + solo_b) else np.nan,
                    "kappa_cohen": (observado - esperado) / (1 - esperado) if esperado < 1 else np.nan,
                }
            )
    return pd.DataFrame(filas)


def tabla_curvas(resultados, umbrales):
    """Tasa en calma, respuesta en 2020 y potencia (5 % y 10 %) de cada método
    al mover su umbral."""
    filas = []
    for resultado in resultados:
        tabla = resultado.tabla
        periodos = mascaras_periodos(tabla)
        evaluable = es_evaluable(resultado)
        calma = periodos["calma"] & evaluable
        episodio = periodos["mar_jun_2020"] & evaluable
        abril = periodos["abril_2020"] & evaluable
        inyeccion = {periodo: periodos[mascara] & evaluable for periodo, mascara in PERIODOS_INYECCION.items()}
        subidas = {
            p: val.subida_en_personas(tabla["paro_mes_anterior"], p).fillna(0).to_numpy() for p in (0.05, 0.10)
        }
        for umbral in umbrales:
            alerta = alertas_metodo(resultado, 0, umbral).fillna(False).to_numpy(dtype=bool)
            fila = {
                "metodo": resultado.clave,
                "umbral": umbral,
                "pct_alertas_calma": val.porcentaje((calma & alerta).sum(), calma.sum()),
                "pct_alertas_mar_jun_2020": val.porcentaje((episodio & alerta).sum(), episodio.sum()),
                "pct_alertas_abril_2020": val.porcentaje((abril & alerta).sum(), abril.sum()),
            }
            for p, subida in subidas.items():
                detectado = alertas_metodo(resultado, subida, umbral).fillna(False).to_numpy(dtype=bool)
                for periodo, seleccion in inyeccion.items():
                    fila[f"potencia_{100 * p:g}pct{sufijo_periodo(periodo)}"] = val.porcentaje(
                        (seleccion & detectado).sum(), seleccion.sum()
                    )
            filas.append(fila)
    return pd.DataFrame(filas)


def tabla_misma_tasa(curvas, objetivos):
    """Para cada método, el umbral con la mayor tasa en calma que no pasa de
    cada objetivo, y su respuesta en 2020 y su potencia con ese umbral.
    Compara los métodos con las mismas falsas alarmas."""
    filas = []
    for objetivo in objetivos:
        for metodo, curva in curvas.groupby("metodo", sort=False):
            candidatos = curva.loc[curva["pct_alertas_calma"].le(objetivo + 1e-9)]
            if candidatos.empty:
                continue
            fila = candidatos.loc[candidatos["pct_alertas_calma"].idxmax()]
            filas.append({"objetivo_pct_calma": objetivo, **fila.to_dict()})
    return pd.DataFrame(filas)


COLUMNAS_CASO = [
    "n_cambios",
    "referencia_cambio",
    "escala_robusta",
    "cambio_resto_comunidad",
    "prediccion_cambio",
    "prediccion_paro",
    "sobredispersion",
]


def tabla_caso(resultados, alertas):
    """Madrid en octubre de 2026 con cada método: cambio, límite y alerta."""
    caso = (alertas["municipio"].eq(MUNICIPIO_CASO) & alertas["fecha"].eq(FECHA_CASO)).to_numpy()
    filas = []
    for resultado in resultados:
        fila = con_alertas(resultado).loc[caso].iloc[0]
        umbral = np.broadcast_to(np.asarray(resultado.umbral, dtype=float), caso.shape)[caso][0]
        datos = {
            "metodo": resultado.clave,
            "municipio": fila["municipio"],
            "fecha": fila["fecha"],
            "paro_total": fila["paro_total"],
            "cambio_mensual": fila["cambio_mensual"],
            "evaluacion": fila["evaluacion"],
            "umbral": umbral,
            "limite_cambio": fila["limite_cambio"],
            "alerta": fila["alerta"],
        }
        for columna in COLUMNAS_CASO:
            if columna in fila.index:
                datos[columna] = fila[columna]
        filas.append(datos)
    return pd.DataFrame(filas)


def tabla_umbrales_fuera_de_muestra(resultados, tasa_objetivo_pct):
    """Umbral elegido en 2012-2016 y la tasa que da en esos años."""
    filas = []
    for resultado in resultados:
        pct, evaluables, alertas_seleccion = tasa_alertas(resultado, ANOS_SELECCION)
        filas.append(
            {
                "metodo": resultado.clave,
                "anos_seleccion": f"{ANOS_SELECCION[0]}-{ANOS_SELECCION[-1]}",
                "tasa_objetivo_pct": tasa_objetivo_pct,
                "umbral": umbral_principal(resultado),
                "evaluables_seleccion": evaluables,
                "alertas_seleccion": alertas_seleccion,
                "pct_alertas_seleccion": pct,
            }
        )
    return pd.DataFrame(filas)


COLUMNAS_CRITERIO = ["pct_alertas_mar_jun_2020", "pct_alertas_abril_2020", "potencia_5pct", "potencia_10pct"]


def tabla_criterio(curvas):
    """Para cada método, el umbral con menos alertas en calma que el oficial
    que iguala o mejora su respuesta en 2020 (marzo-junio y abril) y su
    potencia (5 % y 10 %). Sin fila si ningún umbral de la rejilla lo cumple."""
    oficial = curvas.loc[curvas["metodo"].eq("oficial") & curvas["umbral"].eq(val.UMBRAL_OFICIAL)].iloc[0]
    filas = [{"metodo": "oficial", "cumple": "referencia", **oficial.drop("metodo").to_dict()}]
    for metodo, curva in curvas.loc[curvas["metodo"].ne("oficial")].groupby("metodo", sort=False):
        cumplen = curva.loc[
            (curva[COLUMNAS_CRITERIO].to_numpy() >= oficial[COLUMNAS_CRITERIO].to_numpy(dtype=float)).all(axis=1)
            & curva["pct_alertas_calma"].lt(oficial["pct_alertas_calma"])
        ]
        if cumplen.empty:
            filas.append({"metodo": metodo, "cumple": "no"})
        else:
            mejor = cumplen.loc[cumplen["pct_alertas_calma"].idxmin()]
            filas.append({"metodo": metodo, "cumple": "sí", **mejor.drop("metodo").to_dict()})
    return pd.DataFrame(filas)


def clasificar_alertas(oficial, metodo_b_resultado, fecha=None):
    """Alertas oficiales como «local» o «regional» según B; las de un mes si se indica.

    Local: B también marca el mes (la subida supera lo esperable dado el cambio
    del resto de la Comunidad). Regional: B no lo marca. El estado oficial no
    cambia: es una etiqueta de contraste.
    """
    oficial_tabla = con_alertas(oficial)
    b_tabla = con_alertas(metodo_b_resultado)
    seleccion = oficial_tabla["alerta"].eq(True).fillna(False)
    if fecha is not None:
        seleccion &= oficial_tabla["fecha"].eq(fecha)
    tabla = oficial_tabla.loc[seleccion, ["municipio", "fecha", "paro_total", "cambio_mensual", "limite_cambio"]].rename(
        columns={"limite_cambio": "limite_oficial"}
    )
    tabla = tabla.merge(
        b_tabla[
            [
                "municipio",
                "fecha",
                "evaluacion",
                "cambio_resto_comunidad",
                "pendiente_b",
                "prediccion_cambio",
                "escala_robusta",
                "limite_cambio",
                "alerta",
            ]
        ].rename(
            columns={
                "evaluacion": "evaluacion_b",
                "prediccion_cambio": "prediccion_cambio_b",
                "escala_robusta": "escala_b",
                "limite_cambio": "limite_b",
                "alerta": "alerta_b",
            }
        ),
        on=["municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )
    tabla["puntuacion_b"] = (tabla["cambio_mensual"] - tabla["prediccion_cambio_b"]) / tabla["escala_b"]
    tabla["clasificacion"] = np.where(
        tabla["evaluacion_b"].ne(EVALUABLE),
        "sin clasificar (B no evaluable)",
        np.where(tabla["alerta_b"].eq(True).fillna(False), "local", "regional"),
    )
    if fecha is not None:
        return tabla.sort_values("cambio_mensual", ascending=False).reset_index(drop=True)
    return tabla.sort_values(["municipio", "fecha"]).reset_index(drop=True)


# Columnas de la clasificación que se publica para la aplicación.
COLUMNAS_CLASIFICACION_APP = [
    "municipio",
    "fecha",
    "cambio_mensual",
    "cambio_resto_comunidad",
    "prediccion_cambio_b",
    "limite_b",
    "puntuacion_b",
    "clasificacion",
]

# Métodos alternativos que muestra la ficha de la aplicación, con el nombre de
# su columna en otros_metodos.csv. C y Cc, con el umbral elegido fuera de
# muestra: dan un número de alertas comparable al oficial.
METODOS_APP = {"Cc_fm": "c_centrado", "C_fm": "c_ampliado", "A": "farrington", "B": "local_b"}


def tabla_otros_metodos(resultados):
    """Alerta de cada método alternativo por municipio y mes, en forma compacta:
    1 alerta, 0 sin alerta, vacío si el método no puede evaluar el mes."""
    por_clave = {r.clave: r for r in resultados}
    tabla = por_clave["oficial"].tabla[["municipio", "fecha"]].copy()
    for clave, columna in METODOS_APP.items():
        tabla[columna] = alertas_metodo(por_clave[clave]).astype("Int64")
    return tabla


# Figura ---------------------------------------------------------------------

COLORES = {
    "oficial": val.AZUL,
    "C5": val.AZUL,
    "C": val.NARANJA,
    "Cc": MAGENTA,
    "A": val.AGUA,
    "B": AMARILLO,
    "C_fm": val.NARANJA,
    "Cc_fm": MAGENTA,
}
MARCADORES = {"oficial": "o", "C5": "D", "C": "o", "Cc": "o", "A": "o", "B": "o", "C_fm": "o", "Cc_fm": "o"}
ETIQUETAS = {
    "oficial": "Oficial",
    "C5": "C5",
    "C": "C",
    "Cc": "Cc",
    "A": "A",
    "B": "B",
    "C_fm": "C fuera de muestra",
    "Cc_fm": "Cc fuera de muestra",
}
HUECOS = {"C_fm", "Cc_fm"}
DESPLAZAMIENTOS = {"C_fm": (-8, 8), "Cc_fm": (8, -3), "oficial": (8, -14)}


def figura_potencia_frente_a_calma(resumen, curvas):
    plt = val.importar_pyplot()
    from matplotlib.ticker import FuncFormatter

    porcentaje_es = FuncFormatter(lambda v, _: f"{v:g} %".replace(".", ","))
    fig, ejes = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True)

    for eje, subida in zip(ejes, ["5", "10"]):
        columna = f"potencia_{subida}pct_2017_2019"
        for metodo in ["oficial", "C", "Cc", "A", "B"]:
            curva = curvas.loc[curvas["metodo"].eq(metodo) & curvas["pct_alertas_calma"].gt(0)]
            nombre_curva = "Oficial y C5 (misma referencia)" if metodo == "oficial" else ETIQUETAS[metodo]
            eje.plot(
                curva["pct_alertas_calma"],
                curva[columna],
                color=COLORES[metodo],
                lw=1.2,
                alpha=0.6,
                label=f"{nombre_curva}: al mover el umbral",
            )
        for _, fila in resumen.iterrows():
            metodo = fila["metodo"]
            x, y = fila["pct_alertas_calma"], fila[columna]
            hueco = metodo in HUECOS
            eje.plot(
                x,
                y,
                marker=MARCADORES[metodo],
                markersize=8,
                color=COLORES[metodo],
                markerfacecolor="white" if hueco else COLORES[metodo],
                markeredgecolor=COLORES[metodo] if hueco else "white",
                markeredgewidth=2 if hueco else 1.2,
                ls="none",
                zorder=5,
            )
            dx, dy = DESPLAZAMIENTOS.get(metodo, (6, 4))
            eje.annotate(
                ETIQUETAS[metodo],
                (x, y),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="right" if dx < 0 else "left",
                fontsize=9,
                color=val.TINTA,
                zorder=6,
            )
        eje.set_xscale("log")
        eje.set_xlim(0.02, 30)
        eje.set_ylim(0, 100)
        eje.xaxis.set_major_formatter(porcentaje_es)
        eje.yaxis.set_major_formatter(porcentaje_es)
        eje.set_xlabel("% de alertas en calma, 2017-2019 (escala logarítmica)")
        eje.set_title(f"Subida del {subida} %", fontsize=11)
        eje.grid(axis="x", color="#e4e3df", lw=0.8)

    ejes[0].set_ylabel("Sensibilidad: meses de 2017-2019 con la subida sintética detectada")
    ejes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(
        "Sensibilidad ante subidas sintéticas frente a alertas en calma: arriba a la izquierda es mejor",
        x=0.01,
        ha="left",
        fontsize=12,
        fontweight="bold",
    )
    fig.text(
        0.01,
        -0.03,
        "Puntos llenos: cada método con su umbral por defecto. Puntos huecos: umbral elegido en 2012-2016 "
        "(misma tasa que el oficial en esos años). Líneas: el mismo método con otros umbrales.\n"
        "Fuente: resultados/validacion/resumen_metodos.csv y curvas_metodos.csv",
        fontsize=8,
        color=val.TINTA_SECUNDARIA,
    )
    fig.tight_layout()
    val.guardar_figura(fig, "potencia_frente_a_calma.png")
    plt.close(fig)


# Programa -------------------------------------------------------------------

def main():
    inicio_total = time.perf_counter()
    alertas, ruta_alertas = val.leer_alertas()
    paro, ruta_paro = val.leer_serie(alertas, ruta_alertas)
    print(f"Alertas: {ruta_alertas.relative_to(val.RAIZ)}")
    print(f"Serie de paro: {ruta_paro.relative_to(val.RAIZ)}")
    val.SALIDA.mkdir(parents=True, exist_ok=True)

    print("\nCalibrando el umbral por número de cambios (simulación normal)...", flush=True)
    inicio = time.perf_counter()
    umbrales = tabla_umbrales_calibrados()
    segundos_calibrado = time.perf_counter() - inicio
    print(f"  {segundos_calibrado:.1f} s")
    val.guardar_csv(umbrales, "umbrales_calibrados.csv")
    de_c = umbrales.loc[umbrales["metodo"].eq("C")]
    umbrales_n = dict(zip(de_c["n_cambios"], de_c["umbral_calibrado"]))
    umbral_cc = float(umbrales.loc[umbrales["metodo"].eq("Cc"), "umbral_calibrado"].iloc[0])

    print("\nCalculando los métodos:", flush=True)
    oficial = metodo_oficial(alertas)
    if not val.mismas_alertas(alertas_metodo(oficial), alertas["alerta_experimental"]):
        raise ValueError("El método oficial no reproduce las alertas de alertas.csv.")
    subida_5 = val.subida_en_personas(alertas["paro_mes_anterior"], 0.05).fillna(0)
    if not val.mismas_alertas(alertas_metodo(oficial, subida_5.to_numpy()), val.alerta_con_subida(alertas, subida_5)):
        raise ValueError("La inyección del método oficial no coincide con la de validar_detector.py.")

    c5 = metodo_oficial(
        alertas,
        umbral=umbrales_n[detector.MIN_OBSERVACIONES],
        clave="C5",
        nombre="C5. Oficial (5 cambios) con umbral calibrado",
    )
    resultados = [oficial, c5]
    for funcion, argumentos in [
        (metodo_c, (paro, umbrales_n)),
        (metodo_c_centrado, (paro, umbral_cc)),
        (metodo_a, (paro,)),
        (metodo_b, (paro,)),
    ]:
        resultado = funcion(*argumentos)
        print(f"  {resultado.nombre}: {resultado.segundos:.1f} s", flush=True)
        resultados.append(resultado)

    # Umbral fuera de muestra: la tasa del oficial (umbral 3) en 2012-2016.
    por_clave = {r.clave: r for r in resultados}
    tasa_objetivo, _, _ = tasa_alertas(oficial, ANOS_SELECCION)
    fuera_de_muestra = [
        con_umbral_fuera_de_muestra(
            por_clave["C"], tasa_objetivo, "C_fm", "C con umbral elegido en 2012-2016 (fuera de muestra)"
        ),
        con_umbral_fuera_de_muestra(
            por_clave["Cc"], tasa_objetivo, "Cc_fm", "Cc con umbral elegido en 2012-2016 (fuera de muestra)"
        ),
    ]
    resultados += fuera_de_muestra
    val.guardar_csv(
        tabla_umbrales_fuera_de_muestra([oficial] + fuera_de_muestra, tasa_objetivo),
        "umbrales_fuera_de_muestra.csv",
    )

    claves = ["municipio", "fecha"]
    for resultado in resultados:
        if not resultado.tabla[claves].equals(oficial.tabla[claves]):
            raise ValueError(f"El método {resultado.clave} no tiene las mismas filas que alertas.csv.")
        if not np.array_equal(
            resultado.tabla["cambio_mensual"].to_numpy(), oficial.tabla["cambio_mensual"].to_numpy(), equal_nan=True
        ):
            raise ValueError(f"El método {resultado.clave} no usa los mismos cambios que alertas.csv.")

    quintiles = val.quintiles_tamano(alertas)
    quintil_fila = (
        oficial.tabla[["municipio"]]
        .merge(quintiles[["municipio", "quintil"]], on="municipio", how="left", validate="many_to_one")["quintil"]
        .to_numpy()
    )

    print("\nComparando:")
    potencia = pd.concat([deteccion_con_subidas(r, quintil_fila) for r in resultados], ignore_index=True)
    resumen = pd.DataFrame([resumen_metodo(r, quintil_fila, potencia) for r in resultados])
    resumen.insert(
        4,
        "segundos_calibrado_umbral",
        [segundos_calibrado if r.clave in ("C5", "C", "Cc") else np.nan for r in resultados],
    )
    val.guardar_csv(resumen, "resumen_metodos.csv")
    val.guardar_csv(potencia, "potencia_metodos.csv")
    val.guardar_csv(tabla_coincidencia(resultados), "coincidencia_metodos.csv")

    comparacion = oficial.tabla[claves].copy()
    for resultado in resultados:
        comparacion[f"alerta_{resultado.clave}"] = alertas_metodo(resultado).to_numpy()
    val.guardar_csv(comparacion, "comparacion_metodos.csv")

    # C5, C_fm y Cc_fm son puntos de las curvas del oficial, C y Cc.
    metodos_curva = [r for r in resultados if r.clave not in ("C5", "C_fm", "Cc_fm")]
    rejilla = np.round(np.concatenate([np.arange(0.5, 10, 0.05), np.arange(10, 60.5, 0.5)]), 2)
    curvas = tabla_curvas(metodos_curva, rejilla)
    val.guardar_csv(curvas, "curvas_metodos.csv")
    objetivos = [100 * P_OBJETIVO, 0.5, 1.0, 2.0, float(resumen.loc[resumen["metodo"].eq("oficial"), "pct_alertas_calma"].iloc[0])]
    val.guardar_csv(tabla_misma_tasa(curvas, objetivos), "comparacion_misma_tasa.csv")
    criterio = tabla_criterio(curvas)
    val.guardar_csv(criterio, "criterio_comparacion.csv")

    val.guardar_csv(tabla_caso(resultados, alertas), "madrid_octubre_2026_metodos.csv")
    metodo_b_resultado = next(r for r in resultados if r.clave == "B")
    val.guardar_csv(
        clasificar_alertas(oficial, metodo_b_resultado, FECHA_CLASIFICACION), "clasificacion_octubre_2026.csv"
    )
    clasificacion = clasificar_alertas(oficial, metodo_b_resultado)
    val.guardar_csv(clasificacion[COLUMNAS_CLASIFICACION_APP], "clasificacion_local_regional.csv")
    val.guardar_csv(tabla_otros_metodos(resultados), "otros_metodos.csv")

    print("\nFigura")
    figura_potencia_frente_a_calma(resumen, curvas)

    print(
        f"\nComparación terminada en {time.perf_counter() - inicio_total:.0f} s. "
        "El detector y resultados/alertas.csv no se han modificado."
    )


if __name__ == "__main__":
    main()
