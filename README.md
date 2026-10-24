# NewsFoundry — Revue de presse automatique par IA

Projet 14 OpenClassrooms « Développeur IA » — **Option B** (cas fictif).

Outil qui aide les journalistes pigistes à suivre l'actualité et à produire des revues de presse :
gros titres du jour, chat avec un agent capable de rechercher des articles, puis génération d'une
revue de presse structurée (avec RAG).

- **Application déployée** : https://wd-newsfoundry.vercel.app
- **Documentation technique complète** (structure, choix techniques, erreurs de l'API, prompts,
  tests, déploiement, pistes d'amélioration) : [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md)

## Fonctionnalités

- Connexion (JWT) — compte de démonstration `test@test.com` / `test`
- Liste des discussions, création et reprise d'une discussion
- Un utilisateur n'accède qu'à ses propres discussions (vérifié par des tests automatisés)
- Agent conversationnel (PydanticAI, Gemini avec Groq en secours) informé des actualités du jour
  ([World News API](https://worldnewsapi.com)) et capable de rechercher d'autres articles
- Génération de revues de presse à sortie structurée, avec RAG (LlamaIndex)
- Messages d'erreur affichés dans l'interface

## Stack

| Partie | Technologies |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS — déployé sur Vercel |
| Backend | Python 3.13, FastAPI, SQLModel, PostgreSQL, PydanticAI, LlamaIndex — déploiement Railway (Docker) |
| Qualité | pytest (46 tests), GitHub Actions |

## Démarrage rapide

Prérequis : Docker, Python 3.13, [uv](https://docs.astral.sh/uv/), Node.js 22.

```bash
# Backend (voir backend/README.md)
cd backend && cp .env.example .env   # renseigner les clés
uv sync
docker run --name newsfoundry_db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=newsfoundry -p 5432:5432 -d postgres:17
uv run --env-file .env src/main.py

# Frontend
cd frontend && npm install && npm run dev
```

Tests : `cd backend && uv run pytest -v`
