import os
import httpx
from app.schemas import TextRequest

LLM_URL = os.getenv("LLM_URL", "http://localhost:8001").rstrip("/")

# Получение уровней сокращения текста
async def get_levels():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{LLM_URL}/levels")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError("Не удалось получить уровни сокращения")
        return data

# Сокращение текста
async def process_text(
    data: TextRequest,
    user_id: str
):
    async with httpx.AsyncClient() as client:

        wait_response = await client.get(f"{LLM_URL}/get_wait_time", timeout=5.0)
        wait_response.raise_for_status()
        wait_seconds = int(wait_response.json()["wait_seconds"])
        
        timeout = httpx.Timeout(
            connect=5.0,
            read=wait_seconds + 10,
            write=30.0,
            pool=5.0
        )

        response = await client.post(
            f"{LLM_URL}/add_to_queue",
            json={
                "text": data.text,
                "compression": data.compression,
                "user_id": user_id
            },
            timeout=timeout
        )

        response.raise_for_status()
        data = response.json()

        return data.get("result", "")

# Отмена обработки текста
async def stop(user_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{LLM_URL}/stop",
            json={"user_id": user_id}
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ValueError("Не удалось остановить обработку")
        
        return { "status": data.get("success", False) }