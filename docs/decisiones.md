# Decisiones metodológicas

Registro de las decisiones del proyecto, sus motivos y las
comprobaciones pendientes. Las propuestas se identificarán como
tales hasta que se adopten.


### 19/11/2026 — Interpretación y evaluación de la MAD


- Decisión de trabajo: conservar el detector de mediana y MAD como
  versión experimental de referencia, pendiente de validación.
- Motivo: reduce la influencia de cambios extremos y es explicable,
  pero cinco observaciones pueden producir estimaciones inestables
  y no permiten modelizar explícitamente la evolución reciente.
- Mantener los casos con MAD cero como no evaluables; no sustituir
  la dispersión por una constante arbitraria para generar puntuaciones.
- Próxima evaluación propuesta: estudiar el comportamiento histórico
  de la versión actual y después comparar ventanas y umbrales,
  utilizando únicamente información anterior al mes evaluado.
- No interpretar la puntuación como probabilidad, gravedad social
  ni nivel de confianza.

### 19/11/2026 — Contrato de `resultados/alertas.csv` y detector en script

- Propuesta: el formato de `resultados/alertas.csv`, la tabla que conecta
  el detector con la aplicación, se define en `docs/contrato_alertas.md`.
  Se basa en las columnas que calcula `notebooks/02_detector_inicial.ipynb`
  y añade `grupo_edad_principal`. Pendiente de confirmación por Roman.
- Decisión de trabajo: trasladar el detector a `src/detectar_alertas.py`
  sin cambios de método ni de parámetros: ventana de 5 años, mínimo de
  5 cambios, umbral de 3 y factor 1,4826. El mes evaluado no entra en su
  propia referencia.
- Comprobación: el script reproduce el notebook en todas las filas y
  columnas comunes. En octubre de 2026 da 15 alertas experimentales,
  157 municipios sin alerta y 7 con dispersión cero.

### 19/11/2026 — Incidencias en los contratos de trabajo

- Constatación: los contratos de mayo de 2026 son menos de la mitad de lo
  habitual en casi todos los municipios, y Velilla de San Antonio repite
  368 contratos desde septiembre de 2025. Ambas incidencias están en el
  archivo original, idéntico al que publica el portal el 19/11/2026, y no
  en la preparación: los 46.898 valores procesados coinciden con el original.
- Decisión de trabajo: no corregir ni excluir estos datos sin una
  confirmación de la fuente. Se deja constancia aquí y en
  docs/fuentes_datos.md.
- Los contratos no intervienen en el detector: las alertas no se ven afectadas.
- La nota del portal sobre el redondeo a múltiplos de 5 desde 2022 no se
  aprecia en los valores municipales del archivo. No se aplica ningún
  tratamiento.
- La ficha avisa de ambas incidencias cuando el gráfico de contratos
  incluye meses afectados. Pendiente: consultar a la D. G. del Servicio
  Público de Empleo si procede.

### 20/11/2026 — Cobertura y casos con MAD cero

- Decisión: mantener los casos con MAD cero como no evaluables,
  conservando sus datos y el estado `dispersion_cero`.
- Motivo: la puntuación robusta requiere una escala positiva.
  No disponer de puntuación no equivale a ausencia de alerta.
- Presentar conjuntamente el porcentaje de alertas entre evaluables
  y la cobertura sobre el total de municipios.
- Pendiente: analizar la recurrencia de MAD cero por municipio
  antes de proponer un tratamiento alternativo.

  ### 20/11/2026 — Limitación de cobertura en series pequeñas

- Constatación: la MAD cero se concentra en municipios con volúmenes
  pequeños de paro registrado y puede impedir su evaluación durante
  gran parte del periodo.
- Decisión: mantener explícitos los casos no evaluables y documentar
  la cobertura por municipio, además de la cobertura mensual agregada.
- Motivo: una cobertura global elevada oculta limitaciones persistentes
  en determinados municipios.
- Próxima comprobación: comparar ventanas históricas sobre un periodo
  común, evaluando cobertura y comportamiento de las alertas.
- No modificar todavía el detector utilizado por la aplicación.

### 20/11/2026 — Copia publicada de los datos para la aplicación

- Decisión: publicar la aplicación en Streamlit Community Cloud con una
  copia versionada de los datos que lee, en datos/publicados/, generada
  con src/publicar_datos.py. La cadena de descarga, preparación y
  detección no se ejecuta en el servidor.
- Motivo: los originales y los procesados no se versionan y la aplicación
  los necesita. Ejecutar la cadena en el servidor haría depender cada
  arranque del portal, y la descarga se detiene a propósito cuando el
  portal publica una versión nueva sin revisar. La copia publica
  exactamente los datos revisados.
- Trazabilidad: publicacion.json registra la fecha de generación, el
  periodo de los datos, el commit, la atribución y las huellas SHA-256 de
  los originales y de cada archivo. El script se detiene si alertas.csv es
  anterior a los datos procesados o si los originales no son la versión
  revisada. .gitattributes impide que Git cambie los finales de línea de
  datos/publicados/, para que las huellas coincidan en cualquier sistema.
