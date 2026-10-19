import logging
import uuid
from collections.abc import Sequence
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends

from app.core.config import get_settings
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60.0


def new_storage_path(extension: str) -> str:
    """Nome gerado por nós (UUID): o nome enviado pelo usuário nunca chega ao storage."""
    return f"works/{uuid.uuid4().hex}.{extension}"


class StorageService:
    """Cliente mínimo da API REST do Supabase Storage (bucket privado).

    Isolado numa classe para trocar de provedor ou mockar nos testes sem tocar nas regras
    de negócio. Usa httpx direto, evitando uma dependência pesada para 4 operações.
    """

    def __init__(
        self,
        base_url: str,
        service_key: str,
        bucket: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._storage_url = f"{base_url}/storage/v1"
        self._bucket = bucket
        self._client = client or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
        self._headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    def _request(
        self,
        method: str,
        url: str,
        *,
        content: bytes | None = None,
        json: object | None = None,
        content_type: str | None = None,
    ) -> httpx.Response:
        headers = dict(self._headers)
        if content_type:
            headers["Content-Type"] = content_type
        try:
            response = self._client.request(
                method, url, headers=headers, content=content, json=json
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Falha no Supabase Storage (%s %s): %s", method, url, exc)
            raise StorageError from exc
        return response

    def upload(self, path: str, content: bytes, mime_type: str) -> None:
        url = f"{self._storage_url}/object/{self._bucket}/{path}"
        self._request("POST", url, content=content, content_type=mime_type)

    def delete(self, paths: Sequence[str]) -> None:
        if not paths:
            return
        url = f"{self._storage_url}/object/{self._bucket}"
        self._request("DELETE", url, json={"prefixes": list(paths)})

    def delete_quietly(self, paths: Sequence[str]) -> None:
        """Para limpezas (compensação, pós-exclusão): falhar aqui não pode derrubar a operação."""
        try:
            self.delete(paths)
        except StorageError:
            logger.error("Arquivos órfãos no storage, remover manualmente: %s", list(paths))

    def create_signed_urls(self, paths: Sequence[str], expires_in: int) -> dict[str, str]:
        """Gera várias URLs assinadas em uma única chamada (evita N chamadas por listagem)."""
        unique_paths = list(dict.fromkeys(paths))
        if not unique_paths:
            return {}
        url = f"{self._storage_url}/object/sign/{self._bucket}"
        response = self._request("POST", url, json={"expiresIn": expires_in, "paths": unique_paths})
        urls: dict[str, str] = {}
        for item in response.json():
            if item.get("signedURL") and not item.get("error"):
                urls[item["path"]] = f"{self._storage_url}{item['signedURL']}"
        return urls

    def ensure_bucket(self, file_size_limit: int, allowed_mime_types: Sequence[str]) -> bool:
        """Cria o bucket privado se não existir. Devolve True se criou."""
        existing = self._request("GET", f"{self._storage_url}/bucket").json()
        if any(bucket.get("name") == self._bucket for bucket in existing):
            return False
        self._request(
            "POST",
            f"{self._storage_url}/bucket",
            json={
                "id": self._bucket,
                "name": self._bucket,
                "public": False,
                "file_size_limit": file_size_limit,
                "allowed_mime_types": list(allowed_mime_types),
            },
        )
        return True


@lru_cache
def get_storage_service() -> StorageService:
    settings = get_settings()
    return StorageService(
        base_url=settings.supabase_url,
        service_key=settings.supabase_service_role_key.get_secret_value(),
        bucket=settings.supabase_bucket,
    )


StorageDep = Annotated[StorageService, Depends(get_storage_service)]
