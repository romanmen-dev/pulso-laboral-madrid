import streamlit as st

from src import datos_app as datos


st.set_page_config(
    page_title="Pulso Laboral Madrid",
    layout="wide",
)

AVISO = (
    "**Alertas experimentales, no validadas.** Señalan subidas del paro "
    "registrado superiores a lo habitual para que se revisen; no explican "
    "sus causas. La puntuación robusta no es una probabilidad ni una medida "
    "de gravedad, y la ausencia de alerta no indica que la evolución sea "
    "favorable."
)

ETIQUETAS = {
    "municipio": "Municipio",
    "cambio_mensual": "Cambio mensual",
    "referencia_cambio": "Cambio habitual",
    "limite_superior": "Límite de alerta",
    "personas_sobre_limite": "Sobre el límite",
    "puntuacion_robusta": "Puntuación",
    "variacion_mensual_pct": "Variación",
    "grupo_edad_principal": "Grupo con mayor aumento",
    "motivo": "Motivo",
}

# Anchos en píxeles para que la tabla de alertas quepa en pantallas de 1440 px.
ANCHOS = {
    "municipio": 160,
    "cambio_mensual": 118,
    "referencia_cambio": 118,
    "limite_superior": 116,
    "personas_sobre_limite": 112,
    "puntuacion_robusta": 96,
    "variacion_mensual_pct": 90,
    "grupo_edad_principal": 165,
}

AYUDAS = {
    "cambio_mensual": "Cambio del paro registrado respecto al mes anterior, en personas.",
    "referencia_cambio": (
        "Mediana de los cambios del mismo mes en los cinco años anteriores, "
        "en personas."
    ),
    "limite_superior": (
        "Cambio habitual más tres veces la dispersión robusta. Por encima "
        "de este cambio se marca alerta experimental."
    ),
    "personas_sobre_limite": (
        "Personas por encima del límite: subida mensual menos el límite de alerta."
    ),
    "puntuacion_robusta": (
        "Puntuación robusta: distancia al cambio habitual en unidades de "
        "dispersión. No es una probabilidad ni una medida de gravedad."
    ),
    "variacion_mensual_pct": (
        "Variación mensual en porcentaje. Solo informativa: no interviene "
        "en la alerta."
    ),
    "grupo_edad_principal": (
        "Grupo de edad con mayor aumento en personas ese mes. No indica una "
        "anomalía propia de ese grupo."
    ),
}


def personas(valor):
    return datos.numero(valor, 0, signo=True)


def personas_1(valor):
    return datos.numero(valor, 1, signo=True)


FORMATOS = {
    "cambio_mensual": personas,
    "referencia_cambio": lambda v: datos.numero_justo(v, 1, signo=True),
    "limite_superior": personas_1,
    "personas_sobre_limite": personas_1,
    "puntuacion_robusta": lambda v: datos.numero(v, 2),
    "variacion_mensual_pct": datos.porcentaje,
}


# ---------------------------------------------------------------
# Datos
# ---------------------------------------------------------------

@st.cache_data(show_spinner="Leyendo resultados/alertas.csv…")
def cargar_alertas(marca_tiempo):
    # marca_tiempo solo sirve para invalidar la caché al regenerar el CSV.
    return datos.leer_alertas()


def mostrar_como_generar(mensaje):
    st.error(mensaje)
    st.markdown("Ejecuta en PowerShell, desde la carpeta principal del proyecto:")
    st.code("\n".join(datos.comandos_para_generar_alertas()), language="powershell")
    st.markdown("Después, recarga esta página.")
    st.stop()


# ---------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------

def mostrar_tabla(tabla, filas_visibles=10, ajustar_anchos=False):
    """Tabla ordenable: se ordena por el valor, se muestra en formato español."""
    vista = tabla.rename(columns=ETIQUETAS)
    formatos = {
        ETIQUETAS[c]: f for c, f in FORMATOS.items() if c in tabla.columns
    }
    columnas = {
        ETIQUETAS[c]: st.column_config.Column(
            help=AYUDAS.get(c),
            width=ANCHOS.get(c) if ajustar_anchos else None,
        )
        for c in tabla.columns
    }
    st.dataframe(
        vista.style.format(formatos),
        hide_index=True,
        width="stretch",
        height=35 * (min(len(tabla), filas_visibles) + 1) + 3,
        column_config=columnas,
    )


def vista_general(alertas, fecha):
    mes = datos.filas_mes(alertas, fecha)
    resumen = datos.resumen_mes(mes)
    nombre = datos.nombre_mes(fecha)

    st.subheader(f"Vista general de {nombre}")
    st.caption(
        f"Cada municipio se compara con los cambios de "
        f"{datos.nombre_mes(fecha, con_anio=False)} en los "
        f"{datos.VENTANA_ANOS} años anteriores. Se marca alerta experimental "
        "cuando el paro sube y la subida supera el límite de alerta."
    )

    col_alerta, col_sin, col_no_eval = st.columns(3)
    col_alerta.metric(
        "Con alerta experimental",
        datos.numero(resumen["alerta"]),
        help="El paro sube y la subida supera el límite de alerta.",
        border=True,
    )
    col_sin.metric(
        "Sin alerta",
        datos.numero(resumen["sin_alerta"]),
        help=(
            "El paro baja o sube sin superar el límite. No indica que la "
            "evolución sea favorable."
        ),
        border=True,
    )
    col_no_eval.metric(
        "No evaluables",
        datos.numero(resumen["no_evaluable"]),
        help=(
            "Sin historial suficiente o con dispersión cero: la regla no "
            "puede decir si hay alerta."
        ),
        border=True,
    )
    st.caption(f"{datos.numero(resumen['total'])} municipios en total.")

    st.markdown(f"#### Alertas experimentales de {nombre}")
    tabla = datos.tabla_alertas(mes)

    if tabla.empty:
        st.info("Ningún municipio tiene alerta experimental este mes.")
    else:
        mostrar_tabla(tabla, filas_visibles=15, ajustar_anchos=True)
        st.caption(
            "Cambios, límites y exceso sobre el límite, en personas. "
            "Ordenadas por puntuación robusta; pulsa en el título de una "
            "columna para reordenar. Con poca dispersión histórica, la "
            "puntuación puede ser alta aunque la subida sea de pocas personas."
        )

    no_evaluables = datos.tabla_no_evaluables(mes)
    with st.expander(f"Municipios no evaluables ({datos.numero(len(no_evaluables))})"):
        if no_evaluables.empty:
            st.write("Todos los municipios se han podido evaluar este mes.")
        else:
            st.caption(
                "Sin un límite de alerta la regla no se puede aplicar, así que "
                "no se presentan como «sin alerta». Dispersión cero: la MAD de "
                "los cambios de referencia es 0. Historial insuficiente: faltan "
                "cambios del mismo mes en los años anteriores."
            )
            mostrar_tabla(no_evaluables)

    sin_alerta = datos.tabla_sin_alerta(mes)
    with st.expander(f"Municipios sin alerta ({datos.numero(len(sin_alerta))})"):
        if sin_alerta.empty:
            st.write("Ningún municipio evaluable queda sin alerta este mes.")
        else:
            mostrar_tabla(sin_alerta)


# ---------------------------------------------------------------
# Página
# ---------------------------------------------------------------

st.title("Pulso Laboral Madrid")

if not datos.RUTA_ALERTAS.is_file():
    mostrar_como_generar(
        "No se encuentra `resultados/alertas.csv`, la tabla que genera el detector."
    )

try:
    alertas = cargar_alertas(datos.marca_tiempo(datos.RUTA_ALERTAS))
except ValueError as error:
    mostrar_como_generar(f"No se puede leer `resultados/alertas.csv`: {error}")

st.warning(AVISO, icon=":material/warning:")

if datos.alertas_desactualizadas():
    st.warning(
        "Hay datos procesados más recientes que `resultados/alertas.csv`. "
        f"Vuelve a ejecutar `{datos.COMANDO_DETECTAR}` y recarga la página.",
        icon=":material/update:",
    )

meses = datos.meses_disponibles(alertas)

with st.sidebar:
    st.header("Selección")
    fecha = st.selectbox(
        "Mes",
        meses,
        index=0,
        format_func=lambda f: datos.nombre_mes(f).capitalize(),
        key="mes",
    )
    st.caption(
        "Tabla de alertas generada el "
        f"{datos.fecha_modificacion(datos.RUTA_ALERTAS):%d/%m/%Y a las %H:%M}."
    )

vista_general(alertas, fecha)

st.divider()
st.caption(
    "Fuente: paro registrado por edad y municipio, Comunidad de Madrid. "
    "Método y columnas: `docs/contrato_alertas.md`."
)
