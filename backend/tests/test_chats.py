"""Tests des discussions, et en particulier de la logique d'autorisation.

Règle testée : un utilisateur ne peut ni lire ni modifier les discussions
d'un autre utilisateur.
"""

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.function import FunctionModel

from conftest import FAKE_LLM_ANSWER, FakeNewsClient, auth_headers
from dependencies import get_chat_model, get_news_client
from main import app
from models import Chat


def create_chat(client, user) -> int:
    response = client.post("/chats", headers=auth_headers(user))
    assert response.status_code == 201
    return response.json()["id"]


# --- Cas nominal : l'utilisateur accède à ses propres discussions ---


def test_user_can_create_and_load_own_chat(client, alice):
    chat_id = create_chat(client, alice)

    response = client.get(f"/chats/{chat_id}", headers=auth_headers(alice))

    assert response.status_code == 200
    assert response.json()["id"] == chat_id
    assert response.json()["messages"] == []


def test_user_can_send_message_and_receive_answer(client, alice):
    chat_id = create_chat(client, alice)

    response = client.post(
        f"/chats/{chat_id}/messages",
        json={"content": "Quelles sont les actualités du jour ?"},
        headers=auth_headers(alice),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "assistant"
    assert response.json()["content"] == FAKE_LLM_ANSWER

    # L'historique est sauvegardé : question puis réponse
    messages = client.get(f"/chats/{chat_id}", headers=auth_headers(alice)).json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Quelles sont les actualités du jour ?"


def test_list_contains_only_own_chats(client, alice, bob):
    alice_chat = create_chat(client, alice)
    create_chat(client, bob)

    response = client.get("/chats", headers=auth_headers(alice))

    assert response.status_code == 200
    assert [chat["id"] for chat in response.json()] == [alice_chat]


# --- Accès interdit : un utilisateur tente d'accéder au chat d'un autre ---


def test_user_cannot_load_another_users_chat(client, alice, bob):
    bob_chat = create_chat(client, bob)

    response = client.get(f"/chats/{bob_chat}", headers=auth_headers(alice))

    # 404 et non 403 : on ne révèle pas l'existence de la discussion
    assert response.status_code == 404
    assert response.json()["detail"] == "Discussion introuvable."


def test_user_cannot_post_message_in_another_users_chat(client, alice, bob):
    bob_chat = create_chat(client, bob)

    response = client.post(
        f"/chats/{bob_chat}/messages",
        json={"content": "Je tente d'écrire chez Bob"},
        headers=auth_headers(alice),
    )

    assert response.status_code == 404
    # La discussion de Bob n'a pas été modifiée
    messages = client.get(f"/chats/{bob_chat}", headers=auth_headers(bob)).json()["messages"]
    assert messages == []


# --- Autres cas d'erreur ---


def test_chats_require_authentication(client):
    assert client.get("/chats").status_code == 401
    assert client.post("/chats").status_code == 401
    assert client.get("/chats/1").status_code == 401
    assert client.post("/chats/1/messages", json={"content": "x"}).status_code == 401


def test_unknown_chat_returns_404(client, alice):
    response = client.get("/chats/9999", headers=auth_headers(alice))

    assert response.status_code == 404


def test_empty_message_is_rejected(client, alice):
    chat_id = create_chat(client, alice)

    response = client.post(
        f"/chats/{chat_id}/messages", json={"content": "   "}, headers=auth_headers(alice)
    )

    assert response.status_code == 422


def test_llm_failure_returns_503_and_keeps_history_clean(client, alice):
    """Si le fournisseur de LLM est en panne, l'API renvoie une erreur claire
    et le message de l'utilisateur n'est pas sauvegardé sans réponse."""

    def failing_model(messages, info):
        raise ModelHTTPError(status_code=503, model_name="test", body="Service indisponible")

    app.dependency_overrides[get_chat_model] = lambda: FunctionModel(failing_model)
    chat_id = create_chat(client, alice)

    response = client.post(
        f"/chats/{chat_id}/messages", json={"content": "Bonjour"}, headers=auth_headers(alice)
    )

    assert response.status_code == 503
    assert "indisponible" in response.json()["detail"]
    messages = client.get(f"/chats/{chat_id}", headers=auth_headers(alice)).json()["messages"]
    assert messages == []


# --- Étape 5 : actualités du jour dans le prompt système ---


def test_new_chat_prompt_contains_todays_news(client, session, alice):
    chat_id = create_chat(client, alice)

    chat = session.get(Chat, chat_id)
    assert "Le Parlement adopte la réforme budgétaire" in chat.system_prompt
    assert "https://exemple.fr/budget" in chat.system_prompt


def test_chat_is_created_even_if_news_api_fails(client, session, alice):
    app.dependency_overrides[get_news_client] = lambda: FakeNewsClient(error="quota épuisé")

    chat_id = create_chat(client, alice)

    chat = session.get(Chat, chat_id)
    assert "n'ont pas pu être chargées" in chat.system_prompt


def test_news_are_fetched_once_for_several_chats(client, alice):
    calls = []

    class CountingClient(FakeNewsClient):
        async def top_news(self, **kwargs):
            calls.append(1)
            return await super().top_news(**kwargs)

    app.dependency_overrides[get_news_client] = lambda: CountingClient()

    create_chat(client, alice)
    create_chat(client, alice)

    assert len(calls) == 1  # le second appel est servi par le cache
