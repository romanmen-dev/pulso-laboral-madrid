# Fuentes de datos

Fecha de descarga: 18 de noviembre de 2026 (paro y contratos) y 20 de
noviembre de 2026 (municipios y límites municipales).

## Paro registrado por edad y municipio

- Organismo: Comunidad de Madrid.
- Página de origen:
  https://datos.comunidad.madrid/dataset/paro_registrado_edad_municipio
- Archivo local: datos/originales/paro_edad_municipio.csv
- Uso previsto: serie principal del análisis de paro y desglose por edad.
- Periodo temporal y cobertura: pendientes de comprobar en el CSV.
- Asignación al territorio: la ficha del dataset no indica a qué municipio
  se asigna cada persona en paro; su descripción es «Sin información
  adicional.». Las notas metodológicas del Ayuntamiento de Madrid y del
  Instituto Aragonés de Estadística, que trabajan con datos del SEPE, lo
  asignan al municipio de residencia del parado:
  - Ayuntamiento de Madrid, para la estadística de la ciudad de Madrid, en
    la definición de municipio de residencia:
    > Municipio en el que reside el demandante de empleo en su inscripción
  - Instituto Aragonés de Estadística:
    > El domicilio utilizado para la distribución del paro registrado
    > municipal es el de residencia de cada uno de los parados.

  Es probable que este dataset siga el mismo criterio, pero la fuente no lo
  confirma. Fuentes:
  - Ayuntamiento de Madrid, notas metodológicas del paro registrado de la
    ciudad de Madrid:
    https://www.madrid.es/UnidadesDescentralizadas/UDCEstadistica/Nuevaweb/Mercado%20de%20Trabajo/Paro/nuevo%20paro/2024%20y%202025/NOTAS%20METODOL%C3%93GICAS%20PARO%20REGISTRADO%20AYUNTAMIENTO%20DE%20MADRID.pdf
  - Instituto Aragonés de Estadística, «Paro registrado. Metodología»:
    https://www.aragon.es/documents/20127/674325/Paro_registrado_Metodologia.pdf/90b8117b-0309-75dd-f49c-ba8df018308c

## Contratos de trabajo por municipio

- Organismo: Comunidad de Madrid.
- Página de origen:
  https://datos.comunidad.madrid/dataset/contratos_trabajo_municipio
- Archivo local: datos/originales/contratos_municipio.csv
- Uso previsto: información complementaria sobre contratación.
- Periodo temporal y cobertura: pendientes de comprobar en el CSV.
- Asignación al territorio y unidad: los contratos se agrupan por la
  localidad del centro de trabajo, vivan donde vivan las personas
  contratadas, y se cuentan contratos, no personas. La ficha del dataset no
  lo explica; solo indica «Unidad: Contratos». Lo dicen las notas
  metodológicas del Cuadro de Mando de Entidades Locales de la D. G. del
  Servicio Público de Empleo (versión v09), que usan la misma Estadística de
  Contratos Registrados:
  > Los datos estadísticos de contratos de un mes determinado son los
  > comunicados por las personas empresarias durante ese mes
  > (independientemente de cuando se inicie el contrato) y son agrupados
  > según la localidad del centro de trabajo.

  > Personas contratadas: Las personas únicas que han firmado un contrato
  > registrado durante el periodo de referencia.

  Consultadas el 20/11/2026 en
  https://www.comunidad.madrid/docs/assets/2024/12/04/notas_metodologicas_v09.pdf,
  enlazadas desde
  https://www.comunidad.madrid/empleo/estadisticas-mercado-trabajo.
  Por eso los contratos y el paro no son directamente comparables, y la
  ficha muestra los contratos aparte (docs/decisiones.md, 20/11/2026).
- Notas del portal, copiadas literalmente el 19/11/2026:
  > A partir de octubre de 2021, la categoría "No distribuidos" incluye
  > cuidadoras no profesionales, así como las categorías "Otras provincias"
  > y "Sin descripción". Desde enero del año 2022, por secreto estadístico,
  > todos los datos excepto el total están redondeados al múltiplo de 5
  > más cercano.
- El archivo solo contiene los 179 municipios: no incluye el total de la
  Comunidad ni la categoría «No distribuidos». En sus valores municipales
  no se observa el redondeo: desde 2022, entre el 18,5 % y el 21,0 % son
  múltiplos de 5 según el año, como antes de 2022 y como se espera sin
  redondeo (20 %).
