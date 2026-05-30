import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.loader import ModelLoader

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Загружает модель при старте, освобождает ресурсы при остановке."""
    logger.info("Запуск сервера: загрузка модели ECG-FM...")
    loader = ModelLoader.get_instance()
    try:
        loader.load()
        logger.info("Модель ECG-FM загружена успешно.")
    except Exception as exc:
        logger.error("Ошибка загрузки модели: %s", exc)
        # Сервер стартует даже без модели — /health вернёт статус degraded
    yield
    logger.info("Остановка сервера.")
    loader.unload()


app = FastAPI(
    title="ЭКГ-Интерпретатор",
    description="Автоматический анализ 12-канальных ЭКГ. Не является медицинским диагностическим прибором.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
