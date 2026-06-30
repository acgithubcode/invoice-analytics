from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate


def _normalize_gstin(gstin: str | None) -> str | None:
    if gstin is None:
        return None
    normalized = gstin.strip().upper()
    return normalized or None


def get_client_by_id(db: Session, client_id: int) -> Client | None:
    return db.get(Client, client_id)


def get_client_by_gstin(db: Session, gstin: str | None) -> Client | None:
    normalized_gstin = _normalize_gstin(gstin)
    if normalized_gstin is None:
        return None
    return db.scalar(select(Client).where(Client.gstin == normalized_gstin))


def create_client(db: Session, payload: ClientCreate, current_user: User) -> Client:
    current_balance = payload.current_balance
    if current_balance is None:
        current_balance = payload.opening_balance

    client = Client(
        client_name=payload.client_name,
        billing_name=payload.billing_name,
        address=payload.address,
        gstin=_normalize_gstin(payload.gstin),
        mobile=payload.mobile,
        email=str(payload.email) if payload.email else None,
        opening_balance=payload.opening_balance,
        balance_type=payload.balance_type,
        current_balance=current_balance,
        created_by_user_id=current_user.id,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db: Session, search: str | None = None) -> list[Client]:
    statement = select(Client).order_by(Client.client_name.asc())
    if search:
        statement = statement.where(Client.client_name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(statement).all())


def update_client(db: Session, client: Client, payload: ClientUpdate) -> Client:
    update_data = payload.model_dump(exclude_unset=True)
    if "gstin" in update_data:
        update_data["gstin"] = _normalize_gstin(update_data["gstin"])
    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = str(update_data["email"])

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client: Client) -> None:
    db.delete(client)
    db.commit()
