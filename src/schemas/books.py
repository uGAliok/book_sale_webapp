from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = ["IncomingBook", "ReturnedBook", "ReturnedAllbooks", "BookResponse"]


# Базовый класс "Книги", содержащий поля, которые есть во всех классах-наследниках.
class BaseBook(BaseModel):
    title: str
    author: str
    year: int


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
class IncomingBook(BaseBook):
    pages: int = Field(default=150, alias="count_pages")
    seller_id: int

    @field_validator("year")  # Валидатор, проверяет что дата не слишком древняя
    @staticmethod
    def validate_year(val: int):
        if val < 2020:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedBook(BaseBook):
    id: int
    pages: int
    seller_id: Optional[int] = None


# Класс для возврата массива объектов "Книга"
class ReturnedAllbooks(BaseModel):
    books: List[ReturnedBook]


class BookResponse(BaseBook):
    id: int
    pages: int = Field(default=150, alias="count_pages")
    seller_id: Optional[int] = None
    
    class Config:
        from_attributes = True