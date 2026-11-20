# Pulso Laboral Madrid

Proyecto para DATAMAD 2026 desarrollado por Roman y Rodrigo.

## Objetivo

Desarrollar una herramienta que identifique cambios inusuales en el paro registrado de los municipios de la Comunidad de Madrid, utilizando datos abiertos y series históricas.

La propuesta busca detectar aumentos superiores a lo esperable según la evolución temporal y mostrar qué grupos de edad concentran la variación, para facilitar la revisión de casos por parte de los técnicos de empleo.

## Equipo

- Roman — Estadística Aplicada. Auditoría de datos, análisis exploratorio, definición y evaluación de las alertas.
- Rodrigo — Ingeniería de Datos e Inteligencia Artificial. Descarga y preparación de datos, estructura del proyecto y aplicación.

Ambos revisarán los resultados y documentarán las decisiones metodológicas.

## Estado actual

- Descarga reproducible de los datos con verificación SHA-256 (`src/descargar_datos.py`).
- Comprobación y preparación de las series mensuales, con los nombres de municipio armonizados entre paro y contratos.
- Exploración del paro y definición provisional de las alertas (`notebooks/01_exploracion_paro.ipynb`).
- Tabla de alertas `resultados/alertas.csv`, generada con `src/detectar_alertas.py` según `docs/contrato_alertas.md`. Pendiente de revisión por Roman.
- En curso: evaluación del detector inicial y aplicación Streamlit.
- Pendientes: validación histórica y presentación.

## Requisitos

Estas instrucciones están preparadas para Windows y PowerShell.

- Git.
- Python 3.13 o posterior. El proyecto también se ha ejecutado con Python 3.14.
- Visual Studio Code.
- Extensiones Python y Jupyter de Microsoft.
- Acceso al repositorio de GitHub. Para subir cambios, hay que aceptar la invitación como colaborador.

Comprobar las instalaciones:

```powershell
git --version
python --version
```

## Instalación inicial

Cada integrante realiza estos pasos una vez en su ordenador.

### 1. Clonar el repositorio

En GitHub, abrir este repositorio y copiar su dirección desde Code → HTTPS.

En PowerShell, entrar en la carpeta donde se quiera guardar el proyecto.

Escribir `git clone`, seguido de un espacio y de la dirección copiada. Pulsar Intro y esperar a que finalice la descarga.

Después:

```powershell
cd pulso-laboral-madrid
```

Abrir esta carpeta en VS Code mediante Archivo → Abrir carpeta.

Los siguientes comandos se ejecutan desde la carpeta principal del proyecto, donde se encuentra `app.py`.

### 2. Crear el entorno

```powershell
python -m venv .venv
```

Cada integrante crea su propio entorno `.venv` en su ordenador.

### 3. Instalar las dependencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` incluye `requirements.txt`, así que este comando instala los dos:

- `requirements.txt`: lo mínimo para la aplicación. Es lo que instala Streamlit Community Cloud.
- `requirements-dev.txt`: añade la cadena de datos, Jupyter y las herramientas de desarrollo.

### 4. Seleccionar el intérprete en VS Code

1. Pulsar Ctrl + Shift + P.
2. Buscar Python: Select Interpreter.
3. Seleccionar el intérprete situado en `.venv\Scripts\python.exe`.

En los cuadernos Jupyter, seleccionar también este entorno mediante Select Kernel.

### 5. Ejecutar la aplicación

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abrir en el navegador la dirección que figure como Local URL en la terminal, normalmente http://localhost:8501.

La aplicación lee `resultados/alertas.csv` y muestra la vista general del último mes. Si ese archivo todavía no existe, indica los comandos que hay que ejecutar para generarlo (ver «Datos y reproducibilidad»).

Si se modifica un archivo de `src/` con la aplicación abierta y no se ven los cambios, detenerla y volver a ejecutarla.

Mantener la terminal abierta mientras se utiliza la aplicación. Para detenerla, pulsar Ctrl + C en esa terminal.

Cada ordenador ejecuta su propia copia de la aplicación.

## Organización del proyecto

