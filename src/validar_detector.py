"""Validación del detector oficial de alertas, sin cambiarlo.

Lee resultados/alertas.csv (o, si no está, la copia de datos/publicados/) y la
serie de paro total de datos/procesados/ (o, si no está, la de alertas.csv).
Recalcula variantes con las funciones de src/detectar_alertas.py y escribe sus
resultados en resultados/validacion/: CSV con separador «;» y utf-8-sig, y
figuras PNG. No modifica el detector, sus parámetros ni resultados/alertas.csv.

Ningún cálculo de detección usa información futura: cada mes se compara solo
con el mismo mes de años anteriores, como en el detector oficial. Los quintiles
de tamaño (paro medio de 2019) y los umbrales calibrados en 2017-2019 son
descriptivos: no intervienen en ninguna detección.

Resultados explicados en docs/validacion.md.
"""

import math
from contextlib import contextmanager

import numpy as np
import pandas as pd

import detectar_alertas as detector


RAIZ = detector.RAIZ
RUTA_ALERTAS_PUBLICADAS = RAIZ / "datos" / "publicados" / "alertas.csv"
SALIDA = RAIZ / "resultados" / "validacion"

# Parámetros oficiales, leídos del detector para no copiarlos.
VENTANA_OFICIAL = detector.VENTANA_ANOS
UMBRAL_OFICIAL = detector.UMBRAL

EVALUABLES = ["alerta_experimental", "sin_alerta"]
ESTADOS = EVALUABLES + detector.ESTADOS_NO_EVALUABLES

# 1. Primer mes evaluable con la ventana oficial: febrero de 2010 tiene los
#    cambios de febrero de 2005 a 2009. Enero de 2010 aún no es evaluable.
INICIO = pd.Timestamp("2010-02-01")

# 2. Periodo de calma.
ANOS_CALMA = [2017, 2018, 2019]
OBJETIVOS_CALMA = [0.01, 0.02, 0.05]
REPETICIONES_SIMULACION = 1_000_000
SEMILLA = 2026

# 3. Episodio de 2020.
ANO_EPISODIO = 2020
MESES_EPISODIO = [3, 4, 5, 6]
NOMBRES_MESES = {3: "marzo", 4: "abril", 5: "mayo", 6: "junio"}

# 4. Inyección sintética.
ANOS_INYECCION = [2015, 2016, 2017, 2018, 2019]
SUBIDAS = [0.01, 0.02, 0.05, 0.10]
ANO_TAMANO = 2019
QUINTILES = ["Q1", "Q2", "Q3", "Q4", "Q5"]

# 5. Sensibilidad. La ventana exige historial completo, como la oficial
#    (5 años y mínimo de 5 cambios): con 3 años, 3 cambios; con 7, 7.
VENTANAS = [3, 5, 7]
UMBRALES = [2.5, 3.0, 3.5]
SUBIDA_SENSIBILIDAD = 0.05

# Colores (paleta validada para daltonismo de la guía de visualización).
AZUL = "#2a78d6"
NARANJA = "#eb6834"
AGUA = "#1baf7a"
GRIS = "#8a8984"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
SOMBRA_CALMA = "#e4e3df"
SOMBRA_2020 = "#fbd9c9"
RAMPA_QUINTILES = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]


# Lectura ------------------------------------------------------------------

def leer_alertas():
    if detector.RUTA_ALERTAS.is_file():
        ruta = detector.RUTA_ALERTAS
    else:
        ruta = RUTA_ALERTAS_PUBLICADAS
        detector.comprobar_archivo(ruta)

    alertas = pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
        dtype={
            "paro_mes_anterior": "Int64",
            "cambio_mensual": "Int64",
            "alerta_experimental": "boolean",
        },
    )
    alertas = alertas.sort_values(["municipio", "fecha"]).reset_index(drop=True)
    return alertas, ruta


def leer_serie(alertas, ruta_alertas):
    """Paro total mensual: datos/procesados/ o, si no está, el de alertas.csv."""
    if detector.RUTA_PARO.is_file():
        return detector.leer_paro(), detector.RUTA_PARO

    paro = alertas[["municipio", "fecha", "paro_total"]].copy()
    return paro, ruta_alertas


# Detector con otros parámetros -------------------------------------------

@contextmanager
def parametros_detector(ventana, umbral):
    """Cambia los parámetros del detector solo dentro del bloque.

    aplicar_detector() lee VENTANA_ANOS, MIN_OBSERVACIONES y UMBRAL del módulo
    al ejecutarse, así que basta con cambiarlos en memoria. El archivo
    src/detectar_alertas.py no se modifica y los valores se restauran siempre.
    """
    originales = (detector.VENTANA_ANOS, detector.MIN_OBSERVACIONES, detector.UMBRAL)
    detector.VENTANA_ANOS = ventana
    detector.MIN_OBSERVACIONES = ventana
    detector.UMBRAL = umbral
    try:
        yield
    finally:
        detector.VENTANA_ANOS, detector.MIN_OBSERVACIONES, detector.UMBRAL = originales


def mismas_alertas(a, b):
    """Mismos valores y mismas celdas vacías, sea cual sea el tipo de columna."""
    a = pd.Series(a).reset_index(drop=True)
    b = pd.Series(b).reset_index(drop=True)
    vacias = a.isna()
    if len(a) != len(b) or not vacias.equals(b.isna()):
        return False
    return bool((a[~vacias].astype(object) == b[~vacias].astype(object)).all())


