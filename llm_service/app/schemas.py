from pydantic import BaseModel, UUID4, Field
import os

class CompressRequest(BaseModel):
    text: str
    user_id: str
    compression: str


class UserId(BaseModel):
    user_id: str


class CompressResponse(BaseModel):
    success: bool
    text: str