from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, only_admin
from app.models.ledger import LedgerEntry
from app.models.user import User
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryRead, LedgerSummary
from app.services.ledger_service import (
    can_create_manual_entry,
    create_ledger_entry,
    get_all_ledger_entries,
    get_client_ledger_entries,
    get_ledger_summary,
)

router = APIRouter()


@router.get("/client/{client_id}", response_model=list[LedgerEntryRead])
def read_client_ledger(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[LedgerEntry]:
    return get_client_ledger_entries(db, client_id)


@router.get("/client/{client_id}/summary", response_model=LedgerSummary)
def read_client_ledger_summary(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> dict:
    return get_ledger_summary(db, client_id)


@router.get("/all", response_model=list[LedgerEntryRead], dependencies=[Depends(only_admin)])
def read_all_ledger(db: Session = Depends(get_db)) -> list[LedgerEntry]:
    return get_all_ledger_entries(db)


@router.post("/manual-entry", response_model=LedgerEntryRead, status_code=status.HTTP_201_CREATED)
def create_manual_ledger_entry(
    payload: LedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> LedgerEntry:
    if not can_create_manual_entry(current_user, payload):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manual ledger entry is not allowed.")
    return create_ledger_entry(db, payload, current_user)