| Ruta | Contenido |
|---|---|
| `app.py` | Entrada de la aplicación Streamlit |
| `.streamlit/config.toml` | Tema de la aplicación (modo claro y oscuro) |
| `assets/` | Logo e icono propios del proyecto, en SVG |
| `requirements.txt` | Dependencias mínimas de la aplicación |
| `requirements-dev.txt` | Dependencias de desarrollo (incluye `requirements.txt`) |
| `datos/originales/` | Ficheros descargados de las fuentes |
| `datos/procesados/` | Tablas generadas por la preparación |
| `datos/publicados/` | Copia versionada de los datos que lee la aplicación publicada |
| `notebooks/` | Exploración y análisis |
| `src/` | Código reutilizable |
| `resultados/` | Informes de comprobación, registros de descarga, tablas y gráficos |
| `docs/` | Fuentes y decisiones metodológicas |

Los archivos `.gitkeep` permiten conservar las carpetas vacías en Git.

## Cómo trabajar sincronizados

GitHub contiene el trabajo compartido. Cada integrante trabaja en una copia local.

Guardar un archivo en VS Code modifica la copia local. Para compartirlo hay que crear un commit y subirlo con push. El otro integrante recibe los cambios mediante pull.

### Antes de empezar una tarea

Comprobar si hay cambios locales pendientes:

```powershell
git status
```

Si existen cambios, guardarlos en la rama correspondiente antes de cambiar de rama.

Con el trabajo anterior guardado, actualizar la rama principal:

```powershell
git switch main
git pull --ff-only
```

Crear una rama nueva para la tarea. Por ejemplo, Rodrigo puede usar:

```powershell
git switch -c rodrigo/descarga-datos
```

Roman puede usar:

```powershell
git switch -c roman/exploracion-inicial
```

Estos comandos crean ramas nuevas. Para volver a una rama existente se utiliza `git switch` seguido de su nombre.

### Guardar y subir una tarea

Guardar los archivos en VS Code y revisar los cambios:

```powershell
git status
git diff
```

Después:

```powershell
git add .
git commit -m "Describe brevemente el cambio realizado"
git push -u origin HEAD
```

Sustituir el mensaje del commit por una descripción concreta.

### Incorporar cambios al proyecto compartido

1. Abrir el repositorio en GitHub.
2. Crear una pull request desde la rama de la tarea hacia `main`.
3. Explicar qué se ha cambiado y cómo se ha comprobado.
4. Pedir al otro integrante que revise los archivos.
5. Fusionar la pull request cuando esté revisada.

Después de la fusión, ambos actualizan su copia de `main`, con sus cambios locales previamente guardados:

```powershell
git switch main
git pull --ff-only
```

### Actualizar una tarea que sigue en curso

Con los cambios de la tarea guardados en un commit, ejecutar desde su rama:

```powershell
git fetch origin
git merge origin/main
```

Esto incorpora el trabajo que ya se haya fusionado en la rama principal.

Si aparecen conflictos, revisar conjuntamente los archivos afectados antes de continuar.

## Dependencias

Cuando cambie `requirements.txt` o `requirements-dev.txt`, actualizar el entorno local:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Si alguien añade una biblioteca, debe instalarla dentro de `.venv` y añadirla a mano, con su versión exacta (`paquete==versión`), en el archivo que corresponda:

- `requirements.txt`, si la usa la aplicación (`app.py` o `src/*_app.py`).
- `requirements-dev.txt`, si solo la usan los scripts de datos o los cuadernos.

No sobrescribir `requirements.txt` con `pip freeze`: incluiría paquetes de Windows y de Jupyter que no se pueden o no se deben instalar en Streamlit Community Cloud.

Incluir ese cambio en la pull request y avisar al otro integrante.

## Datos y reproducibilidad

Los CSV originales y procesados no se incluyen en GitHub: `.gitignore` excluye el contenido de `datos/originales/` y `datos/procesados/`, salvo sus `.gitkeep`. Clonar o actualizar el repositorio descarga el código, y los datos se obtienen con los pasos siguientes, desde la carpeta principal del proyecto.

La única excepción es `datos/publicados/`: una copia versionada de las tablas que lee la aplicación, para poder publicarla (paso 4). La aplicación usa las tablas locales si están todas y, si no, esa copia.

Las páginas de origen están documentadas en `docs/fuentes_datos.md`.

### 1. Descargar los datos originales

