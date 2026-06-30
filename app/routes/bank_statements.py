from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user
from app.models.bank_statement import BankStatement
from app.models.user import User
from app.schemas.bank_statement import (
    BankStatementCreate,
    BankStatementImportResult,
    BankStatementMatchClient,
    BankStatementRead,
)
from app.services.bank_statement_service import (
    create_bank_statement,
    create_ledger_from_bank_statement,
    get_bank_statement_by_id,
    import_bank_statement_csv,
    list_bank_statements,
    match_bank_statement_client,
)

router = APIRouter()


@router.post("/manual", response_model=BankStatementRead, status_code=status.HTTP_201_CREATED)
def create_manual_bank_statement(
    payload: BankStatementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> BankStatement:
    return create_bank_statement(db, payload, current_user)


@router.post("/import-csv", response_model=BankStatementImportResult)
async def upload_bank_statement_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> dict:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported.")
    return await import_bank_statement_csv(db, file, current_user)


@router.get("", response_model=list[BankStatementRead])
def read_bank_statements(
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[BankStatement]:
    return list_bank_statements(db)


@router.post("/{statement_id}/match-client", response_model=BankStatementRead)
def match_statement_with_client(
    statement_id: int,
    payload: BankStatementMatchClient,
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> BankStatement:
    statement = get_bank_statement_by_id(db, statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank statement not found.")
    return match_bank_statement_client(db, statement, payload.client_id)


@router.post("/{statement_id}/create-ledger-entry", response_model=BankStatementRead)
def create_statement_ledger_entry(
    statement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> BankStatement:
    statement = get_bank_statement_by_id(db, statement_id)
    if statement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank statement not found.")
    return create_ledger_from_bank_statement(db, statement, current_user)
