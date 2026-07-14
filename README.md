# Invoice Ledger API

FastAPI backend for an invoice, ledger, client, product, payment, bank statement, and reporting system.

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Alembic migrations
- Pydantic schemas
- JWT authentication
- Role-based access control
- bcrypt password hashing
- python-dotenv

## Project Structure

```text
backend/
  app/
    main.py
    config.py
    database.py
    models/
    schemas/
    routes/
    services/
    utils/
    dependencies/
  alembic/
  alembic.ini
  requirements.txt
  .env.example
```

## Main Modules

- Authentication and users
- Client account master
- Product master
- Sales invoices
- Purchase invoices
- Ledger
- Payments
- Bank statements with CSV import
- Reports and dashboard

## Roles

- `superadmin`
- `employee`
- `manager`
- `admin`

General access rules:

- Superadmins can create admin users and have admin-level access.
- Admins can create employee and manager users and share the credentials they set.
- Employees can create sales/purchase records and view limited reports.
- Managers can approve invoices and manage operational records.
- Admins can manage everything and view all reports.

## Setup

From the backend folder:

```powershell
cd "E:\efleet\getx_Project\invoce app\invoice_app_backend\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set your PostgreSQL connection:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@127.0.0.1:5432/invoice_ledger
JWT_SECRET_KEY=change-this-secret
```

If your password contains special characters such as `@`, `#`, `%`, `:`, or `/`, URL-encode them.

## Database

Create the PostgreSQL database:

```powershell
createdb -U postgres -h 127.0.0.1 invoice_ledger
```

Check database connectivity:

```powershell
.\.venv\Scripts\python.exe -m app.utils.db_preflight
```

Run migrations:

```powershell
alembic upgrade head
```

## Run Server

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

## API Groups

Authentication:

```text
POST /auth/setup-superadmin
POST /auth/register
POST /auth/login
GET  /auth/me
```

Create the first superadmin once:

```http
POST /auth/setup-superadmin
Content-Type: application/json

{
  "full_name": "Super Admin",
  "email": "superadmin@example.com",
  "mobile": "9999999999",
  "password": "ChangeMe123"
}
```

After this, log in with `/auth/login`. The setup endpoint returns `409` once a superadmin already exists.

User management:

```text
POST /users
```

- Superadmin can create `admin`, `manager`, and `employee` users.
- Admin can create `manager` and `employee` users.
- Superadmin accounts cannot be created from `/users`.

Clients:

```text
POST   /clients
GET    /clients
GET    /clients/{client_id}
PUT    /clients/{client_id}
DELETE /clients/{client_id}
```

Products:

```text
POST   /products
GET    /products
GET    /products/{product_id}
PUT    /products/{product_id}
DELETE /products/{product_id}
```

Sales invoices:

```text
POST /sales-invoices
GET  /sales-invoices
GET  /sales-invoices/{invoice_id}
PUT  /sales-invoices/{invoice_id}
POST /sales-invoices/{invoice_id}/generate
POST /sales-invoices/{invoice_id}/approve
POST /sales-invoices/{invoice_id}/cancel
```

Purchase invoices:

```text
POST /purchase-invoices
GET  /purchase-invoices
GET  /purchase-invoices/{purchase_invoice_id}
PUT  /purchase-invoices/{purchase_invoice_id}
POST /purchase-invoices/{purchase_invoice_id}/generate
POST /purchase-invoices/{purchase_invoice_id}/approve
POST /purchase-invoices/{purchase_invoice_id}/cancel
```

Ledger:

```text
GET  /ledger/client/{client_id}
GET  /ledger/client/{client_id}/summary
GET  /ledger/all
POST /ledger/manual-entry
```

Payments:

```text
POST /payments
GET  /payments
GET  /payments/{payment_id}
```

Bank statements:

```text
POST /bank-statements/manual
POST /bank-statements/import-csv
GET  /bank-statements
POST /bank-statements/{statement_id}/match-client
POST /bank-statements/{statement_id}/create-ledger-entry
```

Reports:

```text
GET /reports/dashboard
GET /reports/client-balances
GET /reports/sales-register
GET /reports/purchase-register
GET /reports/gst-summary
```

## Ledger Behavior

- Sales invoice generation/approval creates a debit ledger entry.
- Purchase invoice generation/approval creates a credit ledger entry.
- Payment received creates a credit ledger entry.
- Payment paid creates a debit ledger entry.
- Bank statement entries can be matched to clients and converted to ledger entries.
- Duplicate ledger entries are prevented using reference data.

## CSV Import

Bank statement CSV import supports common columns:

```text
transaction_date,date,txn_date
description,narration,remarks
reference_no,reference,transaction_no,utr,cheque_no
debit,withdrawal,withdrawals
credit,deposit,deposits
balance,closing_balance
```

## Git Notes

Do not commit local secrets or virtual environments.

Ignored by `.gitignore`:

- `.env`
- `.venv/`
- `__pycache__/`
- logs
- local database files
- editor files

Use `.env.example` for shared configuration examples.
