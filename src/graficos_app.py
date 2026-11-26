"""Gráficos Plotly de la aplicación.

Solo construye figuras a partir de tablas ya preparadas por
src/datos_app.py. No lee archivos ni contiene código de Streamlit.

Colores: azul para los datos, gris para lo que acompaña y naranja de
estado solo para las alertas experimentales, siempre con etiqueta o
leyenda. El fondo, la tipografía y la cuadrícula los pone el tema de
Streamlit, que se adapta al modo claro u oscuro.
"""

import plotly.graph_objects as go

from src import datos_app as datos


PALETAS = {
    "claro": {
        "serie": "#2a78d6",
        "serie_suave": "#86b6ef",
        "gris": "#898781",
        "gris_suave": "#c3c2b7",
        "alerta": "#ec835a",
        "tinta": "#52514e",
        "superficie": "#ffffff",
        # Pestaña «¿Cómo sabemos que funciona?». Rampa de un solo tono para los
        # quintiles de tamaño (de menos a más paro) y, en la figura de métodos,
        # azul para el oficial, verde agua para la propuesta de versión 2 y gris
        # para los demás, siempre con su nombre al lado. Validadas para
        # daltonismo frente al fondo de cada modo.
        "rampa": ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"],
        "propuesta": "#1baf7a",
    },
    "oscuro": {
        "serie": "#3987e5",
        "serie_suave": "#184f95",
        "gris": "#898781",
        "gris_suave": "#383835",
        "alerta": "#ec835a",
        "tinta": "#c3c2b7",
        "superficie": "#0e1117",
        "rampa": ["#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4"],
        "propuesta": "#199e70",
    },
}


# Ancho de una barra mensual en un eje de fechas, en milisegundos (~24 días).
ANCHO_BARRA_MES = 24 * 24 * 60 * 60 * 1000


def paleta(oscuro=False):
    return PALETAS["oscuro" if oscuro else "claro"]


def _base(fig, alto, leyenda=False):
    fig.update_layout(
        height=alto,
        separators=",.",
        margin=dict(l=8, r=8, t=36 if leyenda else 12, b=8),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(namelength=-1),
    )
    fig.update_xaxes(showgrid=False)
    return fig


def _eje_fechas(fig, fechas):
    """Marcas del eje en español, terminando en el mes elegido."""
    fechas = list(fechas)
    n = len(fechas)
    paso = 3 if n <= 36 else 12 if n <= 120 else 24
    marcas = fechas[::-1][::paso][::-1]
    fig.update_xaxes(
        tickmode="array",
        tickvals=marcas,
        ticktext=[datos.mes_corto(f) for f in marcas],
        hoverformat="%m/%Y",
    )


def figura_paro(serie, fecha, p):
    """Paro registrado de los últimos meses, con el mes elegido destacado."""
    fig = go.Figure()
    fig.add_scatter(
        x=serie["fecha"],
        y=serie["paro_total"],
        mode="lines+markers",
        line=dict(color=p["serie"], width=2),
        marker=dict(size=6, color=p["serie"]),
        customdata=[datos.nombre_mes(f) for f in serie["fecha"]],
        hovertemplate="%{customdata}<br>Paro registrado: %{y:,.0f} personas<extra></extra>",
        name="Paro registrado",
    )

    elegido = serie.loc[serie["fecha"].eq(fecha)]
    if len(elegido):
        valor = elegido["paro_total"].iloc[0]
        fig.add_scatter(
            x=[fecha],
            y=[valor],
            mode="markers",
            marker=dict(size=14, color=p["serie"], line=dict(color=p["superficie"], width=2)),
            hoverinfo="skip",
            showlegend=False,
        )
        # La etiqueta va hacia el interior del gráfico: debajo del punto si
        # está en la mitad alta, encima si está en la baja.
        mitad = (serie["paro_total"].max() + serie["paro_total"].min()) / 2
        fig.add_annotation(
            x=fecha,
            y=valor,
            text=f"<b>{datos.mes_corto(fecha)}: {datos.numero(valor)}</b>",
            showarrow=True,
            arrowhead=0,
            ax=-44,
            ay=30 if valor >= mitad else -30,
            xanchor="right",
            bgcolor=p["superficie"],
            borderpad=3,
        )

    _base(fig, 300)
    _eje_fechas(fig, serie["fecha"])
    fig.update_yaxes(title_text="Personas en paro", tickformat=",.0f")
    return fig


