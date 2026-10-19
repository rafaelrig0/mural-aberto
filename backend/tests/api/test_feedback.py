import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.modules.feedback.models import Feedback, FeedbackType

PUBLIC = "/api/v1/feedback"
ADMIN = "/api/v1/admin/feedback"


def valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "author_name": "Ana",
        "feedback_type": "suggestion",
        "message": "Gostaria de poder filtrar as obras por bairro.",
        "rating": 4,
    }
    payload.update(overrides)
    return payload


def make_feedback(db: Session, **overrides: object) -> Feedback:
    data: dict[str, object] = {
        "author_name": "Joana",
        "feedback_type": FeedbackType.OPINION,
        "message": "Site muito bonito!",
        "rating": 5,
    }
    data.update(overrides)
    feedback = Feedback(**data)
    db.add(feedback)
    db.commit()
    return feedback


def test_submit_feedback_is_persisted(client: TestClient, db: Session) -> None:
    response = client.post(PUBLIC, json=valid_payload())
    assert response.status_code == 201
    assert set(response.json()) == {"id"}  # a resposta pública não devolve mais nada

    saved = db.scalars(select(Feedback)).one()
    assert saved.id == response.json()["id"]
    assert saved.author_name == "Ana"
    assert saved.feedback_type is FeedbackType.SUGGESTION
    assert saved.message == "Gostaria de poder filtrar as obras por bairro."
    assert saved.rating == 4


def test_name_and_rating_are_optional(client: TestClient, db: Session) -> None:
    body = {"feedback_type": "bug", "message": "O botão de enviar não responde."}
    assert client.post(PUBLIC, json=body).status_code == 201
    saved = db.scalars(select(Feedback)).one()
    assert saved.author_name is None
    assert saved.rating is None


def test_blank_name_becomes_none_and_text_is_trimmed(client: TestClient, db: Session) -> None:
    body = valid_payload(author_name="   ", message="   Mensagem com espaços nas pontas.  ")
    assert client.post(PUBLIC, json=body).status_code == 201
    saved = db.scalars(select(Feedback)).one()
    assert saved.author_name is None
    assert saved.message == "Mensagem com espaços nas pontas."


@pytest.mark.parametrize("feedback_type", ["opinion", "suggestion", "bug", "other"])
def test_all_feedback_types_are_accepted(client: TestClient, feedback_type: str) -> None:
    response = client.post(PUBLIC, json=valid_payload(feedback_type=feedback_type))
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"message": ""}, "message"),
        ({"message": "    "}, "message"),
        ({"message": "oi"}, "message"),
        ({"message": "a" * 2001}, "message"),
        ({"feedback_type": "elogio"}, "feedback_type"),
        ({"rating": 0}, "rating"),
        ({"rating": 6}, "rating"),
        ({"rating": "muito bom"}, "rating"),
        ({"author_name": "a" * 121}, "author_name"),
    ],
)
def test_invalid_data_is_rejected_with_clear_field(
    client: TestClient, db: Session, overrides: dict[str, object], field: str
) -> None:
    response = client.post(PUBLIC, json=valid_payload(**overrides))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert field in [detail["field"] for detail in error["details"]]
    assert db.scalars(select(Feedback)).all() == []  # nada é gravado


def test_missing_required_fields_are_rejected(client: TestClient) -> None:
    response = client.post(PUBLIC, json={})
    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["error"]["details"]}
    assert {"feedback_type", "message"} <= fields


def test_sql_injection_attempt_is_stored_as_plain_text(client: TestClient, db: Session) -> None:
    attack = "'); DROP TABLE feedbacks; --"
    response = client.post(PUBLIC, json=valid_payload(author_name=attack, message=attack + "!!"))
    assert response.status_code == 201
    saved = db.scalars(select(Feedback)).one()  # a tabela continua existindo
    assert saved.author_name == attack
    assert db.execute(text("SELECT count(*) FROM feedbacks")).scalar() == 1


def test_html_is_stored_verbatim_for_the_frontend_to_escape(
    client: TestClient, db: Session
) -> None:
    script = "<script>alert(1)</script>"
    assert client.post(PUBLIC, json=valid_payload(message=script)).status_code == 201
    assert db.scalars(select(Feedback)).one().message == script


def test_admin_endpoint_requires_auth(client: TestClient) -> None:
    assert client.get(ADMIN).status_code == 401


def test_admin_lists_feedback_with_filter_and_order(
    client: TestClient, auth: dict[str, str], db: Session
) -> None:
    make_feedback(db, message="Primeira opinião.")
    make_feedback(db, feedback_type=FeedbackType.BUG, message="Segundo relato.", rating=None)

    everything = client.get(ADMIN, headers=auth).json()
    assert everything["total"] == 2
    assert [item["message"] for item in everything["items"]] == [
        "Segundo relato.",
        "Primeira opinião.",
    ]

    oldest = client.get(ADMIN, params={"order": "oldest"}, headers=auth).json()
    assert oldest["items"][0]["message"] == "Primeira opinião."

    bugs = client.get(ADMIN, params={"feedback_type": "bug"}, headers=auth).json()
    assert bugs["total"] == 1
    assert bugs["items"][0]["rating"] is None
    assert set(bugs["items"][0]) == {
        "id",
        "author_name",
        "feedback_type",
        "message",
        "rating",
        "created_at",
    }


def test_admin_pagination(client: TestClient, auth: dict[str, str], db: Session) -> None:
    for number in range(3):
        make_feedback(db, message=f"Mensagem número {number}")
    page = client.get(ADMIN, params={"page": 2, "page_size": 2}, headers=auth).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1


def test_database_rejects_rating_out_of_range(db: Session) -> None:
    """A regra também vale no banco, não só na API."""
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        make_feedback(db, rating=9)
    db.rollback()


def test_feedback_submission_is_rate_limited(client: TestClient) -> None:
    limiter.enabled = True
    try:
        codes = [client.post(PUBLIC, json=valid_payload()).status_code for _ in range(12)]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert codes[:10] == [201] * 10
    assert codes[10:] == [429, 429]
