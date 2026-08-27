import csv
import io
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionImportRowResult,
    TransactionImportSummary,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

MAX_IMPORT_ROWS = 1000
REQUIRED_IMPORT_COLUMNS = {"date", "description", "category", "amount"}


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


@router.post("/import", response_model=TransactionImportSummary)
def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a .csv file")

    try:
        raw_text = file.file.read().decode("utf-8-sig")  # utf-8-sig strips Excel's BOM, if present
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be UTF-8 encoded text")

    reader = csv.DictReader(io.StringIO(raw_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file has no header row")

    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    missing_columns = REQUIRED_IMPORT_COLUMNS - set(reader.fieldnames)
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required column(s): {', '.join(sorted(missing_columns))}"
        )

    # Drop fully-blank rows (a trailing newline in the file becomes one of these).
    rows = [row for row in reader if any((value or "").strip() for value in row.values())]
    if len(rows) > MAX_IMPORT_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV has {len(rows)} rows, which exceeds the {MAX_IMPORT_ROWS}-row limit per import"
        )

    # Loaded once up front instead of querying per row.
    categories_by_name = {
        category.name.strip().lower(): category
        for category in db.query(Category).filter(Category.user_id == current_user.id).all()
    }

    results: List[TransactionImportRowResult] = []
    imported_count = 0

    for line_number, row in enumerate(rows, start=2):  # data starts on line 2; line 1 is the header
        error = _validate_import_row(row, categories_by_name)
        if error is None:
            category = categories_by_name[(row.get("category") or "").strip().lower()]
            db.add(Transaction(
                user_id=current_user.id,
                category_id=category.id,
                amount=Decimal(row["amount"].strip()),
                description=(row.get("description") or "").strip() or None,
                transaction_date=date.fromisoformat(row["date"].strip()),
            ))
            imported_count += 1
        results.append(TransactionImportRowResult(
            row_number=line_number,
            status="failed" if error else "imported",
            error=error,
        ))

    db.commit()

    return TransactionImportSummary(
        total_rows=len(rows),
        imported_count=imported_count,
        failed_count=len(rows) - imported_count,
        results=results,
    )


def _validate_import_row(row: dict, categories_by_name: dict) -> Optional[str]:
    """Return an error message if the row can't be imported, or None if it's valid."""
    category_name = (row.get("category") or "").strip()
    category = categories_by_name.get(category_name.lower())
    if category is None:
        return f"Unknown category '{category_name}'"

    try:
        amount = Decimal((row.get("amount") or "").strip())
    except InvalidOperation:
        return f"Invalid amount '{row.get('amount')}'"

    if category.type == "expense" and amount > 0:
        return "Expense transactions must have a negative amount"
    if category.type == "income" and amount < 0:
        return "Income transactions must have a positive amount"

    try:
        date.fromisoformat((row.get("date") or "").strip())
    except ValueError:
        return f"Invalid date '{row.get('date')}' (expected YYYY-MM-DD)"

    return None


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