def aplicar_variante(paro, ventana, umbral):
    with parametros_detector(ventana, umbral):
        resultado = detector.aplicar_detector(paro)
    return resultado.sort_values(["municipio", "fecha"]).reset_index(drop=True)


def comprobar_reproduce_oficial(oficial, alertas):
    """El detector recalculado con los parámetros oficiales da alertas.csv."""
    claves = ["municipio", "fecha"]
    if not oficial[claves].equals(alertas[claves]):
        raise ValueError("alertas.csv no tiene los mismos municipios y meses que la serie.")

    if not oficial["paro_total"].astype(float).equals(alertas["paro_total"].astype(float)):
        raise ValueError(
            "El paro de alertas.csv no coincide con la serie procesada. "
            "Ejecuta de nuevo src/detectar_alertas.py."
        )

    if not mismas_alertas(oficial["estado_detector"], alertas["estado_detector"]):
        raise ValueError("El detector recalculado no reproduce estado_detector de alertas.csv.")

    if not mismas_alertas(oficial["alerta_experimental"], alertas["alerta_experimental"]):
        raise ValueError("El detector recalculado no reproduce alerta_experimental de alertas.csv.")

    for columna in ["referencia_cambio", "escala_robusta", "limite_superior", "puntuacion_robusta"]:
        if not np.allclose(
            oficial[columna].astype(float),
            alertas[columna].astype(float),
            rtol=1e-12,
            atol=0,
            equal_nan=True,
        ):
            raise ValueError(f"El detector recalculado no reproduce {columna} de alertas.csv.")


# Inyección sintética --------------------------------------------------------

def subida_en_personas(paro_mes_anterior, proporcion):
    """Subida artificial: proporción del paro del mes anterior en personas.

    Se redondea al entero más próximo, con las mitades hacia arriba. Vacía si
    no hay mes anterior.
    """
    base = pd.to_numeric(pd.Series(paro_mes_anterior), errors="coerce").astype(float)
    return np.floor(proporcion * base + 0.5)


def alerta_con_subida(resultado, subida, umbral=None):
    """Alerta del detector si al cambio mensual se le suman `subida` personas.

    Solo cambia el mes evaluado: la referencia, la escala y que el mes sea
    evaluable dependen únicamente de años anteriores, así que se toman del
    resultado del detector. La regla es la suya: cambio mensual > 0 y
    puntuación robusta > umbral. Los meses no evaluables quedan vacíos.
    """
    if umbral is None:
        umbral = detector.UMBRAL

    subida = pd.Series(subida, index=resultado.index).astype(float)
    evaluable = resultado["estado_detector"].isin(EVALUABLES)

    if subida[evaluable].isna().any():
        raise ValueError("Hay meses evaluables sin subida definida.")

    cambio = resultado["cambio_mensual"].astype(float) + subida
    puntuacion = (cambio - resultado["referencia_cambio"]) / resultado["escala_robusta"]

    alerta = pd.Series(pd.NA, index=resultado.index, dtype="boolean")
    alerta[evaluable] = cambio[evaluable].gt(0) & puntuacion[evaluable].gt(umbral)
    return alerta


def serie_con_subidas(paro, subida):
    """Paro con `subida` personas sumadas al cambio mensual de cada mes.

    Desplaza el nivel desde ese mes en adelante, así que el cambio de los demás
    meses no varía. `paro` debe estar ordenado por municipio y fecha.
    """
    desplazamiento = (
        pd.Series(subida, index=paro.index)
        .fillna(0)
        .groupby(paro["municipio"])
        .cumsum()
    )
    inyectado = paro.copy()
    inyectado["paro_total"] = paro["paro_total"] + desplazamiento
    return inyectado


def comprobar_inyeccion_con_detector(paro, oficial, ano=2019, proporcion=SUBIDA_SENSIBILIDAD):
    """La inyección rápida coincide con ejecutar el detector sobre la serie alterada.

    Se suma la subida a todos los meses de un año a la vez: la referencia de
    cada uno usa solo años anteriores, que no se tocan.
    """
    en_ano = oficial["fecha"].dt.year.eq(ano)
    subida = subida_en_personas(oficial["paro_mes_anterior"], proporcion).where(en_ano, 0)

    rapido = alerta_con_subida(oficial, subida)
    completo = detector.aplicar_detector(serie_con_subidas(paro, subida))
    completo = completo.sort_values(["municipio", "fecha"]).reset_index(drop=True)

    if not mismas_alertas(rapido[en_ano], completo.loc[en_ano, "alerta_experimental"]):
        raise ValueError("La inyección no coincide con el detector ejecutado sobre la serie alterada.")

    return int(en_ano.sum()), int(rapido[en_ano].sum())


# Utilidades -----------------------------------------------------------------

