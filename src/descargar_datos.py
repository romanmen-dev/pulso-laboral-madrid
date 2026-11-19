from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import requests


RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
REGISTROS = RAIZ / "resultados" / "descargas"

BASE = "https://datos.comunidad.madrid/catalogo/dataset/"

FUENTES = [
    {
        "archivo": "paro_edad_municipio.csv",
        "url": (
            BASE
            + "270edb5a-6788-41d5-ab8a-551c9daead0a/"
            "resource/c2be6e03-4915-41ab-9b5e-6ce66602c718/"
            "download/extraccionesmovimiento-laboral-registrado.-"
            "paro-registrado-por-edad-y-municipio.-comunidad-de-ma.csv"
        ),
        "sha256": (
            "0d14f265a8d5f9abb76b158f89c2dae983"
            "133a033d51bde25d6fce29087be8e2"
        ),
    },
    {
        "archivo": "contratos_municipio.csv",
        "url": (
            BASE
            + "19900d46-e62b-4ab1-a65e-ea0fb83bfdcb/"
            "resource/8b41acdd-cb88-404d-8767-e99b2cecc431/"
            "download/extraccionesmovimiento-laboral-registrado.-"
            "contratos-de-trabajo-por-municipio.-comunidad-de-madr.csv"
        ),
        "sha256": (
            "a3ecd519dfe302e2c1da96b54c9ea8e1"
            "e4581b4ea369a1581357f2761be66866"
        ),
    },
]


def huella(contenido):
    return hashlib.sha256(contenido).hexdigest()


def descargar(fuente):
    nombre = fuente["archivo"]
    destino = ORIGINALES / nombre
    registro = {
        "archivo": nombre,
        "url_solicitada": fuente["url"],
        "sha256_esperado": fuente["sha256"],
        "inicio_utc": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\nDescargando: {nombre}", flush=True)

    try:
        respuesta = requests.get(fuente["url"], timeout=(15, 120))
        respuesta.raise_for_status()

        contenido = respuesta.content
        firma = huella(contenido)

        registro.update({
            "descarga_completada_utc": datetime.now(timezone.utc).isoformat(),
            "url_final": respuesta.url,
            "bytes": len(contenido),
            "sha256_descargado": firma,
        })

        # Solo aceptamos la versión que hemos revisado.
        if firma != fuente["sha256"]:
            raise ValueError(
                "La descarga no coincide con la versión revisada. "
                "Puede haber cambiado el archivo del portal. "
                "No se ha sustituido el original."
            )

        if destino.exists():
            if huella(destino.read_bytes()) != firma:
                raise ValueError(
                    "El archivo local tiene otro contenido. "
                    "Se conserva sin modificar."
                )
            registro["estado"] = "verificado_original_existente"
            print("Correcto: coincide con tu original; se conserva.")
        else:
            # Modo exclusivo: no sobrescribe un archivo existente.
            with destino.open("xb") as archivo:
                archivo.write(contenido)
            registro["estado"] = "descargado_y_guardado"
            print("Correcto: original descargado y guardado.")

        print(f"SHA-256: {firma}")
        return registro, True

    except (requests.RequestException, OSError, ValueError) as error:
        registro["estado"] = "error"
        registro["detalle"] = str(error)
        print(f"ERROR: {error}")
        return registro, False


def main():
    ORIGINALES.mkdir(parents=True, exist_ok=True)
    REGISTROS.mkdir(parents=True, exist_ok=True)

    registros = []
    todo_correcto = True

    for fuente in FUENTES:
        registro, correcto = descargar(fuente)
        registros.append(registro)
        todo_correcto = todo_correcto and correcto

    instante = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ruta_registro = REGISTROS / f"descarga_{instante}.json"
    ruta_registro.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nRegistro guardado en: {ruta_registro}")

    if not todo_correcto:
        raise SystemExit(
            "Hay incidencias. Revisa el registro antes de preparar los datos."
        )

    print("Los dos originales coinciden con la versión del proyecto.")


if __name__ == "__main__":
    main()