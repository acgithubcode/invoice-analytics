from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import authenticated_user, manager_or_admin
from app.models.purchase_invoice import PurchaseInvoice
from app.models.sales_invoice import SalesInvoice
from app.models.user import User
from app.schemas.report import (
    ClientBalanceReport,
    DashboardReport,
    GstSummaryReport,
    PurchaseRegisterRow,
    SalesRegisterRow,
)
from app.services.report_service import (
    get_client_balances_report,
    get_dashboard_report,
    get_gst_summary,
    get_purchase_register,
    get_sales_register,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardReport)
def read_dashboard_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> dict:
    return get_dashboard_report(db, current_user)


@router.get("/client-balances", response_model=list[ClientBalanceReport])
def read_client_balances_report(
    db: Session = Depends(get_db),
    _: User = Depends(authenticated_user),
) -> list[dict]:
    return get_client_balances_report(db)


@router.get("/sales-register", response_model=list[SalesRegisterRow])
def read_sales_register(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    client_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> list[SalesInvoice]:
    return get_sales_register(db, current_user, from_date, to_date, client_id)


@router.get("/purchase-register", response_model=list[PurchaseRegisterRow])
def read_purchase_register(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    supplier_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_user),
) -> list[PurchaseInvoice]:
    return get_purchase_register(db, current_user, from_date, to_date, supplier_id)


@router.get("/gst-summary", response_model=GstSummaryReport, dependencies=[Depends(manager_or_admin)])
def read_gst_summary(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return get_gst_summary(db, from_date, to_date)
