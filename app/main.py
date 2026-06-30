from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import (
    auth,
    bank_statements,
    clients,
    health,
    invoices,
    ledger,
    payments,
    products,
    purchase_invoices,
    reports,
    sales_invoices,
    users,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(bank_statements.router, prefix="/bank-statements", tags=["bank-statements"])
    app.include_router(clients.router, prefix="/clients", tags=["clients"])
    app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
    app.include_router(ledger.router, prefix="/ledger", tags=["ledger"])
    app.include_router(payments.router, prefix="/payments", tags=["payments"])
    app.include_router(products.router, prefix="/products", tags=["products"])
    app.include_router(purchase_invoices.router, prefix="/purchase-invoices", tags=["purchase-invoices"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(sales_invoices.router, prefix="/sales-invoices", tags=["sales-invoices"])
    app.include_router(users.router, prefix="/users", tags=["users"])

    return app


app = create_app()
