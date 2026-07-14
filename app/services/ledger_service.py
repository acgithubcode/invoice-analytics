from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import BalanceType, Client
from app.models.ledger import LedgerEntry, LedgerEntryType
from app.models.user import Role, User
from app.schemas.ledger import LedgerEntryCreate

MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _opening_balance(client: Client) -> Decimal:
    if client.balance_type == BalanceType.credit:
        return _money(-client.opening_balance)
    return _money(client.opening_balance)


def _get_last_balance(db: Session, client: Client) -> Decimal:
    last_entry = db.scalar(
        select(LedgerEntry)
        .where(LedgerEntry.client_id == client.id)
        .order_by(LedgerEntry.entry_date.desc(), LedgerEntry.id.desc())
        .limit(1)
    )
    if last_entry:
        return _money(last_entry.balance_after_entry)
    return _opening_balance(client)


def get_client_ledger_entries(db: Session, client_id: int) -> list[LedgerEntry]:
    return list(
        db.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.client_id == client_id)
            .order_by(LedgerEntry.entry_date.asc(), LedgerEntry.id.asc())
        ).all()
    )


def get_all_ledger_entries(db: Session) -> list[LedgerEntry]:
    return list(db.scalars(select(LedgerEntry).order_by(LedgerEntry.entry_date.desc(), LedgerEntry.id.desc())).all())


def get_ledger_summary(db: Session, client_id: int) -> dict[str, Decimal | int]:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    entries = get_client_ledger_entries(db, client_id)
    opening_balance = _opening_balance(client)
    total_debit = _money(sum((entry.debit for entry in entries), Decimal("0.00")))
    total_credit = _money(sum((entry.credit for entry in entries), Decimal("0.00")))
    current_balance = _money(opening_balance + total_debit - total_credit)

    return {
        "client_id": client_id,
        "opening_balance": opening_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "current_balance": current_balance,
    }


def create_ledger_entry(db: Session, payload: LedgerEntryCreate, current_user: User, commit: bool = True) -> LedgerEntry:
    client = db.get(Client, payload.client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    existing_entry = None
    if payload.reference_id is not None:
        existing_entry = db.scalar(
            select(LedgerEntry).where(
                LedgerEntry.entry_type == payload.entry_type,
                LedgerEntry.reference_id == payload.reference_id,
            )
        )
    if existing_entry is None and payload.reference_no:
        existing_entry = db.scalar(
            select(LedgerEntry).where(
                LedgerEntry.entry_type == payload.entry_type,
                LedgerEntry.reference_no == payload.reference_no,
            )
        )
    if existing_entry:
        return existing_entry

    previous_balance = _get_last_balance(db, client)
    balance_after_entry = _money(previous_balance + payload.debit - payload.credit)
    entry = LedgerEntry(
        client_id=payload.client_id,
        entry_date=payload.entry_date,
        entry_type=payload.entry_type,
        reference_id=payload.reference_id,
        reference_no=payload.reference_no,
        description=payload.description,
        debit=_money(payload.debit),
        credit=_money(payload.credit),
        balance_after_entry=balance_after_entry,
        created_by_user_id=current_user.id,
    )
    db.add(entry)
    client.current_balance = balance_after_entry

    if commit:
        db.commit()
        db.refresh(entry)
    return entry


def create_sales_invoice_ledger_entry(
    db: Session,
    *,
    client_id: int,
    invoice_id: int,
    invoice_no: str,
    invoice_date,
    total_amount: Decimal,
    current_user: User,
) -> LedgerEntry:
    payload = LedgerEntryCreate(
        client_id=client_id,
        entry_date=invoice_date,
        entry_type=LedgerEntryType.sales_invoice,
        reference_id=invoice_id,
        reference_no=invoice_no,
        description=f"Sales invoice {invoice_no}",
        debit=_money(total_amount),
        credit=Decimal("0.00"),
    )
    return create_ledger_entry(db, payload, current_user, commit=False)


def create_purchase_invoice_ledger_entry(
    db: Session,
    *,
    supplier_id: int,
    purchase_invoice_id: int,
    purchase_invoice_no: str,
    purchase_date,
    total_amount: Decimal,
    current_user: User,
) -> LedgerEntry:
    payload = LedgerEntryCreate(
        client_id=supplier_id,
        entry_date=purchase_date,
        entry_type=LedgerEntryType.purchase_invoice,
        reference_id=purchase_invoice_id,
        reference_no=purchase_invoice_no,
        description=f"Purchase invoice {purchase_invoice_no}",
        debit=Decimal("0.00"),
        credit=_money(total_amount),
    )
    return create_ledger_entry(db, payload, current_user, commit=False)


def create_payment_ledger_entry(
    db: Session,
    *,
    client_id: int,
    payment_id: int,
    payment_date,
    payment_type,
    amount: Decimal,
    transaction_no: str | None,
    current_user: User,
) -> LedgerEntry:
    is_received = str(payment_type) == "PaymentType.received" or payment_type == "received"
    payload = LedgerEntryCreate(
        client_id=client_id,
        entry_date=payment_date,
        entry_type=LedgerEntryType.payment_received if is_received else LedgerEntryType.payment_paid,
        reference_id=payment_id,
        reference_no=transaction_no,
        description="Payment received" if is_received else "Payment paid",
        debit=Decimal("0.00") if is_received else _money(amount),
        credit=_money(amount) if is_received else Decimal("0.00"),
    )
    return create_ledger_entry(db, payload, current_user, commit=False)


def create_bank_statement_ledger_entry(
    db: Session,
    *,
    client_id: int,
    bank_statement_id: int,
    transaction_date,
    reference_no: str | None,
    description: str | None,
    debit: Decimal,
    credit: Decimal,
    current_user: User,
) -> LedgerEntry:
    payload = LedgerEntryCreate(
        client_id=client_id,
        entry_date=transaction_date,
        entry_type=LedgerEntryType.bank_statement,
        reference_id=bank_statement_id,
        reference_no=reference_no,
        description=description,
        debit=_money(debit),
        credit=_money(credit),
    )
    return create_ledger_entry(db, payload, current_user, commit=False)


def can_create_manual_entry(current_user: User, payload: LedgerEntryCreate) -> bool:
    if current_user.role in {Role.manager, Role.admin, Role.superadmin}:
        return True
    if current_user.role == Role.employee:
        return current_user.can_add_manual_ledger_entries and payload.entry_type != LedgerEntryType.adjustment
    return False
