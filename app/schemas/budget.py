from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class BudgetCreate(BaseModel):
    category_id: int | None = None
    month: int
    year: int
    limit_amount: Decimal

class BudgetUpdate(BaseModel):
    limit_amount: Decimal | None = None

class BudgetResponse(BaseModel):
    id: int
    category_id: int | None = None
    month: int
    year: int
    limit_amount: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: float
    is_exceeded: bool
    created_at: datetime

    class Config:
        from_attributes = True
        