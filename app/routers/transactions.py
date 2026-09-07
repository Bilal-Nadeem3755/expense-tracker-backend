from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.database import SessionLocal
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
)
from app.auth import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
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
# Create Transaction
# ==========================================

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if category belongs to current user
    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    transaction = Transaction(
        amount=transaction_data.amount,
        type=transaction_data.type,
        description=transaction_data.description,
        user_id=current_user.id,
        category_id=transaction_data.category_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


# ==========================================
# Get All Transactions
# ==========================================

@router.get(
    "/",
    response_model=list[TransactionResponse]
)
def get_transactions(
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    # ==========================================
    # Filter by transaction type
    # ==========================================

    if type:
        query = query.filter(
            Transaction.type == type
        )

    # ==========================================
    # Filter by category
    # ==========================================

    if category_id:
        query = query.filter(
            Transaction.category_id == category_id
        )

    # ==========================================
    # Filter by start date
    # ==========================================

    if start_date:
        query = query.filter(
            Transaction.created_at >= start_date
        )

    # ==========================================
    # Filter by end date
    # ==========================================

    if end_date:
        query = query.filter(
            Transaction.created_at <= end_date
        )

    return query.order_by(
        Transaction.created_at.desc()
    ).all()


# ==========================================
# Get Single Transaction
# ==========================================

@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse
)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


# ==========================================
# Update Transaction
# ==========================================

@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse
)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    # Check if new category belongs to current user
    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    transaction.amount = transaction_data.amount
    transaction.type = transaction_data.type
    transaction.description = transaction_data.description
    transaction.category_id = transaction_data.category_id

    db.commit()
    db.refresh(transaction)

    return transaction


# ==========================================
# Delete Transaction
# ==========================================

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }