"""Lectura y preparación de datos para la aplicación Streamlit.

Este módulo no contiene código de interfaz ni recalcula el detector:
lee resultados/alertas.csv, cuyo formato fija docs/contrato_alertas.md,
y las tablas de datos/procesados/.
"""

import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
PROCESADOS = RAIZ / "datos" / "procesados"

RUTA_ALERTAS = RAIZ / "resultados" / "alertas.csv"
RUTA_PARO_TOTAL = PROCESADOS / "paro_total_mensual.csv"
RUTA_PARO_EDAD = PROCESADOS / "paro_edad_mensual.csv"
RUTA_CONTRATOS = PROCESADOS / "contratos_mensuales.csv"

RUTAS_ORIGINALES = [
    ORIGINALES / "paro_edad_municipio.csv",
    ORIGINALES / "contratos_municipio.csv",
]
RUTAS_PROCESADOS = [RUTA_PARO_TOTAL, RUTA_PARO_EDAD, RUTA_CONTRATOS]

COMANDO_DESCARGAR = r".\.venv\Scripts\python.exe .\src\descargar_datos.py"
COMANDO_COMPROBAR = r".\.venv\Scripts\python.exe .\src\comprobar_datos.py"
COMANDO_PREPARAR = r".\.venv\Scripts\python.exe .\src\preparar_datos.py"
COMANDO_DETECTAR = r".\.venv\Scripts\python.exe .\src\detectar_alertas.py"

# Columnas de docs/contrato_alertas.md. La aplicación las lee por nombre.
COLUMNAS_ALERTAS = [
    "municipio",
    "fecha",
    "paro_total",
    "paro_mes_anterior",
    "cambio_mensual",
    "variacion_mensual_pct",
    "n_historico",
    "referencia_cambio",
    "mad_cambio",
    "escala_robusta",
    "limite_superior",
    "puntuacion_robusta",
    "alerta_experimental",
    "estado_detector",
    "grupo_edad_principal",
]

ESTADOS = ["alerta_experimental", "sin_alerta", "dispersion_cero", "historial_insuficiente"]
ESTADOS_NO_EVALUABLES = ["dispersion_cero", "historial_insuficiente"]

# Años de referencia descritos en el contrato («los 5 años anteriores»).
VENTANA_ANOS = 5

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ---------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------

def comandos_para_generar_alertas():
    """Comandos necesarios para obtener resultados/alertas.csv."""
    comandos = []

    if not all(ruta.is_file() for ruta in RUTAS_PROCESADOS):
        if not all(ruta.is_file() for ruta in RUTAS_ORIGINALES):
            comandos.append(COMANDO_DESCARGAR)
        comandos += [COMANDO_COMPROBAR, COMANDO_PREPARAR]

    comandos.append(COMANDO_DETECTAR)
    return comandos


def marca_tiempo(ruta):
    """Fecha de modificación, usada para invalidar la caché."""
    return ruta.stat().st_mtime


def fecha_modificacion(ruta):
    return datetime.fromtimestamp(marca_tiempo(ruta))


def alertas_desactualizadas():
    """True si algún dato procesado es posterior a alertas.csv."""
    return any(
        ruta.is_file() and marca_tiempo(ruta) > marca_tiempo(RUTA_ALERTAS)
        for ruta in RUTAS_PROCESADOS
    )


# ---------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------

def leer_alertas(ruta=RUTA_ALERTAS):
    alertas = pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
    )

    faltan = [c for c in COLUMNAS_ALERTAS if c not in alertas.columns]
    if faltan:
        raise ValueError(
            "resultados/alertas.csv no sigue docs/contrato_alertas.md. "
            f"Faltan las columnas: {', '.join(faltan)}."
        )

    desconocidos = set(alertas["estado_detector"]) - set(ESTADOS)
    if desconocidos:
        raise ValueError(
            "resultados/alertas.csv contiene estados desconocidos: "
            f"{', '.join(sorted(desconocidos))}."
        )

    for columna in ["paro_total", "paro_mes_anterior", "cambio_mensual", "n_historico"]:
        alertas[columna] = alertas[columna].astype("Int64")

    alertas["alerta_experimental"] = alertas["alerta_experimental"].astype("boolean")

    return alertas


# ---------------------------------------------------------------
# Vista general del mes
# ---------------------------------------------------------------

def meses_disponibles(alertas):
    """Meses de la tabla, del más reciente al más antiguo."""
    return [pd.Timestamp(f) for f in sorted(alertas["fecha"].unique(), reverse=True)]


