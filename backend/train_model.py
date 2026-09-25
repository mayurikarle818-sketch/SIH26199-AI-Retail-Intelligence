import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# ========================================
# 1. LOAD INTEGRATED DATA
# ========================================

df = pd.read_csv(
    "data/sales_festival_weather_integrated.csv"
)

df["date"] = pd.to_datetime(df["date"])
df["sales"] = pd.to_numeric(df["sales"])


# ========================================
# 2. HANDLE MISSING VALUES
# ========================================

df["festival"] = df["festival"].fillna("No Festival")

weather_columns = [
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain"
]

for column in weather_columns:
    df[column] = df[column].fillna(
        df[column].median()
    )


# ========================================
# 3. WEEKDAY ENCODING
# ========================================

weekday_mapping = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}

df["weekday_code"] = (
    df["weekday"].map(weekday_mapping)
)


# ========================================
# 4. LAG FEATURES
# ========================================

df["lag_1"] = df["sales"].shift(1)

df["lag_7"] = df["sales"].shift(7)

df["rolling_7"] = (
    df["sales"]
    .shift(1)
    .rolling(7)
    .mean()
)


# ========================================
# 5. REMOVE MISSING VALUES
# ========================================

df = df.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "rolling_7",
        "weekday_code"
    ]
)


# ========================================
# 6. FEATURES
# ========================================

features = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "month",
    "weekday_code",

    # Festival
    "festival_flag",
    "festival_impact",

    # Weather
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag"
]

X = df[features]
y = df["sales"]


# ========================================
# 7. CHRONOLOGICAL TRAIN / TEST SPLIT
# ========================================

split = int(len(df) * 0.8)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]


# ========================================
# 8. TRAIN MODEL
# ========================================

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)


# ========================================
# 9. PREDICTION
# ========================================

predictions = model.predict(X_test)


# ========================================
# 10. MODEL EVALUATION
# ========================================

mae = mean_absolute_error(
    y_test,
    predictions
)


print("\n========================================")
print("      WEATHER-AWARE AI FORECAST")
print("========================================")

print(
    "Product:",
    df["item_id"].iloc[0]
)

print(
    "Store:",
    df["store_id"].iloc[0]
)

print(
    "Training records:",
    len(X_train)
)

print(
    "Testing records:",
    len(X_test)
)

print(
    "MAE:",
    round(mae, 2)
)


# ========================================
# 11. SAMPLE PREDICTIONS
# ========================================

result = pd.DataFrame({
    "Date": df.iloc[split:]["date"].values,
    "Actual": y_test.values,
    "Predicted": predictions.round(2),
    "Festival": df.iloc[split:]["festival"].values,
    "Temperature":
        df.iloc[split:]["temperature_mean"].values,
    "Rain":
        df.iloc[split:]["rain"].values
})

print("\nSample Predictions:")

print(
    result.tail(10)
    .to_string(index=False)
)


# ========================================
# 12. FEATURE IMPORTANCE
# ========================================

importance = pd.DataFrame({
    "Feature": features,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

print("\nFeature Importance:")

print(
    importance.to_string(index=False)
)