"""Train a global RandomForest on the cleaned multi-product M5 context data and
produce a true recursive 7-day forecast for every product-store series.

This is an offline artifact-generation script; the web API can serve the saved CSV.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "m5_multi_product_context.csv"
OUT = ROOT / "data" / "next_7_day_forecast.csv"
MODEL = ROOT / "ml" / "demand_forecasting" / "saved_model" / "demand_rf.joblib"
FEATURES = ["lag_1","lag_7","rolling_7","rolling_30","month","weekday_code"]


def main():
    df = pd.read_csv(DATA, parse_dates=["date"])
    df = df.sort_values(["item_id","store_id","date"]).copy()
    df[FEATURES + ["sales"]] = df[FEATURES + ["sales"]].apply(pd.to_numeric, errors="coerce")
    train = df.dropna(subset=FEATURES + ["sales"]).copy()
    X, y = train[FEATURES], train["sales"]
    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1, min_samples_leaf=2)
    model.fit(X, y)
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL)

    rows=[]
    for (item, store), g in df.groupby(["item_id","store_id"]):
        g=g.sort_values("date")
        history=g["sales"].dropna().tolist()
        last_date=g["date"].max()
        for step in range(1,8):
            target_date=last_date + pd.Timedelta(days=step)
            lag1=history[-1] if len(history)>=1 else 0
            lag7=history[-7] if len(history)>=7 else lag1
            roll7=float(np.mean(history[-7:])) if history else 0
            roll30=float(np.mean(history[-30:])) if history else roll7
            features=pd.DataFrame([{"lag_1":lag1,"lag_7":lag7,"rolling_7":roll7,"rolling_30":roll30,"month":target_date.month,"weekday_code":target_date.weekday()}])
            pred=max(float(model.predict(features)[0]),0)
            history.append(pred)
            rows.append({"item_id":item,"store_id":store,"forecast_date":target_date.strftime("%Y-%m-%d"),"day_ahead":step,"predicted_demand":round(pred,2)})
    pd.DataFrame(rows).to_csv(OUT,index=False)
    print(f"Saved {len(rows)} forecasts to {OUT}")

if __name__ == "__main__": main()
