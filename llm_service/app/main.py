from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="LLM Service"
)

app.include_router(router)



