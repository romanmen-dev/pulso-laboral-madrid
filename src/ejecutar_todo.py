"""Ejecuta toda la cadena de datos, en orden.

Descarga y verifica los originales, los comprueba, prepara las tablas y el
mapa, detecta las alertas, valida el detector, lo compara con los métodos
alternativos y publica la copia de datos/publicados/. Cada paso
es uno de los scripts de src/ y se ejecuta igual que a mano. La cadena se
detiene en el primer paso que falle e indica cuál ha sido.
"""

import subprocess
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parent

PASOS = [
    ("Descargar y verificar los originales", "descargar_datos.py"),
    ("Comprobar los originales", "comprobar_datos.py"),
    ("Preparar las tablas mensuales", "preparar_datos.py"),
    ("Preparar el mapa", "preparar_mapa.py"),
    ("Preparar la población de 15 a 64 años", "preparar_poblacion.py"),
    ("Detectar las alertas", "detectar_alertas.py"),
    ("Validar el detector", "validar_detector.py"),
    ("Comparar con los métodos alternativos", "comparar_metodos.py"),
    ("Publicar los datos de la aplicación", "publicar_datos.py"),
]


def main():
    total = len(PASOS)
    for numero, (descripcion, script) in enumerate(PASOS, start=1):
        print(f"\n=== Paso {numero} de {total}: {descripcion} (src/{script}) ===", flush=True)
        resultado = subprocess.run([sys.executable, str(SRC / script)], cwd=SRC.parent)
        if resultado.returncode != 0:
            raise SystemExit(
                f"\nERROR en el paso {numero} de {total}: {descripcion} (src/{script}). "
                "Los pasos siguientes no se han ejecutado."
            )

    print(
        f"\nCadena completa: {total} pasos sin errores. "
        "Para que la aplicación publicada use estos datos, haz commit de datos/publicados/."
    )


if __name__ == "__main__":
    main()
