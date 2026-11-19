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
