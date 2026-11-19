"""Investigación de las incidencias de los contratos de trabajo.

Reproduce las comprobaciones anotadas en docs/decisiones.md (19/11/2026):
la caída de mayo de 2026, los valores repetidos de Velilla de San Antonio
y la nota del portal sobre el redondeo a múltiplos de 5.

Solo lee datos/originales/ y datos/procesados/. No modifica ningún dato y
no descarga nada: la comparación con el archivo del portal se hizo aparte
y su huella SHA-256 se imprime para poder repetirla.
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from preparar_datos import NOMBRES_CONTRATOS_A_PARO


RAIZ = Path(__file__).resolve().parents[1]
RUTA_ORIGINAL = RAIZ / "datos" / "originales" / "contratos_municipio.csv"
RUTA_PROCESADO = RAIZ / "datos" / "procesados" / "contratos_mensuales.csv"
RUTA_PARO = RAIZ / "datos" / "procesados" / "paro_total_mensual.csv"
SALIDA = RAIZ / "resultados" / "investigacion_contratos"

ANIO = 2026
MES_INCIDENCIA = 5  # Mayo, comparado con abril y junio del mismo año.
UMBRAL_CAIDA = 0.70  # Cociente por debajo del cual se cuenta una caída de más del 30 %.
MINIMO_RACHA = 50  # Valor mínimo para buscar meses consecutivos idénticos.
MESES_RACHA = 3

INDICADOR_SERIE = "Serie"
TASA_MENSUAL = "Tasa de variación sobre el periodo anterior"
TASA_ANUAL = "Tasa de variación sobre igual periodo del año anterior"

lineas = []


def informar(texto=""):
    print(texto)
    lineas.append(str(texto))


def titulo(texto):
    informar()
    informar("=" * 72)
    informar(texto)
    informar("=" * 72)


def miles(valor):
    return f"{valor:,.0f}".replace(",", ".")


def guardar_csv(tabla, nombre):
    tabla.to_csv(SALIDA / nombre, sep=";", index=False, encoding="utf-8-sig")
    informar(f"  -> {SALIDA.relative_to(RAIZ) / nombre}")


def leer_datos():
    for ruta in (RUTA_ORIGINAL, RUTA_PROCESADO, RUTA_PARO):
        if not ruta.is_file():
            raise FileNotFoundError(
                f"No se encuentra {ruta}. Ejecuta antes src/descargar_datos.py "
                "y src/preparar_datos.py."
            )

    original = pd.read_csv(
        RUTA_ORIGINAL, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False
    )
    original["v"] = pd.to_numeric(original["Valor"])

    procesado = pd.read_csv(
        RUTA_PROCESADO, sep=";", encoding="utf-8-sig", parse_dates=["fecha"]
    )
    paro = pd.read_csv(RUTA_PARO, sep=";", encoding="utf-8-sig", parse_dates=["fecha"])
    return original, procesado, paro


def serie_mensual(original):
    serie = original[original["Indicador"].eq(INDICADOR_SERIE)].copy()
    serie["fecha"] = pd.to_datetime(serie["Año"] + "-" + serie["Periodo"].str[1:] + "-01")
    serie["municipio"] = serie["Territorio"].replace(NOMBRES_CONTRATOS_A_PARO)
    return serie


def mes(anio, numero):
    return pd.Timestamp(year=anio, month=numero, day=1)


def comprobar_origen(serie, procesado):
    titulo("1a. ¿La caída está en el original o aparece al preparar los datos?")
    for numero in (MES_INCIDENCIA - 1, MES_INCIDENCIA, MES_INCIDENCIA + 1):
        fecha = mes(ANIO, numero)
        total_original = serie.loc[serie["fecha"].eq(fecha), "v"].sum()
        total_procesado = procesado.loc[procesado["fecha"].eq(fecha), "contratos"].sum()
        informar(
            f"  {fecha:%Y-%m}: original {miles(total_original)} | "
            f"procesado {miles(total_procesado)}"
        )

    cruce = serie[["municipio", "fecha", "v"]].merge(
        procesado[["municipio", "fecha", "contratos"]],
        on=["municipio", "fecha"],
        how="outer",
        indicator=True,
    )
    informar(
        f"  Cruce completo: {cruce['_merge'].eq('both').sum()} pares en ambos, "
        f"{cruce['_merge'].ne('both').sum()} sin pareja, "
        f"{int((cruce['v'] != cruce['contratos']).sum())} valores distintos."
    )


def comprobar_filas(original):
    titulo("1b. Filas del original en los meses comparados")
    periodos = [f"M{numero:02d}" for numero in (MES_INCIDENCIA - 1, MES_INCIDENCIA, MES_INCIDENCIA + 1)]
    filas = original[original["Año"].eq(str(ANIO)) & original["Periodo"].isin(periodos)]
    informar(pd.crosstab(filas["Indicador"], filas["Periodo"]).to_string())

    territorios = {
        periodo: set(filas.loc[filas["Periodo"].eq(periodo) & filas["Indicador"].eq(INDICADOR_SERIE), "Territorio"])
        for periodo in periodos
    }
    anterior, incidencia, siguiente = periodos
    informar(
        f"  Municipios con valor mensual: {[len(t) for t in territorios.values()]}. "
        f"Faltan en el mes de la incidencia: "
        f"{sorted((territorios[anterior] | territorios[siguiente]) - territorios[incidencia])}"
    )
    informar(f"  Indicadores del original: {original['Indicador'].unique().tolist()}")
    informar(
        "  'Estado dato' en el año: "
        f"{original.loc[original['Año'].eq(str(ANIO)), 'Estado dato'].value_counts().to_dict()}"
    )


def comprobar_tasas(original, tabla):
    titulo("1b'. Tasas publicadas por la fuente para el mes de la incidencia")
    tasas = original[
        original["Año"].eq(str(ANIO)) & original["Periodo"].eq(f"M{MES_INCIDENCIA:02d}")
    ].pivot(index="Territorio", columns="Indicador", values="v")

    fecha = mes(ANIO, MES_INCIDENCIA)
    calculada_mes = (100 * (tabla[fecha] / tabla[mes(ANIO, MES_INCIDENCIA - 1)] - 1)).round(1)
    calculada_anual = (100 * (tabla[fecha] / tabla[mes(ANIO - 1, MES_INCIDENCIA)] - 1)).round(1)

    for nombre, publicada, calculada in (
        ("mensual", tasas[TASA_MENSUAL], calculada_mes),
        ("anual", tasas[TASA_ANUAL], calculada_anual),
    ):
        hay = publicada.notna()
        coinciden = ((publicada - calculada).abs() <= 0.1) & hay
        informar(
            f"  Tasa {nombre}: publicada en {int(hay.sum())} municipios, "
            f"coincide con la calculada en {int(coinciden.sum())}. "
            f"Mediana publicada: {publicada.median():.1f} %."
        )
    informar(
        f"  Madrid: mensual {tasas.loc['Madrid', TASA_MENSUAL]} %, "
        f"anual {tasas.loc['Madrid', TASA_ANUAL]} %."
    )


def comprobar_municipios(tabla):
    titulo("1c. Cociente entre el mes de la incidencia y la media del mes anterior y el siguiente")
    anterior = tabla[mes(ANIO, MES_INCIDENCIA - 1)]
    incidencia = tabla[mes(ANIO, MES_INCIDENCIA)]
    siguiente = tabla[mes(ANIO, MES_INCIDENCIA + 1)]
    media = (anterior + siguiente) / 2
    cociente = (incidencia / media).replace([np.inf, -np.inf], np.nan)

    resultado = pd.DataFrame(
        {
            "municipio": tabla.index,
            "mes_anterior": anterior.to_numpy(),
            "mes_incidencia": incidencia.to_numpy(),
            "mes_siguiente": siguiente.to_numpy(),
            "cociente": cociente.round(3).to_numpy(),
        }
    ).sort_values("cociente")

    comparables = cociente.notna()
    informar(f"  Municipios: {len(tabla)} | comparables: {int(comparables.sum())}")
    informar(f"  Sin cociente (media 0): {sorted(media.index[media.eq(0)])}")
    informar(f"  Bajan (cociente < 1): {int((cociente < 1).sum())}")
    informar(f"  Caen más de un 30 % (cociente < {UMBRAL_CAIDA}): {int((cociente < UMBRAL_CAIDA).sum())}")
    informar(f"  No bajan (cociente >= 1): {int((cociente >= 1).sum())}")
    informar(f"  Cuartiles: {cociente.quantile([0.25, 0.5, 0.75]).round(2).to_dict()}")
    informar(f"  Total de los municipios: {incidencia.sum() / media.sum():.3f}")
    guardar_csv(resultado, f"cociente_{ANIO}_{MES_INCIDENCIA:02d}_por_municipio.csv")


def comprobar_estacionalidad(tabla):
    titulo("1d. El mismo cociente en los años anteriores")
    filas = []
    for anio in sorted({f.year for f in tabla.columns}):
        fechas = [mes(anio, MES_INCIDENCIA + d) for d in (-1, 0, 1)]
        if not all(f in tabla.columns for f in fechas):
            continue
        anterior, incidencia, siguiente = (tabla[f] for f in fechas)
        media = (anterior + siguiente) / 2
        cociente = (incidencia / media).replace([np.inf, -np.inf], np.nan)
        filas.append(
            {
                "anio": anio,
                "mes_anterior": int(anterior.sum()),
                "mes_incidencia": int(incidencia.sum()),
                "mes_siguiente": int(siguiente.sum()),
                "cociente_total": round(incidencia.sum() / media.sum(), 3),
                "mediana_municipal": round(cociente.median(), 3),
                "municipios_caida_mas_30": int((cociente < UMBRAL_CAIDA).sum()),
            }
        )
    resultado = pd.DataFrame(filas)
    informar(resultado.to_string(index=False))
    previos = resultado.loc[resultado["anio"] < ANIO, "cociente_total"]
    informar(
        f"  Años anteriores: cociente total entre {previos.min()} y {previos.max()} "
        f"(media {previos.mean():.3f})."
    )
    guardar_csv(resultado, f"cociente_mes_{MES_INCIDENCIA:02d}_por_anio.csv")


def comprobar_paro(paro):
    titulo("1e. Contexto: paro registrado en los mismos meses")
    for numero in (MES_INCIDENCIA - 1, MES_INCIDENCIA, MES_INCIDENCIA + 1):
        fecha = mes(ANIO, numero)
        informar(f"  {fecha:%Y-%m}: {miles(paro.loc[paro['fecha'].eq(fecha), 'paro_total'].sum())}")


def buscar_valores_repetidos(tabla):
    titulo(f"Valores idénticos durante {MESES_RACHA} o más meses seguidos (valor >= {MINIMO_RACHA})")
    rachas = []
    for municipio, fila in tabla.iterrows():
        valores = fila.to_numpy()
        fechas = fila.index
        inicio = 0
        for i in range(1, len(valores) + 1):
            if i == len(valores) or valores[i] != valores[inicio]:
                largo = i - inicio
                if largo >= MESES_RACHA and valores[inicio] >= MINIMO_RACHA:
                    rachas.append(
                        {
                            "municipio": municipio,
                            "inicio": fechas[inicio].strftime("%Y-%m"),
                            "fin": fechas[i - 1].strftime("%Y-%m"),
                            "meses": largo,
                            "valor": int(valores[inicio]),
                        }
                    )
                inicio = i
    resultado = pd.DataFrame(rachas, columns=["municipio", "inicio", "fin", "meses", "valor"])
    informar(resultado.sort_values("meses", ascending=False).to_string(index=False))
    guardar_csv(resultado, "valores_repetidos.csv")


def comprobar_redondeo(original, serie):
    titulo("2b. Porcentaje de valores múltiplos de 5, por indicador y año")
    cuentas = original[original["Indicador"].isin([INDICADOR_SERIE, "Media"])].copy()
    cuentas["entero"] = cuentas["v"] % 1 == 0
    cuentas["multiplo_5"] = cuentas["entero"] & (cuentas["v"] % 5 == 0)

    filas = []
    for (indicador, anio), grupo in cuentas.groupby(["Indicador", "Año"]):
        sin_ceros = grupo[grupo["v"] != 0]
        grandes = grupo[grupo["v"] >= 100]
        filas.append(
            {
                "indicador": indicador,
                "anio": anio,
                "valores": len(grupo),
                "pct_enteros": round(100 * grupo["entero"].mean(), 1),
                "pct_multiplos_5": round(100 * grupo["multiplo_5"].mean(), 1),
                "pct_multiplos_5_sin_ceros": round(100 * sin_ceros["multiplo_5"].mean(), 1),
                "pct_multiplos_5_valores_100_o_mas": (
                    round(100 * grandes["multiplo_5"].mean(), 1) if len(grandes) else np.nan
                ),
            }
        )
    resultado = pd.DataFrame(filas)
    informar(resultado.to_string(index=False))
    informar("  Sin redondeo se espera un 20 %; con redondeo a múltiplos de 5, un 100 %.")
    guardar_csv(resultado, "multiplos_de_5_por_anio.csv")

    valores = serie[serie["v"] >= 100].copy()
    valores["periodo"] = np.where(valores["fecha"] >= "2022-01-01", "2022 en adelante", "2005-2021")
    valores["ultima_cifra"] = (valores["v"] % 10).astype(int)
    informar("  Última cifra de los valores mensuales de 100 o más (% por periodo):")
    informar(
        (100 * pd.crosstab(valores["periodo"], valores["ultima_cifra"], normalize="index"))
        .round(1)
        .to_string()
    )


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    original, procesado, paro = leer_datos()

    titulo("Archivo analizado")
    informar(f"  {RUTA_ORIGINAL.relative_to(RAIZ)}")
    informar(f"  SHA-256: {hashlib.sha256(RUTA_ORIGINAL.read_bytes()).hexdigest()}")

    serie = serie_mensual(original)
    tabla = serie.pivot(index="Territorio", columns="fecha", values="v")

    comprobar_origen(serie, procesado)
    comprobar_filas(original)
    comprobar_tasas(original, tabla)
    comprobar_municipios(tabla)
    comprobar_estacionalidad(tabla)
    comprobar_paro(paro)
    buscar_valores_repetidos(tabla)
    comprobar_redondeo(original, serie)

    informe = SALIDA / "informe.txt"
    informe.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"\nInforme: {informe.relative_to(RAIZ)}")
    print("Investigación terminada. Los datos no se han modificado.")


if __name__ == "__main__":
    main()
