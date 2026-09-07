from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import SessionLocal
from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    ProfileUpdate,
    PasswordChange,
)

from app.utils import hash_password, verify_password

from app.auth import (
    create_access_token,
    get_current_user,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
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
# Register
# ==========================================

@router.post(
    "/",
    response_model=UserResponse
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # ------------------------------------------
    # Check duplicate email
    # ------------------------------------------

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered."
        )

    # ------------------------------------------
    # Hash password
    # ------------------------------------------

    hashed_password = hash_password(
        user_data.password
    )

    # ------------------------------------------
    # Create user
    # ------------------------------------------

    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ==========================================
# Login
# ==========================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # ------------------------------------------
    # Create JWT
    # ------------------------------------------

    access_token = create_access_token(
        user.id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# Get Current User
# ==========================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

# ==========================================
# Update Profile
# ==========================================

@router.put(
    "/profile",
    response_model=UserResponse
)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    # ------------------------------------------
    # Clean name
    # ------------------------------------------

    name = profile_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty."
        )

    # ------------------------------------------
    # Check duplicate email
    # ------------------------------------------

    existing_user = db.query(User).filter(
        User.email == profile_data.email,
        User.id != current_user.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered."
        )

    # ------------------------------------------
    # Get user from current database session
    # ------------------------------------------

    user = db.query(User).filter(
        User.id == current_user.id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # ------------------------------------------
    # Update profile
    # ------------------------------------------

    user.name = name
    user.email = profile_data.email

    db.commit()

    # ------------------------------------------
    # Refresh user
    # ------------------------------------------

    db.refresh(user)

    return user


# ==========================================
# Change Password
# ==========================================

@router.put("/password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    # ------------------------------------------
    # Get user from current database session
    # ------------------------------------------

    user = db.query(User).filter(
        User.id == current_user.id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # ------------------------------------------
    # Verify current password
    # ------------------------------------------

    if not verify_password(
        password_data.current_password,
        user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    # ------------------------------------------
    # Check new password confirmation
    # ------------------------------------------

    if (
        password_data.new_password
        != password_data.confirm_password
    ):
        raise HTTPException(
            status_code=400,
            detail="New passwords do not match."
        )

    # ------------------------------------------
    # Prevent same password
    # ------------------------------------------

    if verify_password(
        password_data.new_password,
        user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the current password."
        )

    # ------------------------------------------
    # Hash new password
    # ------------------------------------------

    user.password = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully."
    }


# ==========================================
# Logout
# ==========================================

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "Successfully logged out"
    }