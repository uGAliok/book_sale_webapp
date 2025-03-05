import pytest
from sqlalchemy import select
from src.models.books import Book
from src.models.sellers import Seller
from fastapi import status
from icecream import ic


# Тест на ручку создающую книгу
@pytest.mark.asyncio
async def test_create_book(async_client, create_seller):
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": create_seller.id
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "id": 1,
        "seller_id": create_seller.id,
    }

@pytest.mark.asyncio
async def test_create_book_with_invalid_seller(async_client, create_seller): 
    data = {
        "title": "Invalid Book",
        "author": "Unknown",
        "count_pages": 100,
        "year": 2025,
        "seller_id": 999
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Seller with id 999 not found"


@pytest.mark.asyncio
async def test_create_book_with_old_year(async_client, create_seller): 
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": create_seller.id,
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio
async def test_get_books(db_session, async_client, create_seller): 
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=create_seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=create_seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/books/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["books"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2001,
                "id": book.id,
                "pages": 104,
                "seller_id": create_seller.id,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 1997,
                "id": book_2.id,
                "pages": 104,
                "seller_id": create_seller.id,
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio
async def test_get_single_book(db_session, async_client, create_seller): 
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=create_seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=create_seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": create_seller.id,
    }


# Тест на ручку обновления книги
@pytest.mark.asyncio
async def test_update_book(db_session, async_client, create_seller): 
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=create_seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/books/{book.id}",
        json={
            "title": "Mziri",
            "author": "Lermontov",
            "pages": 100,
            "year": 2007,
            "id": book.id,
            "seller_id": create_seller.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 100
    assert res.year == 2007
    assert res.id == book.id


@pytest.mark.asyncio
async def test_delete_book(db_session, async_client, create_seller): 
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=create_seller.id)

    db_session.add(book)
    await db_session.flush()
    ic(book.id)

    response = await async_client.delete(f"/api/v1/books/{book.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio
async def test_delete_book_with_invalid_book_id(db_session, async_client, create_seller): 
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=create_seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/books/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
