# Cifras clave para la presentación

Todo lo necesario para las diapositivas de DATAMAD 2026, con la fuente de cada
cifra en el repositorio. Las cifras se han recalculado el 26/11/2026 a partir de
esos archivos. Los datos son los de
[`publicacion.json`](../../datos/publicados/publicacion.json): generados el
26/11/2026, commit `bae7cce`, de enero de 2005 a octubre de 2026.

> **Lenguaje para las diapositivas**
>
> - Di siempre **alerta experimental**: señala una subida que merece revisarse,
>   no demuestra un deterioro ni explica su causa.
> - **Tasa de alertas en calma**, no «falsas alarmas»: sin anomalías
>   verificadas no se puede saber cuántas alertas son falsas.
> - **Sensibilidad ante subidas sintéticas**, no «potencia»: son saltos de un
>   solo mes sumados a cambios reales, que pueden ser negativos; no son crisis
>   graduales ni prolongadas.
> - **Local** y **regional** son etiquetas estadísticas, no causas.
> - El 0,135 % es la referencia de una normal con parámetros conocidos, no la
>   tasa que debería dar el detector. No lo compares con el 5,5 % como «tantas
>   veces más».

## 1. Datos abiertos

| Conjunto de datos | Enlace | Licencia | Uso |
|---|---|---|---|
| Paro registrado por edad y municipio | [datos.comunidad.madrid](https://datos.comunidad.madrid/dataset/paro_registrado_edad_municipio) | CC BY 4.0 | Serie principal: detector y desglose por edad |
| Contratos de trabajo por municipio | [datos.comunidad.madrid](https://datos.comunidad.madrid/dataset/contratos_trabajo_municipio) | CC BY 4.0 | Contexto en la ficha; no interviene en el detector |
| Municipios de la Comunidad de Madrid | [datos.comunidad.madrid](https://datos.comunidad.madrid/dataset/municipio_comunidad_madrid) | CC BY 4.0 | Códigos INE para cruzar el mapa |
| Límites municipales (Geoportal IDEM) | [idem.comunidad.madrid](https://idem.comunidad.madrid/catalogocartografia/srv/spa/catalog.search#/metadata/spacm_divisionesadmin) | CC BY 4.0 Comunidad de Madrid | Mapa de la vista general |

Fuente: [`docs/fuentes_datos.md`](../fuentes_datos.md) (una sección por
conjunto y «Licencia y atribución») y `publicacion.json` (`originales` y
`atribucion`). Paro y contratos se descargaron el 18/11/2026; municipios y
límites, el 20/11/2026. Todos se verifican con su huella SHA-256. El código
tiene licencia MIT ([`LICENSE`](../../LICENSE)).

Atribución para la diapositiva de créditos. La primera es la del pie de la
aplicación; la segunda, la que pide el aviso legal del Geoportal IDEM
([`README.md`](../../README.md#datos)):

> Datos: Portal de Datos Abiertos de la Comunidad de Madrid, con licencia CC BY
> 4.0. Fuente: D. G. del Servicio Público de Empleo. Este proyecto los
> transforma: series mensuales y alertas experimentales calculadas.
>
> Información geográfica de la Comunidad de Madrid. Acceso público y gratuito en
> CC BY 4.0 Comunidad de Madrid.

## 2. Cobertura

| Cifra | Valor | Fuente |
|---|---|---|
| Municipios | **179**, todos los de la Comunidad | [`alertas.csv`](../../datos/publicados/alertas.csv): valores distintos de `municipio` |
| Periodo | **enero de 2005 a octubre de 2026** (262 meses) | `alertas.csv`: `fecha`; `publicacion.json`: `datos_desde` y `datos_hasta` |
| Combinaciones municipio-mes | 46.898 | `alertas.csv`: número de filas |
| Primer mes evaluable | febrero de 2010, porque hacen falta 5 años de historial | [`validacion_mensual.csv`](../../resultados/validacion/validacion_mensual.csv): 201 meses, de febrero de 2010 a octubre de 2026 |
| Meses evaluados | 33.739 municipio-mes, con 1.859 alertas (5,5 %) | `alertas.csv`: `estado_detector` desde febrero de 2010 |

## 3. Octubre de 2026

Fuente: `alertas.csv`, filas con `fecha` 2026-10-01, columna
`estado_detector`; la etiqueta, en
[`clasificacion_local_regional.csv`](../../datos/publicados/clasificacion_local_regional.csv),
columna `clasificacion`.

| Estado | Municipios |
|---|---:|
| Con alerta experimental | **15** |
| Sin alerta | 157 |
| No evaluables (dispersión cero) | 7 |
| **Total** | **179** |

- **De las 15 alertas, 2 son locales** (Soto del Real y Alameda del Valle):
  destacan también frente al resto de la Comunidad. Las otras 13 son
  regionales: compatibles con la evolución del resto de la Comunidad (método
  B). Son etiquetas estadísticas, no causas.
- Con alerta, de mayor a menor puntuación: Guadarrama, San Martín de la Vega,
  Madrid, Navalagamella, Soto del Real, Perales de Tajuña, Fuentidueña de Tajo,
  Galapagar, Alameda del Valle, El Vellón, Móstoles, Batres, Campo Real, Getafe
  y Collado Villalba.
- No evaluables: El Atazar, Braojos, Orusco de Tajuña, Quijorna, Robregordo,
  Somosierra y Valdaracete.
- Paro registrado de los 179 municipios: 287.356 personas, 4.071 más que en
  septiembre (`alertas.csv`: suma de `paro_total` y `paro_mes_anterior`). Es la
  suma de los tres grupos de edad y no se ha contrastado con los totales
  oficiales: no la presentes como cifra oficial.

### Caso de Madrid

Fuente: `alertas.csv`, fila de Madrid de 2026-10-01, salvo donde se indica.

| Cifra | Valor | Columna o archivo |
|---|---|---|
| Paro registrado | 136.522 en septiembre y **138.652** en octubre | `paro_mes_anterior`, `paro_total` |
| Cambio mensual | **+2.130 personas** (+1,6 %) | `cambio_mensual`, `variacion_mensual_pct` |
| Lo habitual en octubre | **+61**: mediana de −5.282, −91, +61, +233 y +1.495 (octubres de 2021 a 2025) | `referencia_cambio`; `cambio_mensual` de esos meses |
| Dispersión | MAD de 172, que da una escala de 1,4826 × 172 = 255,0 | `mad_cambio`, `escala_robusta` |
| Límite de alerta | **+826** (61 + 3 × 255,0) | `limite_superior` |
| Exceso sobre el límite | 1.304 personas | `cambio_mensual` − `limite_superior` |
| Puntuación robusta | 8,11, con un umbral de 3 | `puntuacion_robusta` |
| Grupo con mayor aumento | **De 25 a 44 años: +1.074**. Menores de 25: +704; mayores de 44: +352 | [`paro_edad_mensual.csv`](../../datos/publicados/paro_edad_mensual.csv), septiembre y octubre de 2026 |
| Etiqueta | **Regional**: compatible con la evolución del resto de la Comunidad. El resto subió +1.941 y, con esa subida, el método B esperaba unas +1.831 personas en Madrid | `clasificacion_local_regional.csv`: `cambio_resto_comunidad`, `prediccion_cambio_b`, `clasificacion` |
| Otros métodos | C centrado y C, con el umbral elegido fuera de muestra, no dan alerta: sus límites son +2.388 y +2.621 | [`resumen_metodos.csv`](../../resultados/validacion/resumen_metodos.csv): filas `Cc_fm` y `C_fm`, columna `madrid_oct_2026_limite_cambio` |

Frase para la diapositiva: «En octubre de 2026 el paro de Madrid subió 2.130
personas, cuando lo habitual en octubre era +61 y el límite de alerta, +826. Es
una alerta regional: la subida es compatible con la evolución del resto de la
Comunidad.»

## 4. Validación

No hay una lista de anomalías confirmadas, así que se mide el comportamiento del
detector, sin información futura, en 201 meses (de febrero de 2010 a octubre de
2026). Detalle en [`docs/validacion.md`](../validacion.md) y resumen en
[`docs/metodologia.md`](../metodologia.md).

| Cifra | Qué dice | Fuente |
|---|---|---|
| **67,5 % frente a 5,5 %** | En abril de 2020 saltó la alerta en 114 de los 169 municipios evaluables, frente al 5,5 % en los abriles de 2017-2019 | [`episodio_2020.csv`](../../resultados/validacion/episodio_2020.csv): `mes` 4, periodos 2020 y «2017-2019», `con_alerta`, `evaluables`, `pct_alertas_evaluables` |
| **98,7 %** | Esos 114 municipios reunían el 98,7 % del paro registrado de los 179 municipios en abril de 2020 | `episodio_2020.csv`: `pct_paro_comunidad_en_alerta` |
| **55,4 % y 30,3 % (2015-2019)** | Sensibilidad ante subidas sintéticas: al sumar a mano una subida al cambio real de un mes de 2015-2019, que puede ser negativo, detecta el 55,4 % de las subidas del 10 % y el 30,3 % de las del 5 %. Incluye el 4,6 % de meses que ya tenían alerta sin la subida | [`potencia.csv`](../../resultados/validacion/potencia.csv): `quintil` Todos, `subida_pct` 10, 5 y 0, `tasa_deteccion_pct` |
| **53,2 % y 27,0 % (2015-2019)** | Lo mismo, contando solo los 9.602 meses que no tenían ya alerta | `potencia.csv`: `quintil` Todos, `tasa_deteccion_sin_alerta_previa_pct` |
| **94,8 % frente a 8,4 % (2015-2019)** | Con la subida del 10 %, detecta el 94,8 % en el 20 % de municipios con más paro y el 8,4 % en el 20 % con menos | `potencia.csv`: `quintil` Q5 y Q1, `subida_pct` 10 |

Son saltos de un solo mes: no dicen cómo responde el detector a crisis
graduales o prolongadas.

**Comparación de métodos, en una frase:** el detector oficial no es el mejor
en todo, pero se mantiene por continuidad, interpretabilidad y prudencia. Con
el umbral elegido fuera de muestra y evaluada en 2017-2019, la referencia
ampliada a los meses contiguos (C) da menos alertas en calma (4,15 % frente a
5,51 %) y detecta más las subidas del 5 % y del 10 %, pero menos las del 1 % y
el 2 %, y mezcla estacionalidades. «C centrado», la propuesta para una versión
2, detecta el 37,9 % de las subidas del 5 % en 2017-2019, frente al 32,4 % del
oficial, con casi la misma tasa en calma (5,62 %).

Fuente: `resumen_metodos.csv`, filas `oficial`, `C_fm` y `Cc_fm`, columnas
`pct_alertas_calma` y `potencia_*pct_2017_2019`; decisión en
[`docs/decisiones.md`](../decisiones.md) (26/11/2026).

> No pongas 30,3 % y 32,4 % en la misma diapositiva sin su periodo. Las dos son
> la sensibilidad del detector oficial ante subidas sintéticas del 5 %, pero la
> primera se mide en 2015-2019 y la segunda en 2017-2019, el periodo de la
> comparación. Con las del 10 %: 55,4 % (2015-2019) y 55,3 % (2017-2019).

## 5. Limitaciones

1. **Sin verdad de referencia:** no existe una lista de subidas anómalas
   confirmadas, así que se mide cuántas alertas da el detector y si detecta
   subidas añadidas a mano, no su acierto ni cuántas alertas son falsas
   ([`metodologia.md`](../metodologia.md), sección 6).
2. **Alertas en calma:** en 2017-2019, periodo de referencia estable, marca el
   5,51 % de los meses (331 de 6.006); una alerta pide revisar el caso, no
   confirma un deterioro
   ([`calma_2017_2019.csv`](../../resultados/validacion/calma_2017_2019.csv)).
3. **Municipios pequeños:** en el 20 % con menos paro, el 26,1 % de los meses
   no se puede evaluar (1.886 de 7.236) y solo detecta el 8,4 % de las subidas
   sintéticas del 10 % en 2015-2019
   ([`municipios_pequenos.csv`](../../resultados/validacion/municipios_pequenos.csv),
   `pct_dispersion_cero` de Q1; `potencia.csv`, Q1).
4. **Versión actual de los datos:** se trabaja con la versión actual, no con la
   que existía en cada fecha ([`validacion.md`](../validacion.md),
   «Limitaciones»).

## 6. Enlaces

- Aplicación: <https://pulso-laboral-madrid.streamlit.app/>
- Repositorio: <https://github.com/romanmen-dev/pulso-laboral-madrid>
- Metodología en una página:
  <https://github.com/romanmen-dev/pulso-laboral-madrid/blob/main/docs/metodologia.md>
- Validación completa:
  <https://github.com/romanmen-dev/pulso-laboral-madrid/blob/main/docs/validacion.md>

Fuente: [`README.md`](../../README.md) y `src/validacion_app.py`
(`URL_METODOLOGIA`, `URL_VALIDACION`).

> La pestaña «¿Cómo sabemos que funciona?», la etiqueta local/regional y
> `docs/metodologia.md` están en la rama `rodrigo/validacion`. Los enlaces a
> `main` darán error 404 hasta que se fusione. Si la aplicación se despliega
> desde `main`, tampoco mostrará la pestaña nueva hasta entonces. Compruébalo
> antes de presentar.

## 7. Material visual de esta carpeta

Capturas al doble de resolución (2.088 píxeles de ancho), en tema claro, de la
aplicación con solo `datos/publicados/`. Se hicieron el 26/11/2026 con los
textos revisados de la rama `rodrigo/validacion`.

| Archivo | Qué muestra | Diapositiva |
|---|---|---|
| [`01_vista_general_octubre_2026.png`](01_vista_general_octubre_2026.png) | Recuento del mes (15, 157 y 7) y mapa | Resultados de octubre |
| [`02_mapa_octubre_2026.png`](02_mapa_octubre_2026.png) | Solo el mapa, con su leyenda | Portada o resultados |
| [`03_alertas_octubre_2026_local_regional.png`](03_alertas_octubre_2026_local_regional.png) | Tabla de las 15 alertas con la columna «Tipo» y la frase «2 son locales» | Etiqueta local/regional |
| [`04_ficha_madrid_octubre_2026.png`](04_ficha_madrid_octubre_2026.png) | Ficha de Madrid: alerta regional, +2.130, +61, +826 y paro de 24 meses | Caso de Madrid |
| [`05_madrid_cambio_por_edad.png`](05_madrid_cambio_por_edad.png) | Cambio por grupo de edad en Madrid (25 a 44 años: +1.074) | Caso de Madrid |
| [`06_validacion_alertas_por_mes.png`](06_validacion_alertas_por_mes.png) | Alertas por mes de 2010 a 2026, con abril de 2020 marcado y la frase del 67,5 % | Validación |
| [`07_validacion_sensibilidad_por_tamano.png`](07_validacion_sensibilidad_por_tamano.png) | Sensibilidad ante subidas sintéticas, por quintil de municipios, con la tasa en meses sin alerta previa | Validación |
| [`08_validacion_comparacion_metodos.png`](08_validacion_comparacion_metodos.png) | Subidas sintéticas detectadas frente a alertas en calma, por método | Comparación de métodos |

**Vídeo:** [`video_recorrido_app.mp4`](video_recorrido_app.mp4). Dura 40 s y
es un MP4 H.264 de 1920 × 1080, sin sonido, de 7,8 MB. Va a velocidad real y sin
cortes, y el puntero se dibujó para la grabación. Recorrido:

| Tiempo | Qué se ve |
|---|---|
| 0:00 | Vista general: 15, 157 y 7 |
| 0:06 | El puntero pasa sobre Madrid en el mapa: cambio +2.130 y límite +826 |
| 0:08 | Clic en Madrid |
| 0:09 | Se abre la ficha: alerta regional, después el paro de 24 meses y el grupo de edad |
| 0:23 | Clic en la pestaña «¿Cómo sabemos que funciona?» |
| 0:27 | Alertas por mes, con abril de 2020 y el 67,5 % |
| 0:32 | Sensibilidad ante subidas sintéticas por tamaño de municipio |
| 0:36 | Comparación con otros métodos, hasta el final |
