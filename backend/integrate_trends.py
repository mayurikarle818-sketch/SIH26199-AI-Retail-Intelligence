import pandas as pd
import os

# File paths
base_file = "data/retail_context_integrated.csv"
trend_file = "data/online_trends.csv"
output_file = "data/retail_intelligence_integrated.csv"

# Load data
sales_data = pd.read_csv(base_file)
trend_data = pd.read_csv(trend_file)

# Convert dates
sales_data["date"] = pd.to_datetime(sales_data["date"])
trend_data["date"] = pd.to_datetime(trend_data["date"])

# Merge trend data using date + product category
merged_data = sales_data.merge(
    trend_data[
        [
            "date",
            "product_category",
            "trend_index",
            "trend_direction",
            "source"
        ]
    ],
    on=["date", "product_category"],
    how="left"
)

# Fill missing trend values
merged_data["trend_index"] = merged_data["trend_index"].fillna(0)
merged_data["trend_direction"] = merged_data["trend_direction"].fillna("No Data")
merged_data["source"] = merged_data["source"].fillna("No Data")

# Save integrated dataset
os.makedirs("data", exist_ok=True)

merged_data.to_csv(
    output_file,
    index=False
)

print("===================================")
print("ONLINE TREND INTEGRATION COMPLETE")
print("===================================")

print("Total records:", len(merged_data))
print(
    "Trend records:",
    (merged_data["trend_index"] > 0).sum()
)

print("\nSample trend data:")
print(
    merged_data[
        [
            "date",
            "product_category",
            "trend_index",
            "trend_direction"
        ]
    ].tail(10)
)

print("\nSaved to:")
print(output_file)