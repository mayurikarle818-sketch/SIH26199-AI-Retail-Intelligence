import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ============================================================
# 1. LOAD FINAL MULTI-PRODUCT CONTEXT DATA
# ============================================================

df = pd.read_csv(
    "data/m5_multi_product_context.csv"
)

print("\n========================================")
print("     AI DEMAND FORECASTING PIPELINE")
print("========================================")


# ============================================================
# 2. BASIC DATA PREPARATION
# ============================================================

df["date"] = pd.to_datetime(df["date"])

df["sales"] = pd.to_numeric(
    df["sales"],
    errors="coerce"
)

df = df.sort_values(
    ["item_id", "store_id", "date"]
).reset_index(drop=True)


# ============================================================
# 3. DATASET INFORMATION
# ============================================================

group_cols = [
    "item_id",
    "store_id"
]

print("\n========================================")
print("        DATASET INFORMATION")
print("========================================")

print(
    "Total records:",
    len(df)
)

print(
    "Products:",
    df["item_id"].nunique()
)

print(
    "Stores:",
    df["store_id"].nunique()
)

print(
    "Product-Store combinations:",
    df[group_cols]
    .drop_duplicates()
    .shape[0]
)

print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)


# ============================================================
# 4. CHECK ZERO SALES
# ============================================================

zero_sales = (
    df["sales"] == 0
).sum()

zero_percentage = (
    zero_sales / len(df)
) * 100

print(
    "\nZero-sales records:",
    zero_sales
)

print(
    "Zero-sales percentage:",
    round(zero_percentage, 2),
    "%"
)


# ============================================================
# 5. REQUIRED COLUMNS
# ============================================================

required_columns = [
    "sales",
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_30",
    "month",
    "weekday_code",
    "festival_flag",
    "festival_impact",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:

    print(
        "\nERROR: Missing columns:"
    )

    print(
        missing_columns
    )

    raise ValueError(
        "Required columns are missing."
    )


# ============================================================
# 6. HANDLE MISSING VALUES
# ============================================================

df["festival_flag"] = (
    df["festival_flag"]
    .fillna(0)
)

df["festival_impact"] = (
    df["festival_impact"]
    .fillna(0)
)


weather_columns = [
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag"
]

for col in weather_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

    df[col] = df[col].fillna(
        df[col].median()
    )


# ============================================================
# 7. NUMERIC CLEANING
# ============================================================

numeric_columns = [
    "sales",
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_30",
    "month",
    "weekday_code",
    "festival_flag",
    "festival_impact",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag"
]

for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ============================================================
# 8. REMOVE INVALID ML RECORDS
# ============================================================

df = df.dropna(
    subset=[
        "sales",
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_30",
        "weekday_code"
    ]
).reset_index(drop=True)


# ============================================================
# 9. FEATURES
# ============================================================

baseline_features = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_30",
    "month",
    "weekday_code"
]


festival_features = (
    baseline_features
    +
    [
        "festival_flag",
        "festival_impact"
    ]
)


context_features = (
    festival_features
    +
    [
        "temperature_mean",
        "temperature_max",
        "temperature_min",
        "precipitation",
        "rain",
        "rain_flag",
        "heavy_rain_flag"
    ]
)


# ============================================================
# 10. TIME-BASED TRAIN / TEST SPLIT
# ============================================================

# Use the same date cutoff for ALL product-store combinations.
# This prevents future dates from entering training.

unique_dates = sorted(
    df["date"].unique()
)

split_index = int(
    len(unique_dates) * 0.80
)

train_end_date = unique_dates[
    split_index - 1
]

test_start_date = unique_dates[
    split_index
]

train_df = df[
    df["date"] <= train_end_date
].copy()

test_df = df[
    df["date"] >= test_start_date
].copy()


print("\n========================================")
print("        TRAIN / TEST SPLIT")
print("========================================")

print(
    "Training records:",
    len(train_df)
)

print(
    "Testing records:",
    len(test_df)
)

print(
    "Training period:",
    train_df["date"].min().date(),
    "to",
    train_df["date"].max().date()
)

print(
    "Testing period:",
    test_df["date"].min().date(),
    "to",
    test_df["date"].max().date()
)


# ============================================================
# 11. MODEL TRAINING FUNCTION
# ============================================================

def train_and_evaluate(feature_list):

    X_train = train_df[
        feature_list
    ]

    X_test = test_df[
        feature_list
    ]

    y_train = train_df[
        "sales"
    ]

    y_test = test_df[
        "sales"
    ]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    return (
        model,
        predictions,
        mae,
        rmse
    )


# ============================================================
# 12. BASELINE MODEL
# ============================================================

print(
    "\nTraining Baseline Model..."
)

(
    baseline_model,
    baseline_pred,
    baseline_mae,
    baseline_rmse
) = train_and_evaluate(
    baseline_features
)


