"""Conversion des erreurs des LLM en erreurs HTTP compréhensibles.

Partagé par le chat et la génération de revue de presse pour que toutes les
fonctionnalités IA renvoient les mêmes codes et messages d'erreur.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status
from pydantic_ai.exceptions import (
    FallbackExceptionGroup,
    ModelAPIError,
    UnexpectedModelBehavior,
    UsageLimitExceeded,
)

logger = logging.getLogger(__name__)


@contextmanager
def handle_llm_errors(retry_hint: str) -> Iterator[None]:
    """Transforme les exceptions PydanticAI en HTTPException.

    - 503 : le fournisseur de LLM est indisponible (quota, panne, surcharge),
      y compris quand tous les modèles du FallbackModel ont échoué ;
    - 502 : le modèle a répondu mais sa réponse est inexploitable (format
      invalide après plusieurs essais, boucle d'appels d'outils…).
    """
    try:
        yield
    except (ModelAPIError, FallbackExceptionGroup):
        logger.exception("Échec de l'appel au LLM")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service d'IA est momentanément indisponible. Réessayez dans quelques instants.",
        )
    except (UnexpectedModelBehavior, UsageLimitExceeded):
        logger.exception("Réponse du LLM inexploitable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"L'IA n'a pas pu produire de réponse. {retry_hint}",
        )
