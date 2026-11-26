"""Población de 15 a 64 años del indicador de contexto de la ficha.

datos/publicados/poblacion_15_64.csv tiene la población de los 179 municipios
en todos los años del censo, y cada mes usa la población del año más reciente
que no sea posterior a ese mes: nunca información futura.
"""

import pandas as pd
import pytest

from conftest import PUBLICADOS
from datos_app import SIN_POBLACION, poblacion_del_mes, texto_paro_poblacion
from detectar_alertas import MUNICIPIOS_ESPERADOS
from preparar_poblacion import cruzar


ANIOS = [2021, 2022, 2023, 2024, 2025]


@pytest.fixture(scope="module")
def poblacion():
    return pd.read_csv(PUBLICADOS / "poblacion_15_64.csv", sep=";", encoding="utf-8-sig")


def test_los_179_municipios_tienen_poblacion_todos_los_anios(poblacion, alertas):
    assert poblacion["municipio"].nunique() == MUNICIPIOS_ESPERADOS
    assert set(poblacion["municipio"]) == set(alertas["municipio"])
    assert not poblacion.duplicated(["municipio", "anio"]).any()

    anios = poblacion.groupby("municipio")["anio"].apply(sorted)
    assert all(lista == ANIOS for lista in anios), "Municipios a los que les falta algún año"
    assert (poblacion["poblacion_15_64"] > 0).all()


def test_cada_mes_usa_su_anio_o_uno_anterior(poblacion, alertas):
    """Ningún mes usa la población de un año posterior."""
    madrid = poblacion[poblacion["municipio"].eq("Madrid")]
    for fecha in sorted(alertas["fecha"].unique()):
        fecha = pd.Timestamp(fecha)
        dato = poblacion_del_mes(madrid, "Madrid", fecha)
        if fecha.year < 2021:
            assert dato is None, fecha
        else:
            assert dato[0] == min(fecha.year, 2025), fecha
            assert dato[0] <= fecha.year, fecha


@pytest.mark.parametrize(
    "mes, anio",
    [("2020-12-01", None), ("2021-01-01", 2021), ("2025-12-01", 2025), ("2026-10-01", 2025)],
)
def test_todos_los_municipios_sin_informacion_futura(poblacion, mes, anio):
    fecha = pd.Timestamp(mes)
    for municipio in poblacion["municipio"].unique():
        dato = poblacion_del_mes(poblacion, municipio, fecha)
        assert (dato[0] if dato else None) == anio, municipio


def test_un_anio_sin_datos_usa_el_anterior_y_no_el_siguiente():
    sintetica = pd.DataFrame(
        {"municipio": ["A", "A"], "anio": [2021, 2023], "poblacion_15_64": [1000, 2000]}
    )
    assert poblacion_del_mes(sintetica, "A", pd.Timestamp("2022-06-01")) == (2021, 1000)
    assert poblacion_del_mes(sintetica, "A", pd.Timestamp("2023-01-01")) == (2023, 2000)
    assert poblacion_del_mes(sintetica, "A", pd.Timestamp("2020-12-01")) is None


def test_texto_de_la_ficha(poblacion, alertas):
    fila = alertas.loc[
        alertas["municipio"].eq("Madrid") & alertas["fecha"].eq(pd.Timestamp("2026-10-01"))
    ].iloc[0]
    habitantes = poblacion.loc[
        poblacion["municipio"].eq("Madrid") & poblacion["anio"].eq(2025), "poblacion_15_64"
    ].item()
    etiqueta, valor = texto_paro_poblacion(fila, poblacion)
    assert etiqueta == (
        "Paro registrado por cada 1.000 habitantes de 15 a 64 años "
        "(población del censo anual a 1 de enero de 2025)"
    )
    esperado = f"{1000 * fila['paro_total'] / habitantes:.1f}".replace(".", ",")
    assert valor == esperado

    antigua = alertas.loc[
        alertas["municipio"].eq("Madrid") & alertas["fecha"].eq(pd.Timestamp("2020-12-01"))
    ].iloc[0]
    assert texto_paro_poblacion(antigua, poblacion)[1] == SIN_POBLACION


def test_la_preparacion_se_detiene_si_falta_un_municipio():
    correspondencia = pd.DataFrame({"municipio": ["A", "B"], "codigo_ine": ["28001", "28002"]})
    censo = pd.DataFrame({"codigo_ine": ["28001"], "anio": [2025], "poblacion_15_64": [10]})
    with pytest.raises(ValueError, match="sin población"):
        cruzar(censo, correspondencia)


def test_la_preparacion_se_detiene_si_falta_un_anio():
    correspondencia = pd.DataFrame({"municipio": ["A", "B"], "codigo_ine": ["28001", "28002"]})
    censo = pd.DataFrame(
        {
            "codigo_ine": ["28001", "28001", "28002"],
            "anio": [2024, 2025, 2025],
            "poblacion_15_64": [10, 11, 12],
        }
    )
    with pytest.raises(ValueError, match="falta algún año"):
        cruzar(censo, correspondencia)
