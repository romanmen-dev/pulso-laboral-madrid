"""Identidad visual de la aplicación: logo e icono propios (assets/).

Los SVG cambian de color con el modo del sistema (prefers-color-scheme).
Como en Streamlit se puede elegir un tema distinto del del sistema, la
aplicación fuerza en el logo los colores del tema activo.

El carmesí de marca es el color de acento del tema (.streamlit/config.toml).
No se usa en los gráficos, cuya paleta está en src/graficos_app.py.
"""

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
RUTA_LOGO = RAIZ / "assets" / "logo_horizontal.svg"
RUTA_ICONO = RAIZ / "assets" / "icono.svg"

URL_PORTAL = "https://datos.comunidad.madrid/"
URL_LICENCIA = "https://creativecommons.org/licenses/by/4.0/legalcode.es"

COLORES = {
    "claro": {"carmesi": "#C8102E", "tinta": "#1F2328"},
    "oscuro": {"carmesi": "#E0475B", "tinta": "#F2F1EE"},
}


def svg_para_tema(ruta, oscuro=False):
    """Devuelve el SVG con los colores del tema activo, sin depender del sistema."""
    c = COLORES["oscuro" if oscuro else "claro"]
    forzado = (
        f".linea {{ stroke: {c['carmesi']} !important; }}\n"
        f"    .estrella {{ fill: {c['carmesi']} !important; stroke: {c['carmesi']} !important; }}\n"
        f"    .acento {{ fill: {c['carmesi']} !important; }}\n"
        f"    .tinta {{ fill: {c['tinta']} !important; }}\n"
    )
    svg = ruta.read_text(encoding="utf-8")
    return svg.replace("</style>", f"  {forzado}  </style>", 1)
