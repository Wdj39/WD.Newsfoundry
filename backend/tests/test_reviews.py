"""Tests de la génération de revues de presse (étape 7)."""

from pydantic_ai import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from conftest import auth_headers
from dependencies import get_chat_model
from main import app
from models import Chat

REVIEW_ARGS = {
    "title": "RÉFORME BUDGÉTAIRE - 24/10/2026",
    "summary": "Le Parlement a adopté la réforme en première lecture.",
    "articles": [
        {
            "title": "Le Parlement adopte la réforme budgétaire",
            "source": "Exemple",
            "url": "https://exemple.fr/budget",
            "summary": "Le texte a été voté en première lecture.",
        }
    ],
}


def review_model(captured_prompts: list[str] | None = None):
    """Faux LLM qui renvoie une revue structurée via l'outil de sortie de PydanticAI."""

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if captured_prompts is not None:
            captured_prompts.append(messages[-1].parts[-1].content)
        output_tool = info.output_tools[0].name
        return ModelResponse(parts=[ToolCallPart(output_tool, REVIEW_ARGS)])

    return FunctionModel(model)


def chat_with_one_exchange(client, user) -> int:
    chat_id = client.post("/chats", headers=auth_headers(user)).json()["id"]
    client.post(
        f"/chats/{chat_id}/messages",
        json={"content": "Parle-moi du budget"},
        headers=auth_headers(user),
    )
    return chat_id


def test_generate_review_saves_structured_output(client, session, alice):
    chat_id = chat_with_one_exchange(client, alice)
    prompts: list[str] = []
    app.dependency_overrides[get_chat_model] = lambda: review_model(prompts)

    response = client.post(
        f"/chats/{chat_id}/review", json={"topic": "budget"}, headers=auth_headers(alice)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "RÉFORME BUDGÉTAIRE - 24/10/2026"
    assert body["topic"] == "budget"
    assert body["articles"][0]["url"] == "https://exemple.fr/budget"
    # La revue est enregistrée dans le Chat
    chat = session.get(Chat, chat_id)
    assert chat.review_title == "RÉFORME BUDGÉTAIRE - 24/10/2026"
    assert chat.review_generated_at is not None
    # L'agent a reçu le thème, la discussion et les gros titres du jour
    assert "Thème de la revue de presse : budget" in prompts[0]
    assert "Parle-moi du budget" in prompts[0]
    assert "Le Parlement adopte la réforme budgétaire" in prompts[0]


def test_reviews_list_contains_only_own_reviews(client, alice, bob):
    alice_chat = chat_with_one_exchange(client, alice)
    bob_chat = chat_with_one_exchange(client, bob)
    app.dependency_overrides[get_chat_model] = lambda: review_model()
    for chat_id, user in [(alice_chat, alice), (bob_chat, bob)]:
        client.post(f"/chats/{chat_id}/review", json={"topic": "budget"}, headers=auth_headers(user))

    response = client.get("/reviews", headers=auth_headers(alice))

    assert response.status_code == 200
    assert [review["chat_id"] for review in response.json()] == [alice_chat]


def test_chats_without_review_are_not_listed(client, alice):
    chat_with_one_exchange(client, alice)

    assert client.get("/reviews", headers=auth_headers(alice)).json() == []


def test_user_cannot_generate_review_on_another_users_chat(client, session, alice, bob):
    bob_chat = chat_with_one_exchange(client, bob)
    app.dependency_overrides[get_chat_model] = lambda: review_model()

    response = client.post(
        f"/chats/{bob_chat}/review", json={"topic": "budget"}, headers=auth_headers(alice)
    )

    assert response.status_code == 404
    assert session.get(Chat, bob_chat).review_title is None


def test_review_of_empty_chat_is_rejected(client, alice):
    chat_id = client.post("/chats", headers=auth_headers(alice)).json()["id"]

    response = client.post(
        f"/chats/{chat_id}/review", json={"topic": "budget"}, headers=auth_headers(alice)
    )

    assert response.status_code == 400


def test_empty_topic_is_rejected(client, alice):
    chat_id = chat_with_one_exchange(client, alice)

    response = client.post(
        f"/chats/{chat_id}/review", json={"topic": "  "}, headers=auth_headers(alice)
    )

    assert response.status_code == 422


def test_reviews_require_authentication(client):
    assert client.get("/reviews").status_code == 401
    assert client.post("/chats/1/review", json={"topic": "x"}).status_code == 401
