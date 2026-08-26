from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.goal import SavingsGoal
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalUpdate, GoalContribution, GoalResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/goals", tags=["Savings Goals"])


def build_goal_response(goal: SavingsGoal) -> dict:
    progress = float((goal.current_amount / goal.target_amount) * 100) if goal.target_amount > 0 else 0.0
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "target_date": goal.target_date,
        "progress_percentage": round(min(progress, 100.0), 2),
        "is_completed": goal.current_amount >= goal.target_amount,
        "created_at": goal.created_at,
    }


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_goal = SavingsGoal(
        user_id=current_user.id,
        name=goal_data.name,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount,
        target_date=goal_data.target_date
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return build_goal_response(new_goal)


@router.get("/", response_model=List[GoalResponse])
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()
    return [build_goal_response(g) for g in goals]


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    if goal_data.name is not None:
        goal.name = goal_data.name
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.target_date is not None:
        goal.target_date = goal_data.target_date

    db.commit()
    db.refresh(goal)
    return build_goal_response(goal)


@router.post("/{goal_id}/contribute", response_model=GoalResponse)
def contribute_to_goal(
    goal_id: int,
    contribution: GoalContribution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    if contribution.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contribution amount must be positive"
        )

    goal.current_amount = goal.current_amount + contribution.amount
    db.commit()
    db.refresh(goal)
    return build_goal_response(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return None