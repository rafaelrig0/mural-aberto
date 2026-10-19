from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_unknown_route_uses_standard_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/nao-existe")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_standard_error_shape(client: TestClient) -> None:
    response = client.delete("/api/v1/categories")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_cors_allows_only_configured_origins(client: TestClient) -> None:
    ok = client.options(
        "/api/v1/categories",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    blocked = client.options(
        "/api/v1/categories",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in blocked.headers


def test_openapi_hidden_in_production_only() -> None:
    from app.core.config import get_settings

    assert get_settings().is_production is False  # em teste a documentação fica disponível


def test_id_above_integer_range_is_client_error_not_500(client: TestClient) -> None:
    """Regressão: ids maiores que o INTEGER do Postgres derrubavam a rota com erro 500."""
    for url in ("/api/v1/works/99999999999", "/api/v1/works?category_id=99999999999"):
        response = client.get(url)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_parameter"


def test_internal_error_keeps_cors_headers(client: TestClient, monkeypatch: object) -> None:
    """Regressão: erros 500 saíam sem cabeçalhos CORS e o navegador via 'erro de CORS'."""
    from app.modules.categories import service

    def boom(*_: object) -> None:
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(service, "list_categories", boom)  # type: ignore[attr-defined]
    response = client.get("/api/v1/categories", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Erro interno do servidor."}
    }
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