- Incidencias observadas el 19/11/2026 en el archivo original, sin
  corregir:
  - Mayo de 2026: 96.263 contratos, frente a 176.830 en abril y 233.453
    en junio. Bajan 167 de los 178 municipios comparables y 150 caen más
    de un 30 %. Ningún mayo de 2005 a 2025 bajó así. El portal no publica
    ninguna nota sobre ello.
  - Velilla de San Antonio: 368 contratos todos los meses desde
    septiembre de 2025 hasta octubre de 2026.

## Municipios de la Comunidad de Madrid

- Organismo: Comunidad de Madrid.
- Página de origen:
  https://datos.comunidad.madrid/dataset/municipio_comunidad_madrid
- Archivo local: datos/originales/municipios_comunidad_madrid.csv
  (codificación latin-1, separador `;`).
- Uso: tabla de correspondencia entre el nombre de cada municipio y su
  código INE, para cruzar el mapa por código y no por nombre.
- Contenido: 179 municipios con `municipio_codigo`, `municipio_codigo_ine`
  (6 cifras, con dígito de control) y `municipio_nombre`.
- Los nombres llevan el artículo entre paréntesis («Acebeda (La)») y 8 se
  escriben distinto que en el paro; las equivalencias están en
  src/preparar_mapa.py.
- Licencia: CC BY 4.0, según los metadatos del portal.

## Límites municipales (Geoportal IDEM)

- Organismo: Comunidad de Madrid, Infraestructura de Datos Espaciales (IDEM).
- Servicio: WFS
  https://idem.comunidad.madrid/geoidem/UnidadesAdministrativas/wfs, capa
  `UnidadesAdministrativas:IDEM_CM_UNID_ADMIN` («Divisiones
  Administrativas de la Comunidad de Madrid»). Metadatos:
  https://idem.comunidad.madrid/catalogocartografia/srv/spa/catalog.search#/metadata/spacm_divisionesadmin
- Archivo local: datos/originales/limites_municipales_idem.csv, con la
  geometría en WKT y coordenadas en EPSG:4326. Se descarga en CSV porque
  sale idéntico en cada petición; el GeoJSON incluye la hora de la petición
  y su huella cambiaría.
- Contenido: 194 entidades: 179 términos municipales, 13 enclaves y 2
  comunidades jurisdiccionales (Los Baldíos, de Cercedilla y Navacerrada; El
  Redegüelo, de El Boalo y Manzanares el Real). El código municipal es
  `CD_INE` (INE, 5 cifras).
- Licencia: «CC BY 4.0 Comunidad de Madrid», según las condiciones de acceso
  del servicio. Su aviso legal pide citar: «Información geográfica de la
  Comunidad de Madrid. Acceso público y gratuito en CC BY 4.0 Comunidad de
  Madrid». Advierte de que los datos son orientativos y de que no se
  garantiza que estén actualizados. No consta la fecha de la versión.
- Uso: límites del mapa de la vista general, tras unir los enclaves a su
  municipio, excluir las comunidades jurisdiccionales y simplificar la
  geometría (src/preparar_mapa.py).

## Licencia y atribución

- Licencia de los dos conjuntos: Creative Commons Reconocimiento 4.0
  (CC BY 4.0), según los metadatos del portal consultados el 20/11/2026:
  https://creativecommons.org/licenses/by/4.0/legalcode.es
- Los publica el Instituto de Estadística de la Comunidad de Madrid en el
  Portal de Datos Abiertos. Fuente de los datos: D. G. del Servicio Público
  de Empleo (Consejería de Economía, Hacienda y Empleo).
- Atribución que usa el proyecto en el pie de la aplicación y en
  datos/publicados/publicacion.json:
  > Datos: Portal de Datos Abiertos de la Comunidad de Madrid, con licencia
  > CC BY 4.0. Fuente: D. G. del Servicio Público de Empleo. Este proyecto
  > los transforma: series mensuales y alertas experimentales calculadas.
- El mapa de la aplicación cita, bajo el propio mapa: «Límites municipales:
  Información geográfica de la Comunidad de Madrid (Geoportal IDEM), CC BY
  4.0».
- datos/publicados/ redistribuye datos derivados de estos conjuntos (ver
  docs/decisiones.md, 20/11/2026).

## Conservación

Los CSV originales se conservan sin modificar.
Las transformaciones se realizarán mediante código Python.