"""RAG (Retrieval Augmented Generation) de la revue de presse, avec LlamaIndex.

Principe :
1. Indexation : le contenu complet des articles chargés pendant la discussion est
   découpé en extraits (chunks), puis chaque extrait est converti en vecteur
   (embedding) qui représente son sens.
2. Recherche (retrieval) : le thème de la revue de presse est converti en vecteur,
   et on récupère les extraits les plus proches.
3. Génération : seuls ces extraits, regroupés par article, sont transmis à
   l'agent de revue de presse (voir services/review_service.py).

L'index est construit en mémoire à chaque génération et n'est pas persisté :
il ne contient que quelques dizaines d'articles, son calcul est rapide.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter

from config import EMBEDDING_MODEL, GEMINI_API_KEY, RAG_CHUNK_SIZE, RAG_TOP_K

logger = logging.getLogger(__name__)


class EmbeddingNotConfiguredError(RuntimeError):
    """Aucune clé n'est disponible pour calculer les embeddings."""


@dataclass
class RetrievedArticle:
    """Article jugé pertinent, avec les extraits retrouvés pour le thème."""

    title: str
    url: str
    publish_date: str
    excerpts: list[str] = field(default_factory=list)
    best_score: float = 0.0


@lru_cache
def get_embedding_model() -> BaseEmbedding:
    """Modèle d'embedding Gemini (importé et créé à la première utilisation)."""
    if not GEMINI_API_KEY:
        raise EmbeddingNotConfiguredError("GEMINI_API_KEY est nécessaire pour le RAG.")
    from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

    return GoogleGenAIEmbedding(model_name=EMBEDDING_MODEL, api_key=GEMINI_API_KEY)


def _to_documents(articles: list[dict[str, Any]]) -> list[Document]:
    """Un Document LlamaIndex par article ; le titre est inclus dans le texte indexé."""
    documents = []
    for article in articles:
        content = article.get("text") or article.get("summary") or ""
        if not content.strip():
            continue
        documents.append(
            Document(
                text=f"{article.get('title', '')}\n\n{content}",
                metadata={
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "publish_date": article.get("publish_date", ""),
                },
                # Les métadonnées servent au regroupement, pas au calcul de similarité
                excluded_embed_metadata_keys=["title", "url", "publish_date"],
                excluded_llm_metadata_keys=["title", "url", "publish_date"],
            )
        )
    return documents


def _retrieve(
    articles: list[dict[str, Any]], topic: str, embed_model: BaseEmbedding, top_k: int
) -> list[RetrievedArticle]:
    """Construit l'index et retrouve les extraits les plus proches du thème (bloquant)."""
    documents = _to_documents(articles)
    if not documents:
        return []

    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=RAG_CHUNK_SIZE, chunk_overlap=50)],
    )
    nodes = index.as_retriever(similarity_top_k=top_k).retrieve(topic)

    # Regroupement des extraits par article : un article n'apparaît qu'une fois,
    # avec tous ses extraits pertinents, classé selon son meilleur extrait.
    by_url: dict[str, RetrievedArticle] = {}
    for node in nodes:
        metadata = node.node.metadata
        url = metadata.get("url", "")
        article = by_url.setdefault(
            url,
            RetrievedArticle(
                title=metadata.get("title", ""),
                url=url,
                publish_date=metadata.get("publish_date", ""),
            ),
        )
        article.excerpts.append(node.node.get_content().strip())
        article.best_score = max(article.best_score, node.score or 0.0)

    return sorted(by_url.values(), key=lambda a: a.best_score, reverse=True)


async def retrieve_relevant_articles(
    articles: list[dict[str, Any]],
    topic: str,
    embed_model: BaseEmbedding,
    top_k: int = RAG_TOP_K,
) -> list[RetrievedArticle]:
    """Version asynchrone : le calcul (appels d'embedding compris) est exécuté dans
    un thread pour ne pas bloquer le serveur pendant ce temps."""
    return await asyncio.to_thread(_retrieve, articles, topic, embed_model, top_k)


def format_retrieved_articles(retrieved: list[RetrievedArticle]) -> str:
    """Mise en forme des extraits pour le prompt de l'agent de revue de presse."""
    blocks = []
    for index, article in enumerate(retrieved, start=1):
        excerpts = "\n".join(f"> {excerpt}" for excerpt in article.excerpts)
        blocks.append(
            f"### Article {index} : {article.title}\n"
            f"URL : {article.url}\nDate : {article.publish_date}\n{excerpts}"
        )
    return "\n\n".join(blocks)
