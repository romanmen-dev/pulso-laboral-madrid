import pandas as pd
import streamlit as st

from src import datos_app as datos
from src import graficos_app as graficos
from src import identidad_app as identidad


st.set_page_config(
    page_title="Pulso Laboral Madrid",
    page_icon=str(identidad.RUTA_ICONO),
    layout="wide",
)

PESTANAS = ["Vista general", "Ficha de municipio", "Cambios frente al límite"]

PERIODOS = {"Últimos 3 años": 36, "Últimos 10 años": 120, "Toda la serie": None}

MESES_FICHA = 24

CONFIG_PLOTLY = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
}

AVISO = (
    "**Alertas experimentales, no validadas.** Señalan subidas del paro "
    "registrado superiores a lo habitual para que se revisen; no explican "
    "sus causas. La puntuación robusta no es una probabilidad ni una medida "
    "de gravedad, y la ausencia de alerta no indica que la evolución sea "
    "favorable."
)

ETIQUETAS = {
    "municipio": "Municipio",
    "fecha": "Mes",
    "paro_total": "Paro registrado",
    "cambio_mensual": "Cambio mensual",
    "referencia_cambio": "Cambio habitual",
    "limite_superior": "Límite de alerta",
    "personas_sobre_limite": "Sobre el límite",
    "puntuacion_robusta": "Puntuación",
    "variacion_mensual_pct": "Variación",
    "grupo_edad_principal": "Grupo con mayor aumento",
    "estado_detector": "Estado",
    "contratos": "Contratos",
    "motivo": "Motivo",
    "grupo_edad": "Grupo de edad",
    "paro_anterior": "Paro mes anterior",
    "paro": "Paro",
    "cambio": "Cambio",
}

# Anchos en píxeles para que la tabla de alertas, con su casilla de
# selección, quepa en pantallas de 1440 px.
ANCHOS = {
    "municipio": 150,
    "cambio_mensual": 112,
    "referencia_cambio": 112,
    "limite_superior": 108,
    "personas_sobre_limite": 106,
    "puntuacion_robusta": 92,
    "variacion_mensual_pct": 86,
    "grupo_edad_principal": 160,
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
    "fecha": datos.mes_corto,
    "paro_total": datos.numero,
    "paro_anterior": datos.numero,
    "paro": datos.numero,
    "contratos": datos.numero,
    "cambio_mensual": personas,
    "cambio": personas,
    "referencia_cambio": lambda v: datos.numero_justo(v, 1, signo=True),
    "limite_superior": personas_1,
    "personas_sobre_limite": personas_1,
    "puntuacion_robusta": lambda v: datos.numero(v, 2),
    "variacion_mensual_pct": datos.porcentaje,
}


# ---------------------------------------------------------------
# Datos
# ---------------------------------------------------------------
# La marca de tiempo del archivo solo sirve para invalidar la caché
# cuando se regenera.

@st.cache_data(show_spinner="Leyendo resultados/alertas.csv…")
def cargar_alertas(marca_tiempo):
    return datos.leer_alertas()


@st.cache_data(show_spinner="Leyendo el paro por edad…")
def cargar_paro_edad(marca_tiempo):
    return datos.leer_paro_edad()


@st.cache_data(show_spinner="Leyendo los contratos…")
def cargar_contratos(marca_tiempo):
    return datos.leer_contratos()


def cargar_si_existe(ruta, cargar):
    return cargar(datos.marca_tiempo(ruta)) if ruta.is_file() else None


def mostrar_como_generar(mensaje):
    st.error(mensaje)
    st.markdown("Ejecuta en PowerShell, desde la carpeta principal del proyecto:")
    st.code("\n".join(datos.comandos_para_generar_alertas()), language="powershell")
    st.markdown("Después, recarga esta página.")
    st.stop()


def avisar_datos_procesados(que_falta):
    st.info(
        f"Para ver {que_falta} faltan tablas de `datos/procesados/`. "
        "Ejecuta en PowerShell, desde la carpeta principal del proyecto:"
    )
    st.code("\n".join(datos.comandos_para_preparar_datos()), language="powershell")


def modo_oscuro():
    try:
        return st.context.theme.type == "dark"
    except AttributeError:
        return False


def abrir_ficha(clave, municipios_tabla):
    """Al seleccionar una fila de la tabla de alertas, abre su ficha."""
    filas = st.session_state[clave].selection.rows
    if filas:
        st.session_state["municipio"] = municipios_tabla[filas[0]]
        st.session_state["pestana"] = PESTANAS[1]
        # Una clave nueva deja la tabla sin selección al volver a ella.
        st.session_state["version_tabla"] = st.session_state.get("version_tabla", 0) + 1


# ---------------------------------------------------------------
# Componentes
# ---------------------------------------------------------------

