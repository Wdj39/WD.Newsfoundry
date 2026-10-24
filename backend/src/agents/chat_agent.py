"""Agent conversationnel du chat NewsFoundry."""

import os
from dataclasses import dataclass

# Masque la bannière d'accueil affichée par PydanticAI au premier lancement d'un agent
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, RunContext  # noqa: E402


@dataclass
class ChatDeps:
    """Dépendances injectées à chaque exécution de l'agent."""

    # Prompt système propre à la discussion (stocké en base avec le Chat)
    system_prompt: str


# Le modèle n'est pas fixé ici : il est passé à chaque `run` (voir agents/llm.py et
# la dépendance `get_chat_model`), ce qui permet aux tests d'utiliser un TestModel.
chat_agent = Agent(deps_type=ChatDeps, name="newsfoundry_chat")


@chat_agent.instructions
def chat_instructions(ctx: RunContext[ChatDeps]) -> str:
    """Instructions envoyées au modèle à chaque appel.

    Contrairement à un `system_prompt` classique (envoyé une seule fois en début
    d'historique), les instructions sont recalculées à chaque appel à partir du
    prompt enregistré pour cette discussion.
    """
    return ctx.deps.system_prompt
