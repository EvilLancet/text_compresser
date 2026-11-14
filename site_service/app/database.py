import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sqlite3.db")

engine = create_engine(DATABASE_URL)

# Создание cессии базы данных
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

# Управленрие сессией базы данных
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

