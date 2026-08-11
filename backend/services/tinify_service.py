"""Compresión de imágenes con Tinify (TinyPNG).

La compresión es opcional: al exportar, si el usuario la pide y hay una API
key configurada, se comprime el PNG final. Si falta la clave, se agota la
cuota o falla la red, se devuelve el PNG original: la exportación nunca falla
por la compresión.
"""
import logging

from config import TINIFY_API_KEY

logger = logging.getLogger(__name__)


def compress_image(data: bytes) -> bytes:
    """Comprime bytes de imagen con Tinify y devuelve el resultado.

    Devuelve los bytes originales si no hay clave, si no se pudo comprimir o
    si la compresión no aportó nada.
    """
    if not TINIFY_API_KEY or not data:
        return data
    try:
        import tinify

        tinify.key = TINIFY_API_KEY
        source = tinify.from_buffer(data)
        compressed = source.to_buffer()
        if compressed and len(compressed) < len(data):
            logger.info(
                "Imagen comprimida con Tinify: %d -> %d bytes (%.0f%% menos).",
                len(data),
                len(compressed),
                (1 - len(compressed) / len(data)) * 100,
            )
            return compressed
        logger.info("Tinify no redujo el tamaño; se conserva el original.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No se pudo comprimir con Tinify (%s); se devuelve el original.", exc
        )
    return data
