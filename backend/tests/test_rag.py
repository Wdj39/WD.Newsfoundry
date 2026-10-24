"""Tests du RAG de la revue de presse (étape 8)."""

import asyncio

from llama_index.core.base.embeddings.base import BaseEmbedding

from conftest import FakeNewsClient, auth_headers
from dependencies import get_chat_model, get_embedding_model_or_none, get_news_client
from main import app
from models import Chat
from services.news_api import NewsArticle
from services.rag import retrieve_relevant_articles
from test_agent_tools import searching_model
from test_reviews import review_model

VOCABULARY = ["budget", "parlement", "football", "match", "grève", "sncf"]


class KeywordEmbedding(BaseEmbedding):
    """Faux modèle d'embedding déterministe : un vecteur de présence de mots-clés.
    Deux textes sont « proches » s'ils partagent des mots du vocabulaire."""

    def _vector(self, text: str) -> list[float]:
        words = text.lower()
        return [1.0 if word in words else 0.0 for word in VOCABULARY] + [0.01]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._vector(text)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._vector(query)


class FailingEmbedding(KeywordEmbedding):
    def _get_text_embedding(self, text: str) -> list[float]:
        raise RuntimeError("quota d'embedding épuisé")


ARTICLES = [
    {"title": "Le budget adopté", "url": "https://a.fr/budget", "publish_date": "",
     "text": "Le Parlement a adopté le budget après un long débat sur les économies."},
    {"title": "Victoire au match", "url": "https://a.fr/foot", "publish_date": "",
     "text": "Le club de football a gagné son match de championnat samedi soir."},
    {"title": "Grève à la SNCF", "url": "https://a.fr/sncf", "publish_date": "",
     "text": "Une grève perturbe le trafic de la SNCF ce week-end."},
]


def test_retrieval_returns_the_articles_closest_to_the_topic():
    retrieved = asyncio.run(
        retrieve_relevant_articles(ARTICLES, "le budget au parlement", KeywordEmbedding(), top_k=1)
    )

    assert [article.url for article in retrieved] == ["https://a.fr/budget"]
    assert "adopté le budget" in retrieved[0].excerpts[0]


def test_articles_without_content_are_ignored():
    retrieved = asyncio.run(
        retrieve_relevant_articles([{"title": "Vide", "url": "u", "text": ""}], "budget", KeywordEmbedding())
    )

    assert retrieved == []


def test_loaded_articles_are_saved_with_full_text(client, session, alice):
    chat_id = client.post("/chats", headers=auth_headers(alice)).json()["id"]

    [article] = session.get(Chat, chat_id).loaded_articles
    assert article["url"] == "https://exemple.fr/budget"
    assert "économies" in article["text"]


def test_articles_found_by_search_are_added_without_duplicates(client, session, alice):
    other = NewsArticle(title="Grève SNCF", summary="Trafic perturbé.", url="https://s.fr", publish_date="", text="Grève.")
    news = FakeNewsClient()

    async def search(query, **kwargs):
        # 1re recherche : un nouvel article + un article déjà connu (gros titre)
        return [other, *FakeNewsClient().articles]

    news.search_news = search
    app.dependency_overrides[get_news_client] = lambda: news
    app.dependency_overrides[get_chat_model] = lambda: searching_model(["grève sncf"])
    chat_id = client.post("/chats", headers=auth_headers(alice)).json()["id"]

    client.post(f"/chats/{chat_id}/messages", json={"content": "La grève ?"}, headers=auth_headers(alice))

    urls = [a["url"] for a in session.get(Chat, chat_id).loaded_articles]
    assert urls == ["https://exemple.fr/budget", "https://s.fr"]


def _chat_with_articles(client, session, user) -> int:
    chat_id = client.post("/chats", headers=auth_headers(user)).json()["id"]
    client.post(f"/chats/{chat_id}/messages", json={"content": "Quoi de neuf ?"}, headers=auth_headers(user))
    chat = session.get(Chat, chat_id)
    chat.loaded_articles = ARTICLES
    session.add(chat)
    session.commit()
    return chat_id


def test_review_uses_only_relevant_excerpts(client, session, alice):
    chat_id = _chat_with_articles(client, session, alice)
    prompts: list[str] = []
    app.dependency_overrides[get_chat_model] = lambda: review_model(prompts)
    app.dependency_overrides[get_embedding_model_or_none] = lambda: KeywordEmbedding()

    response = client.post(f"/chats/{chat_id}/review", json={"topic": "grève SNCF"}, headers=auth_headers(alice))

    assert response.status_code == 200
    prompt = prompts[0]
    assert "<extraits_articles>" in prompt
    assert "Une grève perturbe le trafic de la SNCF" in prompt
    assert "Quoi de neuf ?" in prompt  # la discussion est toujours transmise


def test_review_falls_back_without_rag_when_embeddings_fail(client, session, alice):
    chat_id = _chat_with_articles(client, session, alice)
    prompts: list[str] = []
    app.dependency_overrides[get_chat_model] = lambda: review_model(prompts)
    app.dependency_overrides[get_embedding_model_or_none] = lambda: FailingEmbedding()

    response = client.post(f"/chats/{chat_id}/review", json={"topic": "budget"}, headers=auth_headers(alice))

    assert response.status_code == 200
    assert "<extraits_articles>" not in prompts[0]
    assert "Le Parlement adopte la réforme budgétaire" in prompts[0]  # gros titres de la discussion
