import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# ==========================================
# FILE
# ==========================================

FILE = "data/m5_multi_product_sales.csv"

# ==========================================
# LOAD REAL M5 DATA
# ==========================================

print("Loading multi-product M5 data...")

df = pd.read_csv(FILE)

df["date"] = pd.to_datetime(df["date"])

df = df.sort_values(
    ["item_id", "date"]
).reset_index(drop=True)

print("Total records:", len(df))
print("Products:", df["item_id"].nunique())

# ==========================================
# FEATURE ENGINEERING
# ==========================================

print("\nCreating ML features...")

df["lag_1"] = (
    df.groupby("item_id")["sales"]
    .shift(1)
)

df["lag_7"] = (
    df.groupby("item_id")["sales"]
    .shift(7)
)

df["rolling_7"] = (
    df.groupby("item_id")["sales"]
    .shift(1)
    .rolling(7)
    .mean()
    .reset_index(level=0, drop=True)
)

df["rolling_30"] = (
    df.groupby("item_id")["sales"]
    .shift(1)
    .rolling(30)
    .mean()
    .reset_index(level=0, drop=True)
)

df["day_of_week"] = df["date"].dt.dayofweek

df["month_number"] = df["date"].dt.month

# ==========================================
# REMOVE MISSING VALUES
# ==========================================

df = df.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_30"
    ]
)

# ==========================================
# ML FEATURES
# ==========================================

features = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_30",
    "day_of_week",
    "month_number"
]

target = "sales"

# ==========================================
# TRAIN + PREDICT FOR EACH PRODUCT
# ==========================================

results = []

products = df["item_id"].unique()

print("\nTraining models...\n")

for product in products:

    product_df = df[
        df["item_id"] == product
    ].copy()

    product_df = product_df.sort_values("date")

    # Last 30 days for testing
    train = product_df.iloc[:-30]
    test = product_df.iloc[-30:]

    X_train = train[features]
    y_train = train[target]

    X_test = test[features]
    y_test = test[target]

    # ======================================
    # MODEL
    # ======================================

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    # ======================================
    # TEST PREDICTION
    # ======================================

    test_prediction = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        test_prediction
    )

    # ======================================
    # FUTURE PREDICTION
    # ======================================

    latest = product_df.iloc[-1]

    future_features = pd.DataFrame([
        {
            "lag_1": latest["sales"],
            "lag_7": latest["lag_7"],
            "rolling_7": latest["rolling_7"],
            "rolling_30": latest["rolling_30"],
            "day_of_week":
                (latest["date"] +
                 pd.Timedelta(days=1)).dayofweek,
            "month_number":
                (latest["date"] +
                 pd.Timedelta(days=1)).month
        }
    ])

    future_prediction = model.predict(
        future_features
    )[0]

    future_prediction = max(
        0,
        round(float(future_prediction))
    )

    # ======================================
    # STORE RESULT
    # ======================================

    results.append(
        {
            "product": product,
            "store": latest["store_id"],
            "last_date":
                latest["date"].strftime("%Y-%m-%d"),
            "last_sales":
                int(latest["sales"]),
            "predicted_demand":
                future_prediction,
            "mae":
                round(float(mae), 2)
        }
    )

    print(
        f"{product} → "
        f"Prediction: {future_prediction} | "
        f"MAE: {mae:.2f}"
    )

# ==========================================
# SAVE RESULTS
# ==========================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "predicted_demand",
    ascending=False
)

output_file = (
    "data/multi_product_predictions.csv"
)

results_df.to_csv(
    output_file,
    index=False
)

# ==========================================
# FINAL OUTPUT
# ==========================================

print("\n====================================")
print("MULTI-PRODUCT ML SUCCESS")
print("====================================")

print(
    "Products predicted:",
    len(results_df)
)

print(
    "\nPrediction results:"
)

print(
    results_df.to_string(index=False)
)

print(
    f"\nSaved to: {output_file}"
)