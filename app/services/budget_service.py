from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from app.models.transaction import Transaction

def calculate_spent(
    db: Session,
    user_id: int,
    category_id: int | None,
    month: int,
    year: int
) -> Decimal:
    query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.amount < 0,
        func.extract("month", Transaction.transaction_date) == month,
        func.extract("year", Transaction.transaction_date) == year,
    )

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    total = query.scalar()
    return abs(total) if total is not None else Decimal("0.00")