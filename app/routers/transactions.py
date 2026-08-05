from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_owned_category(db: Session, category_id: int, user_id: int) -> Category:
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = get_owned_category(db, transaction_data.category_id, current_user.id)

    if category.type == "expense" and transaction_data.amount > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense transactions must have a negative amount"
        )
    if category.type == "income" and transaction_data.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Income transactions must have a positive amount"
        )

    new_transaction = Transaction(
        user_id=current_user.id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None, description="Search in description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    query = query.order_by(Transaction.transaction_date.desc())
    transactions = query.offset(skip).limit(limit).all()
    return transactions


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if transaction_data.category_id is not None:
        get_owned_category(db, transaction_data.category_id, current_user.id)
        transaction.category_id = transaction_data.category_id
    if transaction_data.amount is not None:
        transaction.amount = transaction_data.amount
    if transaction_data.description is not None:
        transaction.description = transaction_data.description
    if transaction_data.transaction_date is not None:
        transaction.transaction_date = transaction_data.transaction_date

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    db.delete(transaction)
    db.commit()
    return None