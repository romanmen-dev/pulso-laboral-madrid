# Metodología

Pulso Laboral Madrid en una página: cómo se calcula la alerta, cuándo no se
evalúa, cómo se ha validado, con qué se ha comparado, qué significa la
etiqueta local/regional y qué límites tiene. El formato de los resultados está
en [`contrato_alertas.md`](contrato_alertas.md), las cifras completas en
[`validacion.md`](validacion.md) y los motivos de cada decisión en
[`decisiones.md`](decisiones.md).

## 1. Detector oficial

Para cada uno de los 179 municipios y cada mes $t$, con el paro registrado
(suma de los tres grupos de edad):

| Paso | Fórmula |
|---|---|
| Cambio mensual | $c_t = \text{paro}_t - \text{paro}_{t-1}$ |
| Cambio habitual | $r_t = \text{mediana}(c_{t-12},\ c_{t-24},\ \dots,\ c_{t-60})$: el mismo mes de los 5 años anteriores |
| Dispersión | $\text{MAD}_t = \text{mediana}\lvert c_{t-12k} - r_t \rvert$, con $k = 1, \dots, 5$, y escala $s_t = 1{,}4826 \cdot \text{MAD}_t$ |
| Límite de alerta | $L_t = r_t + 3\,s_t$ |
| Puntuación robusta | $z_t = (c_t - r_t) / s_t$ |
| **Alerta experimental** | $c_t > 0$ y $z_t > 3$, es decir, el paro sube y supera el límite |

El mes evaluado nunca entra en su propia referencia, y ningún cálculo usa meses
posteriores. La puntuación no es una probabilidad ni una medida de gravedad.

**Ejemplo: Madrid, octubre de 2026.** Los cambios de septiembre a octubre de
2021 a 2025 fueron −5.282, −91, +61, +233 y +1.495 personas. Su mediana es
**+61** (lo habitual). Las distancias a la mediana son 5.343, 152, 0, 172 y
1.434, así que la MAD es 172 y la escala, 1,4826 × 172 = 255,0. El límite es
61 + 3 × 255,0 = **+826**. En octubre de 2026 el paro subió **+2.130**: la
puntuación es (2.130 − 61) / 255,0 = 8,11 > 3, así que se marca alerta
experimental. La subida supera el límite en 1.304 personas.

## 2. Cuándo no se evalúa

Un mes no evaluable no se presenta nunca como «sin alerta»:

- **Historial insuficiente:** hay menos de 5 cambios del mismo mes. Afecta a
  los primeros 61 meses de cada municipio, de enero de 2005 a enero de 2010.
- **Dispersión cero:** la MAD es 0 (los cambios de referencia casi no
  varían) y la puntuación no se puede calcular. Afecta a 2.240 municipio-mes
  desde febrero de 2010. Se concentra en los municipios con menos paro: en el
  20 % más pequeño, al 26,1 % de los meses.

## 3. Validación

No hay una lista de anomalías municipales confirmadas, así que no se puede
medir el acierto. Se mide el comportamiento del detector, de febrero de 2010 a
octubre de 2026 (`src/validar_detector.py`, [`validacion.md`](validacion.md)):

- **Frecuencia:** 1.859 alertas en 33.739 municipio-mes evaluables, el 5,51 %.
- **Calma (2017-2019):** 5,51 % de alertas, frente al 0,135 % que se esperaría
  con datos normales y una referencia exacta, P(Z > 3). La causa es estimar la
  escala con solo 5 cambios: aun con datos normales, la simulación da un 7,58 %
  de puntuaciones mayores que 3.
- **Crisis de 2020:** en abril de 2020 saltó la alerta en el 67,5 % de los
  municipios evaluables (114 de 169), frente al 5,5 % en los abriles de
  2017-2019.
- **Potencia:** sumando a mano una subida al cambio de un mes de 2015-2019,
  se detecta el 30,3 % de las subidas del 5 % y el 55,4 % de las del 10 %. Con
  la del 10 %, el 94,8 % en el 20 % de municipios con más paro y el 8,4 % en el
  20 % con menos.
