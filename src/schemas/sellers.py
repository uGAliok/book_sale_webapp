from pydantic import BaseModel, EmailStr
from typing import List, Optional
from .books import BookResponse

class SellerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class SellerCreate(SellerBase):
    pass

class SellerResponse(SellerBase):
    id: int
    books: List[BookResponse] = []

    class Config:
        from_attributes = True  # Используется для конвертации SQLAlchemy-моделей в Pydantic

class SellerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
