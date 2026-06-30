from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.purchase_invoice import PurchaseInvoiceStatus
from app.models.sales_invoice import SalesInvoiceStatus


class DashboardReport(BaseModel):
    total_sales: Decimal
    total_purchase: Decimal
    total_receivable: Decimal
    total_payable: Decimal
    total_clients: int
    pending_invoices: int
    today_collection: Decimal


class ClientBalanceReport(BaseModel):
    client_id: int
    client_name: str
    total_debit: Decimal
    total_credit: Decimal
    current_balance: Decimal
    balance_type: str


class SalesRegisterRow(BaseModel):
    id: int
    invoice_no: str
    invoice_date: date
    client_id: int
    invoice_to: str
    subtotal: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    status: SalesInvoiceStatus


class PurchaseRegisterRow(BaseModel):
    id: int
    purchase_invoice_no: str
    purchase_date: date
    supplier_id: int
    supplier_name: str
    subtotal: Decimal
    igst_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    status: PurchaseInvoiceStatus


class GstSummaryReport(BaseModel):
    taxable_amount: Decimal
    igst: Decimal
    cgst: Decimal
    sgst: Decimal
    total_invoice_amount: Decimal
