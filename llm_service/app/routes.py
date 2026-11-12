from fastapi import APIRouter
from app.schemas import UserId, CompressRequest
from app.llm_queue import ai_queue
from app.prompts import COMPRESSION_LEVELS

router = APIRouter()

@router.post("/stop")
async def stop(data: UserId):
    ai_queue.cancel(data.user_id)
    return {"success": True}

@router.post("/add_to_queue")
async def process_text(data: CompressRequest):
    result = await ai_queue.add_request(payload=data)
    return {"result":result, "success": True}

@router.get("/get_wait_time")
async def get_wait_time():
    result = ai_queue.get_wait_time()
    return {"wait_seconds": result}

@router.get("/levels")
async def get_levels():
    return {
        "success": True,
        "items": [
            {
                "id": level["id"],
                "name": level["name"],
                "percent": level["percent"]
            }
            for level in COMPRESSION_LEVELS
        ]
    }
 