def porcentaje(parte, total):
    parte = np.asarray(parte, dtype=float)
    total = np.asarray(total, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        resultado = np.where(total > 0, 100 * parte / total, np.nan)
    return resultado.item() if resultado.ndim == 0 else resultado


def es_evaluable(tabla):
    return tabla["estado_detector"].isin(EVALUABLES)


def es_alerta(tabla):
    return tabla["estado_detector"].eq("alerta_experimental")


def guardar_csv(tabla, nombre):
    ruta = SALIDA / nombre
    tabla.to_csv(
        ruta,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
        na_rep="",
    )
    print(f"  Generado: resultados/validacion/{nombre}")
    return ruta


def quintiles_tamano(alertas):
    """Quintiles de los 179 municipios por su paro medio de 2019.

    Los empates se deshacen por orden alfabético (rank «first»).
    """
    paro_medio = (
        alertas.loc[alertas["fecha"].dt.year.eq(ANO_TAMANO)]
        .groupby("municipio")["paro_total"]
        .mean()
        .rename(f"paro_medio_{ANO_TAMANO}")
    )
    quintil = pd.qcut(paro_medio.rank(method="first"), len(QUINTILES), labels=QUINTILES)
    tabla = paro_medio.to_frame().assign(quintil=quintil.astype(str)).reset_index()
    return tabla.sort_values([f"paro_medio_{ANO_TAMANO}", "municipio"]).reset_index(drop=True)


# 1. Comportamiento histórico -----------------------------------------------

def resumen_mensual(alertas):
    periodo = alertas.loc[alertas["fecha"].ge(INICIO)]
    conteo = pd.crosstab(periodo["fecha"], periodo["estado_detector"]).reindex(
        columns=ESTADOS, fill_value=0
    )

    tabla = pd.DataFrame(
        {
            "fecha": conteo.index,
            "municipios": conteo.sum(axis=1).to_numpy(),
            "evaluables": (conteo["alerta_experimental"] + conteo["sin_alerta"]).to_numpy(),
            "con_alerta": conteo["alerta_experimental"].to_numpy(),
            "sin_alerta": conteo["sin_alerta"].to_numpy(),
            "no_evaluables_dispersion_cero": conteo["dispersion_cero"].to_numpy(),
            "no_evaluables_historial_insuficiente": conteo["historial_insuficiente"].to_numpy(),
        }
    )
    tabla["pct_alertas_evaluables"] = porcentaje(tabla["con_alerta"], tabla["evaluables"])
    return tabla


def resumen_anual(mensual):
    anual = (
        mensual.assign(ano=mensual["fecha"].dt.year)
        .groupby("ano", as_index=False)
        .agg(
            meses=("fecha", "count"),
            evaluables=("evaluables", "sum"),
            con_alerta=("con_alerta", "sum"),
            no_evaluables_dispersion_cero=("no_evaluables_dispersion_cero", "sum"),
            no_evaluables_historial_insuficiente=("no_evaluables_historial_insuficiente", "sum"),
        )
    )
    anual["pct_alertas_evaluables"] = porcentaje(anual["con_alerta"], anual["evaluables"])
    return anual


# 2. Falsas alarmas en calma ------------------------------------------------

def en_calma(tabla):
    return tabla["fecha"].dt.year.isin(ANOS_CALMA)


def simular_normal(n_observaciones, umbral, repeticiones=REPETICIONES_SIMULACION, semilla=SEMILLA):
    """Proporción de puntuaciones > umbral con datos normales independientes.

    Cada repetición: n cambios históricos y uno nuevo, todos N(0, 1); la
    referencia y la escala se estiman como en el detector (mediana y
    1,4826 × MAD de los n históricos). El resultado no depende de la media ni
    de la desviación típica.
    """
    rng = np.random.default_rng(semilla)
    valores = rng.standard_normal((repeticiones, n_observaciones + 1))
    historicos, nuevo = valores[:, :n_observaciones], valores[:, n_observaciones]
    mediana = np.median(historicos, axis=1)
    mad = np.median(np.abs(historicos - mediana[:, None]), axis=1)
    puntuacion = (nuevo - mediana) / (detector.FACTOR_ESCALA * mad)
    return float(np.mean(puntuacion > umbral)), puntuacion


def puntuacion_efectiva(tabla):
    """Puntuación que decide la alerta: −inf si el paro no sube."""
    return (
        tabla["puntuacion_robusta"]
        .astype(float)
        .where(tabla["cambio_mensual"].astype(float).gt(0), -np.inf)
        .to_numpy()
    )


def falsas_alarmas_calma(alertas, simulado):
    calma = alertas.loc[en_calma(alertas) & es_evaluable(alertas)]
    n = len(calma)
    n_alertas = int(es_alerta(calma).sum())
    pct_alertas = porcentaje(n_alertas, n)
    teorico = 100 * 0.5 * math.erfc(UMBRAL_OFICIAL / math.sqrt(2))
    puntuacion = calma["puntuacion_robusta"].astype(float)
    mad_pequena = calma["mad_cambio"].astype(float).le(1)

    filas = [
        ("meses_evaluables", n, "Municipio-mes evaluables de 2017 a 2019"),
        ("alertas", n_alertas, "Alertas experimentales en esos meses"),
        ("pct_alertas_evaluables", pct_alertas, "% de alertas entre evaluables"),
        (
            "pct_teorico_normal",
            teorico,
            "P(Z > 3) con normalidad y referencia y escala conocidas",
        ),
        (
            "pct_simulado_normal_5_observaciones",
            100 * simulado,
            "% de puntuaciones > 3 con datos normales y mediana y MAD de 5 observaciones "
            f"(simulación: {numero_es(REPETICIONES_SIMULACION)} repeticiones, semilla {SEMILLA})",
        ),
        ("cociente_observado_teorico", pct_alertas / teorico, "Observado / teórico"),
        ("cociente_observado_simulado", pct_alertas / (100 * simulado), "Observado / simulado"),
        (
            "pct_puntuacion_mayor_3",
            porcentaje(puntuacion.gt(3).sum(), n),
            "% de evaluables con puntuación > 3, suba o no el paro",
        ),
        (
            "pct_puntuacion_menor_menos_3",
            porcentaje(puntuacion.lt(-3).sum(), n),
            "% de evaluables con puntuación < −3 (cola inferior)",
        ),
        (
            "puntuacion_mediana_evaluables",
            float(puntuacion.median()),
            "Mediana de la puntuación robusta; con referencia sin sesgo sería cercana a 0",
        ),
        (
            "pct_evaluables_mad_hasta_1",
            porcentaje(mad_pequena.sum(), n),
            "% de evaluables con MAD de 1 persona o menos",
        ),
        (
            "pct_alertas_mad_hasta_1",
            porcentaje(es_alerta(calma)[mad_pequena].sum(), mad_pequena.sum()),
            "% de alertas entre evaluables con MAD de 1 persona o menos",
        ),
        (
            "pct_alertas_mad_mayor_1",
            porcentaje(es_alerta(calma)[~mad_pequena].sum(), (~mad_pequena).sum()),
            "% de alertas entre evaluables con MAD mayor de 1 persona",
        ),
    ]
    return pd.DataFrame(filas, columns=["medida", "valor", "descripcion"])


def umbrales_calma(alertas):
    """Umbral que daría un 1 %, 2 % y 5 % de alertas en 2017-2019.

    Con k = ⌊p · N⌋, el umbral es la (k+1)-ésima puntuación efectiva más alta;
    hay alerta si la puntuación lo supera estrictamente, como en el detector.
    Es una calibración dentro de la muestra: solo informa.
    """
    calma = alertas.loc[en_calma(alertas) & es_evaluable(alertas)]
    efectiva = puntuacion_efectiva(calma)
    n = len(efectiva)
    ordenada = np.sort(efectiva)[::-1]

    filas = []
    for objetivo in OBJETIVOS_CALMA:
        k = int(np.floor(objetivo * n + 1e-9))
        umbral = float(ordenada[k])
        n_alertas = int((efectiva > umbral).sum())
        filas.append(("calibrado", 100 * objetivo, umbral, n, n_alertas, porcentaje(n_alertas, n)))

    n_oficial = int((efectiva > UMBRAL_OFICIAL).sum())
    filas.append(("oficial", np.nan, UMBRAL_OFICIAL, n, n_oficial, porcentaje(n_oficial, n)))

    return pd.DataFrame(
        filas,
        columns=[
            "tipo",
            "objetivo_pct",
            "umbral",
            "meses_evaluables",
            "alertas",
            "pct_alertas_obtenido",
        ],
    )


def tasa_por_umbral(alertas, puntuacion_simulada, umbrales):
    calma = alertas.loc[en_calma(alertas) & es_evaluable(alertas)]
    efectiva = puntuacion_efectiva(calma)
    puntuacion = calma["puntuacion_robusta"].astype(float).to_numpy()
    filas = []
    for umbral in umbrales:
        filas.append(
            {
                "umbral": umbral,
                "pct_alertas_calma": 100 * np.mean(efectiva > umbral),
                "pct_puntuacion_mayor_umbral_calma": 100 * np.mean(puntuacion > umbral),
                "pct_simulado_normal_5_observaciones": 100 * np.mean(puntuacion_simulada > umbral),
                "pct_teorico_normal": 100 * 0.5 * math.erfc(umbral / math.sqrt(2)),
            }
        )
    return pd.DataFrame(filas)


# 3. Episodio de 2020 --------------------------------------------------------

def episodio_2020(alertas):
    anos = ANOS_CALMA + [ANO_EPISODIO]
    datos = alertas.loc[
        alertas["fecha"].dt.year.isin(anos) & alertas["fecha"].dt.month.isin(MESES_EPISODIO)
    ].assign(
        ano=lambda t: t["fecha"].dt.year,
        mes=lambda t: t["fecha"].dt.month,
        evaluable=es_evaluable,
        alerta=es_alerta,
    )
    datos["paro_en_alerta"] = datos["paro_total"].where(datos["alerta"], 0)

    por_ano = datos.groupby(["mes", "ano"], as_index=False).agg(
        evaluables=("evaluable", "sum"),
        con_alerta=("alerta", "sum"),
        paro_comunidad=("paro_total", "sum"),
        paro_municipios_en_alerta=("paro_en_alerta", "sum"),
        cambio_paro_comunidad=("cambio_mensual", "sum"),
    )

    filas = []
    for mes in MESES_EPISODIO:
        del_mes = por_ano.loc[por_ano["mes"].eq(mes)]
        for _, fila in del_mes.iterrows():
            filas.append(
                {
                    "mes": mes,
                    "nombre_mes": NOMBRES_MESES[mes],
                    "periodo": str(int(fila["ano"])),
                    "evaluables": fila["evaluables"],
                    "con_alerta": fila["con_alerta"],
                    "pct_alertas_evaluables": porcentaje(fila["con_alerta"], fila["evaluables"]),
                    "paro_comunidad": fila["paro_comunidad"],
                    "paro_municipios_en_alerta": fila["paro_municipios_en_alerta"],
                    "pct_paro_comunidad_en_alerta": porcentaje(
                        fila["paro_municipios_en_alerta"], fila["paro_comunidad"]
                    ),
                    "cambio_paro_comunidad": fila["cambio_paro_comunidad"],
                }
            )

        calma = del_mes.loc[del_mes["ano"].isin(ANOS_CALMA)]
        filas.append(
            {
                "mes": mes,
                "nombre_mes": NOMBRES_MESES[mes],
                "periodo": "2017-2019 (media anual; % agregados)",
                "evaluables": calma["evaluables"].mean(),
                "con_alerta": calma["con_alerta"].mean(),
                "pct_alertas_evaluables": porcentaje(calma["con_alerta"].sum(), calma["evaluables"].sum()),
                "paro_comunidad": calma["paro_comunidad"].mean(),
                "paro_municipios_en_alerta": calma["paro_municipios_en_alerta"].mean(),
                "pct_paro_comunidad_en_alerta": porcentaje(
                    calma["paro_municipios_en_alerta"].sum(), calma["paro_comunidad"].sum()
                ),
                "cambio_paro_comunidad": calma["cambio_paro_comunidad"].mean(),
            }
        )

    tabla = pd.DataFrame(filas)
    orden = {p: i for i, p in enumerate([str(a) for a in ANOS_CALMA] + ["2017-2019 (media anual; % agregados)", str(ANO_EPISODIO)])}
    tabla["_orden"] = tabla["periodo"].map(orden)
    return tabla.sort_values(["mes", "_orden"]).drop(columns="_orden").reset_index(drop=True)


# 4. Inyección sintética -----------------------------------------------------

def tabla_potencia(alertas, quintiles):
    datos = alertas.merge(quintiles[["municipio", "quintil"]], on="municipio", how="left", validate="many_to_one")
    seleccion = datos["fecha"].dt.year.isin(ANOS_INYECCION) & es_evaluable(datos)
    alerta_previa = es_alerta(datos)

    filas = []
    for proporcion in [0.0] + SUBIDAS:
        subida = subida_en_personas(datos["paro_mes_anterior"], proporcion)
        detectado = alerta_con_subida(datos, subida).fillna(False).astype(bool)

        grupos = [("Todos", seleccion)] + [(q, seleccion & datos["quintil"].eq(q)) for q in QUINTILES]
        for nombre, filtro in grupos:
            sin_previa = filtro & ~alerta_previa
            filas.append(
                {
                    "subida_pct": 100 * proporcion,
                    "quintil": nombre,
                    "municipios": datos.loc[filtro, "municipio"].nunique(),
                    "meses_evaluables": int(filtro.sum()),
                    "meses_subida_nula": int((filtro & subida.eq(0)).sum()),
                    "subida_mediana_personas": float(subida[filtro].median()),
                    "alertas_sin_subida": int((filtro & alerta_previa).sum()),
                    "detectados": int((filtro & detectado).sum()),
                    "tasa_deteccion_pct": porcentaje((filtro & detectado).sum(), filtro.sum()),
                    "meses_sin_alerta_previa": int(sin_previa.sum()),
                    "detectados_sin_alerta_previa": int((sin_previa & detectado).sum()),
                    "tasa_deteccion_sin_alerta_previa_pct": porcentaje(
                        (sin_previa & detectado).sum(), sin_previa.sum()
                    ),
                }
            )
    return pd.DataFrame(filas)


# 5. Sensibilidad ------------------------------------------------------------

def inicio_comun(variantes):
    """Primer mes desde el que ninguna variante tiene historial insuficiente."""
    inicio = INICIO
    for resultado in variantes.values():
        insuficiente = resultado.loc[resultado["estado_detector"].eq("historial_insuficiente"), "fecha"]
        if len(insuficiente):
            inicio = max(inicio, insuficiente.max() + pd.offsets.MonthBegin(1))
    return inicio


def tabla_sensibilidad(variantes):
    oficial = variantes[(VENTANA_OFICIAL, UMBRAL_OFICIAL)]
    desde = inicio_comun(variantes)
    clave = ["municipio", "fecha"]

    def conjunto_alertas(resultado):
        filtro = resultado["fecha"].ge(desde) & es_alerta(resultado)
        return set(map(tuple, resultado.loc[filtro, clave].to_numpy()))

    alertas_oficial = conjunto_alertas(oficial)

    filas = []
    for (ventana, umbral), resultado in variantes.items():
        evaluable = es_evaluable(resultado)
        alerta = es_alerta(resultado)
        ano = resultado["fecha"].dt.year
        mes = resultado["fecha"].dt.month

        calma = ano.isin(ANOS_CALMA)
        episodio = ano.eq(ANO_EPISODIO) & mes.isin(MESES_EPISODIO)
        mismos_meses_calma = calma & mes.isin(MESES_EPISODIO)
        inyeccion = ano.isin(ANOS_INYECCION) & evaluable

        subida = subida_en_personas(resultado["paro_mes_anterior"], SUBIDA_SENSIBILIDAD)
        detectado = alerta_con_subida(resultado, subida, umbral=umbral).fillna(False).astype(bool)

        propias = conjunto_alertas(resultado)
        union = propias | alertas_oficial
        comunes = propias & alertas_oficial

        filas.append(
            {
                "ventana_anos": ventana,
                "umbral": umbral,
                "oficial": "sí" if (ventana, umbral) == (VENTANA_OFICIAL, UMBRAL_OFICIAL) else "no",
                "pct_evaluables_calma": porcentaje((calma & evaluable).sum(), calma.sum()),
                "pct_alertas_calma": porcentaje((calma & alerta).sum(), (calma & evaluable).sum()),
                "alertas_mar_jun_2020": int((episodio & alerta).sum()),
                "pct_alertas_mar_jun_2020": porcentaje((episodio & alerta).sum(), (episodio & evaluable).sum()),
                "pct_alertas_mar_jun_2017_2019": porcentaje(
                    (mismos_meses_calma & alerta).sum(), (mismos_meses_calma & evaluable).sum()
                ),
                "alertas_abril_2020": int((episodio & mes.eq(4) & alerta).sum()),
                "potencia_subida_5_pct": porcentaje((inyeccion & detectado).sum(), inyeccion.sum()),
                "potencia_subida_5_pct_sin_alerta_previa": porcentaje(
                    (inyeccion & ~alerta & detectado).sum(), (inyeccion & ~alerta).sum()
                ),
                "periodo_comun_desde": desde,
                "alertas_periodo_comun": len(propias),
                "alertas_oficial_periodo_comun": len(alertas_oficial),
                "alertas_coincidentes": len(comunes),
                "jaccard_con_oficial": len(comunes) / len(union) if union else np.nan,
            }
        )
    return pd.DataFrame(filas)


# 6. Municipios pequeños -----------------------------------------------------

def tabla_municipios_pequenos(alertas, quintiles):
    datos = alertas.loc[alertas["fecha"].ge(INICIO)].merge(
        quintiles, on="municipio", how="left", validate="many_to_one"
    )
    columna_tamano = f"paro_medio_{ANO_TAMANO}"

    filas = []
    for quintil in QUINTILES:
        grupo = datos.loc[datos["quintil"].eq(quintil)]
        con_historial = grupo["estado_detector"].ne("historial_insuficiente")
        evaluable = es_evaluable(grupo)
        alerta = es_alerta(grupo)
        calma = en_calma(grupo)
        de_alertas = grupo.loc[alerta]
        filas.append(
            {
                "quintil": quintil,
                "municipios": grupo["municipio"].nunique(),
                f"{columna_tamano}_min": grupo[columna_tamano].min(),
                f"{columna_tamano}_max": grupo[columna_tamano].max(),
                "meses_municipio": len(grupo),
                "meses_con_historial": int(con_historial.sum()),
                "meses_dispersion_cero": int(grupo["estado_detector"].eq("dispersion_cero").sum()),
                "pct_dispersion_cero": porcentaje(
                    grupo["estado_detector"].eq("dispersion_cero").sum(), con_historial.sum()
                ),
                "meses_evaluables": int(evaluable.sum()),
                "alertas": int(alerta.sum()),
                "pct_alertas_evaluables": porcentaje(alerta.sum(), evaluable.sum()),
                "pct_alertas_evaluables_calma": porcentaje((alerta & calma).sum(), (evaluable & calma).sum()),
                "puntuacion_mediana_alertas": float(de_alertas["puntuacion_robusta"].median()),
                "cambio_mediano_alertas_personas": float(de_alertas["cambio_mensual"].astype(float).median()),
            }
        )
    return pd.DataFrame(filas)


# 7. Persistencia ------------------------------------------------------------

def tabla_persistencia(alertas):
    datos = alertas.copy()
    datos["estado_siguiente"] = datos.groupby("municipio")["estado_detector"].shift(-1)
    datos["alerta"] = es_alerta(datos)
    datos["evaluable"] = es_evaluable(datos)
    # Mes siguiente evaluable en el mismo municipio, para la tasa base.
    datos["siguiente_evaluable"] = datos["estado_siguiente"].isin(EVALUABLES)
    datos["siguiente_alerta"] = datos["estado_siguiente"].eq("alerta_experimental")

    ano = datos["fecha"].dt.year
    mes = datos["fecha"].dt.month
    base = datos["fecha"].ge(INICIO) & datos["estado_siguiente"].notna() & datos["evaluable"]

    periodos = [
        ("Febrero de 2010 a septiembre de 2026", base),
        (
            "Sin marzo a junio de 2020",
            base & ~(ano.eq(ANO_EPISODIO) & mes.isin(MESES_EPISODIO)),
        ),
        ("2017-2019", base & ano.isin(ANOS_CALMA)),
    ]

    filas = []
    for nombre, filtro in periodos:
        con_alerta = filtro & datos["alerta"]
        sin_alerta = filtro & ~datos["alerta"]
        repetidas = con_alerta & datos["siguiente_alerta"]
        filas.append(
            {
                "periodo_mes_de_la_alerta": nombre,
                "alertas_con_mes_siguiente": int(con_alerta.sum()),
                "siguiente_con_alerta": int(repetidas.sum()),
                "siguiente_sin_alerta": int((con_alerta & datos["estado_siguiente"].eq("sin_alerta")).sum()),
                "siguiente_no_evaluable": int((con_alerta & ~datos["siguiente_evaluable"]).sum()),
                "pct_repetidas": porcentaje(repetidas.sum(), con_alerta.sum()),
                "pct_repetidas_entre_siguientes_evaluables": porcentaje(
                    repetidas.sum(), (con_alerta & datos["siguiente_evaluable"]).sum()
                ),
                "pct_alerta_siguiente_tras_mes_sin_alerta": porcentaje(
                    (sin_alerta & datos["siguiente_alerta"]).sum(),
                    (sin_alerta & datos["siguiente_evaluable"]).sum(),
                ),
            }
        )
    return pd.DataFrame(filas)


def tabla_rachas(alertas):
    """Rachas de meses consecutivos con alerta en el mismo municipio."""
    datos = alertas.loc[alertas["fecha"].ge(INICIO)].copy()
    datos["alerta"] = es_alerta(datos)
    inicio_racha = datos["alerta"] & ~datos.groupby("municipio")["alerta"].shift(1, fill_value=False)
    datos["racha"] = inicio_racha.cumsum().where(datos["alerta"])
    longitudes = datos.dropna(subset=["racha"]).groupby("racha").size()
    tabla = longitudes.value_counts().sort_index().rename_axis("meses_seguidos").reset_index(name="rachas")
    tabla["alertas"] = tabla["meses_seguidos"] * tabla["rachas"]
    tabla["pct_rachas"] = porcentaje(tabla["rachas"], tabla["rachas"].sum())
    return tabla


# Figuras --------------------------------------------------------------------

def importar_pyplot():
    # matplotlib solo hace falta para las figuras (requirements-dev.txt).
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.edgecolor": GRIS,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "axes.titlecolor": TINTA,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": TINTA_SECUNDARIA,
            "ytick.color": TINTA_SECUNDARIA,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": "#e4e3df",
            "grid.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "legend.frameon": False,
        }
    )
    return plt


