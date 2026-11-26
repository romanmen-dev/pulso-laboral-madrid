"""Datos y textos de la pestaña «¿Cómo sabemos que funciona?».

Solo lee los CSV de resultados/validacion/ (o su copia en datos/publicados/)
que escriben src/validar_detector.py y src/comparar_metodos.py, y resume lo que
ya está calculado. No recalcula el detector ni la validación, y no contiene
código de Streamlit. Los resultados completos están en docs/validacion.md.
"""

import math

import pandas as pd

from src import datos_app as datos


URL_REPOSITORIO = "https://github.com/romanmen-dev/pulso-laboral-madrid/blob/main"
URL_METODOLOGIA = f"{URL_REPOSITORIO}/docs/metodologia.md"
URL_VALIDACION = f"{URL_REPOSITORIO}/docs/validacion.md"

ANOS_CALMA = [2017, 2018, 2019]
FECHA_EPISODIO = pd.Timestamp("2020-04-01")

# Lo que se esperaría en calma con datos normales y referencia y escala
# exactas: P(Z > 3).
PCT_TEORICO = 100 * 0.5 * math.erfc(3 / math.sqrt(2))

# Puntos de la figura de métodos (claves de resumen_metodos.csv) y la curva
# de curvas_metodos.csv a la que pertenece cada uno.
METODOS_FIGURA = {
    "oficial": "Oficial",
    "Cc_fm": "C centrado (propuesta v2)",
    "C_fm": "C ampliado",
    "A": "Farrington (A)",
    "B": "Local frente a la Comunidad (B)",
}
CURVA_DE = {"oficial": "oficial", "Cc_fm": "Cc", "C_fm": "C", "A": "A", "B": "B"}

METODO_V2 = "Cc_fm"
QUINTILES = ["Q1", "Q2", "Q3", "Q4", "Q5"]
NOMBRES_QUINTIL = {
    "Q1": "Q1 · 20 % con menos paro",
    "Q2": "Q2",
    "Q3": "Q3",
    "Q4": "Q4",
    "Q5": "Q5 · 20 % con más paro",
    "Todos": "Todos los municipios",
}


def porcentaje(valor, decimales=1):
    return datos.porcentaje(valor, decimales, signo=False)


# ---------------------------------------------------------------
# Alertas por mes y episodio de 2020
# ---------------------------------------------------------------

def alertas_por_mes(mensual):
    """Alertas y municipios evaluables por mes, con los textos del gráfico."""
    tabla = mensual[["fecha", "evaluables", "con_alerta", "pct_alertas_evaluables"]].copy()
    tabla["texto"] = [
        f"{datos.nombre_mes(f)}: {datos.numero(a)} municipios con alerta de "
        f"{datos.numero(e)} evaluables ({porcentaje(p)})"
        for f, a, e, p in zip(
            tabla["fecha"], tabla["con_alerta"], tabla["evaluables"], tabla["pct_alertas_evaluables"]
        )
    ]
    return tabla


def episodio_abril_2020(mensual):
    """Abril de 2020 frente a los abriles de 2017-2019 (porcentajes agregados)."""
    abril = mensual.loc[mensual["fecha"].dt.month.eq(FECHA_EPISODIO.month)]
    episodio = abril.loc[abril["fecha"].eq(FECHA_EPISODIO)].iloc[0]
    normales = abril.loc[abril["fecha"].dt.year.isin(ANOS_CALMA)]
    return {
        "alertas": int(episodio["con_alerta"]),
        "evaluables": int(episodio["evaluables"]),
        "pct": 100 * episodio["con_alerta"] / episodio["evaluables"],
        "pct_normales": 100 * normales["con_alerta"].sum() / normales["evaluables"].sum(),
    }


def frase_abril_2020(episodio):
    return (
        f"En abril de 2020 saltó la alerta en el **{porcentaje(episodio['pct'])}** de los "
        f"municipios evaluables ({datos.numero(episodio['alertas'])} de "
        f"{datos.numero(episodio['evaluables'])}), frente al **{porcentaje(episodio['pct_normales'])}** "
        "en los abriles normales (2017-2019)."
    )


def tasa_calma(mensual):
    """% de alertas entre los meses evaluables de 2017-2019."""
    calma = mensual.loc[mensual["fecha"].dt.year.isin(ANOS_CALMA)]
    return 100 * calma["con_alerta"].sum() / calma["evaluables"].sum()


# ---------------------------------------------------------------
# Potencia por tamaño de municipio
# ---------------------------------------------------------------

def potencia_por_tamano(potencia):
    """Tasa de detección por subida y quintil de tamaño (2015-2019)."""
    tabla = potencia[["subida_pct", "quintil", "tasa_deteccion_pct", "meses_evaluables"]].copy()
    tabla["nombre"] = tabla["quintil"].map(NOMBRES_QUINTIL)
    return tabla


def tabla_potencia_ancha(potencia):
    """La tabla del gráfico de potencia: una fila por subida, una columna por quintil."""
    tabla = potencia.pivot(index="subida_pct", columns="quintil", values="tasa_deteccion_pct")
    tabla = tabla[["Todos"] + QUINTILES]
    vista = pd.DataFrame({"Subida": [f"{datos.numero(s)} %" for s in tabla.index]})
    for columna in tabla.columns:
        vista[NOMBRES_QUINTIL[columna]] = [porcentaje(valor) for valor in tabla[columna]]
    return vista


def deteccion(potencia, subida_pct, quintil="Todos"):
    fila = potencia.loc[potencia["subida_pct"].eq(subida_pct) & potencia["quintil"].eq(quintil)]
    return float(fila["tasa_deteccion_pct"].iloc[0])


