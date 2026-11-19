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

NOMBRES_ESTADO = {
    "alerta_experimental": "Alerta experimental",
    "sin_alerta": "Sin alerta",
    "dispersion_cero": "No evaluable: dispersión cero",
    "historial_insuficiente": "No evaluable: historial insuficiente",
}

GRUPOS_EDAD = ["Menor de 25 años", "De 25 a 44 años", "Mayor de 44 años"]

# Años de referencia descritos en el contrato («los 5 años anteriores»).
VENTANA_ANOS = 5

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_CORTOS = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]

# Incidencias de los contratos en la fuente, documentadas en
# docs/decisiones.md (19/11/2026) y docs/fuentes_datos.md. Los datos no
# se corrigen: la ficha solo avisa cuando el gráfico incluye meses afectados.
MES_CONTRATOS_ANOMALO = pd.Timestamp("2026-05-01")
AVISO_CONTRATOS_MES_ANOMALO = (
    "Los contratos de mayo de 2026 son menos de la mitad que los de abril y "
    "junio en casi todos los municipios; el dato está así en la fuente y no "
    "se ha corregido."
)

MUNICIPIO_CONTRATOS_REPETIDOS = "Velilla de San Antonio"
INICIO_CONTRATOS_REPETIDOS = pd.Timestamp("2025-09-01")
AVISO_CONTRATOS_REPETIDOS = (
    "La fuente repite 368 contratos todos los meses desde septiembre de "
    "2025; puede que no refleje la contratación real."
)


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


def comandos_para_preparar_datos():
    """Comandos necesarios para obtener las tablas de datos/procesados/."""
    comandos = []
    if not all(ruta.is_file() for ruta in RUTAS_ORIGINALES):
        comandos.append(COMANDO_DESCARGAR)
    return comandos + [COMANDO_COMPROBAR, COMANDO_PREPARAR]


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


def leer_paro_edad(ruta=RUTA_PARO_EDAD):
    return pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
        usecols=["municipio", "fecha", "grupo_edad", "paro"],
    )


def leer_contratos(ruta=RUTA_CONTRATOS):
    return pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
        usecols=["municipio", "fecha", "contratos"],
    )


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
# Ficha de municipio
# ---------------------------------------------------------------

def municipios(alertas):
    return sorted(alertas["municipio"].unique(), key=clave_texto)


def fila_municipio(alertas, municipio, fecha):
    filas = alertas.loc[alertas["municipio"].eq(municipio) & alertas["fecha"].eq(fecha)]
    if len(filas) != 1:
        raise ValueError(f"No hay una fila única para {municipio} en {fecha:%Y-%m}.")
    return filas.iloc[0]


def es_evaluable(fila):
    return fila["estado_detector"] not in ESTADOS_NO_EVALUABLES


def serie_municipio(alertas, municipio, fecha, meses=None):
    """Filas del municipio hasta el mes elegido, sin meses posteriores."""
    serie = alertas.loc[
        alertas["municipio"].eq(municipio) & alertas["fecha"].le(fecha)
    ].sort_values("fecha")
    return serie.tail(meses) if meses else serie


def cambios_por_edad(paro_edad, municipio, fecha):
    """Cambio de cada grupo de edad respecto al mes anterior.

    Devuelve una tabla vacía si no hay mes anterior.
    """
    anterior = fecha - pd.DateOffset(months=1)
    filas = paro_edad.loc[
        paro_edad["municipio"].eq(municipio)
        & paro_edad["fecha"].isin([anterior, fecha])
    ]
    tabla = filas.pivot(index="grupo_edad", columns="fecha", values="paro")

    if anterior not in tabla.columns or fecha not in tabla.columns:
        return pd.DataFrame(columns=["grupo_edad", "paro_anterior", "paro", "cambio"])

    tabla = tabla.reindex(GRUPOS_EDAD)
    return pd.DataFrame(
        {
            "grupo_edad": GRUPOS_EDAD,
            "paro_anterior": tabla[anterior].to_numpy(),
            "paro": tabla[fecha].to_numpy(),
            "cambio": (tabla[fecha] - tabla[anterior]).to_numpy(),
        }
    )


def contratos_municipio(contratos, municipio, fecha, meses=24):
    serie = contratos.loc[
        contratos["municipio"].eq(municipio) & contratos["fecha"].le(fecha)
    ].sort_values("fecha")
    return serie.tail(meses)


def avisos_contratos(municipio, serie_contratos):
    """Avisos de incidencias de la fuente que afectan a los meses del gráfico."""
    fechas = serie_contratos["fecha"]
    avisos = []

    if fechas.eq(MES_CONTRATOS_ANOMALO).any():
        avisos.append(AVISO_CONTRATOS_MES_ANOMALO)

    if (
        municipio == MUNICIPIO_CONTRATOS_REPETIDOS
        and fechas.ge(INICIO_CONTRATOS_REPETIDOS).any()
    ):
        avisos.append(AVISO_CONTRATOS_REPETIDOS)

    return avisos


def tabla_datos_ficha(serie, contratos):
    """Valores de los gráficos de la ficha, como tabla."""
    tabla = serie[["fecha", "paro_total", "cambio_mensual"]].merge(
        contratos[["fecha", "contratos"]], on="fecha", how="left"
    )
    return tabla.sort_values("fecha", ascending=False).reset_index(drop=True)


def tabla_historial(serie):
    tabla = serie[
        ["fecha", "cambio_mensual", "referencia_cambio", "limite_superior", "estado_detector"]
    ].copy()
    tabla["estado_detector"] = tabla["estado_detector"].map(NOMBRES_ESTADO)
    return tabla.sort_values("fecha", ascending=False).reset_index(drop=True)


