from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sellers import Seller


class Book(BaseModel):
    __tablename__ = "books_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int]
    pages: Mapped[int]
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers_table.id", ondelete="CASCADE"), nullable=True)

    seller: Mapped["Seller"] = relationship("Seller", back_populates="books")
