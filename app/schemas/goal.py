from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime

class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
    target_date: date | None = None

class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: Decimal | None = None
    target_date: date | None = None

class GoalContribution(BaseModel):
    amount: Decimal

class GoalResponse(BaseModel):
    id: int
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None = None
    progress_percentage: float
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True