def filas_mes(alertas, fecha):
    return alertas.loc[alertas["fecha"].eq(fecha)]


def resumen_mes(mes):
    estados = mes["estado_detector"]
    return {
        "alerta": int(estados.eq("alerta_experimental").sum()),
        "sin_alerta": int(estados.eq("sin_alerta").sum()),
        "no_evaluable": int(estados.isin(ESTADOS_NO_EVALUABLES).sum()),
        "total": len(mes),
    }


def personas_sobre_limite(filas):
    """Personas por encima del límite. Lo permite el contrato."""
    return filas["cambio_mensual"].astype("Float64") - filas["limite_superior"]


def tabla_alertas(mes):
    alertas = mes.loc[mes["estado_detector"].eq("alerta_experimental")].copy()
    alertas["personas_sobre_limite"] = personas_sobre_limite(alertas)
    alertas["grupo_edad_principal"] = [
        texto_grupo_principal(grupo, cambio)
        for grupo, cambio in zip(
            alertas["grupo_edad_principal"], alertas["cambio_mensual"]
        )
    ]

    columnas = [
        "municipio",
        "cambio_mensual",
        "referencia_cambio",
        "limite_superior",
        "personas_sobre_limite",
        "puntuacion_robusta",
        "variacion_mensual_pct",
        "grupo_edad_principal",
    ]
    return (
        alertas[columnas]
        .sort_values("puntuacion_robusta", ascending=False)
        .reset_index(drop=True)
    )


def tabla_no_evaluables(mes):
    filas = mes.loc[mes["estado_detector"].isin(ESTADOS_NO_EVALUABLES)].copy()
    filas["motivo"] = [motivo_no_evaluable(fila) for _, fila in filas.iterrows()]
    filas = filas.sort_values("municipio", key=clave_orden)
    return filas[["municipio", "motivo", "cambio_mensual"]].reset_index(drop=True)


def tabla_sin_alerta(mes):
    filas = mes.loc[mes["estado_detector"].eq("sin_alerta")]
    filas = filas.sort_values("municipio", key=clave_orden)
    columnas = ["municipio", "cambio_mensual", "referencia_cambio", "limite_superior"]
    return filas[columnas].reset_index(drop=True)


# ---------------------------------------------------------------
# Textos
# ---------------------------------------------------------------

def nombre_mes(fecha, con_anio=True):
    fecha = pd.Timestamp(fecha)
    nombre = MESES[fecha.month - 1]
    return f"{nombre} de {fecha.year}" if con_anio else nombre


def texto_grupo_principal(grupo, cambio):
    if isinstance(grupo, str) and grupo:
        return grupo
    if pd.notna(cambio) and cambio > 0:
        return "Empate entre grupos"
    return "—"


def motivo_no_evaluable(fila):
    mes = nombre_mes(fila["fecha"], con_anio=False)

    if fila["estado_detector"] == "dispersion_cero":
        return (
            f"Dispersión cero: la MAD de los cambios de {mes} "
            f"en los {VENTANA_ANOS} años anteriores es 0."
        )

    if pd.isna(fila["cambio_mensual"]):
        return "Primer mes de la serie: no hay mes anterior."

    return (
        f"Historial insuficiente: {fila['n_historico']} de los "
        f"{VENTANA_ANOS} cambios de {mes} necesarios."
    )


# ---------------------------------------------------------------
# Formato español
# ---------------------------------------------------------------

def numero(valor, decimales=0, signo=False):
    """2130 -> «2.130»; 826.0216 -> «826,0» con un decimal."""
    if valor is None or pd.isna(valor):
        return "—"
    plantilla = f"{{:{'+' if signo else ''},.{decimales}f}}"
    texto = plantilla.format(float(valor))
    texto = texto.replace(",", "\0").replace(".", ",").replace("\0", ".")
    if texto.lstrip("+-").strip("0,.") == "":
        texto = texto.lstrip("+-")
    return texto


def numero_justo(valor, decimales=1, signo=False):
    """Como numero(), pero sin decimales cuando el valor es entero."""
    if valor is None or pd.isna(valor):
        return "—"
    return numero(valor, 0 if float(valor).is_integer() else decimales, signo)


def porcentaje(valor, decimales=1, signo=True):
    if valor is None or pd.isna(valor):
        return "—"
    return f"{numero(valor, decimales, signo)} %"


def clave_orden(serie):
    """Orden alfabético que no deja los nombres con tilde al final."""
    def clave(texto):
        sin_tildes = unicodedata.normalize("NFD", texto)
        sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
        return sin_tildes.casefold()

    return serie.map(clave)