def figura_edad(cambios, grupo_principal, p):
    """Cambio mensual de cada grupo de edad, con el de mayor aumento destacado."""
    principal = grupo_principal if isinstance(grupo_principal, str) else None
    valores = cambios["cambio"].astype(float)

    textos = []
    for grupo, valor in zip(cambios["grupo_edad"], valores):
        texto = datos.numero(valor, signo=True)
        if grupo == principal:
            texto = f"<b>{texto} · Grupo con mayor aumento</b>"
        textos.append(texto)

    fig = go.Figure()
    fig.add_bar(
        y=cambios["grupo_edad"],
        x=valores,
        orientation="h",
        marker=dict(
            color=[p["serie"] if g == principal else p["gris"] for g in cambios["grupo_edad"]],
            cornerradius=4,
        ),
        text=textos,
        textposition="outside",
        cliponaxis=False,
        customdata=cambios[["paro_anterior", "paro"]].to_numpy(),
        hovertemplate=(
            "%{y}<br>Cambio: %{x:+,.0f} personas"
            "<br>De %{customdata[0]:,.0f} a %{customdata[1]:,.0f}<extra></extra>"
        ),
    )

    minimo, maximo = min(0.0, valores.min()), max(0.0, valores.max())
    amplitud = (maximo - minimo) or 1.0
    izquierda = minimo - (0.25 * amplitud if minimo < 0 else 0.02 * amplitud)
    derecha = maximo + (0.95 if principal else 0.25) * amplitud

    _base(fig, 210)
    fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), bargap=0.35)
    fig.update_xaxes(
        range=[izquierda, derecha],
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor=p["tinta"],
        tickformat=",.0f",
        title_text="Cambio respecto al mes anterior (personas)",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=datos.GRUPOS_EDAD[::-1])
    return fig


def figura_contratos(serie, fecha, p):
    """Contratos registrados en centros de trabajo del municipio, en su propio
    gráfico: sin eje compartido ni cocientes con el paro. El mes elegido, destacado."""
    fig = go.Figure()
    fig.add_bar(
        x=serie["fecha"],
        y=serie["contratos"],
        marker=dict(
            color=[p["serie"] if f == fecha else p["serie_suave"] for f in serie["fecha"]],
            cornerradius=3,
        ),
        customdata=[datos.nombre_mes(f) for f in serie["fecha"]],
        hovertemplate="%{customdata}<br>Contratos: %{y:,.0f}<extra></extra>",
        name="Contratos",
    )
    _base(fig, 230)
    fig.update_layout(bargap=0.2)
    _eje_fechas(fig, serie["fecha"])
    fig.update_yaxes(title_text="Contratos", tickformat=",.0f")
    return fig


def figura_mapa(mapa, tabla, p):
    """Municipios coloreados por el estado del mes.

    Mismo código de color que la pestaña de cambios: azul sin alerta, naranja
    alerta experimental y gris no evaluable. Una traza por estado, cada una
    con solo sus municipios, para que la leyenda tenga una entrada por estado
    sin repetir la geometría.
    """
    colores = {"alerta": p["alerta"], "sin_alerta": p["serie"], "no_evaluable": p["gris_suave"]}
    fig = go.Figure()

    for categoria, etiqueta in datos.CATEGORIAS_MAPA.items():
        filas = tabla.loc[tabla["categoria"].eq(categoria)]
        if filas.empty:
            continue
        nombres = set(filas["municipio"])
        geometria = {
            "type": "FeatureCollection",
            "features": [f for f in mapa["features"] if f["properties"]["municipio"] in nombres],
        }
        fig.add_choropleth(
            geojson=geometria,
            featureidkey="properties.municipio",
            locations=filas["municipio"],
            z=[1] * len(filas),
            colorscale=[[0, colores[categoria]], [1, colores[categoria]]],
            showscale=False,
            marker=dict(line=dict(color=p["superficie"], width=0.6)),
            name=f"{etiqueta} ({datos.numero(len(filas))})",
            showlegend=True,
            customdata=filas[["municipio", "estado", "texto_cambio", "texto_limite"]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}"
                "<br>Cambio mensual: %{customdata[2]}"
                "<br>Límite de alerta: %{customdata[3]}<extra></extra>"
            ),
        )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=34, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
        clickmode="event+select",
        dragmode=False,
    )
    return fig


