import logging
import os
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_db
from routers import auth, chats, reviews

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NewsFoundry API")

# Le frontend (Next.js) tourne sur un autre domaine que l'API :
# le navigateur bloque ses requêtes si l'API ne l'autorise pas explicitement (CORS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("newsfoundry.perf")


@app.middleware("http")
async def log_request_duration(request: Request, call_next):
    """Mesure la durée de chaque requête (hors requêtes CORS « OPTIONS »).

    Ces mesures servent à suivre la performance de l'application
    (voir la section « Pistes d'amélioration » de docs/DOCUMENTATION.md).
    """
    start = time.perf_counter()
    response = await call_next(request)
    if request.method != "OPTIONS":
        logger.info(
            "%s %s -> %d en %.2f s",
            request.method,
            request.url.path,
            response.status_code,
            time.perf_counter() - start,
        )
    return response


app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(reviews.router)


@app.get("/")
async def hello():
    return {"message": "👋"}


if __name__ == "__main__":
    init_db()

    # Railway fournit le port à utiliser via la variable d'environnement PORT.
    # En local, on garde 8000 par défaut.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
