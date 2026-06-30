from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import (
    create_product,
    delete_product,
    get_product_by_id,
    list_products,
    update_product,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(manager_or_admin)],
)
def create_new_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    return create_product(db, payload)


@router.get("", response_model=list[ProductRead])
def read_products(
    search: str | None = Query(default=None, description="Search by product name or HSN code."),
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[Product]:
    return list_products(db, search)


@router.get("/{product_id}", response_model=ProductRead)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> Product:
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.put("/{product_id}", response_model=ProductRead, dependencies=[Depends(manager_or_admin)])
def update_existing_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> Product:
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return update_product(db, product, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(manager_or_admin)])
def delete_existing_product(product_id: int, db: Session = Depends(get_db)) -> Response:
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    delete_product(db, product)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
