from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongo import ensure_chunk_indexes
from app.api.upload import router as upload_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Voice Research Assistant API")


@app.on_event("startup")
def initialize_ingestion_dependencies() -> None:
    # Fail fast if MongoDB is unavailable or index creation fails.
    ensure_chunk_indexes()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(upload_router)
