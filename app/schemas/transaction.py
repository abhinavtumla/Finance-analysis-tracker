from pydantic import BaseModel, field_validator
from decimal import Decimal
from datetime import date, datetime

class TransactionCreate(BaseModel):
    category_id: int
    amount: Decimal
    description: str | None = None
    transaction_date: date

class TransactionUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = None
    description: str | None = None
    transaction_date: date | None = None

class TransactionResponse(BaseModel):
    id: int
    category_id: int
    amount: Decimal
    description: str | None = None
    transaction_date: date
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionImportRowResult(BaseModel):
    row_number: int  # 1-indexed, counting the header row, so it matches what a spreadsheet shows
    status: str  # "imported" or "failed"
    error: str | None = None

class TransactionImportSummary(BaseModel):
    total_rows: int
    imported_count: int
    failed_count: int
    results: list[TransactionImportRowResult]

class CategorySuggestionRequest(BaseModel):
    description: str

class CategorySuggestionResponse(BaseModel):
    category_id: int | None = None
    category_name: str | None = None