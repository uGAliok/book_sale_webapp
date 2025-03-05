from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from icecream import ic
from src.configurations import get_async_session
from src.models.sellers import Seller
from src.schemas.sellers import SellerCreate, SellerResponse, SellerUpdate

seller_router = APIRouter(prefix="/seller", tags=["Sellers"])

# Создать нового продавца
@seller_router.post("/", response_model=SellerResponse, status_code=status.HTTP_201_CREATED
)
async def create_seller(seller: SellerCreate, session: AsyncSession = Depends(get_async_session)):
    print("Полученные данные:", seller.model_dump())
    result = await session.execute(select(Seller).where(Seller.email == seller.email))
    existing_seller = result.scalars().first()
    
    if existing_seller: # опять же с return.status работает некорректно
        raise HTTPException(400, detail="Seller with this email already exists")
    
    new_seller = Seller(
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email
    )

    session.add(new_seller)
    await session.commit()
    await session.refresh(new_seller)

    # чтобы избежать ошибки MissingGreenlet
    result = await session.execute(
        select(Seller).options(selectinload(Seller.books)).where(Seller.id == new_seller.id)
    )
    new_seller = result.scalars().first()

    return new_seller

# Получить всех продавцов
@seller_router.get("/", response_model=List[SellerResponse])
async def get_all_sellers(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Seller).options(selectinload(Seller.books))
    )
    sellers = result.scalars().all()
    return sellers

# Получить одного продавца (с его книгами)
@seller_router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller(seller_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Seller).options(selectinload(Seller.books)).where(Seller.id == seller_id)
    )
    seller = result.scalars().first()

    if not seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return seller

# Обновить данные продавца
@seller_router.put("/{seller_id}", response_model=SellerResponse)
async def update_seller(seller_id: int, seller_update: SellerUpdate, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Seller).options(selectinload(Seller.books)).where(Seller.id == seller_id)
    )
    existing_seller = result.scalars().first()

    if not existing_seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    existing_seller.first_name = seller_update.first_name or existing_seller.first_name
    existing_seller.last_name = seller_update.last_name or existing_seller.last_name
    existing_seller.email = seller_update.email or existing_seller.email

    await session.commit()
    await session.refresh(existing_seller)
    return existing_seller


# Удалить продавца (вместе с книгами)
@seller_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Seller).where(Seller.id == seller_id)
    )
    seller = result.scalars().first()

    if not seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    await session.delete(seller)
    await session.commit()
    return {"message": "Seller deleted"}