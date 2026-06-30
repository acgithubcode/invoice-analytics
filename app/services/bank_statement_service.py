import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bank_statement import BankStatement, BankStatementStatus
from app.models.client import Client
from app.models.user import User
from app.schemas.bank_statement import BankStatementCreate
from app.services.ledger_service import create_bank_statement_ledger_entry


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _decimal(value: str | None) -> Decimal:
    cleaned = _clean(value)
    if cleaned is None:
        return Decimal("0.00")
    cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc


def _date(value: str | None) -> date:
    cleaned = _clean(value)
    if cleaned is None:
        raise ValueError("transaction_date is required")
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date value: {value}")


def _first(row: dict[str, str], *keys: str) -> str | None:
    normalized = {key.strip().lower().replace(" ", "_"): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(key)
        if value is not None:
            return value
    return None


def get_bank_statement_by_id(db: Session, statement_id: int) -> BankStatement | None:
    return db.get(BankStatement, statement_id)


def get_bank_statement_by_reference_no(db: Session, reference_no: str | None) -> BankStatement | None:
    if not reference_no:
        return None
    return db.scalar(select(BankStatement).where(BankStatement.reference_no == reference_no.strip()))


def create_bank_statement(db: Session, payload: BankStatementCreate, current_user: User) -> BankStatement:
    reference_no = payload.reference_no.strip() if payload.reference_no else None
    if get_bank_statement_by_reference_no(db, reference_no):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reference number already exists.")

    statement = BankStatement(
        transaction_date=payload.transaction_date,
        description=payload.description,
        reference_no=reference_no,
        debit=payload.debit,
        credit=payload.credit,
        balance=payload.balance,
        status=BankStatementStatus.unmatched,
        created_by_user_id=current_user.id,
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return statement


async def import_bank_statement_csv(db: Session, file: UploadFile, current_user: User) -> dict:
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    imported = 0
    skipped_duplicates = 0
    errors: list[str] = []

    for index, row in enumerate(reader, start=2):
        try:
            reference_no = _clean(_first(row, "reference_no", "reference", "transaction_no", "utr", "cheque_no"))
            if reference_no and get_bank_statement_by_reference_no(db, reference_no):
                skipped_duplicates += 1
                continue
            payload = BankStatementCreate(
                transaction_date=_date(_first(row, "transaction_date", "date", "txn_date")),
                description=_clean(_first(row, "description", "narration", "remarks")),
                reference_no=reference_no,
                debit=_decimal(_first(row, "debit", "withdrawal", "withdrawals")),
                credit=_decimal(_first(row, "credit", "deposit", "deposits")),
                balance=_decimal(_first(row, "balance", "closing_balance")),
            )
            statement = BankStatement(
                transaction_date=payload.transaction_date,
                description=payload.description,
                reference_no=payload.reference_no,
                debit=payload.debit,
                credit=payload.credit,
                balance=payload.balance,
                status=BankStatementStatus.unmatched,
                created_by_user_id=current_user.id,
            )
            db.add(statement)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {index}: {exc}")

    db.commit()
    return {"imported": imported, "skipped_duplicates": skipped_duplicates, "errors": errors}


def list_bank_statements(db: Session) -> list[BankStatement]:
    return list(db.scalars(select(BankStatement).order_by(BankStatement.transaction_date.desc(), BankStatement.id.desc())).all())


def match_bank_statement_client(db: Session, statement: BankStatement, client_id: int) -> BankStatement:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    statement.matched_client_id = client_id
    db.commit()
    db.refresh(statement)
    return statement


def create_ledger_from_bank_statement(db: Session, statement: BankStatement, current_user: User) -> BankStatement:
    if statement.matched_client_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bank statement is not matched with a client.")
    if statement.matched_ledger_entry_id is not None:
        return statement
    entry = create_bank_statement_ledger_entry(
        db,
        client_id=statement.matched_client_id,
        bank_statement_id=statement.id,
        transaction_date=statement.transaction_date,
        reference_no=statement.reference_no,
        description=statement.description,
        debit=statement.debit,
        credit=statement.credit,
        current_user=current_user,
    )
    db.flush()
    statement.matched_ledger_entry_id = entry.id
    statement.status = BankStatementStatus.matched
    db.commit()
    db.refresh(statement)
    return statement
