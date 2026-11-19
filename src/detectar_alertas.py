from pathlib import Path

import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / "datos" / "procesados"
RESULTADOS = RAIZ / "resultados"

RUTA_PARO = PROCESADOS / "paro_total_mensual.csv"
RUTA_PARO_EDAD = PROCESADOS / "paro_edad_mensual.csv"
RUTA_ALERTAS = RESULTADOS / "alertas.csv"

# Parámetros del detector, los mismos que en
# notebooks/02_detector_inicial.ipynb. Si cambian, se anota
# en docs/decisiones.md.
VENTANA_ANOS = 5
MIN_OBSERVACIONES = 5
UMBRAL = 3.0
FACTOR_ESCALA = 1.4826

MUNICIPIOS_ESPERADOS = 179

GRUPOS_EDAD = [
    "Menor de 25 años",
    "De 25 a 44 años",
    "Mayor de 44 años",
]

ESTADOS_NO_EVALUABLES = ["dispersion_cero", "historial_insuficiente"]

# Columnas de resultados/alertas.csv en el orden de
# docs/contrato_alertas.md.
COLUMNAS = [
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


def comprobar_archivo(ruta):
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encuentra {ruta}. "
            "Ejecuta antes src/preparar_datos.py."
        )


def leer_paro():
    comprobar_archivo(RUTA_PARO)

    paro = pd.read_csv(
        RUTA_PARO,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
    )

    paro = paro.sort_values(["municipio", "fecha"]).reset_index(drop=True)

    # Comprobaciones de entrada del notebook 02.
    columnas_necesarias = ["municipio", "fecha", "paro_total"]

    if not set(columnas_necesarias).issubset(paro.columns):
        raise ValueError("Faltan columnas necesarias.")

    if paro[columnas_necesarias].isna().any().any():
        raise ValueError("Hay valores ausentes en columnas esenciales.")

    if paro.duplicated(["municipio", "fecha"]).any():
        raise ValueError("Hay municipios y fechas duplicados.")

    paro["paro_total"] = pd.to_numeric(paro["paro_total"], errors="raise")

    if (paro["paro_total"] < 0).any():
        raise ValueError("Hay valores negativos de paro.")

    if (paro["paro_total"] % 1 != 0).any():
        raise ValueError("Hay recuentos de personas no enteros.")

    if not paro["fecha"].dt.is_month_start.all():
        raise ValueError("Las fechas deben representar el inicio del mes.")

    for municipio, grupo in paro.groupby("municipio"):
        fechas_esperadas = pd.date_range(
            grupo["fecha"].min(),
            grupo["fecha"].max(),
            freq="MS",
        )

        if not pd.DatetimeIndex(grupo["fecha"]).equals(fechas_esperadas):
            raise ValueError(
                f"Faltan meses o hay fechas incorrectas en {municipio}."
            )

    return paro


def leer_paro_edad(paro):
    comprobar_archivo(RUTA_PARO_EDAD)

    paro_edad = pd.read_csv(
        RUTA_PARO_EDAD,
        sep=";",
        encoding="utf-8-sig",
        parse_dates=["fecha"],
        usecols=["municipio", "fecha", "grupo_edad", "paro"],
    )

    if set(paro_edad["grupo_edad"]) != set(GRUPOS_EDAD):
        raise ValueError(
            "Grupos de edad inesperados en paro_edad_mensual.csv: "
            f"{sorted(set(paro_edad['grupo_edad']))}"
        )

    # Los dos archivos deben describir el mismo paro.
    suma_edades = (
        paro_edad.groupby(["municipio", "fecha"], as_index=False)["paro"]
        .sum()
    )
    comparacion = paro[["municipio", "fecha", "paro_total"]].merge(
        suma_edades,
        on=["municipio", "fecha"],
        how="outer",
        indicator=True,
    )

    if not (
        comparacion["_merge"].eq("both").all()
        and comparacion["paro_total"].eq(comparacion["paro"]).all()
    ):
        raise ValueError(
            "paro_edad_mensual.csv no suma lo mismo que "
            "paro_total_mensual.csv. Ejecuta de nuevo "
            "src/preparar_datos.py."
        )

    return paro_edad


def calcular_mad(valores):
    valores = np.asarray(valores, dtype=float)
    mediana = np.median(valores)
    return np.median(np.abs(valores - mediana))


