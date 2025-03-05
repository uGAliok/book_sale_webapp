import pytest
import random
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.sellers import Seller
from fastapi import status


# создание продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {
        "first_name": "Uliana",
        "last_name": "Gagarina",
        "email": f"test{random.randint(1, 100000)}@example.com"
    }
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()
    result_data.pop("books", None)
    assert "id" in result_data
    result_data.pop("id")

    assert result_data == {
        "first_name": "Uliana",
        "last_name": "Gagarina",
        "email": data["email"]
    }


# тест на повторяющеееся email
@pytest.mark.asyncio
async def test_create_seller_duplicate_email(async_client, db_session):
    email = "duplicate@example.com"
    seller = Seller(first_name="Test", last_name="Seller", email=email)
    db_session.add(seller)
    await db_session.flush()

    data = {
        "first_name": "Another",
        "last_name": "Seller",
        "email": email
    }
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# получение всех продавцов
@pytest.mark.asyncio
async def test_get_sellers(async_client, db_session):
    seller1 = Seller(first_name="Alice", last_name="Smith", email=f"alice{random.randint(1, 100000)}@example.com")
    seller2 = Seller(first_name="Bob", last_name="Johnson", email=f"bob{random.randint(1, 100000)}@example.com")

    db_session.add_all([seller1, seller2])
    await db_session.flush()

    response = await async_client.get("/api/v1/seller/")
    assert response.status_code == status.HTTP_200_OK

    sellers_data = response.json()
    assert len(sellers_data) == 2


# получение продавца по `id`
@pytest.mark.asyncio
async def test_get_seller_by_id(async_client, db_session):
    seller = Seller(first_name="Charlie", last_name="Brown", email=f"charlie{random.randint(1, 100000)}@example.com")

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/seller/{seller.id}")
    assert response.status_code == status.HTTP_200_OK

    seller_data = response.json()
    assert seller_data["id"] == seller.id
    assert seller_data["email"] == seller.email


# тест на ошибку при запросе несуществующего продавца
@pytest.mark.asyncio
async def test_get_nonexistent_seller(async_client):
    response = await async_client.get("/api/v1/seller/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    

# тест на ошибку при обновлении несуществующего продавца
@pytest.mark.asyncio
async def test_update_nonexistent_seller(async_client):
    updated_data = {
        "first_name": "Nobody",
        "last_name": "Nonexistent",
        "email": "nonexistent@example.com"
    }
    response = await async_client.put("/api/v1/seller/9999", json=updated_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND


# удаление продавца
@pytest.mark.asyncio
async def test_delete_seller(async_client, db_session):
    seller = Seller(first_name="Eve", last_name="Taylor", email=f"eve{random.randint(1, 100000)}@example.com")

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/seller/{seller.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    result = await db_session.execute(select(Seller).where(Seller.id == seller.id))
    deleted_seller = result.scalars().first()
    assert deleted_seller is None