def mostrar_tabla(tabla, filas_visibles=10, ajustar_anchos=False, al_seleccionar=None, clave=None):
    """Tabla ordenable: se ordena por el valor, se muestra en formato español."""
    vista = tabla.rename(columns=ETIQUETAS)
    formatos = {
        ETIQUETAS[c]: f for c, f in FORMATOS.items() if c in tabla.columns
    }
    columnas = {
        ETIQUETAS.get(c, c): st.column_config.Column(
            help=AYUDAS.get(c),
            width=ANCHOS.get(c) if ajustar_anchos else None,
        )
        for c in tabla.columns
    }
    seleccion = {}
    if al_seleccionar:
        seleccion = dict(on_select=al_seleccionar, selection_mode="single-row", key=clave)

    st.dataframe(
        vista.style.format(formatos),
        hide_index=True,
        width="stretch",
        height=35 * (min(len(tabla), filas_visibles) + 1) + 3,
        column_config=columnas,
        **seleccion,
    )


def grafico(figura):
    st.plotly_chart(figura, width="stretch", config=CONFIG_PLOTLY)


# ---------------------------------------------------------------
# Vista general
# ---------------------------------------------------------------

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
        clave = f"tabla_alertas_{fecha:%Y%m}_{st.session_state.get('version_tabla', 0)}"
        lista = tabla["municipio"].tolist()
        mostrar_tabla(
            tabla,
            filas_visibles=15,
            ajustar_anchos=True,
            al_seleccionar=lambda: abrir_ficha(clave, lista),
            clave=clave,
        )
        st.caption(
            "Selecciona una fila para abrir la ficha del municipio. Cambios, "
            "límites y exceso sobre el límite, en personas. Ordenadas por "
            "puntuación robusta; pulsa en el título de una columna para "
            "reordenar. Con poca dispersión histórica, la puntuación puede ser "
            "alta aunque la subida sea de pocas personas."
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
# Ficha de municipio
# ---------------------------------------------------------------

def tres_cifras(fila):
    evaluable = datos.es_evaluable(fila)
    referencia = fila["referencia_cambio"]
    motivo = datos.motivo_no_evaluable(fila) if not evaluable else ""

    col_cambio, col_habitual, col_limite = st.columns(3)
    col_cambio.metric(
        "Cambio mensual (personas)",
        datos.numero(fila["cambio_mensual"], signo=True),
        help="Cambio del paro registrado respecto al mes anterior.",
        border=True,
    )
    inicio, fin = datos.periodo_referencia(fila["fecha"])
    col_habitual.metric(
        "Cambio habitual (personas)",
        datos.numero_justo(referencia, 1, signo=True) if pd.notna(referencia) else "—",
        help=(
            f"Mediana de los cambios de {datos.nombre_mes(fila['fecha'], con_anio=False)} "
            f"entre {inicio} y {fin}."
            if pd.notna(referencia)
            else f"No se calcula. {motivo}"
        ),
        border=True,
    )
    col_limite.metric(
        "Límite de alerta (personas)",
        datos.numero(fila["limite_superior"], 1, signo=True) if evaluable else "—",
        help=(
            AYUDAS["limite_superior"] if evaluable
            else f"No hay límite: el mes no es evaluable. {motivo}"
        ),
        border=True,
    )
    if not evaluable:
        st.caption("Sin límite de alerta: este mes no se puede evaluar con la regla.")


def ficha(alertas, fecha, municipio, paro_edad, contratos, paleta):
    fila = datos.fila_municipio(alertas, municipio, fecha)

    st.subheader(f"{municipio} · {datos.nombre_mes(fecha)}")

    tipo, texto = datos.frase_estado(fila)
    if tipo == "alerta":
        st.warning(texto, icon=":material/notification_important:")
    elif tipo == "sin_alerta":
        st.info(texto, icon=":material/remove:")
    else:
        st.info(texto, icon=":material/block:")

    tres_cifras(fila)

    serie = datos.serie_municipio(alertas, municipio, fecha, MESES_FICHA)
    st.markdown(f"##### Paro registrado: {len(serie)} meses hasta {datos.mes_corto(fecha)}")
    grafico(graficos.figura_paro(serie, fecha, paleta))

    st.markdown("##### Cambio mensual por grupo de edad")
    cambios = None
    if paro_edad is None:
        avisar_datos_procesados("el desglose por edad")
    else:
        cambios = datos.cambios_por_edad(paro_edad, municipio, fecha)
        if cambios.empty:
            st.caption("Primer mes de la serie: no hay mes anterior con el que comparar.")
        else:
            grafico(graficos.figura_edad(cambios, fila["grupo_edad_principal"], paleta))
            cambio = fila["cambio_mensual"]
            if pd.notna(cambio) and cambio <= 0:
                st.caption(
                    "El paro total no sube este mes, así que no se señala "
                    "grupo con mayor aumento."
                )
            elif not isinstance(fila["grupo_edad_principal"], str):
                st.caption("Empate entre grupos: el mayor aumento lo comparten varios.")

    st.markdown("##### Interpretación")
    st.markdown(datos.frase_interpretacion(fila, cambios))

    with st.expander("Detalle técnico"):
        st.dataframe(datos.detalle_tecnico(fila), hide_index=True, width="stretch")

    st.markdown("##### Contexto: contratos de trabajo registrados")
    serie_contratos = None
    if contratos is None:
        avisar_datos_procesados("los contratos")
    else:
        serie_contratos = datos.contratos_municipio(contratos, municipio, fecha, MESES_FICHA)
        grafico(graficos.figura_contratos(serie_contratos, fecha, paleta))
        for aviso in datos.avisos_contratos(municipio, serie_contratos):
            st.info(aviso, icon=":material/info:")
        st.caption(
            "Contratos de trabajo registrados en el municipio cada mes. Se "
            "muestran como contexto: no intervienen en el detector."
        )

    with st.expander("Ver los datos de los gráficos"):
        if serie_contratos is not None:
            mostrar_tabla(datos.tabla_datos_ficha(serie, serie_contratos))
        else:
            mostrar_tabla(serie[["fecha", "paro_total", "cambio_mensual"]].iloc[::-1])
        if cambios is not None and not cambios.empty:
            mostrar_tabla(cambios)


# ---------------------------------------------------------------
# Cambios frente al límite
# ---------------------------------------------------------------

def cambios_frente_al_limite(alertas, fecha, municipio, paleta):
    st.subheader(f"{municipio}: cambio mensual frente al límite de alerta")

    periodo = st.segmented_control(
        "Periodo",
        list(PERIODOS),
        default="Últimos 3 años",
        required=True,
        key="periodo",
    )
    serie = datos.serie_municipio(alertas, municipio, fecha, PERIODOS[periodo])

    n_alertas = int(serie["estado_detector"].eq("alerta_experimental").sum())
    n_no_evaluables = int(serie["estado_detector"].isin(datos.ESTADOS_NO_EVALUABLES).sum())
    st.caption(
        f"Hasta {datos.nombre_mes(fecha)}; no se muestran meses posteriores. "
        f"En este periodo: {datos.numero(n_alertas)} alertas experimentales y "
        f"{datos.numero(n_no_evaluables)} meses no evaluables."
    )

    grafico(graficos.figura_cambios(serie, fecha, paleta))
    st.caption(
        "Cada barra es el cambio del paro respecto al mes anterior. La línea "
        "discontinua es el límite de alerta y la gris, el cambio habitual. "
        "Los huecos en las líneas corresponden a meses no evaluables, sin límite."
    )

    with st.expander("Ver los datos del gráfico"):
        mostrar_tabla(datos.tabla_historial(serie))


# ---------------------------------------------------------------
# Página
# ---------------------------------------------------------------

st.logo(
    identidad.svg_para_tema(identidad.RUTA_LOGO, modo_oscuro()),
    icon_image=identidad.svg_para_tema(identidad.RUTA_ICONO, modo_oscuro()),
    size="large",
)

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
municipios = datos.municipios(alertas)

if st.session_state.get("municipio") not in municipios:
    st.session_state["municipio"] = "Madrid" if "Madrid" in municipios else municipios[0]

with st.sidebar:
    st.header("Selección")
    fecha = st.selectbox(
        "Mes",
        meses,
        index=0,
        format_func=lambda f: datos.nombre_mes(f).capitalize(),
        key="mes",
    )
    municipio = st.selectbox(
        "Municipio",
        municipios,
        key="municipio",
        help="También se abre al seleccionar una fila de la tabla de alertas.",
    )
    st.caption(
        "Tabla de alertas generada el "
        f"{datos.fecha_modificacion(datos.RUTA_ALERTAS):%d/%m/%Y a las %H:%M}."
    )

paleta = graficos.paleta(modo_oscuro())
paro_edad = cargar_si_existe(datos.RUTA_PARO_EDAD, cargar_paro_edad)
contratos = cargar_si_existe(datos.RUTA_CONTRATOS, cargar_contratos)

pestana_general, pestana_ficha, pestana_cambios = st.tabs(
    PESTANAS, key="pestana", on_change="rerun"
)

with pestana_general:
    vista_general(alertas, fecha)

with pestana_ficha:
    ficha(alertas, fecha, municipio, paro_edad, contratos, paleta)

with pestana_cambios:
    cambios_frente_al_limite(alertas, fecha, municipio, paleta)

st.divider()
st.caption(f"Datos: [Portal de Datos Abiertos de la Comunidad de Madrid]({identidad.URL_PORTAL})")
st.caption(
    "Proyecto independiente para DATAMAD 2026; no es una herramienta oficial "
    "de la Comunidad de Madrid. Método y columnas: `docs/contrato_alertas.md`."
)
