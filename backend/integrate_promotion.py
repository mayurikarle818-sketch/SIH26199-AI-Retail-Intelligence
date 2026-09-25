import pandas as pd

# ========================================
# 1. LOAD DATA
# ========================================

df = pd.read_csv(
    "data/sales_festival_weather_integrated.csv"
)

promotions = pd.read_csv(
    "data/promotions.csv"
)

df["date"] = pd.to_datetime(df["date"])
promotions["date"] = pd.to_datetime(promotions["date"])


# ========================================
# 2. MERGE PROMOTIONS
# ========================================

df = df.merge(
    promotions[
        [
            "date",
            "promotion_name",
            "promotion_type",
            "discount_percentage",
            "promotion_flag"
        ]
    ],
    on="date",
    how="left"
)


# ========================================
# 3. HANDLE NO PROMOTION DAYS
# ========================================

df["promotion_name"] = (
    df["promotion_name"]
    .fillna("No Promotion")
)

df["promotion_type"] = (
    df["promotion_type"]
    .fillna("None")
)

df["discount_percentage"] = (
    df["discount_percentage"]
    .fillna(0)
)

df["promotion_flag"] = (
    df["promotion_flag"]
    .fillna(0)
)


# ========================================
# 4. DISPLAY RESULTS
# ========================================

print("\n========================================")
print(" SALES + FESTIVAL + WEATHER + PROMOTION")
print("========================================")

print("Total Records:", len(df))

print(
    "Promotion Days:",
    int(df["promotion_flag"].sum())
)

print(
    "Average Discount:",
    round(df["discount_percentage"].mean(), 2),
)


# ========================================
# 5. SHOW PROMOTION DATA
# ========================================

promotion_data = df[
    df["promotion_flag"] == 1
]

print("\nPromotion Records:")

print(
    promotion_data[
        [
            "date",
            "sales",
            "festival",
            "temperature_mean",
            "rain",
            "promotion_name",
            "discount_percentage"
        ]
    ].to_string(index=False)
)


# ========================================
# 6. SAVE FINAL DATASET
# ========================================

output_file = (
    "data/retail_context_integrated.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\n========================================")
print("FINAL INTEGRATED DATASET SAVED")
print("========================================")

print("File:", output_file)