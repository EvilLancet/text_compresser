from sqlalchemy import  create_engine, Integer, Text, String,\
    Column, DateTime
from datetime import datetime
from app.database import Base

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
    