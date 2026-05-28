import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import chat, image
from app.services.bible_rag import BibleRAG, set_rag

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising FaithCompass backend...")
    rag = BibleRAG(
        verses_file=settings.verses_file, 
        persist_dir=settings.chroma_persist_dir,
        api_key=settings.gemini_api_key
    )
    await rag.initialize()
    set_rag(rag)
    yield
    logger.info("Shutting down FaithCompass backend.")


app = FastAPI(
    title="FaithCompass API",
    description="Christianity-focused AI assistant — Scripture-grounded, safety-first",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(image.router, prefix="/api", tags=["image"])


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.gemini_model}
