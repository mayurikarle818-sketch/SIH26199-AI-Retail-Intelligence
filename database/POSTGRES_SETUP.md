# PostgreSQL setup — RetailEdge final database

This project includes the PostgreSQL dump supplied for the final database.

## 1. Create the database

In pgAdmin or `psql`, create a database named:

`siH26179`

PostgreSQL names are case-insensitive unless quoted, so the recommended name is lowercase `sih26179`.

## 2. Restore the supplied dump

From PowerShell, after `psql` is available in PATH:

```powershell
psql -U postgres -d sih26179 -f database\RetailEdge_Final_Database.sql
```

The dump contains **37 public tables**, including the `team_*` retail/ML tables and the `prati_*` factory/customer/supply-chain tables.

## 3. Configure the application

Copy `.env.example` to `.env` and set your actual PostgreSQL password:

```text
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sih26179
```

Do not commit `.env` to GitHub.

## 4. Start

```powershell
python -m uvicorn backend.app:app --reload --port 8003
```

or use:

```powershell
.\start_all.bat
```

## 5. Verify the database connection

Open:

`http://127.0.0.1:8003/api/db-status`

When PostgreSQL is connected, the response reports `database: PostgreSQL` and row counts for the supplied tables.

## Data used by the API

When PostgreSQL is configured, these endpoints read the supplied database first:

- `/api/sales` → `team_m5_multi_product_sales`
- `/api/recommendation` → `team_multi_product_recommendations`
- `/api/multi-products` → `team_multi_product_recommendations`
- `/api/products` → `team_inventory_multi_product`
- `/api/factory/capacity` → `prati_factory_capacity_data`
- `/api/factory/raw-materials` → `prati_raw_material_data`
- `/api/factory/production-data` → `prati_production_order_data` + `prati_production_status_data`
- `/api/factory/dispatch-data` → `prati_dispatch_data` + `prati_delivery_status_data`
- `/api/customer/feedback-history` → `prati_customer_feedback_data`

The web application retains CSV fallback files so the MVP can still be demonstrated if PostgreSQL is temporarily unavailable.
