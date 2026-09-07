from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class ExpenseByCategory(BaseModel):
    category: str
    total: Decimal


class MonthlyDashboard(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal