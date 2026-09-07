from pydantic import BaseModel


# ==========================================
# Create Category
# ==========================================

class CategoryCreate(BaseModel):
    name: str


# ==========================================
# Update Category
# ==========================================

class CategoryUpdate(BaseModel):
    name: str


# ==========================================
# Category Response
# ==========================================

class CategoryResponse(BaseModel):
    id: int
    name: str
    user_id: int

    class Config:
        from_attributes = True