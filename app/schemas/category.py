from pydantic import BaseModel
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    type: str  # "income" or "expense"

class CategoryUpdate(BaseModel):
    name: str | None = None
    type: str | None = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True