- Se publican solo alertas.csv, paro_edad_mensual.csv y
  contratos_mensuales.csv: 14,2 MB en CSV sin comprimir, para poder leerlos
  y compararlos. Git guarda el historial comprimido, unos 2 MB por
  actualización.
- La aplicación usa las tablas locales si están todas y, si no, la copia
  publicada; nunca mezcla las dos. La barra lateral indica hasta qué mes
  llegan los datos y de dónde salen.
- Licencia: los datos del portal tienen licencia CC BY 4.0, que permite
  redistribuirlos con atribución e indicando los cambios. La atribución
  figura en docs/fuentes_datos.md, en publicacion.json y en el pie de la
  aplicación.
- Para actualizar la aplicación publicada hay que repetir la cadena en
  local, ejecutar src/publicar_datos.py y hacer commit de datos/publicados/.

### 20/11/2026 — Mapa de municipios en la vista general

- Decisión: mostrar encima de la tabla de alertas un mapa de los 179
  municipios coloreado por el estado del mes elegido. Al pinchar un
  municipio se abre su ficha, igual que con una fila de la tabla.
- Fuentes: la tabla de municipios del portal, para pasar del nombre al
  código, y los límites municipales del Geoportal IDEM. Las dos tienen
  licencia CC BY 4.0 y se descargan con su huella SHA-256, como los demás
  originales (docs/fuentes_datos.md).
- Cruce por código INE, no por nombre: los nombres del paro se traducen a
  código con la tabla de municipios (artículo al final y 8 equivalencias
  explícitas). src/preparar_mapa.py se detiene si algún municipio no tiene
  exactamente un término municipal, si sobra alguno o si un nombre no casa.
- Los 13 enclaves se unen a su municipio. Las 2 comunidades
  jurisdiccionales (Los Baldíos y El Redegüelo) no se colorean: son
  territorios compartidos y no pertenecen a un solo municipio.
- La geometría se simplifica con shapely.coverage_simplify (tolerancia de
  0,001°, unos 100 m), que no deja huecos ni solapes entre vecinos. Ningún
  municipio cambia más de un 0,56 % de superficie y el GeoJSON ocupa unos
  280 KB. shapely solo está en requirements-dev.txt: la aplicación lee el
  GeoJSON ya simplificado, también desde datos/publicados/.
- Colores: los mismos que la pestaña de cambios frente al límite (azul sin
  alerta, naranja alerta experimental, gris no evaluable), comprobados con
  un validador de paletas para daltonismo en modo claro y oscuro. No se
  añaden categorías.

### 20/11/2026 — Contratos fuera de la parte principal de la ficha

- Planteamiento de Roman: el paro y los contratos no miden la misma
  población. Según las notas metodológicas, el paro registrado se asigna al
  municipio de residencia de la persona y los contratos, a la localidad del
  centro de trabajo. Además, se cuentan contratos, no personas.
- Comprobación (docs/fuentes_datos.md): la agrupación de los contratos por
  el centro de trabajo y la diferencia entre contratos y personas constan en
  las notas metodológicas v09 de la D. G. del Servicio Público de Empleo. La
  asignación del paro a la residencia la recogen las notas del Ayuntamiento
  de Madrid y del Instituto Aragonés de Estadística, con datos del SEPE; para
  este dataset es probable, pero la fuente no lo confirma.
- Decisión: sacar los contratos de la parte principal de la ficha. Esa
  parte muestra solo el paro: estado del mes, cifras, evolución, edades,
  interpretación y detalle técnico.
- Los contratos pasan a una sección al final de la ficha, plegada por
  defecto: «Contratos registrados en centros de trabajo del municipio». Un
  texto explica qué recoge la serie y por qué no es directamente comparable
  con el paro, y se mantienen los avisos de las incidencias de mayo de 2026
  y de Velilla de San Antonio (19/11/2026).
- Sin doble eje ni cocientes entre contratos y paro. La tabla con los datos
  de los gráficos del paro ya no incluye los contratos: tienen su propia
  tabla en la sección.
- Los contratos siguen sin intervenir en el detector.

### 26/11/2026 — Validación: se mantiene el detector oficial y se añade la etiqueta local/regional

- Constatación: la validación (`src/validar_detector.py`, `docs/validacion.md`)
  mide el comportamiento del detector sin verdad de referencia. Responde a la
  crisis de 2020: en abril saltó la alerta en el 67,5 % de los municipios
  evaluables, frente al 5,5 % en los abriles de 2017-2019. En calma
  (2017-2019) marca el 5,51 % de los meses. El 0,135 % de una normal con
  parámetros conocidos no es la referencia de este detector, que estima la
  escala con solo 5 cambios. En 2015-2019 detecta el 30,3 % de las subidas
  sintéticas del 5 % y el 55,4 % de las del 10 %, y apenas nada en los
  municipios pequeños: con la del 10 %, el 8,4 % en el 20 % con menos paro.