```powershell
.\.venv\Scripts\python.exe .\src\descargar_datos.py
```

El script descarga del Portal de Datos Abiertos de la Comunidad de Madrid los dos archivos del proyecto y los guarda en `datos/originales/`:

- `paro_edad_municipio.csv`
- `contratos_municipio.csv`

Para garantizar que todos trabajan con los mismos datos, compara la huella SHA-256 de cada descarga con la de la versión revisada:

- Si coincide y el archivo no existía, lo guarda.
- Si el archivo ya existía, comprueba que es idéntico y lo conserva.
- Nunca sobrescribe un original.

Cada ejecución deja un registro en `resultados/descargas/` con la dirección, la hora, el tamaño y la huella de cada archivo.

Si el portal publica una versión nueva, la huella no coincidirá y el script se detendrá sin modificar nada. Es intencionado: para usar datos nuevos hay que revisarlos y actualizar las huellas en `src/descargar_datos.py`.

### 2. Comprobar y preparar los datos

```powershell
.\.venv\Scripts\python.exe .\src\comprobar_datos.py
.\.venv\Scripts\python.exe .\src\preparar_datos.py
```

El primer script genera informes en `resultados/`.
El segundo genera estas tablas en `datos/procesados/`:

| Archivo | Contenido |
|---|---|
| paro_edad_mensual.csv | Paro mensual por municipio y grupo de edad |
| paro_total_mensual.csv | Suma mensual de los tres grupos de edad por municipio |
| contratos_mensuales.csv | Recuento mensual de contratos por municipio |

Los CSV generados utilizan separador `;` y codificación `utf-8-sig`.
La columna `fecha` identifica el mes mediante su primer día.

La versión revisada, descargada el 18/11/2026, contiene 179 municipios
y 262 meses, desde enero de 2005 hasta octubre de 2026.

Se excluyen las medias anuales y las tasas publicadas.
Los archivos originales se conservan sin modificar.

`preparar_datos.py` armoniza los nombres de contratos con los de paro
(6 equivalencias) y comprueba que ambos conjuntos de municipios coinciden,
así que las dos tablas se pueden cruzar por `municipio`.

El paro total calculado aún está pendiente de contraste con
una fuente independiente de totales oficiales.

### 3. Detectar alertas

```powershell
.\.venv\Scripts\python.exe .\src\detectar_alertas.py
```

El script aplica el detector experimental de `notebooks/02_detector_inicial.ipynb`
y genera `resultados/alertas.csv`, con una fila por municipio y mes.
Su formato se describe en `docs/contrato_alertas.md`. Antes de escribirlo,
comprueba las reglas del contrato y se detiene si alguna falla.
El archivo no se incluye en GitHub.

### 4. Publicar los datos de la aplicación

```powershell
.\.venv\Scripts\python.exe .\src\publicar_datos.py
```

Copia a `datos/publicados/` lo que lee la aplicación (`resultados/alertas.csv`, `paro_edad_mensual.csv` y `contratos_mensuales.csv`) y escribe `publicacion.json`, con la fecha de generación, el periodo de los datos, el commit, la atribución de la licencia y las huellas SHA-256 de los originales y de cada archivo. Se detiene si `alertas.csv` es anterior a los datos procesados o si los originales no son la versión revisada. Después hay que hacer commit de `datos/publicados/` para que la aplicación publicada use los datos nuevos. `.gitattributes` hace que Git guarde esa carpeta byte a byte, sin cambiar los finales de línea, para que las huellas sigan siendo válidas.

Para reproducir la revisión de las incidencias de los contratos (mayo de 2026, Velilla de San Antonio y redondeo a múltiplos de 5), ejecutar `.\.venv\Scripts\python.exe .\src\investigar_contratos.py`: no modifica datos y escribe sus resultados en `resultados/investigacion_contratos/` (ver `docs/decisiones.md`).

## Acuerdos de trabajo

- Comunicar qué tarea y archivos está modificando cada integrante.
- Acordar los nombres de columnas y formatos antes de integrar análisis y aplicación.
- Utilizar rutas relativas al proyecto.
- Guardar las decisiones metodológicas en `docs/`.
- Mantener actualizado este README cuando cambie la instalación o la ejecución.