def aplicar_detector(paro):
    paro = paro.copy()

    paro["paro_mes_anterior"] = paro.groupby("municipio")["paro_total"].shift(1)
    paro["cambio_mensual"] = paro["paro_total"] - paro["paro_mes_anterior"]

    base_porcentaje = paro["paro_mes_anterior"].where(
        paro["paro_mes_anterior"] > 0
    )
    paro["variacion_mensual_pct"] = (
        100 * paro["cambio_mensual"] / base_porcentaje
    )

    paro["mes"] = paro["fecha"].dt.month

    # Dentro de cada municipio y mes, las observaciones están
    # ordenadas por año. shift(1) excluye el mes evaluado de su
    # propia referencia.
    grupos = paro.groupby(["municipio", "mes"])["cambio_mensual"]

    paro["n_historico"] = grupos.transform(
        lambda serie: (
            serie.shift(1)
            .rolling(VENTANA_ANOS, min_periods=1)
            .count()
        )
    ).fillna(0).astype(int)

    paro["referencia_cambio"] = grupos.transform(
        lambda serie: (
            serie.shift(1)
            .rolling(VENTANA_ANOS, min_periods=MIN_OBSERVACIONES)
            .median()
        )
    )

    paro["mad_cambio"] = grupos.transform(
        lambda serie: (
            serie.shift(1)
            .rolling(VENTANA_ANOS, min_periods=MIN_OBSERVACIONES)
            .apply(calcular_mad, raw=True)
        )
    )

    paro["escala_robusta"] = FACTOR_ESCALA * paro["mad_cambio"]

    historial_suficiente = paro["n_historico"] >= MIN_OBSERVACIONES

    evaluable = (
        historial_suficiente
        & paro["referencia_cambio"].notna()
        & paro["escala_robusta"].gt(0)
        & paro["cambio_mensual"].notna()
    )

    desviacion_personas = paro["cambio_mensual"] - paro["referencia_cambio"]

    paro["puntuacion_robusta"] = (
        desviacion_personas / paro["escala_robusta"].where(evaluable)
    )

    paro["limite_superior"] = (
        paro["referencia_cambio"] + UMBRAL * paro["escala_robusta"]
    ).where(evaluable)

    # Booleano con valores ausentes: no evaluable no equivale a False.
    paro["alerta_experimental"] = pd.Series(
        pd.NA,
        index=paro.index,
        dtype="boolean",
    )

    paro.loc[evaluable, "alerta_experimental"] = (
        paro.loc[evaluable, "cambio_mensual"].gt(0)
        & paro.loc[evaluable, "puntuacion_robusta"].gt(UMBRAL)
    )

    paro["estado_detector"] = "historial_insuficiente"

    paro.loc[
        historial_suficiente & paro["escala_robusta"].eq(0),
        "estado_detector",
    ] = "dispersion_cero"

    paro.loc[evaluable, "estado_detector"] = "sin_alerta"

    paro.loc[
        paro["alerta_experimental"].fillna(False),
        "estado_detector",
    ] = "alerta_experimental"

    return paro


