from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def _normalize_hsn_code(hsn_code: str | None) -> str | None:
    if hsn_code is None:
        return None
    normalized = hsn_code.strip().upper()
    return normalized or None


def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(
        product_name=payload.product_name,
        hsn_code=_normalize_hsn_code(payload.hsn_code),
        default_rate=payload.default_rate,
        gst_rate=payload.gst_rate,
        unit=payload.unit,
        is_active=payload.is_active,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session, search: str | None = None) -> list[Product]:
    statement = select(Product).order_by(Product.product_name.asc())
    if search:
        search_term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Product.product_name.ilike(search_term),
                Product.hsn_code.ilike(search_term),
            )
        )
    return list(db.scalars(statement).all())


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    update_data = payload.model_dump(exclude_unset=True)
    if "hsn_code" in update_data:
        update_data["hsn_code"] = _normalize_hsn_code(update_data["hsn_code"])

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()
