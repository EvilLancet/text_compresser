from app.schemas import CompressRequest
from app.prompts import build_compression_messages
import httpx
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


timeout = httpx.Timeout(
    connect=5.0,  
    read=1000.0,    # время работы модели, потом можно уменьшить
    write=30.0,
    pool=5.0
)


async def generate_text(payload: CompressRequest):
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"

    messages = build_compression_messages(
    text=payload.text,
    compression=payload.compression
    )

    data = {
    'model': OLLAMA_MODEL,
    'messages': messages,
    'stream': False,
    }  
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        body = response.json()
        message = body.get("message") or {}
        text = (message.get("content") or "").strip()

        # на всякий случай, если модель вернула другой формат
        if not text and isinstance(body.get("response"), str):
            text = body["response"].strip()

        return text
    