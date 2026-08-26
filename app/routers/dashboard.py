from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.core.dependencies import get_current_user
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    month: int = Query(default=None),
    year: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    target_month = month if month is not None else today.month
    target_year = year if year is not None else today.year

    summary = get_dashboard_summary(db, current_user.id, target_month, target_year)
    return summary