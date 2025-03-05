# Для импорта из корневого модуля
# import sys
# sys.path.append("..")
# from main import app

from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.sellers import Seller
from src.models.books import Book
from src.schemas import IncomingBook, ReturnedAllbooks, ReturnedBook
from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session

books_router = APIRouter(tags=["books"], prefix="/books")

# CRUD - Create, Read, Update, Delete

DBSession = Annotated[AsyncSession, Depends(get_async_session)]

# Ручка для создания записи о книге в БД. Возвращает созданную книгу.
# @books_router.post("/books/", status_code=status.HTTP_201_CREATED)
@books_router.post(
    "/", response_model=ReturnedBook, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_book(
    book: IncomingBook,
    session: DBSession,
):  # прописываем модель валидирующую входные данные
    # session = get_async_session() вместо этого мы используем иньекцию зависимостей DBSession

    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    result = await session.execute(select(Seller).where(Seller.id == book.seller_id))
    seller = result.scalars().first()

    if not seller: 
        # просто return status.HTTP не работает,тк сервер крашится
        raise HTTPException(status_code=400, detail=f"Seller with id {book.seller_id} not found")
    
    new_book = Book(
        **{
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "pages": book.pages,
            "seller_id": book.seller_id
        }
    )

    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)
    return new_book


# Ручка, возвращающая все книги
@books_router.get("/", response_model=ReturnedAllbooks)
async def get_all_books(session: DBSession):
    # Хотим видеть формат
    # books: [{"id": 1, "title": "blabla", ...., "year": 2023},{...}]
    query = select(Book).options(selectinload(Book.seller))  # SELECT * FROM book
    result = await session.execute(query)
    books = result.scalars().all()
    return {"books": books}


# Ручка для получения книги по ее ИД
@books_router.get("/{book_id}", response_model=ReturnedBook)
async def get_book(book_id: int, session: DBSession):
    result = await session.execute(
        select(Book).options(selectinload(Book.seller)).where(Book.id == book_id)
    )
    book = result.scalars().first()

    if not book:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return book


# Ручка для удаления книги
@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: DBSession):
    result = await session.execute(select(Book).where(Book.id == book_id))
    deleted_book = result.scalars().first()
    ic(deleted_book)  # Красивая и информативная замена для print. Полезна при отладке.
    if deleted_book:
        await session.delete(deleted_book)
        await session.commit()
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для обновления данных о книге
@books_router.put("/{book_id}", response_model=ReturnedBook)
async def update_book(book_id: int, new_book_data: ReturnedBook, session: DBSession):
    result = await session.execute(select(Book).where(Book.id == book_id))
    updated_book = result.scalars().first()

    if not updated_book:
        return status.HTTP_404_NOT_FOUND

    if new_book_data.seller_id:
        seller_result = await session.execute(select(Seller).where(Seller.id == new_book_data.seller_id))
        seller = seller_result.scalars().first()

        if not seller:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

        updated_book.seller_id = new_book_data.seller_id

    updated_book.author = new_book_data.author
    updated_book.title = new_book_data.title
    updated_book.year = new_book_data.year
    updated_book.pages = new_book_data.pages

    await session.commit()
    await session.refresh(updated_book)

    return updated_book