from pydantic import BaseModel
from decimal import Decimal

class DashboardResponse(BaseModel):
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_budget: Decimal | None = None
    remaining_budget: Decimal | None = None
    percentage_used: float | None = None
    amount_exceeded: Decimal | None = None