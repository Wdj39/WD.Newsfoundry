import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_db
from routers import auth, chats

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

app.include_router(auth.router)
app.include_router(chats.router)


@app.get("/")
async def hello():
    return {"message": "👋"}


if __name__ == "__main__":
    init_db()

    # Railway fournit le port à utiliser via la variable d'environnement PORT.
    # En local, on garde 8000 par défaut.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
