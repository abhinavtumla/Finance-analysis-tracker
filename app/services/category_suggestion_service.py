import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction

MIN_WORD_LENGTH = 3


def suggest_category(db: Session, user_id: int, description: str) -> Category | None:
    """Guess a category for `description` from the user's own transaction history.

    Tokenizes the description and looks for past transactions (for this user)
    that share at least one word, then returns whichever category shows up
    most often among those matches. Returns None if there's no usable
    description or no historical overlap at all.
    """
    words = _tokenize(description)
    if not words:
        return None

    past_transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.description.isnot(None))
        .all()
    )

    votes = Counter()
    for transaction in past_transactions:
        if words & _tokenize(transaction.description):
            votes[transaction.category_id] += 1

    if not votes:
        return None

    best_category_id, _ = votes.most_common(1)[0]
    return db.query(Category).filter(Category.id == best_category_id, Category.user_id == user_id).first()


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= MIN_WORD_LENGTH}
