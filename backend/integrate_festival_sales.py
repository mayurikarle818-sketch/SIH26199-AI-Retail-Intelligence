import pandas as pd

# ========================================
# 1. LOAD DATASETS
# ========================================

sales_df = pd.read_csv("data/sales_train_validation.csv")
calendar_df = pd.read_csv("data/calendar.csv")
festival_df = pd.read_csv("data/indian_festivals_historical.csv")
mapping_df = pd.read_csv("data/festival_product_mapping.csv")

# Convert date columns to datetime
calendar_df["date"] = pd.to_datetime(calendar_df["date"])
festival_df["date"] = pd.to_datetime(festival_df["date"])


# ========================================
# 2. SELECT PRODUCT
# ========================================

product = sales_df[
    sales_df["item_id"] == "FOODS_3_090"
].iloc[0]

print("Selected Product:", product["item_id"])


# ========================================
# 3. CONVERT SALES TO DAILY FORMAT
# ========================================

sales = product.iloc[6:].values

df = pd.DataFrame({
    "d": [f"d_{i}" for i in range(1, len(sales) + 1)],
    "sales": sales
})


# ========================================
# 4. ADD DATE FROM M5 CALENDAR
# ========================================

df = df.merge(
    calendar_df[["d", "date"]],
    on="d",
    how="left"
)

df["date"] = pd.to_datetime(df["date"])


# ========================================
# 5. ADD PRODUCT INFORMATION
# ========================================

df["item_id"] = product["item_id"]
df["product_category"] = product["cat_id"]
df["store_id"] = product["store_id"]


# ========================================
# 6. ADD INDIAN FESTIVAL INFORMATION
# ========================================

df = df.merge(
    festival_df[
        ["date", "festival", "category", "importance"]
    ],
    on="date",
    how="left"
)


# ========================================
# 7. CREATE FESTIVAL FLAG
# ========================================

df["festival_flag"] = df["festival"].notna().astype(int)


# ========================================
# 8. MATCH FESTIVAL WITH PRODUCT CATEGORY
# ========================================

df = df.merge(
    mapping_df[
        ["festival", "product_category", "expected_impact"]
    ],
    on=["festival", "product_category"],
    how="left"
)


# ========================================
# 9. HANDLE MISSING VALUES
# ========================================

df["festival"] = df["festival"].fillna("No Festival")
df["category"] = df["category"].fillna("None")
df["importance"] = df["importance"].fillna("None")
df["expected_impact"] = df["expected_impact"].fillna("None")


# ========================================
# 10. CREATE NUMERIC IMPACT FEATURE
# ========================================

impact_mapping = {
    "None": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3
}

df["festival_impact"] = (
    df["expected_impact"]
    .map(impact_mapping)
    .fillna(0)
)


# ========================================
# 11. DISPLAY RESULTS
# ========================================

print("\n========================================")
print("      FESTIVAL + SALES INTEGRATION")
print("========================================")

print("Product:", product["item_id"])
print("Category:", product["cat_id"])
print("Store:", product["store_id"])

print("\nTotal Sales Records:", len(df))

print(
    "Total Festival Days:",
    df["festival_flag"].sum()
)


# ========================================
# 12. SHOW FESTIVAL SALES
# ========================================

festival_sales = df[
    df["festival_flag"] == 1
]

print("\nFestival Sales Records:")

if len(festival_sales) > 0:

    print(
        festival_sales[
            [
                "date",
                "sales",
                "festival",
                "product_category",
                "expected_impact",
                "festival_impact"
            ]
        ].to_string(index=False)
    )

else:

    print("No matching festival records found.")


# ========================================
# 13. SAVE INTEGRATED DATASET
# ========================================

output_file = "data/festival_sales_integrated.csv"

df.to_csv(
    output_file,
    index=False
)

print("\n========================================")
print("Integrated dataset saved successfully!")
print("File:", output_file)
print("========================================")