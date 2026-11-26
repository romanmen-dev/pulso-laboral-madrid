# Validación del detector

Evaluación del detector oficial (`src/detectar_alertas.py`: ventana de 5 años,
mínimo de 5 cambios, umbral 3) sin modificarlo. Los resultados los genera
`src/validar_detector.py` en `resultados/validacion/`, y cada cifra de este
documento indica el CSV del que sale.

```powershell
.\.venv\Scripts\python.exe .\src\validar_detector.py
.\.venv\Scripts\python.exe .\src\comparar_metodos.py
```

El segundo script compara el detector con tres métodos alternativos; sus
resultados están en la sección
[Comparación con métodos alternativos](#comparación-con-métodos-alternativos).

## Cómo se ha hecho

- El script lee `resultados/alertas.csv` (o `datos/publicados/alertas.csv`) y
  `datos/procesados/paro_total_mensual.csv`, y recalcula el detector con sus
  propias funciones. Antes de seguir comprueba que, con los parámetros
  oficiales, reproduce `alertas.csv` en estado, alerta, referencia, escala,
  límite y puntuación.
- Las variantes (ventana de 3, 5 y 7 años; umbral de 2,5, 3 y 3,5) cambian los
  parámetros del módulo solo en memoria. Como en el oficial, la ventana exige
  historial completo: 3, 5 o 7 cambios.
- Sin información futura: cada mes se compara solo con el mismo mes de años
  anteriores. Los quintiles de tamaño (paro medio de 2019) y los umbrales
  calibrados en 2017-2019 solo describen resultados: no intervienen en ninguna
  detección.
- Inyección sintética: se suma la subida al cambio del mes evaluado y se aplica
  la regla del detector (sube y puntuación > umbral) con su referencia y su
  escala, que solo dependen de años anteriores. El script lo comprueba
  ejecutando el detector completo sobre la serie con la subida de 2019 (5 %), y
  `tests/test_validacion.py` lo comprueba con varios años y tamaños: una subida
  nula da las alertas oficiales y una enorme se detecta en todos los meses
  evaluables.

## 1. Comportamiento histórico

Febrero de 2010 (primer mes evaluable) a octubre de 2026: 201 meses
([`validacion_mensual.csv`](../resultados/validacion/validacion_mensual.csv)).

- 33.739 municipio-mes evaluables, con 1.859 alertas: el **5,51 %**. Además,
  2.240 municipio-mes no evaluables por dispersión cero y ninguno por historial
  insuficiente. Cada mes hay entre 160 y 177 municipios evaluables de 179.
- La mediana mensual del % de alertas es 4,35 %. En 8 meses no hay ninguna
  alerta.
- Los meses con más alertas son abril de 2020 (114), mayo de 2020 (58) y marzo
  de 2020 (42). Les siguen enero de 2012 y diciembre de 2020 (31 cada uno).
- Por años ([`validacion_anual.csv`](../resultados/validacion/validacion_anual.csv)),
  2020 tiene un 16,3 % de alertas. El resto de los años, entre el 2,7 % (2016)
  y el 7,7 % (2019).

![Municipios con alerta por mes, con 2017-2019 y marzo-junio de 2020 marcados](../resultados/validacion/alertas_por_mes.png)

## 2. Falsas alarmas en calma (2017-2019)

Se toma 2017-2019 como periodo sin crisis, pero no hay una lista de anomalías
reales, así que «falsa alarma» es una suposición: 2019 ya tiene un 7,7 % de
alertas ([`validacion_anual.csv`](../resultados/validacion/validacion_anual.csv)).

| Medida | Valor |
|---|---:|
| Municipio-mes evaluables | 6.006 |
| Alertas | 331 |
| **% de alertas** | **5,51 %** |
| Teórico con normalidad, P(Z > 3) | 0,135 % |
| Observado / teórico | 40,8 veces |
| Simulado con normalidad, mediana y MAD de 5 cambios | 7,58 % |
| Observado sin exigir que el paro suba (puntuación > 3) | 7,43 % |
| Puntuación < −3 (cola inferior) | 5,13 % |
| Puntuación mediana de los evaluables | 0,10 |

Fuente: [`calma_2017_2019.csv`](../resultados/validacion/calma_2017_2019.csv).
La simulación usa 1.000.000 de repeticiones con semilla 2026.

**Por qué no sale un 0,135 %.** Las colas pesadas no están en los datos, sino
en la puntuación, porque la escala se estima con solo 5 cambios:

- Con 5 valores, uno de los desvíos respecto a la mediana es siempre 0, y la
  MAD es el segundo menor de los otros cuatro. Suele quedar pequeña y varía
  mucho de un caso a otro, así que la puntuación se dispara. Aunque los cambios
  fueran normales, un 7,58 % de los meses superaría 3, no un 0,135 %.
- En calma, el 7,43 % de los meses evaluables supera 3 si no se exige que el
  paro suba: casi lo mismo que la simulación. Con umbrales más altos, lo
  observado queda por debajo de la simulación. Con 6: 2,01 % frente a 2,47 %.
  Con 10: 0,67 % frente a 0,99 %
  ([`tasa_alertas_segun_umbral.csv`](../resultados/validacion/tasa_alertas_segun_umbral.csv)).
  Una vez descontado el efecto de la MAD de 5, los datos no muestran colas más
  pesadas que la normal.
- Exigir que el paro suba lo reduce del 7,43 % al 5,51 %.
- Los recuentos pequeños pesan: el 14,9 % de los meses evaluables tiene una MAD
  de 1 persona o menos. En ellos hay un 9,85 % de alertas, frente al 4,75 % del
  resto ([`calma_2017_2019.csv`](../resultados/validacion/calma_2017_2019.csv)).

![Tasa de meses por encima de cada umbral: observado y simulado](../resultados/validacion/tasa_alertas_segun_umbral.png)

**Umbral que daría cada tasa en 2017-2019.** Solo informa: el umbral oficial
no cambia. Se calibra dentro de la misma muestra
([`umbrales_calma.csv`](../resultados/validacion/umbrales_calma.csv)).

| Objetivo | Umbral | Alertas | % obtenido |
|---:|---:|---:|---:|
| 1 % | 6,74 | 60 | 1,00 % |
| 2 % | 5,06 | 119 | 1,98 % |
| 5 % | 3,15 | 293 | 4,88 % |
| Oficial | 3 | 331 | 5,51 % |

## 3. Episodio de 2020

Comparación de marzo a junio de 2020 con los mismos meses de 2017-2019
([`episodio_2020.csv`](../resultados/validacion/episodio_2020.csv)).
Para 2017-2019 se da la media anual de alertas y los porcentajes de los tres
años agregados. El % del paro es el paro de los municipios en alerta sobre el
de los 179 municipios ese mes.

| Mes | Alertas 2017-2019 (media) | % evaluables 2017-2019 | % paro 2017-2019 | Alertas 2020 | % evaluables 2020 | % paro 2020 |
|---|---:|---:|---:|---:|---:|---:|
| Marzo | 9,7 | 5,9 % | 3,0 % | 42 de 163 | 25,8 % | 78,1 % |
| **Abril** | 9,3 | 5,5 % | 0,8 % | **114 de 169** | **67,5 %** | **98,7 %** |
| Mayo | 9,3 | 5,5 % | 1,1 % | 58 de 169 | 34,3 % | 86,9 % |
| Junio | 9,0 | 5,4 % | 1,1 % | 10 de 168 | 6,0 % | 1,4 % |

**La señal se concentra en abril de 2020.** Ese mes, el paro de la Comunidad
(suma de los 179 municipios) subió en 41.263 personas, frente a una media de
−9.283 en abril de 2017-2019. En junio, el detector vuelve a niveles de calma.

## 4. Inyección sintética (potencia)

Meses evaluables de 2015 a 2019: 10.068 municipio-mes. A cada uno se le suma
una subida del 1 %, 2 %, 5 % o 10 % del paro del mes anterior, redondeada a
personas (las mitades, hacia arriba). La tasa de detección incluye los meses
que ya tenían alerta sin la subida: es la fila del 0 %
([`potencia.csv`](../resultados/validacion/potencia.csv)).

Quintiles de los 179 municipios por su paro medio de 2019 (Q1, los más
pequeños: de 1,8 a 39,3 personas; Q5: de 811,8 a 163.525,8). Detalle por
municipio en
[`quintiles_tamano.csv`](../resultados/validacion/quintiles_tamano.csv).

| Subida | Todos | Q1 | Q2 | Q3 | Q4 | Q5 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 % | 4,6 % | 2,5 % | 5,8 % | 5,9 % | 5,0 % | 3,5 % |
| 1 % | 7,5 % | 2,5 % | 7,2 % | 8,2 % | 9,0 % | 9,3 % |
| 2 % | 11,9 % | 3,0 % | 9,2 % | 11,3 % | 13,5 % | 20,0 % |
| 5 % | **30,3 %** | 4,6 % | 16,8 % | 23,6 % | 33,8 % | 65,4 % |
| 10 % | **55,4 %** | 8,4 % | 33,2 % | 53,6 % | 73,9 % | 94,8 % |

- Solo entre los meses sin alerta previa, se detecta el 3,0 %, 7,6 %, 27,0 % y
  53,2 % de las subidas del 1 %, 2 %, 5 % y 10 %.
- En Q1 la subida mediana es de 0 personas con el 1 % y el 2 %, y de 1 persona
  con el 5 % y el 10 %. Con el 1 %, la subida es nula en 1.517 de sus 1.586
  meses.

![Curvas de potencia por quintil de tamaño](../resultados/validacion/curvas_potencia.png)

## 5. Sensibilidad a la ventana y al umbral

Fuente: [`sensibilidad.csv`](../resultados/validacion/sensibilidad.csv).
«Cobertura» es el % de municipio-mes evaluables en 2017-2019. «2020» es el %
de alertas entre evaluables de marzo a junio de 2020. «Potencia» es la
detección de la subida del 5 % en 2015-2019. Jaccard compara los conjuntos de
alertas con los del oficial desde febrero de 2012, primer mes en que todas las
variantes tienen historial (1.594 alertas oficiales).

| Ventana | Umbral | Cobertura | % alertas en calma | 2020 | Potencia (5 %) | Jaccard |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 2,5 | 84,3 % | 11,4 % | 44,0 % | 46,7 % | 0,33 |
| 3 | 3 | 84,3 % | 9,5 % | 38,2 % | 41,8 % | 0,35 |
| 3 | 3,5 | 84,3 % | 7,7 % | 35,7 % | 37,5 % | 0,33 |
| 5 | 2,5 | 93,2 % | 7,2 % | 38,0 % | 36,4 % | 0,77 |
| **5** | **3** | **93,2 %** | **5,5 %** | **33,5 %** | **30,3 %** | **1** |
| 5 | 3,5 | 93,2 % | 4,0 % | 30,6 % | 25,3 % | 0,76 |
| 7 | 2,5 | 96,1 % | 4,0 % | 38,5 % | 27,3 % | 0,43 |
| 7 | 3 | 96,1 % | 2,5 % | 31,9 % | 21,1 % | 0,44 |
| 7 | 3,5 | 96,1 % | 1,5 % | 25,6 % | 16,5 % | 0,34 |

- Todas las variantes responden a 2020: entre el 25,6 % y el 44,0 % de alertas
  de marzo a junio, frente a entre el 1,7 % y el 9,5 % en esos meses de
  2017-2019 (columna `pct_alertas_mar_jun_2017_2019`).
- Cambiar la ventana cambia qué meses se marcan mucho más que cambiar el
  umbral: con ventana de 3 o 7 años, Jaccard entre 0,33 y 0,44; con ventana de
  5 y otro umbral, 0,76 y 0,77.
- La ventana de 3 años da más alertas en calma y menos cobertura. La de 7 da
  menos alertas en calma y más cobertura.
- Con la misma tasa en calma (4,0 %), la ventana de 7 años con umbral 2,5
  responde más en 2020 que la de 5 años con umbral 3,5 (38,5 % frente a
  30,6 %) y detecta algo más la subida del 5 % (27,3 % frente a 25,3 %). Es una
  comparación dentro de la muestra: no justifica por sí sola un cambio.

## 6. Municipios pequeños

Febrero de 2010 a octubre de 2026, por quintil de paro medio de 2019
([`municipios_pequenos.csv`](../resultados/validacion/municipios_pequenos.csv)).

| Quintil | Paro medio 2019 | Meses con dispersión cero | % alertas (evaluables) | % alertas en calma | Puntuación mediana de las alertas | Cambio mediano de las alertas |
|---|---:|---:|---:|---:|---:|---:|
| Q1 | 1,8 a 39,3 | 26,1 % | 2,7 % | 2,7 % | 4,05 | +5 personas |
| Q2 | 40,6 a 142,3 | 3,3 % | 6,1 % | 5,7 % | 4,05 | +8 |
| Q3 | 145,5 a 361,6 | 1,2 % | 6,7 % | 7,5 % | 4,61 | +13 |
| Q4 | 362,2 a 803,7 | 0,4 % | 6,1 % | 5,8 % | 4,72 | +22 |
| Q5 | 811,8 a 163.525,8 | 0,07 % | 5,3 % | 5,1 % | 4,98 | +80 |

- En Q1, uno de cada cuatro meses no es evaluable por dispersión cero
  (1.886 de 7.236), y los meses evaluables tienen menos alertas que en el
  resto de quintiles.
- La puntuación mediana de las alertas no es mayor en los municipios pequeños,
  sino algo menor. Lo que cambia es la subida que hay detrás: una mediana de
  5 personas en Q1, frente a 80 en Q5.
- Con la potencia, el detector apenas puede ver subidas relativas en Q1 (8,4 %
  con una subida del 10 %, sección 4).

## 7. Persistencia

¿Hay otra alerta en el mismo municipio el mes siguiente?
([`persistencia.csv`](../resultados/validacion/persistencia.csv)). La tasa
base es el % de meses con alerta tras un mes evaluable sin alerta.

| Mes de la alerta | Alertas con mes siguiente | Se repiten | % | Tasa base |
|---|---:|---:|---:|---:|
| Febrero de 2010 a septiembre de 2026 | 1.844 | 159 | 8,6 % | 5,4 % |
| Sin marzo a junio de 2020 | 1.620 | 66 | 4,1 % | 5,1 % |
| 2017-2019 | 331 | 14 | 4,2 % | 5,8 % |

- 93 de las 159 repeticiones (159 − 66) son de alertas de marzo a junio de
  2020. Fuera de ese episodio, tras una alerta hay menos alertas que tras un
  mes sin alerta.
- El 92,2 % de las rachas de alertas dura un solo mes (1.568 de 1.700). Hay
  108 de dos meses, 22 de tres, una de cuatro y una de cinco
  ([`rachas_alertas.csv`](../resultados/validacion/rachas_alertas.csv)).

## Conclusión

- El detector reproduce `alertas.csv` sin información futura. En calma marca el 5,51 % de los meses evaluables, 40,8 veces el 0,135 % teórico: con 5 cambios, datos normales ya darían un 7,58 %.
- Responde con claridad a 2020: en abril, 114 de 169 municipios evaluables (67,5 %, el 98,7 % del paro), frente a un 5,5 % en abril de 2017-2019.
- Detecta una subida puntual del 5 % en el 30,3 % de los meses y una del 10 % en el 55,4 %. En el quintil mayor, en el 65,4 % y el 94,8 %; en el menor, en el 4,6 % y el 8,4 %.
- Fuera de 2020 las alertas no se repiten más de lo esperable (4,1 % frente al 5,1 % de base): son avisos para revisar, no una confirmación.
- Con ventana de 7 años y umbral 2,5, la tasa en calma es la misma que con 5 años y umbral 3,5 (4,0 %), con más respuesta en 2020: merece estudiarse, sin cambiar todavía el detector.

## Limitaciones

- **Sin verdad de referencia.** No hay una lista de anomalías municipales
  confirmadas, así que no se puede medir la precisión ni la tasa real de falsas
  alarmas. 2017-2019 se trata como calma y 2020 como episodio conocido, pero es
  un episodio regional, no una etiqueta por municipio.
- **La serie empieza en 2005.** El primer mes evaluable es febrero de 2010, o
  febrero de 2012 con ventana de 7 años. La crisis de 2008-2009 no se puede
  evaluar, y 2020 es el único episodio de referencia.
- **Recuentos, no tasas.** El paro registrado se cuenta en personas, sin
  población de referencia. Las subidas sintéticas son relativas al paro del
  mes anterior, y en los municipios pequeños los recuentos enteros hacen que la
  MAD sea 0 o 1 con frecuencia y que una subida pequeña se redondee a 0.
- La inyección prueba un salto aislado en un solo mes. No prueba subidas
  graduales a lo largo de varios meses, que además contaminarían las
  referencias de años posteriores.
- Los quintiles usan el paro medio de 2019 para todo el periodo. Los umbrales
  de la sección 2 se calibran en la misma muestra que evalúan. Ninguno de los
  dos interviene en las detecciones.
- La simulación supone cambios normales e independientes, sin tendencia.
- Se usa la versión actual de los datos, no la publicada en cada fecha.
- El paro de la Comunidad es la suma de los 179 municipios (suma de los tres
  grupos de edad), pendiente de contraste con los totales oficiales.

## Comparación con métodos alternativos

La validación muestra que el problema principal del detector oficial es
estimar la referencia y la escala con solo 5 cambios. `src/comparar_metodos.py`
compara tres alternativas con el mismo banco de pruebas: periodo de calma
2017-2019, episodio de marzo a junio de 2020 e inyección sintética en
2015-2019, con las funciones de `src/validar_detector.py`. Ninguna usa
información futura, y `tests/test_comparar_metodos.py` lo comprueba alterando
los datos posteriores a un mes de corte. Todas las rutas son de
`resultados/validacion/`.

**Criterio:** menos falsas alarmas en calma, y la misma o mejor respuesta en
2020 y potencia.

### Métodos

- **Oficial:** mediana y MAD de los cambios del mismo mes en los 5 años
  anteriores (5 cambios), umbral 3.
- **C. Robusto ampliado y calibrado** (alternativa principal). Misma regla,
  con los cambios del mismo mes y de los meses contiguos (±1) en los 5 años
  anteriores: hasta 15 cambios, con un mínimo de 5. El umbral se corrige por
  tamaño de muestra. Para cada n, una simulación con datos normales
  (2.000.000 de repeticiones) da el umbral con el que un 0,135 % de las
  puntuaciones lo supera, que es lo que significa «3» con n infinito: 27,99
  con 5 cambios, 6,97 con 10 y 5,34 con 15. Con otro millón de simulaciones
  independientes, esos umbrales dan entre el 0,13 % y el 0,14 %
  ([`umbrales_calibrados.csv`](../resultados/validacion/umbrales_calibrados.csv)).
- **C5:** el oficial (5 cambios) con el umbral calibrado de 27,99. Separa el
  efecto de calibrar el umbral del de tener más datos.
- **A. Quasi-Poisson tipo Farrington** sobre el nivel de paro. Para cada
  municipio y mes, regresión de Poisson con tendencia lineal sobre el paro del
  mismo mes y de los contiguos (±1) en los 5 años anteriores (15 meses, solo
  pasado). La sobredispersión es φ = máx(1, X² de Pearson / 13). El límite
  superior de predicción usa la transformación de potencia 2/3 de Farrington
  et al. (1996) con z = 3 (cuantil del 99,865 %, el mismo 0,135 % que C). Hay
  alerta si el paro supera el límite y además sube respecto al mes anterior.
- **B. Anomalía local.** Con los 60 meses anteriores estima la recta
  cambio del municipio = a + b × cambio del resto de la Comunidad, por
  Theil-Sen (mediana de las pendientes entre pares de meses), y la escala
  robusta de sus residuos (1,4826 × MAD). El resto excluye al propio
  municipio, para que Madrid no se explique a sí mismo. Hay alerta si el
  residuo del mes supera 3 escalas y el paro sube. Separa «sube en toda la
  Comunidad» de «sube aquí más que en el resto».

**Qué se simplifica de Farrington.** Farrington et al. (1996), *A statistical
algorithm for the early detection of outbreaks of infectious disease*
(Journal of the Royal Statistical Society, Series A, 159(3), 547-563), y
Noufaily et al. (2013), *An improved algorithm for outbreak detection in
multiple surveillance systems* (Statistics in Medicine, 32(7), 1206-1222),
trabajan con datos semanales. En el original, la tendencia solo se mantiene si
es significativa y la predicción no se sale del rango de la referencia; los
valores pasados con residuos de Anscombe altos (posibles brotes) pierden peso;
y no se da alarma con menos de 5 casos en las últimas 4 semanas. Noufaily et
al. rebajan el peso solo de los residuos mayores de 2,58, amplían la
referencia con un factor estacional de 10 periodos, excluyen las 26 semanas
más recientes y calculan el umbral con una binomial negativa. Aquí, en
cambio:

- Datos mensuales, 5 años y ±1 mes.
- La tendencia se mantiene siempre, sin contraste ni control de rango.
- Sin repesado de valores atípicos: los niveles altos de 2020 entran sin
  rebaja en las referencias de 2021 a 2025.
- El umbral es el de potencia 2/3 del original, no el de la binomial negativa.
- En lugar de la regla del mínimo de casos, se exige que el paro suba.
- Si el paro de los 15 meses de referencia es siempre 0, el mes no es
  evaluable.

**Tiempo de cálculo.** A ajusta a la vez todas las regresiones, una por
municipio y mes, con Newton-Raphson vectorizado en numpy, sin un bucle de
statsmodels. statsmodels
solo se usa en las pruebas, para comprobar que da los mismos coeficientes,
sobredispersión y error típico. En el último cálculo, A tardó 0,5 s, C 0,1 s,
B 3,5 s y la calibración de los umbrales 22,6 s
([`resumen_metodos.csv`](../resultados/validacion/resumen_metodos.csv),
columnas `segundos_*`). El script entero tarda unos 35 s.

### Resultados con el umbral de cada método

Fuente: [`resumen_metodos.csv`](../resultados/validacion/resumen_metodos.csv).
La potencia es el % de meses evaluables de 2015-2019 en los que se detecta
una subida puntual del % indicado del paro del mes anterior.

| Método | % alertas en calma | 2020: marzo-junio | Abril 2020 | % paro en alerta, abril 2020 | Potencia 1 % | 2 % | 5 % | 10 % | No evaluables |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Oficial** | **5,51 %** | **33,5 %** | **114 de 169 (67,5 %)** | **98,7 %** | **7,5 %** | **11,9 %** | **30,3 %** | **55,4 %** | **6,2 %** |
| C5 | 0,03 % | 1,9 % | 11 de 169 (6,5 %) | 16,0 % | 0,06 % | 0,16 % | 0,8 % | 2,5 % | 6,2 % |
| C | 0,11 % | 11,4 % | 60 de 174 (34,5 %) | 92,9 % | 0,14 % | 0,30 % | 1,6 % | 12,1 % | 2,3 % |
| A | 1,54 % | 39,2 % | 96 de 179 (53,6 %) | 98,1 % | 1,6 % | 2,4 % | 4,8 % | 10,2 % | 0,003 % |
| B | 0,38 % | 1,0 % | 4 de 174 (2,3 %) | 48,1 % | 1,1 % | 3,0 % | 19,5 % | 46,0 % | 1,7 % |

«No evaluables» es el % de municipio-mes de febrero de 2010 a octubre de 2026
que no se pueden evaluar. Por quintil de tamaño (Q1, los municipios más
pequeños), potencia con la subida del 10 % y no evaluables en Q1
(detalle en [`potencia_metodos.csv`](../resultados/validacion/potencia_metodos.csv)):

| Método | Q1 | Q2 | Q3 | Q4 | Q5 | No evaluables en Q1 |
|---|---:|---:|---:|---:|---:|---:|
| Oficial | 8,4 % | 33,2 % | 53,6 % | 73,9 % | 94,8 % | 26,1 % |
| C5 | 0,0 % | 0,0 % | 0,6 % | 2,7 % | 8,2 % | 26,1 % |
| C | 0,5 % | 2,5 % | 5,0 % | 14,8 % | 36,3 % | 11,6 % |
| A | 0,4 % | 2,9 % | 6,0 % | 13,6 % | 28,1 % | 0,01 % |
| B | 2,3 % | 13,5 % | 35,2 % | 76,6 % | 97,8 % | 8,3 % |

En los quintiles Q2 a Q5, C, A y B evalúan todos los meses.

- **C y C5 consiguen lo que promete la calibración:** en calma marcan el
  0,11 % y el 0,03 %, cerca o por debajo del 0,135 % nominal. Pero pierden casi
  toda la potencia y buena parte de la respuesta a 2020. Calibrar el umbral
  solo, con 5 cambios (C5), es lo peor de todo: el umbral necesario, 27,99, no
  deja pasar casi nada.
- **A** responde a 2020 más que el oficial de marzo a junio (39,2 % frente a
  33,5 %), aunque menos en abril (53,6 % frente a 67,5 %). Probablemente
  influye que trabaja con el nivel, y el paro siguió alto varios meses. Pero
  apenas detecta subidas puntuales (4,8 % con el 5 %).
- **B** apenas responde a 2020, y es lo esperado: descuenta lo que sube en
  toda la Comunidad. En cambio, con muy pocas falsas alarmas (0,38 %) detecta
  el 46,0 % de las subidas del 10 %, y en los quintiles Q4 y Q5 más que el
  oficial (76,6 % y 97,8 %).
- **Ningún municipio pequeño queda bien cubierto:** en Q1 ningún método pasa
  del 8,4 % con una subida del 10 %. C, A y B sí reducen los meses no
  evaluables de Q1 (del 26,1 % al 11,6 %, 0,01 % y 8,3 %).

### Con las mismas falsas alarmas

Cada método se puede mover a lo largo de su curva cambiando el umbral. Para
compararlos con justicia, se fija la tasa en calma y se mira cuál responde más
([`comparacion_misma_tasa.csv`](../resultados/validacion/comparacion_misma_tasa.csv):
el umbral con la mayor tasa en calma que no pasa de la indicada; curvas
completas en [`curvas_metodos.csv`](../resultados/validacion/curvas_metodos.csv)).

| Tasa en calma | Método (umbral) | % en calma | 2020: marzo-junio | Abril 2020 | Potencia 5 % | Potencia 10 % |
|---|---|---:|---:|---:|---:|---:|
| ≤ 0,135 % | Oficial (15) | 0,13 % | 4,2 % | 13,6 % | 2,3 % | 7,7 % |
| | C (4,75) | 0,13 % | 13,2 % | 39,1 % | 2,4 % | 16,5 % |
| | A (6) | 0,12 % | 17,9 % | 27,9 % | 0,8 % | 2,0 % |
| | B (3,5) | 0,13 % | 0,6 % | 1,7 % | 14,2 % | 38,1 % |
| ≤ 1 % | Oficial (6,75) | 1,00 % | 15,2 % | 40,8 % | 9,9 % | 25,2 % |
| | C (3,05) | 0,93 % | 23,6 % | 62,6 % | 10,9 % | 39,3 % |
| | A (3,55) | 0,99 % | 34,4 % | 45,8 % | 3,3 % | 7,3 % |
| | B (2,55) | 0,97 % | 2,0 % | 2,3 % | 25,5 % | 54,2 % |
| ≤ 5,51 % | Oficial (3) | 5,51 % | 33,5 % | 67,5 % | 30,3 % | 55,4 % |
| | C (1,7) | 4,93 % | 41,4 % | 78,2 % | 35,4 % | 67,0 % |
| | A (1,85) | 5,45 % | 49,6 % | 67,6 % | 12,0 % | 20,3 % |
| | B (1,6) | 5,24 % | 5,9 % | 10,9 % | 46,2 % | 72,2 % |

- **Con las mismas falsas alarmas, la referencia de C supera a la oficial en
  las cuatro medidas**, en todos los niveles de la tabla (también al 0,5 % y
  al 2 % del CSV). Lo que le quita potencia en la tabla anterior es el umbral
  calibrado, no la referencia ampliada.
- **Solo C cumple el criterio**
  ([`criterio_comparacion.csv`](../resultados/validacion/criterio_comparacion.csv)).
  Con umbral 1,9 marca un 4,02 % en calma, frente al 5,51 %. Al mismo tiempo
  mejora la respuesta en 2020 (38,1 % frente a 33,5 % de marzo a junio; 77,0 %
  frente a 67,5 % en abril) y la potencia (30,8 % frente a 30,3 % con el 5 %;
  63,5 % frente a 55,4 % con el 10 %). A y B no lo cumplen con ningún umbral
  de la rejilla (de 0,5 a 60).
- **B es el más potente para subidas locales en todos los niveles de la
  tabla**, pero no ve los choques regionales: en 2020 no pasa del 5,9 % ni con
  un 5,24 % de falsas alarmas.
- **A queda por debajo del oficial en potencia en todos los niveles de la
  tabla.**

![Potencia frente a la tasa en calma por método](../resultados/validacion/potencia_frente_a_calma.png)

### Coincidencia entre métodos

Febrero de 2010 a octubre de 2026, en los municipio-mes que evalúan los dos
métodos ([`coincidencia_metodos.csv`](../resultados/validacion/coincidencia_metodos.csv)).

| Frente al oficial | Alertas en común | Jaccard | Kappa de Cohen |
|---|---:|---:|---:|
| C5 | 21 | 0,01 | 0,02 |
| C | 104 | 0,06 | 0,10 |
| A | 315 | 0,12 | 0,18 |
| B | 145 | 0,07 | 0,12 |

La coincidencia es baja con todos, en parte porque cada método da un número
de alertas muy distinto. De las 116 alertas de C en meses que evalúan los
dos, 104 también son oficiales.
Entre los métodos alternativos, la mayor coincidencia es la de C5 con C
(kappa 0,16), y A y B casi no coinciden (kappa 0,01).

### Madrid en octubre de 2026

El paro subió en 2.130 personas
([`madrid_octubre_2026_metodos.csv`](../resultados/validacion/madrid_octubre_2026_metodos.csv)).

| Método | Límite del cambio | Alerta |
|---|---:|---|
| Oficial | +826 | Sí |
| C5 | +7.198 | No |
| C | +9.545 | No |
| A | +16.333 | No |
| B | +3.784 | No |

Solo el oficial la marca. Los otros explican por qué:

- **C** toma también septiembre y noviembre. En Madrid, los cambios de
  noviembre de 2021 a 2025 son todos negativos, de −4.131 a −1.127
  ([`alertas.csv`](../datos/publicados/alertas.csv)). La referencia baja a
  −1.112 y la escala sube a 1.994, frente a 61 y 255 en el oficial. **Esta es
  la principal debilidad de C:** junta meses con estacionalidad distinta.
- **A** predice 116.793 personas con una sobredispersión de 859, así que su
  intervalo es muy ancho.
- **B** predice una subida de 1.831 personas, porque el resto de la Comunidad
  subió en 1.941. La de Madrid está en línea con la región.

**Alertas oficiales de octubre de 2026, local o regional según B**
([`clasificacion_octubre_2026.csv`](../resultados/validacion/clasificacion_octubre_2026.csv)).
«Local» significa que B también marca el mes: la subida supera lo esperable
dado el cambio del resto de la Comunidad. «Regional» significa que B no lo
marca: la subida es compatible con la de la región. Las 15 son evaluables por
B: **13 son regionales y 2 locales**, Soto del Real (+31 personas, residuo de
3,67 escalas) y Alameda del Valle (+9; 3,04). Madrid es regional: residuo de
0,46 escalas.

### Recomendación para una versión futura del detector

- **Ningún método alternativo es claramente mejor tal como se planteó.** C
  con el umbral calibrado al 0,135 % baja las falsas alarmas de 5,51 % a
  0,11 %, pero detecta una subida del 5 % en el 1,6 % de los meses (30,3 % el
  oficial). Hoy no compensa.
- **La referencia ampliada de C sí es mejor que la oficial:** con las mismas
  falsas alarmas responde más en 2020 y tiene más potencia. Con umbral 1,9
  cumple el criterio con un 27 % menos de alertas en calma (4,02 % frente a
  5,51 %). Es una mejora real pero modesta, y el umbral se ha elegido con los
  mismos datos con que se evalúa: hay que confirmarlo fuera de esta muestra
  antes de adoptarlo.
- **Antes, corregir su debilidad:** centrar los cambios de cada mes en su
  propia mediana antes de juntarlos, para no mezclar estacionalidades (caso de
  Madrid). Es lo siguiente que conviene probar; no está evaluado aquí.
- **B no sustituye al detector, pero sirve como complemento:** para etiquetar
  cada alerta como local o regional, como en octubre de 2026. Es el método
  más potente para subidas locales.
- **A, tal como está simplificado, no se recomienda.**
- **Los municipios pequeños siguen sin solución:** ningún método detecta más
  del 8,4 % de las subidas del 10 % en Q1. Con recuentos de pocas personas, la
  información no da para más.

### Limitaciones de la comparación

- Las del resto del documento: sin verdad de referencia, la serie empieza en
  2005 y son recuentos, no tasas.
- La inyección es local: sube un municipio y no el resto de la Comunidad. Eso
  favorece a B. Un choque regional, como el de 2020, lo perjudica.
- Los umbrales de la comparación con las mismas falsas alarmas y el umbral
  1,9 de C se eligen en 2017-2019, que también se usa para evaluar.
- La calibración de C supone cambios normales e independientes. En calma,
  con 15 cambios, se acerca a lo nominal: 0,11 % frente a 0,135 %.
- A es una versión simplificada de Farrington, sin repesado de valores
  atípicos ni contraste de la tendencia. Con esas piezas podría comportarse
  mejor.
