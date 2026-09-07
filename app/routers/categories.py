from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.category import Category
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.auth import get_current_user


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
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
# Create Category
# ==========================================

@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------
    # Clean Category Name
    # --------------------------------------

    category_name = category_data.name.strip()

    if not category_name:
        raise HTTPException(
            status_code=400,
            detail="Category name is required."
        )

    # --------------------------------------
    # Check Duplicate Category
    # --------------------------------------

    existing_category = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name.ilike(category_name)
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category already exists."
        )

    # --------------------------------------
    # Create Category
    # --------------------------------------

    category = Category(
        name=category_name,
        user_id=current_user.id
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# ==========================================
# Get All Categories
# ==========================================

@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).all()

    return categories


# ==========================================
# Update Category
# ==========================================

@router.put(
    "/{category_id}",
    response_model=CategoryResponse
)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------
    # Find Category
    # --------------------------------------

    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    # --------------------------------------
    # Clean Category Name
    # --------------------------------------

    category_name = category_data.name.strip()

    if not category_name:
        raise HTTPException(
            status_code=400,
            detail="Category name is required."
        )

    # --------------------------------------
    # Check Duplicate Category
    #
    # Exclude the current category itself.
    # --------------------------------------

    existing_category = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.id != category_id,
        Category.name.ilike(category_name)
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category already exists."
        )

    # --------------------------------------
    # Update Category
    # --------------------------------------

    category.name = category_name

    db.commit()
    db.refresh(category)

    return category


# ==========================================
# Delete Category
# ==========================================

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }