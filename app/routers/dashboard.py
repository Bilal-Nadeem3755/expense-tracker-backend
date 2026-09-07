from decimal import Decimal
from fastapi import APIRouter, Depends, Query

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from sqlalchemy import func
from app.models.category import Category
from app.schemas.dashboard import (
    DashboardSummary,
    ExpenseByCategory,
    MonthlyDashboard,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ==========================================
# Database Dependency
# ==========================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==========================================
# Dashboard Summary
# ==========================================

@router.get(
    "/summary",
    response_model=DashboardSummary
)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_income = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income"
    ).scalar()

    total_expense = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense"
    ).scalar()

    total_income = total_income or Decimal("0.00")
    total_expense = total_expense or Decimal("0.00")

    balance = total_income - total_expense

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }
    
# ==========================================
# Expense By Category
# ==========================================

@router.get(
    "/expense-by-category",
    response_model=list[ExpenseByCategory]
)
def get_expense_by_category(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = db.query(
        Category.name.label("category"),
        func.sum(Transaction.amount).label("total")
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense"
    ).group_by(
        Category.id,
        Category.name
    ).all()

    return [
        {
            "category": category,
            "total": total
        }
        for category, total in results
    ]
    
# MONTHLY EXPENSE    
    
@router.get(
    "/monthly",
    response_model=MonthlyDashboard
)
def get_monthly_dashboard(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime

    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    total_income = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date
    ).scalar()

    total_expense = db.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date
    ).scalar()

    total_income = total_income or Decimal("0.00")
    total_expense = total_expense or Decimal("0.00")

    balance = total_income - total_expense

    return {
        "year": year,
        "month": month,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }    