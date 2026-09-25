import pandas as pd

# Load data
sales_df = pd.read_csv("data/sales_train_validation.csv")
calendar_df = pd.read_csv("data/calendar.csv")
festival_df = pd.read_csv("data/indian_festivals.csv")
mapping_df = pd.read_csv("data/festival_product_mapping.csv")

# Select one product for testing
product = sales_df[sales_df["item_id"] == "FOODS_3_090"].iloc[0]

# Convert sales into daily format
sales = product.iloc[6:].values

df = pd.DataFrame({
    "sales": sales
})

df["d"] = [f"d_{i}" for i in range(1, len(df) + 1)]

# Add dates from M5 calendar
df = df.merge(
    calendar_df[["d", "date"]],
    on="d",
    how="left"
)

df["date"] = pd.to_datetime(df["date"])

# Product category
product_category = product["cat_id"]

df["product_category"] = product_category

# Add festival information
festival_df["date"] = pd.to_datetime(festival_df["date"])

df = df.merge(
    festival_df[["date", "festival", "category", "importance"]],
    on="date",
    how="left"
)

# Rename festival category
df["festival_category"] = df["category"].fillna("No Festival")

# Add festival flag
df["festival_flag"] = df["festival"].notna().astype(int)

# Match festival with product category
mapping_df = mapping_df.rename(
    columns={"product_category": "cat_id"}
)

df = df.merge(
    mapping_df,
    left_on=["festival", "product_category"],
    right_on=["festival", "cat_id"],
    how="left"
)

df["expected_impact"] = df["expected_impact"].fillna("None")

print("\n========================================")
print("       FESTIVAL IMPACT ANALYSIS")
print("========================================")

print("Product:", product["item_id"])
print("Category:", product_category)

print("\nFestival Records:")
print(
    df[df["festival"].notna()][
        [
            "date",
            "festival",
            "product_category",
            "expected_impact"
        ]
    ].head(20).to_string(index=False)
)

print("\nTotal Festival Days:", df["festival_flag"].sum())