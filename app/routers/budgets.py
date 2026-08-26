from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from decimal import Decimal

from app.database import get_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.core.dependencies import get_current_user
from app.services.budget_service import calculate_spent

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def build_budget_response(db: Session, budget: Budget) -> dict:
    spent = calculate_spent(db, budget.user_id, budget.category_id, budget.month, budget.year)
    remaining = budget.limit_amount - spent
    percentage_used = float((spent / budget.limit_amount) * 100) if budget.limit_amount > 0 else 0.0

    return {
        "id": budget.id,
        "category_id": budget.category_id,
        "month": budget.month,
        "year": budget.year,
        "limit_amount": budget.limit_amount,
        "spent": spent,
        "remaining": remaining,
        "percentage_used": round(percentage_used, 2),
        "is_exceeded": spent > budget.limit_amount,
        "created_at": budget.created_at,
    }


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if budget_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == budget_data.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # The DB-level unique constraint doesn't catch this case: SQL treats every
    # NULL in a unique constraint as distinct from every other NULL, so two
    # "overall" (category_id=NULL) budgets for the same user/month/year would
    # otherwise both insert successfully. Check explicitly instead.
    existing_budget = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.category_id == budget_data.category_id,
        Budget.month == budget_data.month,
        Budget.year == budget_data.year,
    ).first()
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A budget already exists for this category/month/year"
        )

    new_budget = Budget(
        user_id=current_user.id,
        category_id=budget_data.category_id,
        month=budget_data.month,
        year=budget_data.year,
        limit_amount=budget_data.limit_amount
    )

    db.add(new_budget)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A budget already exists for this category/month/year"
        )
    db.refresh(new_budget)

    return build_budget_response(db, new_budget)


@router.get("/", response_model=List[BudgetResponse])
def list_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    return [build_budget_response(db, b) for b in budgets]


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    if budget_data.limit_amount is not None:
        budget.limit_amount = budget_data.limit_amount

    db.commit()
    db.refresh(budget)
    return build_budget_response(db, budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    db.delete(budget)
    db.commit()
    return None