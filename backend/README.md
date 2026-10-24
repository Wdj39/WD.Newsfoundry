# NewsFoundry — Backend

API FastAPI de NewsFoundry. Documentation complète : [`../docs/DOCUMENTATION.md`](../docs/DOCUMENTATION.md).

1. Copier le fichier `.env.example` dans `.env`, puis renseigner les clés (`JWT_SECRET`,
   `GEMINI_API_KEY`, `GROQ_API_KEY`, `WORLD_NEWS_API_KEY`).
   Pour générer `JWT_SECRET` :
   ```bash
   uv run python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Installer les dépendances :
   ```bash
   uv sync
   ```

3. Démarrer la base de données (les fois suivantes : `docker start newsfoundry_db`) :
   ```bash
   docker run --name newsfoundry_db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=newsfoundry -p 5432:5432 -d postgres:17
   ```

4. Lancer le backend (http://localhost:8000, documentation interactive sur `/docs`) :
   ```bash
   uv run --env-file .env src/main.py
   ```

5. Lancer les tests (aucune clé ni base de données nécessaire) :
   ```bash
   uv run pytest -v
   ```
