from pydantic import BaseModel, UUID4, Field
import os

MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))

class TextRequest(BaseModel):
    text: str = Field(max_length=MAX_TEXT_LENGTH)
    compression: str

class UserId(BaseModel):
    user_id: UUID4
