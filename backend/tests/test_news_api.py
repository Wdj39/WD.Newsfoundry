"""Tests du client World News API, avec une API simulée (httpx.MockTransport)."""

import asyncio

import httpx
import pytest

from services.news_api import NewsAPIError, NewsClient


def make_client(handler) -> NewsClient:
    return NewsClient(api_key="cle-de-test", transport=httpx.MockTransport(handler))


TOP_NEWS_RESPONSE = {
    "top_news": [
        {
            "news": [
                {"title": "Sujet A", "summary": "Résumé A", "url": "https://a.fr", "publish_date": "2026-10-24 08:00:00"},
                {"title": "Sujet A (doublon)", "summary": "Autre article sur A", "url": "https://a2.fr"},
            ]
        },
        {"news": [{"title": "Sujet B", "text": "Texte complet de B " * 50, "url": "https://b.fr"}]},
        {"news": [{"title": "", "summary": "Article sans titre ignoré"}]},
    ],
    "language": "fr",
    "country": "fr",
}


def test_top_news_keeps_one_article_per_topic():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/top-news"
        assert request.headers["x-api-key"] == "cle-de-test"
        assert request.url.params["source-country"] == "fr"
        return httpx.Response(200, json=TOP_NEWS_RESPONSE)

    articles = asyncio.run(make_client(handler).top_news())

    assert [a.title for a in articles] == ["Sujet A", "Sujet B"]
    assert articles[0].summary == "Résumé A"


def test_summary_falls_back_to_truncated_text():
    articles = asyncio.run(
        make_client(lambda r: httpx.Response(200, json=TOP_NEWS_RESPONSE)).top_news()
    )

    assert articles[1].summary.startswith("Texte complet de B")
    assert len(articles[1].summary) <= 301  # 300 caractères + "…"
    assert articles[1].summary.endswith("…")


def test_max_stories_limits_the_number_of_topics():
    articles = asyncio.run(
        make_client(lambda r: httpx.Response(200, json=TOP_NEWS_RESPONSE)).top_news(max_stories=1)
    )

    assert len(articles) == 1


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (401, "clé d'API World News invalide"),
        (402, "quota journalier de World News API épuisé"),
        (429, "trop de requêtes envoyées à World News API"),
        (500, "erreur HTTP 500"),
    ],
)
def test_http_errors_are_converted_to_readable_messages(status_code, message):
    client = make_client(lambda r: httpx.Response(status_code, json={"message": "error"}))

    with pytest.raises(NewsAPIError, match=message):
        asyncio.run(client.top_news())


def test_timeout_is_handled():
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    with pytest.raises(NewsAPIError, match="n'a pas répondu à temps"):
        asyncio.run(make_client(handler).top_news())


def test_missing_api_key_is_reported():
    with pytest.raises(NewsAPIError, match="aucune clé"):
        asyncio.run(NewsClient(api_key="").top_news())


def test_search_news_sends_query_and_parses_articles():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search-news"
        assert request.url.params["text"] == "grève SNCF"
        assert request.url.params["number"] == "5"
        return httpx.Response(
            200,
            json={"news": [{"title": "Grève à la SNCF", "summary": "Trafic perturbé.", "url": "https://s.fr"}]},
        )

    articles = asyncio.run(make_client(handler).search_news("grève SNCF"))

    assert [a.title for a in articles] == ["Grève à la SNCF"]
