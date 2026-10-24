"""Agent de génération de revue de presse.

Agent distinct de celui du chat : il n'a pas d'outil et une seule tâche, rédiger
une revue de presse à partir de la discussion. Un agent spécialisé, avec des
consignes ciblées, produit généralement de meilleurs résultats qu'un agent
généraliste.

Sa sortie est structurée (`output_type`) : PydanticAI transmet le schéma au LLM
puis valide la réponse, ce qui garantit des données prêtes à être enregistrées
en base (titre, synthèse, articles) sans analyse de texte libre.
"""

import os

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic import BaseModel, Field  # noqa: E402
from pydantic_ai import Agent  # noqa: E402

from agents.prompts import REVIEW_INSTRUCTIONS  # noqa: E402


class ReviewArticle(BaseModel):
    """Un article cité dans la revue de presse."""

    title: str = Field(description="Titre de l'article, tel qu'il apparaît dans la source")
    source: str = Field(description="Nom du média (ex. « Le Monde »), déduit de l'URL si besoin")
    url: str = Field(description="URL de l'article, recopiée telle quelle depuis la discussion")
    summary: str = Field(description="Résumé de l'article en 2 ou 3 phrases, en français")


class PressReview(BaseModel):
    """Revue de presse structurée, enregistrée telle quelle en base."""

    title: str = Field(
        description="Titre court de la revue de presse, en majuscules (ex. « RÉFORME DES RETRAITES - 24/10/2026 »)"
    )
    summary: str = Field(
        description=(
            "Synthèse générale en Markdown : 2 à 4 paragraphes courts qui dégagent "
            "les faits principaux, les points de vue en présence et les enjeux"
        )
    )
    articles: list[ReviewArticle] = Field(
        description="Articles de la discussion pertinents pour le thème, du plus au moins important"
    )


review_agent = Agent(
    output_type=PressReview,
    instructions=REVIEW_INSTRUCTIONS,
    name="newsfoundry_review",
    # En cas de sortie invalide, le modèle reçoit l'erreur de validation et réessaie
    retries=2,
)
