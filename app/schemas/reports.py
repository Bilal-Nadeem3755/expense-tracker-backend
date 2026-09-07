from datetime import date
from decimal import Decimal

from pydantic import BaseModel


# ==========================================
# Report Summary
# ==========================================

class ReportSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int


# ==========================================
# Category Breakdown
# ==========================================

class CategoryBreakdown(BaseModel):
    category_id: int
    category_name: str
    total: Decimal


# ==========================================
# Monthly Trend
# ==========================================

class MonthlyTrend(BaseModel):
    month: int
    month_name: str
    income: Decimal
    expense: Decimal
    balance: Decimal


# ==========================================
# Reports Response
# ==========================================

class ReportsResponse(BaseModel):
    start_date: date
    end_date: date
    summary: ReportSummary
    category_breakdown: list[CategoryBreakdown]
    monthly_trends: list[MonthlyTrend]