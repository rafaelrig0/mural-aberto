"""Cria o bucket privado no Supabase Storage, se ainda não existir.
Uso: python -m app.scripts.setup_storage

Alternativa: criar o bucket manualmente no painel do Supabase, marcando-o como PRIVADO.
"""

from app.core.config import get_settings
from app.modules.media.storage import get_storage_service
from app.modules.media.validation import ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES


def main() -> None:
    settings = get_settings()
    created = get_storage_service().ensure_bucket(
        file_size_limit=settings.max_video_size_bytes,
        allowed_mime_types=[*ALLOWED_IMAGE_TYPES, *ALLOWED_VIDEO_TYPES],
    )
    state = "criado" if created else "já existia"
    print(f"Bucket '{settings.supabase_bucket}' {state} (privado).")


if __name__ == "__main__":
    main()
