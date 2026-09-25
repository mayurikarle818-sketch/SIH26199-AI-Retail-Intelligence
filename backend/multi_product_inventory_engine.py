import pandas as pd
import numpy as np

# ==========================================
# FILES
# ==========================================

prediction_file = "data/multi_product_predictions.csv"
inventory_file = "data/inventory_multi_product.csv"

output_file = "data/multi_product_recommendations.csv"

# ==========================================
# LOAD DATA
# ==========================================

print("Loading prediction and inventory data...")

pred = pd.read_csv(prediction_file)
inventory = pd.read_csv(inventory_file)
pred = pred.rename(
    columns={
        "product": "item_id",
        "store": "store_id"
    }
)

# ==========================================
# MERGE
# ==========================================

df = pred.merge(
    inventory,
    on=["item_id", "store_id"],
    how="left"
)

# ==========================================
# SAFETY STOCK
# ==========================================

# Use recent prediction error (MAE)
# as a simple MVP uncertainty measure.

df["safety_stock"] = np.ceil(
    df["mae"] * 0.5
).astype(int)

# ==========================================
# REORDER POINT
# ==========================================

df["reorder_point"] = np.ceil(
    (
        df["predicted_demand"]
        * df["lead_time_days"]
    )
    + df["safety_stock"]
).astype(int)

# ==========================================
# AVAILABLE STOCK
# ==========================================

df["available_stock"] = (
    df["current_stock"]
    + df["incoming_stock"]
)

# ==========================================
# STOCK COVER
# ==========================================

df["stock_cover_days"] = np.where(
    df["predicted_demand"] > 0,
    df["available_stock"]
    / df["predicted_demand"],
    999
)

df["stock_cover_days"] = df[
    "stock_cover_days"
].round(1)

# ==========================================
# RISK CLASSIFICATION
# ==========================================

def calculate_risk(row):

    if row["available_stock"] <= 0:
        return "CRITICAL"

    if (
        row["available_stock"]
        < row["reorder_point"]
    ):
        return "HIGH"

    if (
        row["stock_cover_days"]
        < row["lead_time_days"]
    ):
        return "HIGH"

    if (
        row["stock_cover_days"]
        < row["lead_time_days"] + 2
    ):
        return "MEDIUM"

    if (
        row["stock_cover_days"] > 14
    ):
        return "OVERSTOCK"

    return "LOW"


df["risk"] = df.apply(
    calculate_risk,
    axis=1
)

# ==========================================
# RECOMMENDED ORDER
# ==========================================

df["recommended_order"] = np.maximum(
    0,
    df["reorder_point"]
    - df["available_stock"]
).astype(int)

# ==========================================
# ACTION
# ==========================================

def recommendation(row):

    if row["risk"] in ["CRITICAL", "HIGH"]:
        return "Increase Stock"

    if row["risk"] == "MEDIUM":
        return "Plan Reorder"

    if row["risk"] == "OVERSTOCK":
        return "Reduce Stock"

    return "Stock Healthy"


df["recommendation"] = df.apply(
    recommendation,
    axis=1
)

# ==========================================
# EXPLANATION
# ==========================================

def explanation(row):

    if row["risk"] == "CRITICAL":
        return (
            "No available stock. "
            "Immediate replenishment required."
        )

    if row["risk"] == "HIGH":
        return (
            f"Available stock is {int(row['available_stock'])}, "
            f"below the reorder point of "
            f"{int(row['reorder_point'])}. "
            f"Predicted demand is "
            f"{int(row['predicted_demand'])}."
        )

    if row["risk"] == "MEDIUM":
        return (
            "Stock is available but coverage "
            "is getting close to the lead-time requirement."
        )

    if row["risk"] == "OVERSTOCK":
        return (
            "Inventory coverage is high. "
            "Consider reducing replenishment."
        )

    return (
        "Current inventory provides healthy "
        "coverage for predicted demand."
    )


df["explanation"] = df.apply(
    explanation,
    axis=1
)

# ==========================================
# SELECT OUTPUT COLUMNS
# ==========================================

output_columns = [
    "item_id",
    "store_id",
    "last_date",
    "predicted_demand",
    "current_stock",
    "incoming_stock",
    "available_stock",
    "lead_time_days",
    "safety_stock",
    "reorder_point",
    "stock_cover_days",
    "risk",
    "recommended_order",
    "recommendation",
    "mae",
    "explanation"
]
    
result = df[output_columns].copy()

# ==========================================
# SAVE
# ==========================================

result.to_csv(
    output_file,
    index=False
)

# ==========================================
# DISPLAY
# ==========================================

print("\n========================================")
print("MULTI-PRODUCT INVENTORY INTELLIGENCE")
print("========================================")

print(
    result.to_string(index=False)
)

print("\n----------------------------------------")
print("Risk Summary")
print("----------------------------------------")

print(
    result["risk"].value_counts()
)

print("\n----------------------------------------")
print("Total Recommended Units")
print("----------------------------------------")

print(
    int(result["recommended_order"].sum())
)

print("\nSaved to:")
print(output_file)