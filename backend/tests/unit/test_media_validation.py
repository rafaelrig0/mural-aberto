from io import BytesIO

import pytest
from fastapi import UploadFile

from app.core.exceptions import PayloadTooLargeError, UnprocessableError, UnsupportedMediaError
from app.modules.media.models import MediaKind
from app.modules.media.validation import validate_image, validate_video
from tests.helpers import EXECUTABLE_BYTES, MP4_BYTES, image_bytes

LIMIT = 1024 * 1024


def upload(content: bytes, filename: str = "arquivo.bin") -> UploadFile:
    return UploadFile(file=BytesIO(content), filename=filename)


@pytest.mark.parametrize(("fmt", "mime"), [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_accepts_real_images(fmt: str, mime: str) -> None:
    result = validate_image(upload(image_bytes(fmt)), LIMIT)
    assert result.mime_type == mime
    assert result.kind is MediaKind.IMAGE


def test_extension_and_declared_type_are_ignored() -> None:
    """Um executável chamado 'foto.png' continua sendo rejeitado: vale o conteúdo real."""
    with pytest.raises(UnsupportedMediaError):
        validate_image(upload(EXECUTABLE_BYTES, "foto.png"), LIMIT)


def test_rejects_gif_not_in_allowed_list() -> None:
    gif = b"GIF89a" + b"\x01\x00\x01\x00" + b"\x00" * 50
    with pytest.raises(UnsupportedMediaError):
        validate_image(upload(gif), LIMIT)


def test_rejects_truncated_image_with_valid_header() -> None:
    truncated = image_bytes("PNG")[:30]
    with pytest.raises(UnsupportedMediaError):
        validate_image(upload(truncated), LIMIT)


def test_rejects_oversized_file() -> None:
    with pytest.raises(PayloadTooLargeError):
        validate_image(upload(b"\x00" * (LIMIT + 1)), LIMIT)


def test_rejects_empty_file() -> None:
    with pytest.raises(UnprocessableError):
        validate_image(upload(b""), LIMIT)


def test_accepts_mp4_and_rejects_image_as_video() -> None:
    assert validate_video(upload(MP4_BYTES), LIMIT).mime_type == "video/mp4"
    with pytest.raises(UnsupportedMediaError):
        validate_video(upload(image_bytes("PNG")), LIMIT)
