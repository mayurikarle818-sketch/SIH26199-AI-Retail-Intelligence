# Supplied PostgreSQL database audit

Source file: `RetailEdge_Final_Database.sql`

- PostgreSQL dump version: 18.6
- Public tables: 37
- Supplied database is used as the primary source when `DATABASE_URL` points to the restored database.

## Core tables and rows in the supplied dump

| Table | Rows | Role |
|---|---:|---|
| `team_m5_multi_product_sales` | 19,130 | M5-derived historical sales |
| `team_multi_product_predictions` | 10 | Stored demand predictions |
| `team_multi_product_recommendations` | 10 | Inventory/reorder recommendations |
| `team_inventory_multi_product` | 10 | Inventory snapshot |
| `team_calendar` | 1,969 | Calendar/context |
| `team_weather_historical` | 1,969 | Historical weather context |
| `team_indian_festivals` | 19 | Festival reference |
| `team_indian_festivals_historical` | 44 | Historical festival dates |
| `team_festival_sales_integrated` | 1,913 | Integrated festival-sales data |
| `team_retail_context_integrated` | 1,913 | Retail context data |
| `team_retail_intelligence_integrated` | 1,913 | Retail intelligence data |
| `team_sales_festival_weather_integrated` | 1,913 | Sales/festival/weather integration |
| `team_promotions` | 29 | Promotion data |
| `team_online_trends` | 20 | Online trend data |
| `team_feedback` | 8 | Application feedback |
| `prati_product_master_data` | 10 | Product master |
| `prati_customer_feedback_data` | 10 | Customer feedback |
| `prati_customer_preference_data` | 10 | Customer preferences |
| `prati_factory_capacity_data` | 10 | Factory capacity |
| `prati_raw_material_data` | 10 | Raw materials |
| `prati_production_order_data` | 10 | Production orders |
| `prati_production_status_data` | 10 | Production status |
| `prati_dispatch_data` | 10 | Dispatch |
| `prati_delivery_status_data` | 10 | Delivery status |

The complete dump also contains supplier, logistics, BOM, store/retailer and cleaned operational tables.

## Important interpretation

`team_multi_product_predictions` and `team_multi_product_recommendations` are stored model/decision outputs. They are not themselves the ML algorithm. The Python project contains the Random Forest demand-forecasting pipeline; PostgreSQL stores the supplied prediction/recommendation artifacts for application use.
