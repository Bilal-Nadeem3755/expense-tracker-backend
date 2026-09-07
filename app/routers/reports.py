from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import (
    ReportSummary,
    CategoryBreakdown,
    MonthlyTrend,
    ReportsResponse,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
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
# Helper - Date Range
# ==========================================

def get_date_range(
    start_date: date | None,
    end_date: date | None,
):
    """
    Convert date values into datetime range.

    Example:

    start_date = 2026-09-01
    end_date   = 2026-09-30

    becomes:

    2026-09-01 00:00:00
    2026-10-01 00:00:00

    Using an exclusive end date prevents missing
    transactions that occur later on the end date.
    """

    if start_date is None:
        start_date = date.today().replace(
            day=1
        )

    if end_date is None:
        # Last day of current month
        if start_date.month == 12:
            next_month = date(
                start_date.year + 1,
                1,
                1
            )
        else:
            next_month = date(
                start_date.year,
                start_date.month + 1,
                1
            )

        end_date = next_month - timedelta(days=1)

    if start_date > end_date:
        raise ValueError(
            "start_date cannot be greater than end_date."
        )

    start_datetime = datetime.combine(
        start_date,
        datetime.min.time()
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time()
    )

    return (
        start_date,
        end_date,
        start_datetime,
        end_datetime,
    )


# ==========================================
# Report Summary
# ==========================================

@router.get(
    "/summary",
    response_model=ReportSummary
)
def get_report_summary(
    start_date: date | None = Query(
        default=None
    ),
    end_date: date | None = Query(
        default=None
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        (
            _,
            _,
            start_datetime,
            end_datetime,
        ) = get_date_range(
            start_date,
            end_date,
        )

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ------------------------------------------
    # Base query
    # ------------------------------------------

    base_filter = [
        Transaction.user_id == current_user.id,
        Transaction.created_at >= start_datetime,
        Transaction.created_at < end_datetime,
    ]

    # ------------------------------------------
    # Total Income
    # ------------------------------------------

    total_income = db.query(
        func.sum(Transaction.amount)
    ).filter(
        *base_filter,
        Transaction.type == "income",
    ).scalar()

    # ------------------------------------------
    # Total Expense
    # ------------------------------------------

    total_expense = db.query(
        func.sum(Transaction.amount)
    ).filter(
        *base_filter,
        Transaction.type == "expense",
    ).scalar()

    # ------------------------------------------
    # Transaction Count
    # ------------------------------------------

    transaction_count = db.query(
        func.count(Transaction.id)
    ).filter(
        *base_filter
    ).scalar()

    total_income = (
        total_income
        if total_income is not None
        else Decimal("0.00")
    )

    total_expense = (
        total_expense
        if total_expense is not None
        else Decimal("0.00")
    )

    transaction_count = (
        transaction_count
        if transaction_count is not None
        else 0
    )

    balance = (
        total_income - total_expense
    )

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "transaction_count": transaction_count,
    }


# ==========================================
# Category Breakdown
# ==========================================

@router.get(
    "/category-breakdown",
    response_model=list[CategoryBreakdown]
)
def get_category_breakdown(
    start_date: date | None = Query(
        default=None
    ),
    end_date: date | None = Query(
        default=None
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        (
            _,
            _,
            start_datetime,
            end_datetime,
        ) = get_date_range(
            start_date,
            end_date,
        )

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    results = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        func.sum(
            Transaction.amount
        ).label("total"),
    ).join(
        Transaction,
        Transaction.category_id == Category.id,
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.created_at >= start_datetime,
        Transaction.created_at < end_datetime,
        Category.user_id == current_user.id,
    ).group_by(
        Category.id,
        Category.name,
    ).order_by(
        func.sum(
            Transaction.amount
        ).desc()
    ).all()

    return [
        {
            "category_id": category_id,
            "category_name": category_name,
            "total": total,
        }
        for (
            category_id,
            category_name,
            total,
        ) in results
    ]


# ==========================================
# Monthly Trends
# ==========================================

@router.get(
    "/monthly-trends",
    response_model=list[MonthlyTrend]
)
def get_monthly_trends(
    year: int = Query(
        ...,
        ge=2000,
        le=2100,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    results = []

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    for month in range(1, 13):

        start_date = datetime(
            year,
            month,
            1,
        )

        if month == 12:

            end_date = datetime(
                year + 1,
                1,
                1,
            )

        else:

            end_date = datetime(
                year,
                month + 1,
                1,
            )

        # --------------------------------------
        # Monthly Income
        # --------------------------------------

        income = db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.created_at >= start_date,
            Transaction.created_at < end_date,
        ).scalar()

        # --------------------------------------
        # Monthly Expense
        # --------------------------------------

        expense = db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.created_at >= start_date,
            Transaction.created_at < end_date,
        ).scalar()

        income = (
            income
            if income is not None
            else Decimal("0.00")
        )

        expense = (
            expense
            if expense is not None
            else Decimal("0.00")
        )

        balance = income - expense

        results.append(
            {
                "month": month,
                "month_name": month_names[
                    month - 1
                ],
                "income": income,
                "expense": expense,
                "balance": balance,
            }
        )

    return results


# ==========================================
# Complete Reports
# ==========================================

@router.get(
    "/",
    response_model=ReportsResponse
)
def get_reports(
    start_date: date | None = Query(
        default=None
    ),
    end_date: date | None = Query(
        default=None
    ),
    year: int | None = Query(
        default=None,
        ge=2000,
        le=2100,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Returns a complete report containing:

    - Summary
    - Category breakdown
    - Monthly trends
    """

    # ------------------------------------------
    # Resolve date range
    # ------------------------------------------

    try:
        (
            resolved_start_date,
            resolved_end_date,
            start_datetime,
            end_datetime,
        ) = get_date_range(
            start_date,
            end_date,
        )

    except ValueError as error:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ==========================================
    # Summary
    # ==========================================

    base_filter = [
        Transaction.user_id == current_user.id,
        Transaction.created_at >= start_datetime,
        Transaction.created_at < end_datetime,
    ]

    total_income = db.query(
        func.sum(Transaction.amount)
    ).filter(
        *base_filter,
        Transaction.type == "income",
    ).scalar()

    total_expense = db.query(
        func.sum(Transaction.amount)
    ).filter(
        *base_filter,
        Transaction.type == "expense",
    ).scalar()

    transaction_count = db.query(
        func.count(Transaction.id)
    ).filter(
        *base_filter
    ).scalar()

    total_income = (
        total_income
        if total_income is not None
        else Decimal("0.00")
    )

    total_expense = (
        total_expense
        if total_expense is not None
        else Decimal("0.00")
    )

    transaction_count = (
        transaction_count
        if transaction_count is not None
        else 0
    )

    balance = total_income - total_expense

    # ==========================================
    # Category Breakdown
    # ==========================================

    category_results = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        func.sum(
            Transaction.amount
        ).label("total"),
    ).join(
        Transaction,
        Transaction.category_id == Category.id,
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.created_at >= start_datetime,
        Transaction.created_at < end_datetime,
        Category.user_id == current_user.id,
    ).group_by(
        Category.id,
        Category.name,
    ).order_by(
        func.sum(
            Transaction.amount
        ).desc()
    ).all()

    category_breakdown = [
        {
            "category_id": category_id,
            "category_name": category_name,
            "total": total,
        }
        for (
            category_id,
            category_name,
            total,
        ) in category_results
    ]

    # ==========================================
    # Monthly Trends
    # ==========================================

    trend_year = (
        year
        if year is not None
        else resolved_start_date.year
    )

    monthly_trends = []

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    for month in range(1, 13):

        month_start = datetime(
            trend_year,
            month,
            1,
        )

        if month == 12:

            month_end = datetime(
                trend_year + 1,
                1,
                1,
            )

        else:

            month_end = datetime(
                trend_year,
                month + 1,
                1,
            )

        # --------------------------------------
        # Income
        # --------------------------------------

        income = db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.created_at >= month_start,
            Transaction.created_at < month_end,
        ).scalar()

        # --------------------------------------
        # Expense
        # --------------------------------------

        expense = db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.created_at >= month_start,
            Transaction.created_at < month_end,
        ).scalar()

        income = (
            income
            if income is not None
            else Decimal("0.00")
        )

        expense = (
            expense
            if expense is not None
            else Decimal("0.00")
        )

        monthly_trends.append(
            {
                "month": month,
                "month_name": month_names[
                    month - 1
                ],
                "income": income,
                "expense": expense,
                "balance": income - expense,
            }
        )

    return {
        "start_date": resolved_start_date,
        "end_date": resolved_end_date,
        "summary": {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "transaction_count": transaction_count,
        },
        "category_breakdown": category_breakdown,
        "monthly_trends": monthly_trends,
    }