# ---------------------------------------------------------------
# Comparación de métodos
# ---------------------------------------------------------------

def puntos_metodos(resumen):
    """Cada método con su umbral: tasa en calma y potencia en 2017-2019."""
    tabla = resumen.loc[resumen["metodo"].isin(METODOS_FIGURA)].copy()
    tabla["nombre"] = tabla["metodo"].map(METODOS_FIGURA)
    tabla["orden"] = tabla["metodo"].map({m: i for i, m in enumerate(METODOS_FIGURA)})
    return tabla.sort_values("orden").reset_index(drop=True)


def curvas_metodos(curvas):
    """Curva de cada método al mover el umbral (sin los puntos con 0 % en calma,
    que no caben en un eje logarítmico)."""
    metodos = set(CURVA_DE.values())
    tabla = curvas.loc[curvas["metodo"].isin(metodos) & curvas["pct_alertas_calma"].gt(0)].copy()
    return tabla.sort_values(["metodo", "pct_alertas_calma"]).reset_index(drop=True)


def fila_metodo(resumen, metodo):
    return resumen.loc[resumen["metodo"].eq(metodo)].iloc[0]


def frase_compromiso(resumen):
    oficial = fila_metodo(resumen, "oficial")
    v2 = fila_metodo(resumen, METODO_V2)
    return (
        "Cada línea es un método al mover su umbral: un umbral más bajo detecta más "
        "subidas, pero también da más alertas en calma, que son casi todas falsas "
        "alarmas. Un método es mejor si su línea queda más arriba con las mismas "
        "falsas alarmas. Con casi las mismas alertas en calma que el oficial "
        f"({porcentaje(v2['pct_alertas_calma'])} frente a {porcentaje(oficial['pct_alertas_calma'])}), "
        f"C centrado detecta el {porcentaje(v2['potencia_5pct_2017_2019'])} de las subidas del 5 % "
        f"(el oficial, el {porcentaje(oficial['potencia_5pct_2017_2019'])}). El método B detecta "
        "más subidas locales, pero no reacciona a una crisis que afecta a toda la Comunidad, "
        "como la de 2020."
    )


# ---------------------------------------------------------------
# Limitaciones medidas y propuesta de versión 2
# ---------------------------------------------------------------

def limitaciones(mensual, resumen, potencia):
    oficial = fila_metodo(resumen, "oficial")
    return [
        (
            f"**Alertas en calma.** En 2017-2019 salta la alerta en el {porcentaje(tasa_calma(mensual))} "
            "de los meses evaluables, cuando con datos normales y una referencia exacta se "
            f"esperaría un {porcentaje(PCT_TEORICO, 3)}. La causa principal es estimar la "
            "dispersión con solo 5 cambios. Por eso, una alerta pide revisar, no confirma nada."
        ),
        (
            "**Municipios pequeños.** En el 20 % de municipios con menos paro, el "
            f"{porcentaje(oficial['pct_no_evaluables_Q1'])} de los meses no se puede evaluar "
            "(dispersión cero), y una subida del 10 % se detecta solo en el "
            f"{porcentaje(deteccion(potencia, 10.0, 'Q1'))} de los meses: con pocas personas en "
            "paro, la información no da para más."
        ),
        (
            f"**Subidas moderadas.** Una subida de un mes del 5 % se detecta en el "
            f"{porcentaje(deteccion(potencia, 5.0))} de los meses, y una del 10 %, en el "
            f"{porcentaje(deteccion(potencia, 10.0))}."
        ),
        (
            "**Sin verdad de referencia.** No hay una lista de anomalías municipales "
            "confirmadas: se mide cuántas alertas da el detector y si detecta subidas "
            "añadidas a mano, no su acierto."
        ),
    ]


def tabla_propuesta_v2(resumen):
    """Oficial frente a la propuesta de versión 2, con el umbral elegido fuera de muestra."""
    oficial = fila_metodo(resumen, "oficial")
    v2 = fila_metodo(resumen, METODO_V2)
    medidas = [
        ("Alertas en calma, 2017-2019 (menos es mejor)", "pct_alertas_calma"),
        ("Alertas en marzo-junio de 2020", "pct_alertas_mar_jun_2020"),
        ("Alertas en abril de 2020", "pct_alertas_abril_2020"),
        ("Subidas del 5 % detectadas, 2017-2019", "potencia_5pct_2017_2019"),
        ("Subidas del 10 % detectadas, 2017-2019", "potencia_10pct_2017_2019"),
        ("Meses no evaluables", "pct_no_evaluables"),
    ]
    return pd.DataFrame(
        {
            "Medida": [nombre for nombre, _ in medidas],
            "Oficial": [porcentaje(oficial[c]) for _, c in medidas],
            "Propuesta v2 (C centrado)": [porcentaje(v2[c]) for _, c in medidas],
        }
    )


def frase_propuesta_v2(resumen):
    v2 = fila_metodo(resumen, METODO_V2)
    return (
        "**Propuesta para una versión 2: C centrado.** Mantiene el cambio habitual del "
        "detector oficial (la mediana del mismo mes en los 5 años anteriores), pero mide "
        "la dispersión con 15 cambios: el mismo mes y los dos contiguos, cada uno "
        "centrado en la mediana de su mes. El umbral, "
        f"{datos.numero(v2['umbral'], 2)}, se eligió con 2012-2016 para dar las mismas "
        "alertas que el oficial en esos años, y se evaluó después en 2017-2019 y 2020. Con "
        "casi las mismas falsas alarmas, detecta más. No reduce las falsas alarmas y solo "
        "se ha comprobado en tres años de calma y un episodio, así que no sustituye todavía "
        "al detector oficial."
    )
