import pandas as pd
import streamlit as st

from src import datos_app as datos
from src import graficos_app as graficos
from src import identidad_app as identidad
from src import validacion_app as validacion


st.set_page_config(
    page_title="Pulso Laboral Madrid",
    page_icon=str(identidad.RUTA_ICONO),
    layout="wide",
)

PESTANAS = [
    "Vista general",
    "Ficha de municipio",
    "Cambios frente al límite",
    "¿Cómo sabemos que funciona?",
]

PERIODOS = {"Últimos 3 años": 36, "Últimos 10 años": 120, "Toda la serie": None}

MESES_FICHA = 24

CONFIG_PLOTLY = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
}

AVISO = (
    "**Alertas experimentales.** Señalan subidas del paro registrado superiores "
    "a lo habitual para que se revisen; no explican sus causas. Su comportamiento "
    "se ha evaluado con datos históricos (pestaña «¿Cómo sabemos que funciona?»), "
    "pero no hay una lista de anomalías confirmadas con la que medir su acierto. "
    "La puntuación robusta no es una probabilidad ni una medida de gravedad, y la "
    "ausencia de alerta no indica que la evolución sea favorable."
)

# Los contratos se agrupan por el centro de trabajo y cuentan contratos, no
# personas: no miden lo mismo que el paro. Por eso van en una sección aparte,
# plegada, al final de la ficha (docs/decisiones.md, 20/11/2026).
TITULO_CONTRATOS = "Contratos registrados en centros de trabajo del municipio"
TEXTO_CONTRATOS = (
    "Esta serie recoge los contratos comunicados cada mes en centros de trabajo "
    "situados en el municipio, vivan donde vivan las personas contratadas. Se "
    "cuentan contratos, no personas. Por eso no es directamente comparable con "
    "el paro registrado, que cuenta personas."
)