def numero_es(valor, decimales=0):
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def guardar_figura(fig, nombre):
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    print(f"  Generado: resultados/validacion/{nombre}")


def figura_alertas_por_mes(mensual):
    plt = importar_pyplot()
    from matplotlib.ticker import MaxNLocator

    fig, ax = plt.subplots(figsize=(11, 4.4))
    medio_mes = pd.Timedelta(days=15)

    ax.axvspan(pd.Timestamp("2017-01-01") - medio_mes, pd.Timestamp("2019-12-01") + medio_mes, color=SOMBRA_CALMA, lw=0, zorder=0)
    ax.axvspan(pd.Timestamp("2020-03-01") - medio_mes, pd.Timestamp("2020-06-01") + medio_mes, color=SOMBRA_2020, lw=0, zorder=0)

    ax.plot(mensual["fecha"], mensual["con_alerta"], color=AZUL, lw=1.6, zorder=3)

    techo = mensual["con_alerta"].max() * 1.12
    ax.set_ylim(0, techo)
    ax.text(pd.Timestamp("2018-07-01"), techo * 0.97, "Calma\n2017-2019", ha="center", va="top", fontsize=9, color=TINTA_SECUNDARIA)
    ax.text(pd.Timestamp("2020-07-15"), techo * 0.97, "Marzo-junio\n2020", ha="left", va="top", fontsize=9, color=TINTA_SECUNDARIA)

    ax.set_xlim(mensual["fecha"].min() - medio_mes, mensual["fecha"].max() + medio_mes)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel("Municipios con alerta experimental")
    ax.set_title(
        "Municipios con alerta experimental por mes, febrero de 2010 a octubre de 2026",
        pad=12,
    )
    evaluables = f"{numero_es(mensual['evaluables'].min())} y {numero_es(mensual['evaluables'].max())}"
    fig.text(
        0.01,
        -0.02,
        f"Detector oficial (ventana de 5 años, umbral 3). Cada mes hay entre {evaluables} municipios evaluables de 179. "
        "Fuente: resultados/validacion/validacion_mensual.csv",
        fontsize=8,
        color=TINTA_SECUNDARIA,
    )
    guardar_figura(fig, "alertas_por_mes.png")
    plt.close(fig)