def periodo_referencia(fecha):
    """Años cuyos cambios forman la referencia del mes."""
    return fecha.year - VENTANA_ANOS, fecha.year - 1


def frase_estado(fila):
    """Estado del mes en una frase. Devuelve (tipo, texto)."""
    mes = nombre_mes(fila["fecha"])
    cambio = fila["cambio_mensual"]

    if fila["estado_detector"] == "alerta_experimental":
        return "alerta", (
            f"**Alerta experimental** en {mes}: la subida del paro supera "
            "el límite de alerta."
        )

    if fila["estado_detector"] == "sin_alerta":
        if cambio > 0:
            detalle = "la subida del paro no supera el límite de alerta."
        elif cambio < 0:
            detalle = "el paro baja."
        else:
            detalle = "el paro no varía."
        return "sin_alerta", f"**Sin alerta** en {mes}: {detalle}"

    return "no_evaluable", f"**No evaluable** en {mes}. {motivo_no_evaluable(fila)}"


def texto_personas(n):
    n = abs(n)
    return f"{numero(n)} persona" if round(n) == 1 else f"{numero(n)} personas"


def texto_cambio(cambio):
    if cambio > 0:
        return f"subió {texto_personas(cambio)}"
    if cambio < 0:
        return f"bajó {texto_personas(cambio)}"
    return "no varió"


def texto_limite(limite, cambio):
    """Límite sin decimales, salvo que el redondeo cambie su orden con el cambio."""
    decimales = 0 if (round(limite) < cambio) == (limite < cambio) else 1
    return numero(limite, decimales, signo=True)


def frase_interpretacion(fila, cambios_edad=None):
    """Explica el resultado del mes sin atribuirle causas."""
    fecha = fila["fecha"]
    mes = nombre_mes(fecha)
    cambio = fila["cambio_mensual"]

    if pd.isna(cambio):
        return (
            f"{mes.capitalize()} es el primer mes de la serie: no hay mes "
            "anterior con el que calcular el cambio."
        )

    frase = f"En {mes} el paro registrado {texto_cambio(cambio)}"
    if cambio != 0 and pd.notna(fila["variacion_mensual_pct"]):
        frase += f" ({porcentaje(fila['variacion_mensual_pct'])})"
    partes = [frase + "."]

    if es_evaluable(fila):
        inicio, fin = periodo_referencia(fecha)
        limite = fila["limite_superior"]
        frase = (
            f"Lo habitual en {nombre_mes(fecha, con_anio=False)} (mediana "
            f"{inicio}–{fin}) era {numero_justo(fila['referencia_cambio'], 1, signo=True)} "
            f"y el límite, {texto_limite(limite, cambio)}"
        )
        if fila["alerta_experimental"]:
            exceso = cambio - limite
            por = (
                f"en {texto_personas(exceso)}" if round(exceso) >= 1
                else "por menos de una persona"
            )
            frase += f", así que se marca como alerta experimental: la subida supera el límite {por}."
        elif cambio > 0:
            frase += ", así que no se marca alerta: la subida no supera el límite."
        else:
            frase += ". Como el paro no sube, no se marca alerta."
        partes.append(frase)
    else:
        partes.append(
            "Este mes la regla no se puede aplicar, así que no hay límite de "
            f"alerta. {motivo_no_evaluable(fila)}"
        )

    grupo = fila["grupo_edad_principal"]
    if isinstance(grupo, str) and grupo and cambios_edad is not None and len(cambios_edad):
        aumento = cambios_edad.loc[cambios_edad["grupo_edad"].eq(grupo), "cambio"].iloc[0]
        partes.append(
            f"El grupo con mayor aumento fue «{grupo}» ({numero(aumento, signo=True)}), "
            "lo que no indica una anomalía propia de ese grupo."
        )
    elif cambio > 0 and not (isinstance(grupo, str) and grupo):
        partes.append("El mayor aumento está empatado entre varios grupos de edad.")

    return " ".join(partes)


def detalle_tecnico(fila):
    mes = nombre_mes(fila["fecha"], con_anio=False)
    filas = [
        ("n_historico", numero(fila["n_historico"]),
         f"Cambios de {mes} disponibles en los {VENTANA_ANOS} años anteriores."),
        ("mad_cambio", numero_justo(fila["mad_cambio"], 1),
         "Desviación absoluta mediana de esos cambios, sin escalar."),
        ("escala_robusta", numero(fila["escala_robusta"], 1),
         "1,4826 × MAD: la dispersión que usa la regla."),
        ("puntuacion_robusta", numero(fila["puntuacion_robusta"], 2),
         "(Cambio mensual − cambio habitual) / escala robusta. No es una probabilidad."),
        ("estado_detector", fila["estado_detector"],
         "Estado según docs/contrato_alertas.md."),
        ("variacion_mensual_pct", porcentaje(fila["variacion_mensual_pct"]),
         "Cambio respecto al mes anterior, en porcentaje. Solo informativo."),
    ]
    return pd.DataFrame(filas, columns=["Columna", "Valor", "Qué es"])


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


def mes_corto(fecha):
    fecha = pd.Timestamp(fecha)
    return f"{MESES_CORTOS[fecha.month - 1]} {fecha.year}"


def clave_texto(texto):
    """Clave de orden alfabético que no deja los nombres con tilde al final."""
    sin_tildes = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.casefold()


def clave_orden(serie):
    return serie.map(clave_texto)
