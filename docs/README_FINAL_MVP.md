# SIH26179 Final MVP

This is a web application for AI-powered Retail & Supply Chain Intelligence.

## Run backend
```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8003
```

## Run frontend
Open `frontend/index.html` with a local static server (recommended) or serve the folder with any static HTTP server.

## PostgreSQL
Set `DATABASE_URL` in `.env` to a PostgreSQL SQLAlchemy URL. If it is empty, the prototype uses a local SQLite database so the order workflow can be demonstrated without external setup.

## Core demo
1. Open retailer dashboard.
2. Review forecast, inventory risk and recommendation.
3. Place an order.
4. Open Factory Dashboard.
5. Accept / move order through production / ready / dispatched.
6. Review customer recommendation and feedback.
