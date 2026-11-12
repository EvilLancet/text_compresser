from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import Base, engine
from app.routes import router

app = FastAPI(
    title="Text Compressor",
    description="Сервис сокращения текста с помощью LLM",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
engine.connect()

Base.metadata.create_all(engine)
app.include_router(router)

