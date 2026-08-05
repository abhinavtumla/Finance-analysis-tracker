from sqlalchemy.orm import Session
from app.models.category import Category

DEFAULT_CATEGORIES = [
    {"name": "Salary", "type": "income"},
    {"name": "Food", "type": "expense"},
    {"name": "Rent", "type": "expense"},
    {"name": "Transport", "type": "expense"},
    {"name": "Entertainment", "type": "expense"},
    {"name": "Utilities", "type": "expense"},
]

def create_default_categories(db: Session, user_id: int) -> None:
    for cat in DEFAULT_CATEGORIES:
        category = Category(
            user_id=user_id,
            name=cat["name"],
            type=cat["type"],
            is_default=True
        )
        db.add(category)
    db.commit()