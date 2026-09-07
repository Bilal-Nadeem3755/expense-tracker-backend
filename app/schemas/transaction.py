from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


# ==========================================
# Transaction Type
# ==========================================

class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


# ==========================================
# Create Transaction
# ==========================================

class TransactionCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        decimal_places=2
    )

    type: TransactionType

    description: str | None = None

    category_id: int


# ==========================================
# Update Transaction
# ==========================================

class TransactionUpdate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        decimal_places=2
    )

    type: TransactionType

    description: str | None = None

    category_id: int


# ==========================================
# Transaction Response
# ==========================================

class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    type: TransactionType
    description: str | None
    created_at: datetime
    user_id: int
    category_id: int

    class Config:
        from_attributes = True