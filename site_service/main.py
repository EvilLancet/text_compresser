from pydantic import BaseModel, UUID4
from sqlalchemy import  create_engine, Integer, Text, String,\
    Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from uuid import uuid4
from fastapi import Cookie, Response
import httpx
import os

LLM_URL = os.getenv("LLM_URL", "http://localhost:8001")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
engine = create_engine('sqlite:///sqlite3.db')
engine.connect()

Base = declarative_base()

class SaveTable(Base):
    __tablename__ = 'SaveTable'
    id = Column(Integer, primary_key=True)
    UUID = Column(String(100), nullable=False)
    TextBefore = Column(Text, nullable=False)
    TextAfter = Column(Text, nullable=False)
    Compression = Column(String, nullable=False)
    CreateData = Column(DateTime(), default=datetime.now)
    
    def to_dict(self):
        return {
            "id": self.id,
            "original": self.TextBefore,
            "result": self.TextAfter,
            "compression": self.Compression,
            "date": self.CreateData.strftime("%d.%m.%Y, %H:%M:%S") if self.CreateData else ""
        }
    
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine, expire_on_commit=False)

class UserId(BaseModel):
    user_id: UUID4

class TextRequest(BaseModel):
    text: str
    compression: str


@app.get("/")
async def root(): 
    return FileResponse("static/index.html")


@app.get("/levels")
async def get_levels():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LLM_URL}/levels")
        response.raise_for_status()

        data = response.json()
        print(data)
        if not data.get("success"):
            raise HTTPException(
                status_code=502,
                detail="LLM Service не смог получить уровни сокращения"
            )

        return data

    except httpx.HTTPError:
        print("Ошибка при обращении к LLM Service")
        raise HTTPException(
            status_code=502,
            detail="Не удалось связаться с LLM Service"
        )

@app.get("/history")
async def get_all_history(user_id: str | None = Cookie(default=None)):
    if not user_id:
        return {"success": True, "items": []}
    session = Session()
    records = session.query(SaveTable).filter(SaveTable.UUID == user_id).order_by(SaveTable.CreateData.desc()).all()
    items = [r.to_dict() for r in records]
    return {"success": True, "items": items}
    
@app.delete("/historys")
async def delete_all_history(user_id: str | None = Cookie(default=None)):
    session = Session()
    session.query(SaveTable).filter(SaveTable.UUID == user_id).delete()
    session.commit()
    return {"success": True}
    
@app.delete("/history/{record_id}")
async def delete_one_history(
    record_id: int,
    user_id: str | None = Cookie(default=None)
):
    if not user_id:
        return {"success": False}

    session = Session()
    try:
        record = (
            session.query(SaveTable)
            .filter(
                SaveTable.id == record_id,
                SaveTable.UUID == user_id   # важно!
            )
            .first()
        )

        if not record:
            return {"success": False}

        session.delete(record)
        session.commit()
        return {"success": True}
    except Exception:
        session.rollback()
        return {"success": False}
    finally:
        session.close()

@app.post("/process")
async def process_text(
    data: TextRequest,
    response: Response,
    user_id: str | None = Cookie(default=None)
):
    # 1. user_id из cookie или создаём новый
    if not user_id:
        user_id = str(uuid4())
        response.set_cookie(
            key="user_id",
            value=user_id,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite="lax"
        )

    # 2. Запрос в LLM-сервис
    result = None
    try:
        async with httpx.AsyncClient(trust_env=False) as client:

            wait_resp = await client.get(f"{LLM_URL}/get_wait_time", timeout=5.0)
            wait_resp.raise_for_status()
            wait_seconds = int(wait_resp.json()["wait_seconds"])

            print(wait_seconds)
            timeout = httpx.Timeout(
                connect=5.0,
                read=wait_seconds + 10,  # запас на всякий случай
                write=30.0,
                pool=5.0
                )
            
            
            llm_response = await client.post(
                f"{LLM_URL}/add_to_queue",
                json={
                    "text": data.text,
                    "compression": data.compression,
                    "user_id": user_id
                },
                timeout=timeout
            )
            llm_response.raise_for_status()
            llm_data = llm_response.json()
            # Ожидаем от LLM-сервиса:
            # {"success": true, "text": "..."} или {"success": false, "text": ""}
            #if not llm_data.get(c):
            #    return {
            #        "result": "Отменено",
            #        "success": False,
            #        "item": None
            #    }

            result = llm_data["result"]

    except httpx.ConnectError:
        return {
            "result": "LLM-сервис недоступен",
            "success": False,
            "item": None
        }
    except httpx.ReadTimeout:
        return {
            "result": "Превышено время ожидания",
            "success": False,
            "item": None
        }
    except Exception:
        return {
            "result": "Ошибка при обращении к LLM-сервису",
            "success": False,
            "item": None
        }

    if not result:
        return {
            "result": "Отменено",
            "success": False,
            "item": None
        }

    # 3. Сохраняем в БД
    session = Session()
    try:
        record = SaveTable(
            UUID=user_id,
            TextBefore=data.text,
            TextAfter=result,
            Compression=data.compression
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        item = {
            "id": record.id,
            "original": record.TextBefore,
            "result": record.TextAfter,
            "compression": data.compression,
            "date": record.CreateData.strftime("%d.%m.%Y, %H:%M:%S") if record.CreateData else ""
        }

        return {
            "result": result,
            "success": True,
            "item": item
        }

    except Exception:
        session.rollback()
        return {
            "result": result,
            "success": False,
            "item": None
        }
    finally:
        session.close()
        
@app.post("/stop")
async def stop(user_id: str | None = Cookie(default=None)):
    async with httpx.AsyncClient(timeout=180.0, trust_env=False) as client:
                llm_response = await client.post(
                    f"{LLM_URL}/stop",
                    json={
                        "user_id": user_id
                    }
                )
                print(llm_response.text)
                llm_response.raise_for_status()
                llm_data = llm_response.json()

    return {"status": llm_data["status"]}