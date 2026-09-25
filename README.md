# SIH26179 — RetailEdge AI Retail & Supply Chain Intelligence Final MVP

## Final demo flow

**Customer demand → AI demand forecast → inventory risk → stock-out prediction → explainable reorder → digital purchase order → factory → capacity/raw-material analysis → production → dispatch → retailer → customer feedback/recommendation**

The application is a beginner-friendly FastAPI + web frontend MVP. The existing working HTML/CSS/JS frontend is preserved to reduce breakage; the backend is upgraded with real-data AI services and the complete supply-chain workflow.

## What is implemented

### Retailer
- Dashboard, products, sales, demand forecast, inventory risk, AI recommendations, purchase orders and alerts.
- Risk levels: Critical / High / Medium / Low.
- Stock cover, safety stock, reorder point, stock-out days and recommended order quantity are calculated by the backend.
- Explainable recommendation factors are returned by the API.
- Place Order creates a persistent purchase order.

### AI / ML
- **Demand Forecasting:** XGBoost Regressor trained lazily on the selected M5 product/store time series with lag and rolling features.
- **Validation:** chronological hold-out MAE is calculated for the selected series.
- **Inventory Intelligence:** forecast + stock + lead time + safety stock produce the risk and reorder action.
- **Stock-out prediction:** stock-cover/stock-out days are calculated from forecast demand.
- **Anomaly Detection:** Isolation Forest over recent product sales.
- **Customer Recommendation:** popularity plus available preference signals from the supplied operational data.
- **Sentiment Analysis:** TextBlob polarity on customer feedback; the result is explicitly labelled as NLP sentiment analysis.
- **Explainability:** forecast features, inventory factors, context signals and business action are visible directly in the Retailer dashboard and AI Recommendations page.

### Factory / supply chain
- Incoming retailer orders.
- Production plan with finished-stock check, production required, capacity check and raw-material status.
- Status flow: `PENDING → ACCEPTED → IN PRODUCTION → READY → DISPATCHED → DELIVERED`.
- Dispatch records are persisted in the local workflow database.

### Customer
- Product recommendations.
- Feedback and rating submission.
- Sentiment result.
- Purchase/fulfilment visibility through the shared order flow.

### System API
- Product/risk/order/production/dispatch/feedback counts.
- Database mode and system overview.

## Data

### Primary real/public dataset
- **M5 Forecasting dataset derivative:** `data/m5_multi_product_sales.csv` and derived integrated files. The application uses historical sales from the M5/Walmart forecasting data. It is not represented as Indian sales.

### Additional operational dataset
- The supplied `RetailEdge_Final_Database.zip` PostgreSQL dump was inspected. Its operational tables were extracted into small CSV seed files for laptop-friendly fallback mode:
  - factory capacity
  - raw materials
  - production orders/status
  - dispatch/delivery
  - product master
  - BOM
  - customer preferences/feedback

These operational workflow records are prototype/demo data and should be described as such in the SIH presentation.

## Database modes

### Default laptop demo mode
No PostgreSQL is required. The app uses:
- SQLite for purchase orders, production records, dispatch records and feedback.
- Bundled CSV data for analytics and operational seed data.

### PostgreSQL mode
Set `DATABASE_URL` in `.env` using the supplied PostgreSQL dump. The backend will prefer the configured PostgreSQL source tables for supported analytics tables.

## Run on Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8003
```

Open:
- `http://127.0.0.1:8003/`
- API documentation: `http://127.0.0.1:8003/docs`
- Health: `http://127.0.0.1:8003/health`

A `start_all.bat` launcher is also included.

## Demo credentials

Use the same demo account for any role:

- Username: `demo`
- Password: `1234`
- Demo roles: Retailer, Factory/Manufacturer, Customer

Role navigation is enforced at the frontend MVP level and the login endpoint validates the selected role/password combination.

## Important API endpoints

- `POST /api/login`
- `GET /api/recommendation`
- `GET /api/inventory-risk`
- `GET /api/forecast/{product_id}`
- `GET /api/ai-insights`
- `GET /api/anomaly/{product_id}`
- `GET /api/alerts`
- `POST /api/purchase-orders`
- `GET /api/purchase-orders`
- `PUT /api/purchase-orders/{order_id}/status`
- `GET /api/factory/capacity`
- `GET /api/factory/raw-materials`
- `GET /api/production-plan/{order_id}`
- `GET /api/customer/recommendations`
- `POST /api/customer/feedback`
- `GET /api/customer/feedback-history`
- `GET /api/admin/overview`
- `GET /api/db-status`

## SIH demo script

1. Login as **Retailer**.
2. Open **AI Prediction** and show the 7-day M5/XGBoost forecast, MAE and demand table.
3. Open **Inventory Risk** and show risk, stock cover, stock-out days and reorder quantity.
4. Open **AI Recommendations** and click **Place Order**.
5. Open **Orders** and show the digital PO.
6. Login as **Factory / Manufacturer** and move the order through `ACCEPTED → IN PRODUCTION → READY → DISPATCHED → DELIVERED`.
7. Show production/capacity/raw-material analysis and dispatch record.
8. Login as **Customer**, show recommendations and submit feedback.
9. Show the sentiment result.
10. Use **Customer** to show availability, recommendations, purchase history and sentiment feedback.

## Packaging

The final submission package intentionally excludes `.venv`, Python caches, and the very large raw M5 training files that are not required for the runtime demo. The smaller M5-derived runtime datasets, model code, PostgreSQL dump/schema and operational seed data are retained.

## Known limitations

- This is an SIH-ready MVP, not production authentication: the demo role credentials are intentionally simple.
- Weather/online-trend signals are retained in the data/documentation but are not claimed as live external signals.
- Factory capacity/raw-material workflow data are supplied prototype operational data, not live factory ERP data.
- XGBoost is trained lazily for a selected product/store to keep laptop startup fast.
- Optional what-if simulator, computer vision and generic AI copilot are intentionally not part of the core stable build.

## Windows quick start (PowerShell)

From the folder containing `backend`, `frontend`, and `requirements.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

Open `http://127.0.0.1:8002/` and use `demo / 1234` with the selected role.


## SIH Final Demo Navigation
- Retailer: Dashboard → AI Prediction → Inventory Risk → AI Recommendations → Place Order → Orders.
- Factory: Orders → In Production → Ready → Dispatched → Delivered; capacity and raw-material checks are shown.
- Customer: product availability → personalized recommendations → purchase history → feedback sentiment → availability notifications.
- AI/ML Insights and Admin are intentionally removed from the demo navigation.
