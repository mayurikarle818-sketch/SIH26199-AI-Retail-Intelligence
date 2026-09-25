"""Real-data AI services for the SIH26179 Final MVP.

The runtime uses the supplied M5-derived sales data and precomputed MVP
recommendation artifacts. XGBoost is trained lazily per product/store series
for the 7-day forecast and evaluated on a chronological hold-out set.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from textblob import TextBlob

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover
    XGBRegressor = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SALES_PATH = os.path.join(DATA_DIR, "m5_multi_product_sales.csv")
REC_PATH = os.path.join(DATA_DIR, "multi_product_recommendations.csv")
INV_PATH = os.path.join(DATA_DIR, "inventory_multi_product.csv")
PRODUCT_PATH = os.path.join(DATA_DIR, "product_master.csv")
PREF_PATH = os.path.join(DATA_DIR, "customer_preferences.csv")

FEATURES = ["lag_1", "lag_7", "rolling_7", "rolling_30", "month", "weekday"]

sales = pd.read_csv(SALES_PATH, parse_dates=["date"])
sales["sales"] = pd.to_numeric(sales["sales"], errors="coerce").fillna(0)
recs = pd.read_csv(REC_PATH)
inventory = pd.read_csv(INV_PATH)
product_master = pd.read_csv(PRODUCT_PATH) if os.path.exists(PRODUCT_PATH) else pd.DataFrame()
preferences = pd.read_csv(PREF_PATH) if os.path.exists(PREF_PATH) else pd.DataFrame()

CONTEXT_PATH = os.path.join(DATA_DIR, "retail_context_integrated.csv")
context_df = pd.read_csv(CONTEXT_PATH, parse_dates=["date"]) if os.path.exists(CONTEXT_PATH) else pd.DataFrame()
TREND_PATH = os.path.join(DATA_DIR, "online_trends.csv")
trend_context_df = pd.read_csv(TREND_PATH, parse_dates=["date"]) if os.path.exists(TREND_PATH) else pd.DataFrame()

def context_for(product: str, store: str, forecast_date=None) -> Dict[str, Any]:
    """Return real/public-data context signals for a product/store."""
    result = {
        "festival": "No festival in source data",
        "festival_impact": "Low",
        "temperature": None,
        "rain": None,
        "promotion": "No promotion",
        "online_trend": "Stable",
        "trend_index": None,
        "context_date": None,
        "source": "M5-derived retail context + weather + promotion + online trend datasets",
    }
    if not context_df.empty:
        df = context_df[(context_df.item_id.astype(str) == str(product)) & (context_df.store_id.astype(str) == str(store))].sort_values("date")
        if not df.empty:
            row = df.iloc[-1] if forecast_date is None else df.iloc[(df.date - pd.Timestamp(forecast_date)).abs().argsort().iloc[0]]
            result["context_date"] = str(pd.Timestamp(row.date).date())
            festival = row.get("festival")
            if pd.notna(festival) and str(festival).strip():
                result["festival"] = str(festival)
            impact = row.get("expected_impact")
            if pd.isna(impact) or not str(impact).strip():
                impact = row.get("festival_impact")
            if pd.notna(impact):
                try:
                    iv=float(impact)
                    result["festival_impact"] = "High" if iv >= 0.5 else "Medium" if iv > 0 else "Low"
                except Exception:
                    result["festival_impact"] = str(impact)
            for src,dst in [("temperature_mean","temperature"),("rain","rain")]:
                if src in row and pd.notna(row[src]): result[dst]=round(float(row[src]),1)
            promo=row.get("promotion_name")
            if pd.notna(promo) and str(promo).strip(): result["promotion"]=str(promo)
    if not trend_context_df.empty:
        t=trend_context_df.copy()
        if "product_category" in t:
            # M5 products are FOODS in the supplied context data.
            t=t[t.product_category.astype(str).str.upper()=="FOODS"]
        if not t.empty:
            target=pd.Timestamp(forecast_date) if forecast_date is not None else t.date.max()
            row=t.iloc[(t.date-target).abs().argsort().iloc[0]]
            if pd.notna(row.get("trend_index")): result["trend_index"]=round(float(row.trend_index),1)
            if pd.notna(row.get("trend_direction")): result["online_trend"]=str(row.trend_direction)
            if result["context_date"] is None: result["context_date"]=str(pd.Timestamp(row.date).date())
    return result



def _series(product: str, store: str) -> pd.DataFrame:
    df = sales[(sales.item_id == product) & (sales.store_id == store)].sort_values("date").copy()
    if df.empty:
        return df
    df["lag_1"] = df.sales.shift(1)
    df["lag_7"] = df.sales.shift(7)
    df["rolling_7"] = df.sales.shift(1).rolling(7).mean()
    df["rolling_30"] = df.sales.shift(1).rolling(30).mean()
    df["month"] = df.date.dt.month
    df["weekday"] = df.date.dt.weekday
    return df.dropna(subset=FEATURES).reset_index(drop=True)


@lru_cache(maxsize=32)
def _model(product: str, store: str):
    df = _series(product, store)
    if len(df) < 80 or XGBRegressor is None:
        return None
    split = max(int(len(df) * 0.8), 60)
    model = XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=2,
    )
    model.fit(df.iloc[:split][FEATURES], df.iloc[:split].sales)
    test_pred = model.predict(df.iloc[split:][FEATURES])
    mae = float(np.mean(np.abs(test_pred - df.iloc[split:].sales)))
    return model, df, mae, split


def forecast(product: str, store: str, horizon: int = 7) -> Dict[str, Any]:
    result = _model(product, store)
    if result is None:
        row = recs[(recs.item_id == product) & (recs.store_id == store)]
        if row.empty:
            raise ValueError("Product/store combination not found")
        base = max(float(row.iloc[0].predicted_demand), 0)
        last = pd.to_datetime(row.iloc[0].last_date)
        values = [round(base * (1 + 0.01 * i), 1) for i in range(horizon)]
        return {"model": "MVP precomputed Random Forest artifact", "mae": float(row.iloc[0].mae), "forecast": [{"day": i + 1, "date": str(last + pd.Timedelta(days=i + 1)).split(" ")[0], "predicted_demand": v} for i, v in enumerate(values)], "features": ["precomputed prediction artifact"]}

    model, df, mae, _ = result
    history = df[["date", "sales"]].copy()
    preds = []
    for i in range(horizon):
        next_date = history.date.iloc[-1] + pd.Timedelta(days=1)
        row = {
            "lag_1": float(history.sales.iloc[-1]),
            "lag_7": float(history.sales.iloc[-7]) if len(history) >= 7 else float(history.sales.mean()),
            "rolling_7": float(history.sales.tail(7).mean()),
            "rolling_30": float(history.sales.tail(30).mean()),
            "month": int(next_date.month),
            "weekday": int(next_date.weekday()),
        }
        pred = max(float(model.predict(pd.DataFrame([row])[FEATURES])[0]), 0.0)
        pred = round(pred, 1)
        preds.append({"day": i + 1, "date": str(next_date.date()), "predicted_demand": pred})
        history.loc[len(history)] = [next_date, pred]
    importance = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: x[1], reverse=True)
    return {"model": "XGBoost Regressor", "mae": round(mae, 2), "forecast": preds, "features": FEATURES, "feature_importance": [{"feature": f, "importance": round(float(v), 4)} for f, v in importance]}


def inventory_intelligence() -> list[Dict[str, Any]]:
    rows = []
    for r in recs.itertuples():
        product, store = str(r.item_id), str(r.store_id)
        try:
            f = forecast(product, store, 7)["forecast"]
            avg = float(np.mean([x["predicted_demand"] for x in f]))
        except Exception:
            avg = float(r.predicted_demand)
        stock = float(r.current_stock) + float(r.incoming_stock)
        lead = max(float(r.lead_time_days), 1)
        safety = max(float(r.safety_stock), round(avg * 0.5, 1))
        reorder_point = avg * lead + safety
        cover = stock / avg if avg > 0 else 999
        if stock <= safety or cover < lead * 0.75:
            risk = "CRITICAL"
        elif cover < lead:
            risk = "HIGH"
        elif cover < lead + 2:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        reorder = max(0, int(round(reorder_point - stock)))
        stockout_days = round(stock / avg, 1) if avg > 0 else None
        reason = []
        if cover < lead: reason.append(f"stock cover {cover:.1f}d is below {lead:.0f}d lead time")
        if avg > float(r.predicted_demand) * 1.05: reason.append("forecast demand is elevated")
        if stock < reorder_point: reason.append("available stock is below the reorder point")
        if not reason: reason.append("stock covers forecast demand and lead time")
        recommendation_text = (
            f"Place purchase order for {reorder} units"
            if reorder > 0
            else "Monitor inventory — no replenishment required"
        )
        rows.append({
            "product": product,
            "store": store,
            "current_stock": int(r.current_stock),
            "incoming_stock": int(r.incoming_stock),
            "available_stock": int(stock),
            "predicted_daily_demand": round(avg, 1),
            "predicted_demand": round(avg, 1),
            "lead_time_days": int(lead),
            "safety_stock": int(round(safety)),
            "reorder_point": int(round(reorder_point)),
            "stock_cover_days": cover if cover < 999 else None,
            "stockout_days": stockout_days,
            "risk": risk,
            "recommended_order": reorder,
            "recommendation": recommendation_text,
            "action": "PLACE PURCHASE ORDER" if reorder > 0 else "MONITOR INVENTORY",
            "reason": "; ".join(reason),
            "model_mae": float(r.mae)
        })
    return rows


def recommendation(product: str | None = None, store: str = "CA_1") -> Dict[str, Any]:
    rows = inventory_intelligence()
    if product:
        matches = [x for x in rows if x["product"] == product and x["store"] == store]
        if not matches: raise ValueError("Product not found")
        row = matches[0]
    else:
        priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        row = sorted(rows, key=lambda x: (priority[x["risk"]], -x["recommended_order"]))[0]
    row["action"] = "PLACE PURCHASE ORDER" if row["recommended_order"] > 0 else "MONITOR INVENTORY"
    row["predicted_demand"] = row["predicted_daily_demand"]
    context = context_for(product or row["product"], store)
    row.update({
        "festival": context["festival"],
        "festival_impact": context["festival_impact"],
        "temperature": context["temperature"],
        "rain": context["rain"],
        "promotion": context["promotion"],
        "online_trend": context["online_trend"],
        "trend_index": context["trend_index"],
        "context_date": context["context_date"],
        "context_source": context["source"],
        "context_signals": [
            f"Forecast demand: {row['predicted_daily_demand']} units/day",
            f"Stock cover: {row['stock_cover_days']:.1f} days vs {row['lead_time_days']} day lead time",
            f"Safety stock: {row['safety_stock']} units",
            f"Reorder point: {row['reorder_point']} units",
            f"Festival signal: {context['festival']} ({context['festival_impact']})",
            f"Promotion: {context['promotion']}",
            f"Online trend: {context['online_trend']} ({context['trend_index'] if context['trend_index'] is not None else 'n/a'}/100)",
        ],
        "explanation": (
            f"Predicted demand is {row['predicted_daily_demand']} units/day with "
            f"{row['available_stock']} units available. Stock covers about "
            f"{row['stock_cover_days']:.1f} days versus {row['lead_time_days']} days lead time. "
            f"The reorder point is {row['reorder_point']} units, so the AI recommends "
            f"{row['recommended_order']} units. Context: {context['festival']}, "
            f"{context['promotion']}, temperature {context['temperature'] if context['temperature'] is not None else 'n/a'} °C, "
            f"rain {context['rain'] if context['rain'] is not None else 'n/a'} mm, "
            f"online trend {context['online_trend']} ({context['trend_index'] if context['trend_index'] is not None else 'n/a'})."
        )
    })
    row["explainable_factors"] = [
        f"Predicted demand: {row['predicted_daily_demand']} units/day",
        f"Available stock: {row['available_stock']} units",
        f"Lead time: {row['lead_time_days']} days",
        f"Safety stock: {row['safety_stock']} units",
        f"Stock cover: {row['stock_cover_days']} days" if row['stock_cover_days'] is not None else "Stock cover: unavailable",
    ]
    return row


def anomaly_detection(product: str, store: str) -> Dict[str, Any]:
    df = sales[(sales.item_id == product) & (sales.store_id == store)].sort_values("date").tail(120).copy()
    if len(df) < 30:
        return {"product": product, "store": store, "anomalies": [], "message": "Not enough history"}
    model = IsolationForest(contamination=0.08, random_state=42)
    df["score"] = model.fit_predict(df[["sales"]])
    anomalies = df[df.score == -1].tail(10)
    return {"product": product, "store": store, "anomalies": [{"date": str(r.date.date()), "sales": int(r.sales)} for r in anomalies.itertuples()], "method": "Isolation Forest", "window_days": len(df)}


def customer_recommendations(customer_id: str = "CUST_DEMO_001") -> list[Dict[str, Any]]:
    popular = sales.groupby("item_id", as_index=False).sales.sum().sort_values("sales", ascending=False).head(10)
    preferred = set()
    if not preferences.empty and "customer_id" in preferences:
        preferred = set(preferences.loc[preferences.customer_id.astype(str) == str(customer_id), "product_id"].astype(str))
    result = []
    for rank, r in enumerate(popular.itertuples(), start=1):
        product = str(r.item_id)
        result.append({"product": product, "reason": "Matches customer preference" if product in preferred else "High historical demand and available inventory signal", "score": round(1 / rank, 3)})
        if len(result) >= 5: break
    return result


def sentiment(text: str) -> Dict[str, Any]:
    polarity = float(TextBlob(text).sentiment.polarity)
    label = "POSITIVE" if polarity > 0.1 else "NEGATIVE" if polarity < -0.1 else "NEUTRAL"
    return {"sentiment": label, "polarity": round(polarity, 3), "method": "TextBlob polarity analysis"}
