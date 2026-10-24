"""Client de World News API (https://worldnewsapi.com).

Le client renvoie des articles « nettoyés » (titre, résumé, date, URL) plutôt que
la réponse brute de l'API, qui est volumineuse et peu adaptée à un LLM.
"""

import logging
import time
from dataclasses import dataclass

import httpx

from config import (
    NEWS_CACHE_SECONDS,
    NEWS_COUNTRY,
    NEWS_LANGUAGE,
    NEWS_MAX_TOP_STORIES,
    NEWS_SEARCH_MAX_RESULTS,
    WORLD_NEWS_API_KEY,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.worldnewsapi.com"
TIMEOUT_SECONDS = 10.0
SUMMARY_MAX_CHARS = 300


@dataclass(frozen=True)
class NewsArticle:
    title: str
    summary: str
    url: str
    publish_date: str


class NewsAPIError(Exception):
    """Erreur lors d'un appel à World News API (message lisible par un humain)."""


# Messages clairs pour les codes d'erreur documentés par World News API
_HTTP_ERRORS = {
    401: "clé d'API World News invalide",
    403: "clé d'API World News refusée",
    402: "quota journalier de World News API épuisé",
    429: "trop de requêtes envoyées à World News API",
}


def _shorten(text: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    """Tronque un texte proprement, sans couper un mot."""
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def _to_article(raw: dict) -> NewsArticle | None:
    """Convertit un article brut de l'API ; ignore les articles sans titre."""
    title = (raw.get("title") or "").strip()
    if not title:
        return None
    # Le résumé n'est pas toujours fourni : on retombe sur le début du texte
    summary = raw.get("summary") or raw.get("text") or ""
    return NewsArticle(
        title=title,
        summary=_shorten(summary),
        url=raw.get("url") or "",
        publish_date=raw.get("publish_date") or "",
    )


class NewsClient:
    """Client asynchrone de World News API."""

    def __init__(
        self,
        api_key: str = WORLD_NEWS_API_KEY,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.api_key = api_key
        # `transport` permet aux tests de simuler l'API sans appel réseau
        self._transport = transport

    async def _get(self, path: str, params: dict) -> dict:
        if not self.api_key:
            raise NewsAPIError("aucune clé World News API n'est configurée")

        try:
            async with httpx.AsyncClient(
                base_url=BASE_URL,
                timeout=TIMEOUT_SECONDS,
                headers={"x-api-key": self.api_key},
                transport=self._transport,
            ) as client:
                response = await client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise NewsAPIError("World News API n'a pas répondu à temps") from exc
        except httpx.HTTPError as exc:
            raise NewsAPIError("impossible de joindre World News API") from exc

        if response.status_code != 200:
            reason = _HTTP_ERRORS.get(response.status_code, f"erreur HTTP {response.status_code}")
            raise NewsAPIError(reason)

        logger.info("World News API %s — points restants : %s", path, response.headers.get("X-API-Quota-Left"))
        try:
            return response.json()
        except ValueError as exc:
            raise NewsAPIError("réponse invalide de World News API") from exc

    async def top_news(
        self,
        *,
        country: str = NEWS_COUNTRY,
        language: str = NEWS_LANGUAGE,
        max_stories: int = NEWS_MAX_TOP_STORIES,
    ) -> list[NewsArticle]:
        """Gros titres du jour : un article représentatif par sujet.

        L'API regroupe les articles traitant du même sujet en « clusters », classés
        par nombre d'articles. On garde le premier article de chaque cluster pour
        éviter les doublons dans le prompt.
        """
        data = await self._get(
            "/top-news",
            {"source-country": country, "language": language},
        )

        articles: list[NewsArticle] = []
        for cluster in data.get("top_news") or []:
            for raw in cluster.get("news") or []:
                article = _to_article(raw)
                if article:
                    articles.append(article)
                    break  # un seul article par sujet
            if len(articles) >= max_stories:
                break
        return articles


    async def search_news(
        self,
        query: str,
        *,
        language: str = NEWS_LANGUAGE,
        max_results: int = NEWS_SEARCH_MAX_RESULTS,
    ) -> list[NewsArticle]:
        """Recherche d'articles par mots-clés, les plus récents d'abord.

        Le nombre de résultats est volontairement faible : chaque article renvoyé
        consomme du quota (1 point par requête + 0,01 point par article) et allonge
        le contexte envoyé au LLM.
        """
        data = await self._get(
            "/search-news",
            {
                "text": query,
                "language": language,
                "sort": "publish-time",
                "sort-direction": "DESC",
                "number": max_results,
            },
        )
        articles = [_to_article(raw) for raw in data.get("news") or []]
        return [article for article in articles if article]


# --- Cache des gros titres -------------------------------------------------

_cache: dict[tuple[str, str], tuple[float, list[NewsArticle]]] = {}


async def get_top_news_cached(client: NewsClient) -> list[NewsArticle]:
    """Gros titres mis en cache en mémoire pendant NEWS_CACHE_SECONDS.

    Toutes les discussions créées dans l'heure partagent les mêmes actualités :
    une seule requête à l'API au lieu d'une par discussion.
    """
    key = (NEWS_COUNTRY, NEWS_LANGUAGE)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < NEWS_CACHE_SECONDS:
        return cached[1]

    articles = await client.top_news()
    _cache[key] = (time.monotonic(), articles)
    return articles


def clear_news_cache() -> None:
    _cache.clear()
