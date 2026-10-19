from dataclasses import dataclass
from io import BytesIO

import filetype
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.exceptions import PayloadTooLargeError, UnprocessableError, UnsupportedMediaError
from app.modules.media.models import MediaKind

ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4": "mp4", "video/webm": "webm"}
MAX_IMAGE_PIXELS = 50_000_000  # evita "decompression bombs": arquivo pequeno, imagem gigante


@dataclass(frozen=True)
class ValidatedFile:
    kind: MediaKind
    content: bytes
    mime_type: str
    extension: str


def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Lê no máximo max_bytes + 1: basta para saber se estourou o limite sem carregar tudo."""
    content = upload.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise PayloadTooLargeError(f"O arquivo '{upload.filename}' excede {limit_mb} MB.")
    if not content:
        raise UnprocessableError(f"O arquivo '{upload.filename}' está vazio.")
    return content


def _detect_mime(content: bytes) -> str | None:
    """Tipo real pelos primeiros bytes (magic bytes). Ignora extensão e Content-Type do cliente."""
    mime: str | None = filetype.guess_mime(content)
    return mime


def _check_image_is_decodable(content: bytes) -> None:
    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise UnprocessableError("A imagem tem dimensões grandes demais.")
            image.verify()
    except UnprocessableError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise UnsupportedMediaError("O arquivo de imagem está corrompido ou é inválido.") from exc


def validate_image(upload: UploadFile, max_bytes: int) -> ValidatedFile:
    content = read_limited(upload, max_bytes)
    mime = _detect_mime(content)
    if mime not in ALLOWED_IMAGE_TYPES:
        raise UnsupportedMediaError("Imagem inválida. Formatos aceitos: JPEG, PNG e WebP.")
    _check_image_is_decodable(content)
    return ValidatedFile(MediaKind.IMAGE, content, mime, ALLOWED_IMAGE_TYPES[mime])


def validate_video(upload: UploadFile, max_bytes: int) -> ValidatedFile:
    content = read_limited(upload, max_bytes)
    mime = _detect_mime(content)
    if mime not in ALLOWED_VIDEO_TYPES:
        raise UnsupportedMediaError("Vídeo inválido. Formatos aceitos: MP4 e WebM.")
    return ValidatedFile(MediaKind.VIDEO, content, mime, ALLOWED_VIDEO_TYPES[mime])
