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

- Estructura inicial del proyecto preparada.
- Entorno de Python y dependencias configurados.
- Pantalla inicial de Streamlit funcionando en el ordenador de Rodrigo.
- Pendiente comprobar la ejecución en el ordenador de Roman.
- Pendientes la descarga de datos, el análisis y las alertas.

## Requisitos

Estas instrucciones están preparadas para Windows y PowerShell.

- Git.
- Python 3.13, versión utilizada inicialmente por Rodrigo.
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
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

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

La pantalla inicial debe mostrar el título «Pulso Laboral Madrid» y el mensaje de configuración completada.

Mantener la terminal abierta mientras se utiliza la aplicación. Para detenerla, pulsar Ctrl + C en esa terminal.

Cada ordenador ejecuta su propia copia de la aplicación.

## Organización del proyecto

| Ruta | Contenido |
|---|---|
| `app.py` | Entrada de la aplicación Streamlit |
| `requirements.txt` | Versiones de las dependencias |
| `datos/originales/` | Ficheros descargados de las fuentes |
| `datos/procesados/` | Tablas generadas por la preparación |
| `notebooks/` | Exploración y análisis |
| `src/` | Código reutilizable |
| `resultados/` | Tablas y gráficos |
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

Cuando cambie `requirements.txt`, actualizar el entorno local:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si alguien añade una biblioteca necesaria, debe instalarla dentro de `.venv` y actualizar el archivo:

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.txt
```

Incluir ese cambio en la pull request y avisar al otro integrante.

## Datos y reproducibilidad

La configuración actual de `.gitignore` excluye los archivos de `datos/originales/` y `datos/procesados/`, salvo sus `.gitkeep`.

Por tanto, clonar o actualizar el repositorio descarga el código, pero los datos deben obtenerse por separado.

Está pendiente incorporar un procedimiento reproducible de descarga. Cuando esté disponible, se añadirá aquí el comando correspondiente.

Para trabajar con los mismos datos, se documentarán la fuente, la fecha de descarga y la versión utilizada. Los datos originales se conservarán tal como se descargaron.

## Acuerdos de trabajo

- Comunicar qué tarea y archivos está modificando cada integrante.
- Acordar los nombres de columnas y formatos antes de integrar análisis y aplicación.
- Utilizar rutas relativas al proyecto.
- Guardar las decisiones metodológicas en `docs/`.
- Mantener actualizado este README cuando cambie la instalación o la ejecución.
## Preparar los datos

Los CSV no se incluyen en GitHub. Para reproducir la preparación,
coloca estos dos archivos originales en `datos/originales/`:

- `paro_edad_municipio.csv`
- `contratos_municipio.csv`

Las páginas de origen están documentadas en `docs/fuentes_datos.md`.

Desde la carpeta principal del proyecto, ejecuta en PowerShell:

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

La copia descargada el 18/11/2026 contiene 179 municipios y
262 meses, desde enero de 2005 hasta octubre de 2026.

Se excluyen las medias anuales y las tasas publicadas.
Los archivos originales se conservan sin modificar.

Los nombres municipales de paro y contratos todavía no están
armonizados: no cruzar ambas tablas directamente por nombre.
El paro total calculado aún está pendiente de contraste con
una fuente independiente de totales oficiales.