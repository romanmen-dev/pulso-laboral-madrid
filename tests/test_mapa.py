"""datos/publicados/municipios_mapa.geojson: una geometría por municipio."""

from collections import Counter

from detectar_alertas import MUNICIPIOS_ESPERADOS


def anillos(geometria):
    if geometria["type"] == "Polygon":
        return geometria["coordinates"]
    return [anillo for poligono in geometria["coordinates"] for anillo in poligono]


def test_los_179_municipios_tienen_exactamente_una_geometria(mapa, alertas):
    entidades = mapa["features"]
    municipios = [e["properties"]["municipio"] for e in entidades]
    codigos = [e["properties"]["codigo_ine"] for e in entidades]

    assert len(entidades) == MUNICIPIOS_ESPERADOS
    assert [m for m, n in Counter(municipios).items() if n > 1] == []
    assert [c for c, n in Counter(codigos).items() if n > 1] == []

    tabla = set(alertas["municipio"])
    assert sorted(tabla - set(municipios)) == [], "Municipios sin geometría"
    assert sorted(set(municipios) - tabla) == [], "Geometrías sin municipio"


def test_cada_geometria_es_un_poligono_cerrado(mapa):
    for entidad in mapa["features"]:
        geometria = entidad["geometry"]
        nombre = entidad["properties"]["municipio"]
        assert geometria and geometria["type"] in {"Polygon", "MultiPolygon"}, nombre
        assert anillos(geometria), nombre
        for anillo in anillos(geometria):
            assert len(anillo) >= 4 and anillo[0] == anillo[-1], nombre
