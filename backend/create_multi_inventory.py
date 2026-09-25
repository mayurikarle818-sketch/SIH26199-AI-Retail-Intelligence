import pandas as pd
import os

# ==========================================
# LOAD REAL SALES DATA
# ==========================================

sales_file = "data/m5_multi_product_sales.csv"

df = pd.read_csv(sales_file)

df["date"] = pd.to_datetime(df["date"])

# ==========================================
# GET 10 REAL PRODUCTS
# ==========================================

products = df["item_id"].unique()

inventory = []

for product in products:

    product_df = df[
        df["item_id"] == product
    ].sort_values("date")

    # Recent 7-day average demand
    recent_demand = (
        product_df["sales"]
        .tail(7)
        .mean()
    )

    # Demo inventory snapshot
    # Based on recent real demand
    current_stock = round(
        recent_demand * 1.5
    )

    # Lead time assumption for MVP
    lead_time_days = 2

    # Incoming stock
    incoming_stock = 0

    inventory.append(
        {
            "item_id": product,
            "store_id": product_df["store_id"].iloc[0],
            "current_stock": int(current_stock),
            "incoming_stock": incoming_stock,
            "lead_time_days": lead_time_days,
            "source": "MVP Inventory Snapshot"
        }
    )

# ==========================================
# SAVE
# ==========================================

inventory_df = pd.DataFrame(inventory)

os.makedirs("data", exist_ok=True)

output = "data/inventory_multi_product.csv"

inventory_df.to_csv(
    output,
    index=False
)

# ==========================================
# DISPLAY
# ==========================================

print("\n===================================")
print("MULTI-PRODUCT INVENTORY CREATED")
print("===================================")

print(
    inventory_df.to_string(index=False)
)

print("\nProducts:", len(inventory_df))

print("\nSaved to:")
print(output)