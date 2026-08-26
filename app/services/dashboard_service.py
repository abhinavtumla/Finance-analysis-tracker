from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.budget import Budget


def get_dashboard_summary(db: Session, user_id: int, month: int, year: int) -> dict:
    # Total balance = sum of ALL transactions ever (not just this month)
    total_balance_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id
    ).scalar()
    total_balance = total_balance_result if total_balance_result is not None else Decimal("0.00")

    # This month's income = sum of positive amounts this month
    income_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.amount > 0,
        func.extract("month", Transaction.transaction_date) == month,
        func.extract("year", Transaction.transaction_date) == year,
    ).scalar()
    monthly_income = income_result if income_result is not None else Decimal("0.00")

    # This month's expenses = absolute value of sum of negative amounts this month
    expense_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.amount < 0,
        func.extract("month", Transaction.transaction_date) == month,
        func.extract("year", Transaction.transaction_date) == year,
    ).scalar()
    monthly_expenses = abs(expense_result) if expense_result is not None else Decimal("0.00")

    # Overall budget = the budget row with category_id IS NULL for this month/year
    overall_budget = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id.is_(None),
        Budget.month == month,
        Budget.year == year,
    ).first()

    result = {
        "total_balance": total_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_budget": None,
        "remaining_budget": None,
        "percentage_used": None,
        "amount_exceeded": None,
    }

    if overall_budget is not None:
        limit = overall_budget.limit_amount
        remaining = limit - monthly_expenses
        percentage = float((monthly_expenses / limit) * 100) if limit > 0 else 0.0
        exceeded = monthly_expenses - limit if monthly_expenses > limit else Decimal("0.00")

        result["monthly_budget"] = limit
        result["remaining_budget"] = remaining
        result["percentage_used"] = round(percentage, 2)
        result["amount_exceeded"] = exceeded

    return result