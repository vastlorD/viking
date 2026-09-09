"""Normaliza imagens e remove metadados antes do processamento."""

from io import BytesIO
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


def normalize_image(raw, max_bytes):
    if not raw or len(raw) > max_bytes:
        raise ValueError("Envie uma imagem de até 5 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG"} or image.width * image.height > 16_000_000:
                    raise ValueError("Use JPEG ou PNG com no máximo 16 megapixels.")
                if min(image.size) < 80:
                    raise ValueError("A imagem deve ter pelo menos 80 pixels em cada dimensão.")
                normalized = ImageOps.exif_transpose(image).convert("RGB")
                normalized.thumbnail((1600, 1600))
                output = BytesIO()
                normalized.save(output, format="JPEG", quality=90)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("Arquivo de imagem inválido.") from error