- **Persistencia:** fuera de marzo-junio de 2020, solo el 4,1 % de las alertas
  se repite el mes siguiente, menos que la tasa base del 5,1 %.

## 4. Comparación con otros métodos

`src/comparar_metodos.py` prueba, con el mismo banco de pruebas, tres
alternativas ([`validacion.md`](validacion.md#comparación-con-métodos-alternativos)):

- **C:** misma regla con 15 cambios: el mismo mes y los dos contiguos de los 5
  años anteriores.
- **C centrado:** la referencia del oficial, con la escala estimada con esos 15
  cambios, cada uno centrado en la mediana de su mes.
- **A:** quasi-Poisson tipo Farrington sobre el nivel de paro.
- **B:** anomalía local frente al resto de la Comunidad.

Resultados:

- **Calibrar el umbral al 0,135 % no compensa:** los métodos calibrados se
  quedan casi sin potencia.
- **Con las mismas alertas en calma, C y C centrado detectan más que el
  oficial.**
- **Con el umbral elegido fuera de muestra** (en 2012-2016, para dar la tasa
  del oficial en esos años, y evaluado en 2017-2019 y 2020):
  - C centrado da casi las mismas alertas en calma (5,62 % frente a 5,51 %).
    Responde más en 2020 (40,4 % frente a 33,5 % de marzo a junio) y detecta
    más subidas (37,9 % frente a 32,4 % con el 5 %; 63,2 % frente a 55,3 % con
    el 10 %).
  - C da menos alertas en calma (4,15 %), pero detecta menos las subidas del
    1 % y el 2 %.

Ninguno mejora las tres cosas a la vez, así que **se mantiene el detector
oficial**. C centrado es la propuesta para una versión 2, pendiente de
confirmarse con más años.

## 5. Etiqueta local o regional

Cada alerta oficial lleva una etiqueta de contraste, calculada con el método B:

1. Con los 60 meses anteriores, se estima la relación entre el cambio del
   municipio y el del resto de la Comunidad (sin el propio municipio), con una
   recta robusta de Theil-Sen.
2. Su dispersión es 1,4826 × MAD de los residuos.
3. Si este mes la subida supera lo que predice esa recta en más de 3 veces la
   dispersión, la alerta es **local**: el paro sube más que en el resto. Si
   no, es **regional**: sube en línea con el conjunto de la Comunidad.

El estado oficial no cambia. De las 1.859 alertas oficiales, 145 son locales y
1.714 regionales. En octubre de 2026, 2 de 15 son locales: Soto del Real y
Alameda del Valle. La de Madrid es regional: con lo que subió el resto de la
Comunidad (+1.941), B esperaba una subida de unas 1.831 personas.

## 6. Limitaciones

- **Sin verdad de referencia:** se mide cuántas alertas da el detector y si
  detecta subidas añadidas a mano, no su acierto.
- **Alertas en calma:** un 5,5 %, muy por encima del 0,135 % nominal. Una
  alerta pide revisar el caso; no demuestra un deterioro ni explica su causa.
- **Municipios pequeños:** con pocas personas en paro, muchos meses no se
  pueden evaluar y las subidas relativas apenas se detectan.
- **Pocos datos:** la serie empieza en 2005, así que el primer mes evaluable es
  febrero de 2010. La crisis de 2008-2009 no se puede evaluar y 2020 es el
  único episodio de referencia.
- **Recuentos, no tasas:** el paro registrado se cuenta en personas, sin
  población de referencia.
- **Sin tendencia:** el método no modeliza la tendencia reciente.
- **Datos actuales:** se usa la versión de hoy, no la que se publicó cada mes.
- **Paro total sin contrastar:** es la suma de los tres grupos de edad y está
  pendiente de contraste con los totales oficiales.
- **La etiqueta también es experimental:** depende del método B, que asume una
  relación estable con el resto de la Comunidad.