def figura_cambios(serie, fecha, p):
    """Cambio mensual frente al límite de alerta, hasta el mes elegido."""
    meses = [datos.nombre_mes(f) for f in serie["fecha"]]
    serie = serie.assign(mes=meses)

    alerta = serie["estado_detector"].eq("alerta_experimental")
    no_evaluable = serie["estado_detector"].isin(datos.ESTADOS_NO_EVALUABLES)

    fig = go.Figure()
    grupos = [
        (~alerta & ~no_evaluable, "Cambio mensual", p["serie"]),
        (alerta, "Cambio mensual con alerta experimental", p["alerta"]),
        (no_evaluable, "Cambio mensual de un mes no evaluable", p["gris_suave"]),
    ]
    for mascara, nombre, color in grupos:
        filas = serie.loc[mascara]
        if filas.empty:
            continue
        fig.add_bar(
            x=filas["fecha"],
            y=filas["cambio_mensual"].astype(float),
            # Mismo ancho en todas las trazas; si no, Plotly ensancha las
            # barras de las trazas con meses salteados, como las alertas.
            width=ANCHO_BARRA_MES,
            name=nombre,
            marker=dict(color=color, cornerradius=2),
            customdata=filas["mes"],
            hovertemplate="%{customdata}: %{y:+,.0f} personas<extra>" + nombre + "</extra>",
        )

    fig.add_scatter(
        x=serie["fecha"],
        y=serie["referencia_cambio"],
        mode="lines",
        line=dict(color=p["gris"], width=1.5),
        name="Cambio habitual",
        connectgaps=False,
        hovertemplate="%{y:+,.0f}<extra>Cambio habitual</extra>",
    )
    fig.add_scatter(
        x=serie["fecha"],
        y=serie["limite_superior"],
        mode="lines",
        line=dict(color=p["tinta"], width=2, dash="dash"),
        name="Límite de alerta",
        connectgaps=False,
        hovertemplate="%{y:+,.1f}<extra>Límite de alerta</extra>",
    )

    elegido = serie.loc[serie["fecha"].eq(fecha)]
    if len(elegido) and elegido["cambio_mensual"].notna().iloc[0]:
        valor = float(elegido["cambio_mensual"].iloc[0])
        fig.add_annotation(
            x=fecha,
            y=valor,
            text=f"<b>{datos.mes_corto(fecha)}: {datos.numero(valor, signo=True)}</b>",
            showarrow=True,
            arrowhead=0,
            ax=-48,
            ay=-48 if valor >= 0 else 48,
            xanchor="right",
            bgcolor=p["superficie"],
            bordercolor=p["tinta"],
            borderwidth=1,
            borderpad=3,
        )

    _base(fig, 380, leyenda=True)
    fig.update_layout(barmode="overlay", bargap=0.15, hovermode="x unified")
    _eje_fechas(fig, serie["fecha"])
    fig.update_yaxes(
        title_text="Cambio respecto al mes anterior (personas)",
        tickformat=",.0f",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor=p["tinta"],
    )
    return fig


# ---------------------------------------------------------------
# ¿Cómo sabemos que funciona?
# ---------------------------------------------------------------

def figura_alertas_por_mes(tabla, fecha_episodio, anos_calma, p):
    """Municipios con alerta por mes, con la calma de 2017-2019 sombreada y
    abril de 2020 marcado."""
    fig = go.Figure()
    inicio_calma = f"{anos_calma[0]}-01-01"
    fin_calma = f"{anos_calma[-1]}-12-31"
    fig.add_vrect(
        x0=inicio_calma,
        x1=fin_calma,
        fillcolor=p["gris_suave"],
        opacity=0.35,
        line_width=0,
        layer="below",
        annotation_text=f"Calma {anos_calma[0]}-{anos_calma[-1]}",
        annotation_position="top left",
        annotation_font_color=p["tinta"],
    )
    fig.add_scatter(
        x=tabla["fecha"],
        y=tabla["con_alerta"],
        mode="lines",
        line=dict(color=p["serie"], width=2),
        customdata=tabla["texto"],
        hovertemplate="%{customdata}<extra></extra>",
        name="Municipios con alerta",
    )

    episodio = tabla.loc[tabla["fecha"].eq(fecha_episodio)]
    if len(episodio):
        valor = int(episodio["con_alerta"].iloc[0])
        fig.add_scatter(
            x=[fecha_episodio],
            y=[valor],
            mode="markers",
            marker=dict(size=12, color=p["alerta"], line=dict(color=p["superficie"], width=2)),
            hoverinfo="skip",
            showlegend=False,
        )
        fig.add_annotation(
            x=fecha_episodio,
            y=valor,
            text=f"<b>{datos.mes_corto(fecha_episodio)}: {datos.numero(valor)} municipios</b>",
            showarrow=True,
            arrowhead=0,
            ax=60,
            ay=10,
            xanchor="left",
            bgcolor=p["superficie"],
            borderpad=3,
        )

    _base(fig, 340)
    fig.update_xaxes(dtick="M24", tickformat="%Y", hoverformat="%m/%Y")
    fig.update_yaxes(title_text="Municipios con alerta", rangemode="tozero")
    return fig


