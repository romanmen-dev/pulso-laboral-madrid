# Contrato de `resultados/alertas.csv`

Estado: propuesta de Rodrigo del 19/11/2026, pendiente de confirmación
por Roman. Usa los nombres de columna que ya calcula
`notebooks/02_detector_inicial.ipynb`.

## Para qué sirve

Es la tabla que conecta el detector con la aplicación. Mientras se
respete este formato, el detector puede cambiar sus parámetros o su
método y la aplicación puede cambiar su diseño sin que ninguno rompa
al otro.

## Formato

- Ruta: `resultados/alertas.csv`. La genera `src/detectar_alertas.py`
  a partir de `datos/procesados/`. No se versiona en Git.
- Separador `;`, codificación `utf-8-sig`, punto decimal y sin índice.
- Una fila por municipio y mes, haya alerta o no, incluidos los meses
  que no se pueden evaluar. Clave única: `municipio` + `fecha`.
- Una celda vacía significa «no definido». Nunca se rellena con 0.

## Columnas, en este orden

| Columna | Tipo | Significado | Vacía cuando |
|---|---|---|---|
| `municipio` | texto | Nombre armonizado, igual que en `datos/procesados/` | Nunca |
| `fecha` | fecha `AAAA-MM-DD` | Primer día del mes evaluado | Nunca |
| `paro_total` | entero | Personas en paro registrado ese mes (suma de los tres grupos de edad) | Nunca |
| `paro_mes_anterior` | entero | Paro registrado el mes anterior | Primer mes de la serie |
| `cambio_mensual` | entero | `paro_total` − `paro_mes_anterior` | Primer mes de la serie |
| `variacion_mensual_pct` | decimal | 100 × `cambio_mensual` / `paro_mes_anterior`. Solo informativa | `paro_mes_anterior` vacío o 0 |
| `n_historico` | entero | Cambios del mismo mes disponibles en los 5 años anteriores (0 a 5) | Nunca |
| `referencia_cambio` | decimal | Mediana de esos cambios: lo habitual en ese mes | Menos de 5 cambios |
| `mad_cambio` | decimal | Desviación absoluta mediana de esos cambios, sin escalar | Menos de 5 cambios |
| `escala_robusta` | decimal | 1,4826 × `mad_cambio` | Menos de 5 cambios |
| `limite_superior` | decimal | `referencia_cambio` + 3 × `escala_robusta` | Mes no evaluable |
| `puntuacion_robusta` | decimal | (`cambio_mensual` − `referencia_cambio`) / `escala_robusta`. No es una probabilidad ni una medida de gravedad | Mes no evaluable |
| `alerta_experimental` | booleano `True` / `False` | `True` si `cambio_mensual` > 0 y `puntuacion_robusta` > 3 | Mes no evaluable |
| `estado_detector` | texto | `alerta_experimental`, `sin_alerta`, `dispersion_cero` o `historial_insuficiente` | Nunca |
| `grupo_edad_principal` | texto | Grupo de edad con mayor aumento en personas ese mes: `Menor de 25 años`, `De 25 a 44 años` o `Mayor de 44 años`. No indica una anomalía propia de ese grupo | El paro no sube, o hay empate entre grupos |

Un mes no es evaluable cuando `estado_detector` es `dispersion_cero`
o `historial_insuficiente`.

## Reglas que debe cumplir el archivo

El script comprueba estas reglas antes de escribir el CSV y se detiene
si alguna falla:

1. Están los 179 municipios de `datos/procesados/paro_total_mensual.csv`,
   con los mismos nombres y todos los meses de la serie.
2. No hay pares `municipio` + `fecha` repetidos.
3. `alerta_experimental` está vacía si y solo si el mes no es evaluable.
4. `alerta_experimental` es `True` si y solo si `estado_detector` es
   `alerta_experimental`.
5. Toda alerta cumple `cambio_mensual` > 0 y
   `cambio_mensual` > `limite_superior`.

Los parámetros del detector (ventana de 5 años, mínimo de 5 cambios
y umbral de 3) son constantes al principio del script. Si cambian,
se anota en `docs/decisiones.md`.

## Cómo lo usa la aplicación

- Muestra todas las filas del mes elegido, también las no evaluables,
  que nunca se presentan como «sin alerta».
- Lee las columnas por su nombre. Puede calcular otras medidas, como
  las personas por encima del límite (`cambio_mensual` −
  `limite_superior`), sin añadirlas al CSV.
- Presenta las alertas como «alertas experimentales» mientras el
  detector no esté validado.

## Cambios en el contrato

Cualquier cambio de nombre, columna o significado se acuerda entre
los dos y se anota en `docs/decisiones.md` antes de fusionarlo.