# ============================================================
# 13. FESTIVAL-AWARE MODEL
# ============================================================

print(
    "Training Festival-Aware Model..."
)

(
    festival_model,
    festival_pred,
    festival_mae,
    festival_rmse
) = train_and_evaluate(
    festival_features
)


# ============================================================
# 14. CONTEXT-AWARE MODEL
# ============================================================

print(
    "Training Context-Aware Model..."
)

(
    context_model,
    context_pred,
    context_mae,
    context_rmse
) = train_and_evaluate(
    context_features
)


# ============================================================
# 15. MODEL COMPARISON
# ============================================================

print("\n========================================")
print("          MODEL COMPARISON")
print("========================================")

print(
    "Baseline MAE:",
    round(baseline_mae, 2)
)

print(
    "Festival Model MAE:",
    round(festival_mae, 2)
)

print(
    "Context-Aware Model MAE:",
    round(context_mae, 2)
)

print(
    "\nBaseline RMSE:",
    round(baseline_rmse, 2)
)

print(
    "Festival Model RMSE:",
    round(festival_rmse, 2)
)

print(
    "Context-Aware Model RMSE:",
    round(context_rmse, 2)
)


# ============================================================
# 16. IMPROVEMENT CALCULATION
# ============================================================

festival_improvement = (
    baseline_mae
    -
    festival_mae
)

context_improvement = (
    baseline_mae
    -
    context_mae
)

festival_improvement_pct = (
    festival_improvement
    /
    baseline_mae
) * 100

context_improvement_pct = (
    context_improvement
    /
    baseline_mae
) * 100


print("\n========================================")
print("             IMPROVEMENT")
print("========================================")

print(
    "Festival MAE change:",
    round(
        festival_improvement,
        2
    )
)

print(
    "Festival MAE change (%):",
    round(
        festival_improvement_pct,
        2
    ),
    "%"
)

print(
    "Context MAE change:",
    round(
        context_improvement,
        2
    )
)

print(
    "Context MAE change (%):",
    round(
        context_improvement_pct,
        2
    ),
    "%"
)


# ============================================================
# 17. CONTEXT-AWARE PREDICTIONS
# ============================================================

result = test_df[
    [
        "date",
        "item_id",
        "store_id",
        "sales",
        "festival",
        "temperature_mean",
        "rain"
    ]
].copy()

result["predicted_sales"] = (
    context_pred.round(2)
)

result = result.rename(
    columns={
        "sales": "actual_sales"
    }
)


print(
    "\n========================================"
)

print(
    "     SAMPLE CONTEXT-AWARE PREDICTIONS"
)

print(
    "========================================"
)

print(
    result
    .tail(10)
    .to_string(
        index=False
    )
)


# ============================================================
# 18. FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({

    "Feature":
        context_features,

    "Importance":
        context_model
        .feature_importances_

})


importance = importance.sort_values(
    by="Importance",
    ascending=False
)


print(
    "\n========================================"
)

print(
    "          FEATURE IMPORTANCE"
)

print(
    "========================================"
)

print(
    importance
    .to_string(index=False)
)


# ============================================================
# 19. SAVE MODEL RESULTS
# ============================================================

result.to_csv(
    "data/demand_forecast_test_results.csv",
    index=False
)

importance.to_csv(
    "data/demand_feature_importance.csv",
    index=False
)


# ============================================================
# 20. FINAL SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "             FINAL SUMMARY"
)

print(
    "========================================"
)

print(
    "Dataset records:",
    len(df)
)

print(
    "Products:",
    df["item_id"].nunique()
)

print(
    "Stores:",
    df["store_id"].nunique()
)

print(
    "Product-Store combinations:",
    df[group_cols]
    .drop_duplicates()
    .shape[0]
)

print(
    "Baseline MAE:",
    round(baseline_mae, 2)
)

print(
    "Festival MAE:",
    round(festival_mae, 2)
)

print(
    "Context-Aware MAE:",
    round(context_mae, 2)
)

print(
    "Baseline RMSE:",
    round(baseline_rmse, 2)
)

print(
    "Festival RMSE:",
    round(festival_rmse, 2)
)

print(
    "Context-Aware RMSE:",
    round(context_rmse, 2)
)


if context_mae < baseline_mae:

    print(
        "\nObservation:"
    )

    print(
        "Context-aware model has lower MAE "
        "than the baseline on this test period."
    )

elif context_mae > baseline_mae:

    print(
        "\nObservation:"
    )

    print(
        "Baseline has lower MAE than the "
        "context-aware model on this test period."
    )

else:

    print(
        "\nObservation:"
    )

    print(
        "Both models have the same MAE "
        "on this test period."
    )


print(
    "\nAI forecasting evaluation completed."
)

print(
    "Results saved:"
)

print(
    "data/demand_forecast_test_results.csv"
)

print(
    "data/demand_feature_importance.csv"
)