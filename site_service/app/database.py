import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sqlite3.db")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

# для уверенности, что сессия закроется
# https://docs-python.ru/packages/freimvork-fastapi/depends-url-fastapi/
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

