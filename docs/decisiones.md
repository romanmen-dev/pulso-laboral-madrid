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