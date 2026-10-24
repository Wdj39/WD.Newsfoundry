"""Tests du tool `search_news` de l'agent (étape 6).

Les modèles de test de PydanticAI permettent de simuler un LLM qui décide
d'appeler l'outil, sans aucun appel réseau.
"""

from pydantic_ai import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from conftest import FakeNewsClient, auth_headers
from dependencies import get_chat_model, get_news_client
from main import app
from models import Chat
from services.chat_service import load_history


def searching_model(queries: list[str]):
    """Faux LLM : appelle search_news avec chaque requête, puis répond."""

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool_returns = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        if len(tool_returns) < len(queries):
            query = queries[len(tool_returns)]
            return ModelResponse(parts=[ToolCallPart("search_news", {"query": query})])
        return ModelResponse(parts=[TextPart("Synthèse basée sur les articles trouvés.")])

    return FunctionModel(model)


def send(client, user, content="Parle-moi de la réforme budgétaire"):
    chat_id = client.post("/chats", headers=auth_headers(user)).json()["id"]
    response = client.post(
        f"/chats/{chat_id}/messages", json={"content": content}, headers=auth_headers(user)
    )
    return chat_id, response


def tool_returns(session, chat_id) -> list:
    history = load_history(session.get(Chat, chat_id))
    return [
        part.content
        for message in history
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]


def test_agent_calls_search_news_and_uses_results(client, session, alice):
    news = FakeNewsClient()
    app.dependency_overrides[get_news_client] = lambda: news
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["réforme budgétaire"])

    chat_id, response = send(client, alice)

    assert response.status_code == 200
    assert response.json()["content"] == "Synthèse basée sur les articles trouvés."
    assert news.searches == ["réforme budgétaire"]
    # Le résultat du tool, au format simplifié, est conservé dans l'historique
    [result] = tool_returns(session, chat_id)
    assert result[0]["titre"] == "Le Parlement adopte la réforme budgétaire"
    assert result[0]["url"] == "https://exemple.fr/budget"


def test_tool_calls_are_hidden_from_the_displayed_history(client, alice):
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["budget"])

    chat_id, _ = send(client, alice)

    messages = client.get(f"/chats/{chat_id}", headers=auth_headers(alice)).json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]


def test_number_of_searches_per_message_is_limited(client, session, alice):
    news = FakeNewsClient()
    app.dependency_overrides[get_news_client] = lambda: news
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["a", "b", "c", "d", "e"])

    chat_id, response = send(client, alice)

    assert response.status_code == 200
    assert news.searches == ["a", "b", "c"]  # 3 recherches maximum
    assert "Limite de recherches atteinte" in tool_returns(session, chat_id)[-1]


def test_news_api_error_is_reported_to_the_model_not_to_the_user(client, session, alice):
    app.dependency_overrides[get_news_client] = lambda: FakeNewsClient(error="quota épuisé")
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["budget"])

    chat_id, response = send(client, alice)

    # La réponse aboutit : le modèle est informé de l'échec et peut prévenir l'utilisateur
    assert response.status_code == 200
    assert "Recherche impossible (quota épuisé)" in tool_returns(session, chat_id)[0]


def test_no_results_message(client, session, alice):
    app.dependency_overrides[get_news_client] = lambda: FakeNewsClient(articles=[])
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["sujet introuvable"])

    chat_id, _ = send(client, alice)

    assert tool_returns(session, chat_id) == ["Aucun article récent trouvé pour « sujet introuvable »."]
