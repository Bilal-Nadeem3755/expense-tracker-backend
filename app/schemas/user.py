from pydantic import BaseModel, EmailStr, Field


# ==========================================
# Register
# ==========================================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


# ==========================================
# Login
# ==========================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ==========================================
# User Response
# ==========================================

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


# ==========================================
# Token Response
# ==========================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ==========================================
# Update Profile
# ==========================================

class ProfileUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    email: EmailStr


# ==========================================
# Change Password
# ==========================================

class PasswordChange(BaseModel):
    current_password: str = Field(
        ...,
        min_length=1
    )

    new_password: str = Field(
        ...,
        min_length=6
    )

    confirm_password: str = Field(
        ...,
        min_length=6
    )