def figura_potencia(potencia):
    plt = importar_pyplot()
    from matplotlib.ticker import FuncFormatter

    fig, ax = plt.subplots(figsize=(8.5, 5))
    subidas = sorted(potencia["subida_pct"].unique())

    series = [(q, color, 1.6) for q, color in zip(QUINTILES, RAMPA_QUINTILES)] + [("Todos", TINTA, 2.2)]
    for nombre, color, grosor in series:
        datos = potencia.loc[potencia["quintil"].eq(nombre)].sort_values("subida_pct")
        etiqueta = "Todos los municipios" if nombre == "Todos" else nombre
        ax.plot(
            datos["subida_pct"],
            datos["tasa_deteccion_pct"],
            color=color,
            lw=grosor,
            marker="o",
            markersize=5,
            markeredgecolor="white",
            markeredgewidth=1,
            label=etiqueta,
            zorder=4 if nombre == "Todos" else 3,
        )

    ax.set_xticks(subidas)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g} %".replace(".", ",")))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g} %".replace(".", ",")))
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.3, max(subidas) + 0.3)
    ax.set_xlabel("Subida artificial sumada al cambio mensual (% del paro del mes anterior)")
    ax.set_ylabel("Meses evaluables marcados con alerta")
    ax.set_title("Curvas de potencia del detector oficial, meses evaluables de 2015 a 2019", pad=12)
    ax.legend(title="Quintil de paro medio de 2019\n(Q1, municipios más pequeños)", loc="upper left", fontsize=9, title_fontsize=9)
    fig.text(
        0.01,
        -0.03,
        "Con subida 0 % se ve la tasa de alertas sin inyección. Fuente: resultados/validacion/potencia.csv",
        fontsize=8,
        color=TINTA_SECUNDARIA,
    )
    guardar_figura(fig, "curvas_potencia.png")
    plt.close(fig)


def figura_tasa_por_umbral(tasas):
    plt = importar_pyplot()
    from matplotlib.ticker import FuncFormatter

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(tasas["umbral"], tasas["pct_alertas_calma"], color=AZUL, lw=2, label="Observado 2017-2019: alertas (el paro sube)")
    ax.plot(
        tasas["umbral"],
        tasas["pct_puntuacion_mayor_umbral_calma"],
        color=AGUA,
        lw=2,
        label="Observado 2017-2019: puntuación > umbral, suba o no",
    )
    ax.plot(
        tasas["umbral"],
        tasas["pct_simulado_normal_5_observaciones"],
        color=NARANJA,
        lw=2,
        label="Normal, mediana y MAD de 5 observaciones (simulación)",
    )
    ax.plot(tasas["umbral"], tasas["pct_teorico_normal"], color=GRIS, lw=1.6, ls="--", label="Normal, referencia y escala conocidas")
    ax.axvline(UMBRAL_OFICIAL, color=TINTA_SECUNDARIA, lw=1, ls=":")
    ax.text(UMBRAL_OFICIAL + 0.08, 60, "Umbral oficial: 3", fontsize=9, color=TINTA_SECUNDARIA, va="center")

    ax.set_yscale("log")
    ax.set_ylim(0.01, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g} %".replace(".", ",")))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.set_xlabel("Umbral de la puntuación robusta")
    ax.set_ylabel("% de meses evaluables por encima del umbral (escala logarítmica)")
    ax.set_title("Meses por encima de cada umbral en calma (2017-2019) y con datos normales", pad=12)
    ax.legend(loc="lower right", fontsize=9)
    fig.text(
        0.01,
        -0.03,
        "Las simulaciones no exigen que el paro suba: se comparan con la curva verde. "
        "Fuente: resultados/validacion/tasa_alertas_segun_umbral.csv",
        fontsize=8,
        color=TINTA_SECUNDARIA,
    )
    guardar_figura(fig, "tasa_alertas_segun_umbral.png")
    plt.close(fig)


# Programa -------------------------------------------------------------------

def main():
    alertas, ruta_alertas = leer_alertas()
    paro, ruta_paro = leer_serie(alertas, ruta_alertas)
    print(f"Alertas: {ruta_alertas.relative_to(RAIZ)}")
    print(f"Serie de paro: {ruta_paro.relative_to(RAIZ)}")

    SALIDA.mkdir(parents=True, exist_ok=True)

    print("\nRecalculando el detector con cada ventana y umbral:")
    variantes = {}
    for ventana in VENTANAS:
        for umbral in UMBRALES:
            print(f"  ventana {ventana} años, umbral {umbral}", flush=True)
            variantes[(ventana, umbral)] = aplicar_variante(paro, ventana, umbral)

    oficial = variantes[(VENTANA_OFICIAL, UMBRAL_OFICIAL)]
    comprobar_reproduce_oficial(oficial, alertas)
    print("El detector recalculado con los parámetros oficiales reproduce alertas.csv.")

    meses, detectados = comprobar_inyeccion_con_detector(paro, oficial)
    print(
        "La inyección coincide con el detector ejecutado sobre la serie alterada "
        f"(2019, subida del 5 %: {detectados} alertas en {meses} municipio-mes)."
    )

    quintiles = quintiles_tamano(alertas)

    print("\n1. Comportamiento histórico")
    mensual = resumen_mensual(alertas)
    guardar_csv(mensual, "validacion_mensual.csv")
    guardar_csv(resumen_anual(mensual), "validacion_anual.csv")

    print("2. Falsas alarmas en calma")
    simulado, puntuacion_simulada = simular_normal(detector.MIN_OBSERVACIONES, UMBRAL_OFICIAL)
    guardar_csv(falsas_alarmas_calma(alertas, simulado), "calma_2017_2019.csv")
    guardar_csv(umbrales_calma(alertas), "umbrales_calma.csv")
    tasas = tasa_por_umbral(alertas, puntuacion_simulada, np.round(np.arange(0, 10.01, 0.1), 1))
    guardar_csv(tasas, "tasa_alertas_segun_umbral.csv")

    print("3. Episodio de 2020")
    guardar_csv(episodio_2020(alertas), "episodio_2020.csv")

    print("4. Inyección sintética")
    potencia = tabla_potencia(alertas, quintiles)
    guardar_csv(potencia, "potencia.csv")
    guardar_csv(quintiles, "quintiles_tamano.csv")

    print("5. Sensibilidad")
    guardar_csv(tabla_sensibilidad(variantes), "sensibilidad.csv")

    print("6. Municipios pequeños")
    guardar_csv(tabla_municipios_pequenos(alertas, quintiles), "municipios_pequenos.csv")

    print("7. Persistencia")
    guardar_csv(tabla_persistencia(alertas), "persistencia.csv")
    guardar_csv(tabla_rachas(alertas), "rachas_alertas.csv")

    print("\nFiguras")
    figura_alertas_por_mes(mensual)
    figura_tasa_por_umbral(tasas)
    figura_potencia(potencia)

    print("\nValidación terminada. El detector y resultados/alertas.csv no se han modificado.")


if __name__ == "__main__":
    main()
