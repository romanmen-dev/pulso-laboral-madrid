# Fuentes de datos

Fecha de descarga: 18 de noviembre de 2026.

## Paro registrado por edad y municipio

- Organismo: Comunidad de Madrid.
- Página de origen:
  https://datos.comunidad.madrid/dataset/paro_registrado_edad_municipio
- Archivo local: datos/originales/paro_edad_municipio.csv
- Uso previsto: serie principal del análisis de paro y desglose por edad.
- Periodo temporal y cobertura: pendientes de comprobar en el CSV.

## Contratos de trabajo por municipio

- Organismo: Comunidad de Madrid.
- Página de origen:
  https://datos.comunidad.madrid/dataset/contratos_trabajo_municipio
- Archivo local: datos/originales/contratos_municipio.csv
- Uso previsto: información complementaria sobre contratación.
- Periodo temporal y cobertura: pendientes de comprobar en el CSV.
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

## Conservación

Los CSV originales se conservan sin modificar.
Las transformaciones se realizarán mediante código Python.