- Decisión: **se mantiene el detector oficial**, con ventana de 5 años, mínimo
  de 5 cambios y umbral 3, sin cambios en `src/detectar_alertas.py` ni en
  `docs/contrato_alertas.md`.
- Comparación con el umbral elegido fuera de muestra (en 2012-2016, para dar
  la tasa del oficial en esos años, y evaluado en 2017-2019 y 2020; la
  sensibilidad ante subidas sintéticas, en 2017-2019). El oficial no es el
  mejor en todo:
  - C centrado: 5,62 % en calma frente a 5,51 %, 40,4 % de alertas en
    marzo-junio de 2020 frente a 33,5 %, y sensibilidad del 37,9 % frente a
    32,4 % (5 %) y del 63,2 % frente a 55,3 % (10 %). Detecta más, pero no
    reduce las alertas en calma.
  - C: mejora la tasa en calma (4,15 % frente a 5,51 %), la respuesta a 2020
    (39,0 % frente a 33,5 % de marzo a junio) y las subidas del 5 % y del 10 %
    (32,8 % y 63,6 % frente a 32,4 % y 55,3 %). Pero detecta menos las del 1 %
    y el 2 % (6,7 % frente a 8,9 %; 11,1 % frente a 13,9 %) y mezcla
    estacionalidades: junta cada mes con los contiguos.
  - Calibrar el umbral al 0,135 % deja la sensibilidad por debajo del 4 % con
    subidas del 5 %. A (Farrington) tiene menos sensibilidad que el oficial en
    todos los niveles comparados, y B no responde a 2020 (1,0 %).
- Motivo: se mantiene el oficial por continuidad (es el detector del contrato
  y de la aplicación), interpretabilidad («lo habitual» es la mediana del
  mismo mes en 5 años) y prudencia (la evaluación fuera de muestra solo abarca
  tres años de calma y un episodio, y las mejoras son pequeñas o mixtas), no
  porque sea el mejor en todo.
- Decisión: añadir a la aplicación una **etiqueta local/regional**, solo como
  contraste, sin cambiar el estado oficial de la alerta. Usa el método B:
  recta robusta (Theil-Sen) entre el cambio del municipio y el del resto de la
  Comunidad en los 60 meses anteriores. Es local si el residuo supera 3 escalas
  robustas: la subida destaca también frente al resto de la Comunidad. Si no,
  es regional: es compatible con la evolución del resto de la Comunidad. Son
  etiquetas estadísticas, no causas. De las 1.859 alertas oficiales, 145 son
  locales y 1.714 regionales; en octubre de 2026, 2 de 15 (Soto del Real y
  Alameda del Valle). Motivo: B es el método más sensible a subidas sintéticas
  locales con la misma tasa en calma, pero no ve los choques regionales, así
  que complementa al oficial y no lo sustituye.
- Propuesta (pendiente): **versión 2 con C centrado**. Usa la referencia del
  oficial y estima la escala con 15 cambios (el mismo mes y los contiguos,
  centrados en la mediana de su mes), con el umbral elegido fuera de muestra
  (2,59). Antes de adoptarla hay que repetir la evaluación con más años y
  decidir qué se prioriza: más sensibilidad con la misma tasa en calma (C
  centrado) o menos alertas en calma (C).
- La aplicación muestra la validación en la pestaña «¿Cómo sabemos que
  funciona?», que solo lee los CSV publicados. La ficha indica en el detalle
  técnico qué diría cada método alternativo ese mes. `src/publicar_datos.py`
  publica esos resultados con sus huellas en `publicacion.json`. El método,
  en una página, está en `docs/metodologia.md`.

### 26/11/2026 — Lenguaje de la validación

- Decisión: en la documentación y en la aplicación no se habla de «falsas
  alarmas» ni de «potencia». Se usa «tasa de alertas en calma» (o «alertas en
  un periodo de referencia estable») y «sensibilidad ante subidas
  sintéticas». Los nombres de archivos y columnas (`potencia.csv`,
  `potencia_*`) no cambian.
- Motivo: no hay anomalías municipales verificadas, así que no se puede saber
  cuántas alertas de 2017-2019 son falsas. Y las subidas sintéticas son saltos
  de un solo mes sumados a cambios reales, que pueden ser negativos: no miden
  la respuesta a crisis graduales ni prolongadas.
- El 0,135 % se presenta como la referencia de una normal con media y escala
  conocidas, no como la tasa que debería dar el detector, que estima las dos
  con solo 5 cambios.
- Las etiquetas local y regional se describen como estadísticas: «regional»,
  compatible con la evolución del resto de la Comunidad (método B); «local»,
  destaca también frente al resto de la Comunidad. No indican causas.
- Las cifras del oficial llevan siempre su periodo: sensibilidad de 2015-2019
  en la validación (30,3 % y 55,4 % con subidas del 5 % y del 10 %) y de
  2017-2019 en la comparación fuera de muestra (32,4 % y 55,3 %).
- No cambia ningún cálculo ni ningún resultado.
