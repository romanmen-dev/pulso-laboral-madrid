"""La aplicación funciona solo con datos/publicados/ (AppTest de Streamlit).

Se ocultan las tablas locales para que la aplicación use la copia publicada,
como en Streamlit Community Cloud. Las pruebas solo necesitan requirements.txt
y pytest.
"""

import pytest

from conftest import RAIZ


pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


TIEMPO_MAXIMO = 120


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(RAIZ))
    from src import datos_app

    # Rutas locales inexistentes: la aplicación tiene que usar datos/publicados/.
    monkeypatch.setattr(
        datos_app,
        "ARCHIVOS_APP",
        {clave: tmp_path / ruta.name for clave, ruta in datos_app.ARCHIVOS_APP.items()},
    )
    assert datos_app.origen_datos() == "publicado"

    prueba = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=TIEMPO_MAXIMO)
    return prueba.run()


def textos(app):
    elementos = [*app.markdown, *app.caption, *app.warning, *app.info]
    return [e.value for e in elementos]


def contiene(app, fragmento):
    return any(fragmento in texto for texto in textos(app))


def sin_errores(app):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def test_usa_la_copia_publicada(app):
    sin_errores(app)
    assert contiene(app, "datos/publicados")
    assert [t.label for t in app.tabs] == [
        "Vista general",
        "Ficha de municipio",
        "Cambios frente al límite",
        "¿Cómo sabemos que funciona?",
    ]


def test_vista_general_con_el_tipo_de_cada_alerta(app):
    sin_errores(app)
    assert contiene(
        app, "De las 15 alertas de este mes, 2 son locales: destacan también frente al resto de la Comunidad."
    )
    tabla = next(d.value for d in app.dataframe if "Tipo" in d.value.columns)
    assert len(tabla) == 15
    assert set(tabla["Tipo"]) == {"Local", "Regional"}


def test_pestana_como_sabemos_que_funciona(app):
    sin_errores(app)
    assert contiene(app, "En abril de 2020 saltó la alerta en el **67,5 %**")
    assert contiene(app, "frente al **5,5 %** en los abriles normales")
    assert contiene(app, "Propuesta para una versión 2")
    assert contiene(app, "docs/metodologia.md")
    assert contiene(app, "**tasa de alertas en calma**")
    assert contiene(app, "**Sensibilidad ante subidas sintéticas.**")
    assert contiene(
        app,
        "En 2015-2019, contando solo los meses que no tenían ya alerta sin la subida, se detecta el 27,0 % "
        "de las subidas del 5 % y el 53,2 % de las del 10 %",
    )
    assert contiene(app, "**Versión actual de los datos.**")
    assert contiene(app, "**Se mantiene el detector oficial** por continuidad")
    propuesta = next(d.value for d in app.dataframe if "Propuesta v2 (C centrado)" in d.value.columns)
    assert "C ampliado" in propuesta.columns

    app.segmented_control(key="subida_metodos").set_value("10 %").run()
    sin_errores(app)


def test_sin_lenguaje_retirado(app):
    """La app no habla de «falsas alarmas» ni de «potencia», ni compara con el 0,135 % en «veces»."""
    sin_errores(app)
    for texto in textos(app):
        minusculas = texto.lower()
        assert "falsas alarmas" not in minusculas or "no de falsas alarmas" in minusculas, texto
        assert "potencia" not in minusculas, texto
        assert "veces el" not in minusculas, texto


@pytest.mark.parametrize(
    "municipio, esperado",
    [
        (
            "Madrid",
            "**Alerta regional:** la subida es compatible con la evolución del resto de la Comunidad.",
        ),
        ("Soto del Real", "**Alerta local:** la subida destaca también frente al resto de la Comunidad."),
        ("Velilla de San Antonio", "La fuente repite 368 contratos"),
        ("Quijorna", "**No evaluable** en octubre de 2026"),
    ],
)
def test_ficha_de_municipio(app, municipio, esperado):
    app.selectbox(key="municipio").set_value(municipio).run()

    sin_errores(app)
    assert any(s.value == f"{municipio} · octubre de 2026" for s in app.subheader)
    assert contiene(app, esperado)
    assert contiene(app, "**Otros métodos:**")
