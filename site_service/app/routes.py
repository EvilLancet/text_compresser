

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Cookie, Response
from fastapi.responses import FileResponse
import httpx
from app import history

from app import llm_client
from app.database import get_db
from app.schemas import TextRequest
from sqlalchemy.orm import Session


router = APIRouter()

@router.get("/")
async def root(): 
    return FileResponse("static/index.html")

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/levels")
async def get_levels():
    try:
        return await llm_client.get_levels()

    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Не удалось связаться с LLM Service"
        )

    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )


@router.get("/history")
async def get_all_history(
    user_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)):
    return history.get_all_history(user_id, db)

@router.delete("/historys")
async def delete_all_history(
    user_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)):
    return history.delete_all_history(user_id, db)

@router.delete("/history/{record_id}")
async def delete_one_history(
    record_id: int,
    user_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)):
    return history.delete_one_history(record_id, user_id, db)

@router.post("/process")
async def process_text(
    data: TextRequest,
    response: Response,
    user_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not user_id:
        user_id = str(uuid4())

        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite="lax"
        )
    try:
        result = await llm_client.process_text(
            data=data,
            user_id=user_id
        )
    except httpx.ConnectError:
        return {
            "result": "LLM-сервис недоступен",
            "success": False,
            "item": None
        }
    except httpx.TimeoutException:
        return {
            "result": "Превышено время ожидания",
            "success": False,
            "item": None
        }

    except httpx.HTTPError:
        return {
            "result": "Ошибка при обращении к LLM-сервису",
            "success": False,
            "item": None
        }

    except Exception:
        return {
            "result": "Ошибка при обработке текста",
            "success": False,
            "item": None
        }

    if not result:
        return {
            "result": "Отменено",
            "success": False,
            "item": None
        }
    record = history.add_history_record(
        UUID=user_id,
        TextBefore=data.text,
        TextAfter=result,
        Compression=data.compression,
        db=db
    )

    return {
            "result": result,
            "success": True,
            "item": record.to_dict()
        }

@router.post("/stop")
async def stop(
    user_id: str | None = Cookie(default=None)
):
    if not user_id:
        return {"status": False}

    try:
        return await llm_client.stop(user_id)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Не удалось связаться с LLM Service"
        )