def figura_potencia_tamano(tabla, nombres, p):
    """Subidas detectadas según su tamaño, por quintil de paro del municipio."""
    fig = go.Figure()
    series = list(zip(["Q1", "Q2", "Q3", "Q4", "Q5"], p["rampa"])) + [("Todos", p["tinta"])]
    for quintil, color in series:
        filas = tabla.loc[tabla["quintil"].eq(quintil)].sort_values("subida_pct")
        todos = quintil == "Todos"
        fig.add_scatter(
            x=filas["subida_pct"],
            y=filas["tasa_deteccion_pct"],
            mode="lines+markers",
            line=dict(color=color, width=3 if todos else 2),
            marker=dict(size=8, color=color, line=dict(color=p["superficie"], width=1)),
            name=nombres[quintil],
            hovertemplate=(
                "Subida del %{x:,.0f} %: detectada en el %{y:,.1f} % de los meses"
                f"<extra>{nombres[quintil]}</extra>"
            ),
        )
    _base(fig, 380, leyenda=True)
    fig.update_layout(margin=dict(l=8, r=8, t=60, b=8))
    subidas = sorted(tabla["subida_pct"].unique())
    fig.update_xaxes(
        tickmode="array",
        tickvals=subidas,
        ticktext=[f"{datos.numero(s)} %" for s in subidas],
        title_text="Subida añadida al cambio de un mes (% del paro del mes anterior)",
    )
    fig.update_yaxes(range=[0, 100], ticksuffix=" %", title_text="Meses con la subida detectada")
    return fig


# El oficial y la propuesta quedan muy cerca: sus etiquetas van a lados opuestos.
POSICION_ETIQUETA_METODO = {
    "oficial": "bottom right",
    "Cc_fm": "top left",
    "C_fm": "middle left",
    "A": "bottom right",
    "B": "top left",
}


def figura_metodos(curvas, puntos, columna, curva_de, p):
    """Potencia frente a alertas en calma de cada método.

    Líneas: cada método al mover su umbral. Puntos: el umbral de cada uno. El
    oficial en azul, la propuesta de versión 2 en verde agua y los demás en
    gris, todos con su nombre al lado.
    """
    colores = {"oficial": p["serie"], "Cc_fm": p["propuesta"]}
    fig = go.Figure()

    for _, punto in puntos.iterrows():
        metodo = punto["metodo"]
        color = colores.get(metodo, p["gris"])
        curva = curvas.loc[curvas["metodo"].eq(curva_de[metodo])]
        fig.add_scatter(
            x=curva["pct_alertas_calma"],
            y=curva[columna],
            mode="lines",
            line=dict(color=color, width=2 if metodo in colores else 1.2),
            opacity=0.9 if metodo in colores else 0.6,
            hoverinfo="skip",
            showlegend=False,
        )

    for _, punto in puntos.iterrows():
        metodo = punto["metodo"]
        color = colores.get(metodo, p["gris"])
        fig.add_scatter(
            x=[punto["pct_alertas_calma"]],
            y=[punto[columna]],
            mode="markers+text",
            marker=dict(size=12, color=color, line=dict(color=p["superficie"], width=2)),
            text=[f"<b>{punto['nombre']}</b>" if metodo in colores else punto["nombre"]],
            textposition=POSICION_ETIQUETA_METODO.get(metodo, "top center"),
            textfont=dict(color=p["tinta"]),
            name=punto["nombre"],
            hovertemplate=(
                f"<b>{punto['nombre']}</b><br>Alertas en calma: %{{x:,.2f}} %"
                "<br>Subidas detectadas: %{y:,.1f} %<extra></extra>"
            ),
            showlegend=False,
        )

    _base(fig, 440)
    fig.update_xaxes(
        type="log",
        range=[-1.3, 1.5],
        tickvals=[0.1, 0.2, 0.5, 1, 2, 5, 10, 20],
        ticktext=["0,1 %", "0,2 %", "0,5 %", "1 %", "2 %", "5 %", "10 %", "20 %"],
        title_text="Alertas en calma, 2017-2019 (escala logarítmica): menos es mejor",
        showgrid=True,
    )
    fig.update_yaxes(range=[0, 100], ticksuffix=" %", title_text="Subidas detectadas, 2017-2019: más es mejor")
    return fig