ETIQUETAS = {
    "municipio": "Municipio",
    "tipo": "Tipo",
    "evaluables": "Municipios evaluables",
    "con_alerta": "Con alerta",
    "pct_alertas_evaluables": "% con alerta",
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
# selección y la columna «Tipo», quepa en pantallas de 1440 px.
ANCHOS = {
    "municipio": 138,
    "tipo": 70,
    "cambio_mensual": 104,
    "referencia_cambio": 106,
    "limite_superior": 100,
    "personas_sobre_limite": 96,
    "puntuacion_robusta": 80,
    "variacion_mensual_pct": 68,
    "grupo_edad_principal": 164,
}

AYUDAS = {
    "tipo": (
        "Local: la subida destaca también frente al resto de la Comunidad. "
        "Regional: es compatible con la evolución del resto de la Comunidad. "
        "Etiqueta estadística de contraste (método B): no indica la causa ni "
        "cambia la alerta."
    ),
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
    "evaluables": datos.numero,
    "con_alerta": datos.numero,
    "pct_alertas_evaluables": validacion.porcentaje,
}


# ---------------------------------------------------------------
# Datos
# ---------------------------------------------------------------
# La marca de tiempo del archivo solo sirve para invalidar la caché
# cuando se regenera.

@st.cache_data(show_spinner="Leyendo resultados/alertas.csv…")
def cargar_alertas(ruta, marca_tiempo):
    return datos.leer_alertas(ruta)


@st.cache_data(show_spinner="Leyendo el paro por edad…")
def cargar_paro_edad(ruta, marca_tiempo):
    return datos.leer_paro_edad(ruta)


@st.cache_data(show_spinner="Leyendo los contratos…")
def cargar_contratos(ruta, marca_tiempo):
    return datos.leer_contratos(ruta)


@st.cache_data(show_spinner="Leyendo la población…")
def cargar_poblacion(ruta, marca_tiempo):
    return datos.leer_poblacion(ruta)


@st.cache_data(show_spinner="Leyendo el mapa…")
def cargar_mapa(ruta, marca_tiempo):
    return datos.leer_mapa(ruta)


@st.cache_data(show_spinner="Leyendo los resultados de la validación…")
def cargar_validacion(ruta, marca_tiempo):
    return datos.leer_csv_validacion(ruta, fechas=False)


@st.cache_data(show_spinner="Leyendo los resultados de la validación…")
def cargar_validacion_con_fechas(ruta, marca_tiempo):
    return datos.leer_csv_validacion(ruta, fechas=True)


@st.cache_data(show_spinner="Leyendo la clasificación local/regional…")
def cargar_clasificacion(ruta, marca_tiempo):
    return datos.leer_clasificacion(ruta)


@st.cache_data(show_spinner="Leyendo los otros métodos…")
def cargar_otros_metodos(ruta, marca_tiempo):
    return datos.leer_otros_metodos(ruta)


def cargar_si_existe(ruta, cargar):
    return cargar(str(ruta), datos.marca_tiempo(ruta)) if ruta.is_file() else None


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


def ir_a_ficha(municipio):
    st.session_state["municipio"] = municipio
    st.session_state["pestana"] = PESTANAS[1]
    # Una clave nueva deja la tabla y el mapa sin selección al volver a ellos.
    st.session_state["version_tabla"] = st.session_state.get("version_tabla", 0) + 1


def abrir_ficha(clave, municipios_tabla):
    """Al seleccionar una fila de la tabla de alertas, abre su ficha."""
    filas = st.session_state[clave].selection.rows
    if filas:
        ir_a_ficha(municipios_tabla[filas[0]])


def abrir_ficha_desde_mapa(clave, municipios_por_traza):
    """Al pinchar un municipio del mapa, abre su ficha."""
    puntos = st.session_state[clave].selection.get("points", [])
    if not puntos:
        return
    punto = puntos[0]
    municipio = punto.get("location")
    if not municipio:
        try:
            municipio = municipios_por_traza[punto["curve_number"]][punto["point_index"]]
        except (KeyError, IndexError, TypeError):
            return
    ir_a_ficha(municipio)


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

def mapa_del_mes(mes, nombre, fecha, mapa, paleta):
    st.markdown(f"#### Mapa de {nombre}")
    if mapa is None:
        avisar_datos_procesados("el mapa")
        return

    sin_geometria = datos.municipios_sin_geometria(mapa, mes["municipio"])
    if sin_geometria:
        st.warning(f"No hay geometría para: {', '.join(sin_geometria)}.")

    figura = graficos.figura_mapa(mapa, datos.tabla_mapa(mes), paleta)
    municipios_por_traza = [list(traza.locations) for traza in figura.data]
    clave = f"mapa_{fecha:%Y%m}_{st.session_state.get('version_tabla', 0)}"
    st.plotly_chart(
        figura,
        width="stretch",
        config=CONFIG_PLOTLY,
        key=clave,
        on_select=lambda: abrir_ficha_desde_mapa(clave, municipios_por_traza),
        selection_mode="points",
    )
    st.caption(
        "Pulsa en un municipio para abrir su ficha. Los Baldíos y El Redegüelo, "
        "territorios compartidos por dos municipios, no se colorean. Límites "
        "municipales: Información geográfica de la Comunidad de Madrid "
        "(Geoportal IDEM), CC BY 4.0."
    )


def vista_general(alertas, fecha, mapa, paleta, clasificacion):
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

    mapa_del_mes(mes, nombre, fecha, mapa, paleta)

    st.markdown(f"#### Alertas experimentales de {nombre}")
    tabla = datos.tabla_alertas(mes, clasificacion)

    if tabla.empty:
        st.info("Ningún municipio tiene alerta experimental este mes.")
    else:
        frase = datos.frase_tipos_mes(tabla)
        if frase:
            st.markdown(frase, help=datos.AYUDA_TIPO)
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


def ficha(alertas, fecha, municipio, paro_edad, contratos, paleta, clasificacion, otros_metodos, poblacion):
    fila = datos.fila_municipio(alertas, municipio, fecha)

    st.subheader(f"{municipio} · {datos.nombre_mes(fecha)}")

    tipo, texto = datos.frase_estado(fila)
    if tipo == "alerta":
        frase_tipo = None
        if clasificacion is not None:
            frase_tipo = datos.frase_tipo(datos.tipo_alerta(clasificacion, municipio, fecha))
        st.warning(texto + (f"\n\n{frase_tipo}" if frase_tipo else ""), icon=":material/notification_important:")
        if frase_tipo:
            st.caption(
                "La etiqueta local o regional es estadística y de contraste: no indica la "
                "causa de la subida ni cambia el estado oficial de la alerta.",
                help=datos.AYUDA_TIPO,
            )
    elif tipo == "sin_alerta":
        st.info(texto, icon=":material/remove:")
    else:
        st.info(texto, icon=":material/block:")

    tres_cifras(fila)
    paro_por_poblacion(fila, poblacion)

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
        if otros_metodos is not None:
            texto_otros = datos.texto_otros_metodos(otros_metodos, municipio, fecha)
            if texto_otros:
                st.markdown(f"**Otros métodos:** {texto_otros}.", help=datos.AYUDA_OTROS_METODOS)

    with st.expander("Ver los datos de los gráficos"):
        mostrar_tabla(datos.tabla_datos_ficha(serie))
        if cambios is not None and not cambios.empty:
            mostrar_tabla(cambios)

    contratos_del_municipio(contratos, municipio, fecha, paleta)


def paro_por_poblacion(fila, poblacion):
    """Indicador de contexto: no interviene en el detector."""
    if poblacion is None:
        return
    etiqueta, valor = datos.texto_paro_poblacion(fila, poblacion)
    st.markdown(f"**{etiqueta}:** {valor}")
    st.caption(datos.NOTA_PARO_POBLACION)


def contratos_del_municipio(contratos, municipio, fecha, paleta):
    """Sección final y plegada: los contratos no son comparables con el paro."""
    with st.expander(TITULO_CONTRATOS, expanded=False):
        st.markdown(TEXTO_CONTRATOS)
        if contratos is None:
            avisar_datos_procesados("los contratos")
            return

        serie_contratos = datos.contratos_municipio(contratos, municipio, fecha, MESES_FICHA)
        grafico(graficos.figura_contratos(serie_contratos, fecha, paleta))
        for aviso in datos.avisos_contratos(municipio, serie_contratos):
            st.info(aviso, icon=":material/info:")
        st.caption("No intervienen en el detector ni en las alertas.")
        # Streamlit no permite un desplegable dentro de otro: la tabla va a la vista.
        mostrar_tabla(datos.tabla_contratos(serie_contratos), filas_visibles=6)


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
# ¿Cómo sabemos que funciona?
# ---------------------------------------------------------------

def como_sabemos_que_funciona(v, paleta):
    """Validación del detector, leída de los CSV de resultados/validacion/."""
    st.subheader("¿Cómo sabemos que funciona?")
    if any(tabla is None for tabla in v.values()):
        st.info(
            "Faltan los resultados de la validación. Ejecuta en PowerShell, desde la "
            "carpeta principal del proyecto:"
        )
        st.code(f"{datos.COMANDO_VALIDAR}\n{datos.COMANDO_COMPARAR}", language="powershell")
        return

    mensual, potencia, resumen = v["validacion_mensual"], v["potencia"], v["resumen_metodos"]
    st.markdown(
        "No hay una lista de subidas anómalas confirmadas con la que medir el acierto "
        "del detector. Por eso se ha comprobado de tres maneras: cuántas alertas da en "
        "años tranquilos, si reacciona a una crisis conocida y si detecta subidas "
        "añadidas a mano. Sin anomalías verificadas no se puede saber cuántas alertas de "
        "los años tranquilos son falsas, así que se habla de **tasa de alertas en calma**, "
        "no de falsas alarmas. Cada mes se compara solo con meses anteriores. El método está en "
        f"[docs/metodologia.md]({validacion.URL_METODOLOGIA}) y los resultados completos, en "
        f"[docs/validacion.md]({validacion.URL_VALIDACION})."
    )

    tabla_meses = validacion.alertas_por_mes(mensual)
    st.markdown(
        f"#### Alertas por mes, de {datos.nombre_mes(tabla_meses['fecha'].min())} a "
        f"{datos.nombre_mes(tabla_meses['fecha'].max())}"
    )
    grafico(
        graficos.figura_alertas_por_mes(
            tabla_meses, validacion.FECHA_EPISODIO, validacion.ANOS_CALMA, paleta
        )
    )
    st.markdown(validacion.frase_abril_2020(validacion.episodio_abril_2020(mensual)))
    st.caption(
        "Municipios con alerta experimental cada mes desde el primero que se puede "
        "evaluar. El sombreado marca 2017-2019, años sin crisis que sirven para medir "
        "las alertas en calma."
    )

    st.markdown("#### ¿Detecta una subida de golpe?")
    st.markdown(
        "**Sensibilidad ante subidas sintéticas.** En cada mes evaluable de 2015 a 2019 se "
        "suma a mano una subida del 1 %, 2 %, 5 % o 10 % del paro del mes anterior al "
        "cambio real de ese mes, que puede ser negativo, y se mira si el detector la "
        "marca. Son saltos puntuales de un solo mes: no reproducen crisis graduales ni "
        "prolongadas. Como solo cambia ese mes, lo habitual y el límite no cambian."
    )
    grafico(graficos.figura_potencia_tamano(validacion.potencia_por_tamano(potencia), validacion.NOMBRES_QUINTIL, paleta))
    st.markdown(validacion.frase_sin_alerta_previa(potencia))
    st.caption(
        "Quintiles de los 179 municipios por su paro medio de 2019. Con una subida del "
        "0 % se ve la tasa de alertas sin subida añadida."
    )

    st.markdown("#### Comparación con otros métodos")
    subida = st.segmented_control(
        "Tamaño de la subida",
        ["5 %", "10 %"],
        default="5 %",
        required=True,
        key="subida_metodos",
    )
    columna = "potencia_5pct_2017_2019" if subida == "5 %" else "potencia_10pct_2017_2019"
    grafico(
        graficos.figura_metodos(
            validacion.curvas_metodos(v["curvas_metodos"]),
            validacion.puntos_metodos(resumen),
            columna,
            validacion.CURVA_DE,
            paleta,
        )
    )
    st.markdown(validacion.frase_compromiso(resumen))
    st.caption(
        "Puntos: cada método con su umbral. C y C centrado, con el umbral elegido en "
        "2012-2016 para dar las mismas alertas que el oficial en esos años. Alertas en "
        "calma y subidas sintéticas detectadas, en 2017-2019."
    )

    st.markdown("#### Limitaciones medidas")
    st.markdown("\n".join(f"- {texto}" for texto in validacion.limitaciones(mensual, resumen, potencia)))

    st.markdown("#### Propuesta para una versión 2")
    st.markdown(validacion.frase_propuesta_v2(resumen))
    st.dataframe(validacion.tabla_propuesta_v2(resumen), hide_index=True, width="stretch")

    with st.expander("Ver los datos de los gráficos"):
        mostrar_tabla(
            tabla_meses[["fecha", "evaluables", "con_alerta", "pct_alertas_evaluables"]]
            .sort_values("fecha", ascending=False)
            .reset_index(drop=True)
        )
        st.dataframe(validacion.tabla_potencia_ancha(potencia), hide_index=True, width="stretch")


# ---------------------------------------------------------------
# Página
# ---------------------------------------------------------------

st.logo(
    identidad.svg_para_tema(identidad.RUTA_LOGO, modo_oscuro()),
    icon_image=identidad.svg_para_tema(identidad.RUTA_ICONO, modo_oscuro()),
    size="large",
)

st.title("Pulso Laboral Madrid")

origen = datos.origen_datos()
if origen is None:
    mostrar_como_generar(
        "No se encuentran los datos de la aplicación: ni las tablas locales "
        "(`resultados/alertas.csv` y `datos/procesados/`) ni la copia de "
        "`datos/publicados/`."
    )

rutas = datos.rutas_datos(origen)

try:
    alertas = cargar_alertas(str(rutas["alertas"]), datos.marca_tiempo(rutas["alertas"]))
except ValueError as error:
    mostrar_como_generar(f"No se puede leer `{rutas['alertas'].name}`: {error}")

st.warning(AVISO, icon=":material/warning:")

if origen == "local" and datos.alertas_desactualizadas(rutas["alertas"]):
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
    st.caption(datos.texto_origen(origen, alertas, rutas["alertas"]))

paleta = graficos.paleta(modo_oscuro())
paro_edad = cargar_si_existe(rutas["paro_edad"], cargar_paro_edad)
contratos = cargar_si_existe(rutas["contratos"], cargar_contratos)
mapa = cargar_si_existe(rutas["mapa"], cargar_mapa)
poblacion = cargar_si_existe(rutas["poblacion"], cargar_poblacion)
clasificacion = cargar_si_existe(rutas["clasificacion"], cargar_clasificacion)
otros_metodos = cargar_si_existe(rutas["otros_metodos"], cargar_otros_metodos)
resultados_validacion = {
    "validacion_mensual": cargar_si_existe(rutas["validacion_mensual"], cargar_validacion_con_fechas),
    "potencia": cargar_si_existe(rutas["potencia"], cargar_validacion),
    "resumen_metodos": cargar_si_existe(rutas["resumen_metodos"], cargar_validacion),
    "curvas_metodos": cargar_si_existe(rutas["curvas_metodos"], cargar_validacion),
}

pestana_general, pestana_ficha, pestana_cambios, pestana_validacion = st.tabs(
    PESTANAS, key="pestana", on_change="rerun"
)

with pestana_general:
    vista_general(alertas, fecha, mapa, paleta, clasificacion)

with pestana_ficha:
    ficha(alertas, fecha, municipio, paro_edad, contratos, paleta, clasificacion, otros_metodos, poblacion)

with pestana_cambios:
    cambios_frente_al_limite(alertas, fecha, municipio, paleta)

with pestana_validacion:
    como_sabemos_que_funciona(resultados_validacion, paleta)

st.divider()
st.caption(
    f"Datos: [Portal de Datos Abiertos de la Comunidad de Madrid]({identidad.URL_PORTAL}), "
    f"con licencia [CC BY 4.0]({identidad.URL_LICENCIA}). Fuente: D. G. del Servicio "
    "Público de Empleo; población de la ficha: Censo de Población Anual (INE). Este "
    "proyecto los transforma: series mensuales y alertas experimentales calculadas."
)
st.caption(
    "Proyecto independiente para DATAMAD 2026; no es una herramienta oficial "
    f"de la Comunidad de Madrid. Método: [docs/metodologia.md]({validacion.URL_METODOLOGIA}). "
    "Columnas: `docs/contrato_alertas.md`."
)
