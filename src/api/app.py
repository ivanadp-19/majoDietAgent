from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.chat import router as chat_router
from src.api.routers.ingest import router as ingest_router
from src.api.routers.meals import router as meals_router

app = FastAPI(title="Majo Diet Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])
