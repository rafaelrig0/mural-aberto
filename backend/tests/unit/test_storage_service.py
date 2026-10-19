import json

import httpx
import pytest

from app.core.exceptions import StorageError
from app.modules.media.storage import StorageService, new_storage_path

BASE = "https://proj.supabase.co"


def make_service(handler: httpx.MockTransport) -> StorageService:
    return StorageService(BASE, "service-key", "bucket", client=httpx.Client(transport=handler))


def test_upload_sends_auth_and_content_type() -> None:
    seen: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["request"] = request
        return httpx.Response(200, json={})

    make_service(httpx.MockTransport(handler)).upload("works/a.png", b"data", "image/png")
    request = seen["request"]
    assert request.method == "POST"
    assert str(request.url) == f"{BASE}/storage/v1/object/bucket/works/a.png"
    assert request.headers["authorization"] == "Bearer service-key"
    assert request.headers["content-type"] == "image/png"
    assert request.content == b"data"


def test_signed_urls_are_batched_and_made_absolute() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json=[
                {"path": "a.png", "signedURL": "/object/sign/bucket/a.png?token=1", "error": None},
                {"path": "b.png", "signedURL": None, "error": "Not found"},
            ],
        )

    urls = make_service(httpx.MockTransport(handler)).create_signed_urls(
        ["a.png", "b.png", "a.png"], 3600
    )
    assert len(calls) == 1
    assert json.loads(calls[0].content) == {"expiresIn": 3600, "paths": ["a.png", "b.png"]}
    assert urls == {"a.png": f"{BASE}/storage/v1/object/sign/bucket/a.png?token=1"}


def test_http_failure_becomes_storage_error() -> None:
    service = make_service(httpx.MockTransport(lambda _: httpx.Response(500)))
    with pytest.raises(StorageError):
        service.upload("x.png", b"d", "image/png")


def test_delete_quietly_never_raises() -> None:
    service = make_service(httpx.MockTransport(lambda _: httpx.Response(500)))
    service.delete_quietly(["x.png"])


def test_new_storage_path_never_uses_user_input() -> None:
    first, second = new_storage_path("png"), new_storage_path("png")
    assert first != second
    assert first.startswith("works/")
    assert first.endswith(".png")