def anadir_grupo_edad_principal(paro, paro_edad):
    # Grupo de edad con mayor aumento en personas respecto al mes
    # anterior. Vacío si el paro total no sube o si hay empate.
    paro_edad = paro_edad.sort_values(["municipio", "grupo_edad", "fecha"])

    paro_edad["cambio_grupo"] = (
        paro_edad["paro"]
        - paro_edad.groupby(["municipio", "grupo_edad"])["paro"].shift(1)
    )

    cambios = paro_edad.pivot(
        index=["municipio", "fecha"],
        columns="grupo_edad",
        values="cambio_grupo",
    )[GRUPOS_EDAD].dropna()

    maximo = cambios.max(axis=1)
    grupos_con_maximo = cambios.eq(maximo, axis=0).sum(axis=1)

    principal = (
        cambios.idxmax(axis=1)
        .where(grupos_con_maximo.eq(1))
        .rename("grupo_edad_principal")
        .reset_index()
    )

    paro = paro.merge(
        principal,
        on=["municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )

    paro["grupo_edad_principal"] = paro["grupo_edad_principal"].where(
        paro["cambio_mensual"].gt(0)
    )

    return paro


def preparar_salida(paro):
    alertas = paro[COLUMNAS].sort_values(["municipio", "fecha"])

    # El contrato los define como enteros con celdas vacías.
    for columna in ["paro_mes_anterior", "cambio_mensual"]:
        alertas[columna] = alertas[columna].astype("Int64")

    return alertas.reset_index(drop=True)


def comprobar_reglas(alertas, paro):
    # Reglas de docs/contrato_alertas.md.
    errores = []

    municipios = set(paro["municipio"])
    meses = pd.date_range(paro["fecha"].min(), paro["fecha"].max(), freq="MS")

    # 1. Los 179 municipios, con los mismos nombres y todos los meses.
    if len(municipios) != MUNICIPIOS_ESPERADOS:
        errores.append(
            f"Regla 1: se esperaban {MUNICIPIOS_ESPERADOS} municipios "
            f"en paro_total_mensual.csv y hay {len(municipios)}."
        )

    municipios_alertas = set(alertas["municipio"])
    if municipios_alertas != municipios:
        errores.append(
            "Regla 1: los municipios no coinciden con "
            "paro_total_mensual.csv. "
            f"Faltan: {sorted(municipios - municipios_alertas)}. "
            f"Sobran: {sorted(municipios_alertas - municipios)}."
        )

    esperados = pd.MultiIndex.from_product([sorted(municipios), meses])
    presentes = pd.MultiIndex.from_frame(alertas[["municipio", "fecha"]])
    faltan = esperados.difference(presentes)
    sobran = presentes.difference(esperados)

    if len(faltan) or len(sobran):
        errores.append(
            f"Regla 1: faltan {len(faltan)} y sobran {len(sobran)} "
            "pares municipio-mes respecto a la serie completa."
        )

    # 2. Sin pares municipio + fecha repetidos.
    repetidos = alertas.duplicated(["municipio", "fecha"]).sum()
    if repetidos:
        errores.append(
            f"Regla 2: hay {repetidos} pares municipio-fecha repetidos."
        )

    # 3. alerta_experimental vacía si y solo si el mes no es evaluable.
    no_evaluable = alertas["estado_detector"].isin(ESTADOS_NO_EVALUABLES)
    alerta_vacia = alertas["alerta_experimental"].isna()
    incumplen = (alerta_vacia != no_evaluable).sum()
    if incumplen:
        errores.append(
            f"Regla 3: {incumplen} filas tienen alerta_experimental "
            "vacía sin ser no evaluables, o al revés."
        )

    # 4. alerta_experimental True si y solo si el estado es alerta.
    es_alerta = alertas["alerta_experimental"].eq(True).fillna(False)
    estado_alerta = alertas["estado_detector"].eq("alerta_experimental")
    incumplen = (es_alerta != estado_alerta).sum()
    if incumplen:
        errores.append(
            f"Regla 4: {incumplen} filas no concuerdan entre "
            "alerta_experimental y estado_detector."
        )

    # 5. Toda alerta sube y supera el límite superior.
    con_alerta = alertas.loc[es_alerta]
    cumplen = (
        con_alerta["cambio_mensual"].gt(0)
        & con_alerta["cambio_mensual"].gt(con_alerta["limite_superior"])
    ).fillna(False)
    incumplen = (~cumplen).sum()
    if incumplen:
        errores.append(
            f"Regla 5: {incumplen} alertas no cumplen cambio_mensual > 0 "
            "y cambio_mensual > limite_superior."
        )

    if errores:
        raise ValueError(
            "El resultado no cumple docs/contrato_alertas.md. "
            "No se ha escrito resultados/alertas.csv.\n- "
            + "\n- ".join(errores)
        )


def guardar(alertas):
    RESULTADOS.mkdir(parents=True, exist_ok=True)

    alertas.to_csv(
        RUTA_ALERTAS,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
        na_rep="",
    )

    filas = f"{len(alertas):,}".replace(",", ".")
    print(f"Generado: {RUTA_ALERTAS.name} | Filas: {filas}")


def main():
    paro = leer_paro()
    paro_edad = leer_paro_edad(paro)

    resultado = aplicar_detector(paro)
    resultado = anadir_grupo_edad_principal(resultado, paro_edad)
    alertas = preparar_salida(resultado)

    comprobar_reglas(alertas, paro)
    print("Reglas del contrato comprobadas.")

    guardar(alertas)

    ultima_fecha = alertas["fecha"].max()
    ultimo_mes = alertas.loc[alertas["fecha"].eq(ultima_fecha)]

    print(f"\nÚltimo mes: {ultima_fecha:%Y-%m}")
    for estado, n in ultimo_mes["estado_detector"].value_counts().items():
        print(f"  {estado}: {n}")

    print("\nDetección terminada. Los datos procesados no se han modificado.")


if __name__ == "__main__":
    main()
