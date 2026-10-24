FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

# Le contexte de build est le dossier backend/ ("Root Directory" de Railway),
# les chemins sont donc relatifs à ce dossier.
COPY pyproject.toml uv.lock ./
# --no-dev : les outils de test (pytest…) ne sont pas installés en production
RUN uv sync --frozen --no-dev

COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "python", "src/main.py"]
