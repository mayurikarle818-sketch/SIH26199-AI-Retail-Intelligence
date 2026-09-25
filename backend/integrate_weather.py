import pandas as pd

# ============================================================
# 1. LOAD MULTI-PRODUCT M5 DATA
# ============================================================

sales_df = pd.read_csv(
    "data/m5_multi_product_sales.csv"
)

calendar_df = pd.read_csv(
    "data/calendar.csv"
)

festival_df = pd.read_csv(
    "data/indian_festivals_historical.csv"
)

mapping_df = pd.read_csv(
    "data/festival_product_mapping.csv"
)

weather_df = pd.read_csv(
    "data/weather_historical.csv"
)

print("\n========================================")
print("   DATA LOADING")
print("========================================")

print("Sales rows:", len(sales_df))
print("Products:", sales_df["item_id"].nunique())
print("Stores:", sales_df["store_id"].nunique())
print(
    "Product-Store combinations:",
    sales_df[["item_id", "store_id"]]
    .drop_duplicates()
    .shape[0]
)


# ============================================================
# 2. CONVERT DATES
# ============================================================

sales_df["date"] = pd.to_datetime(
    sales_df["date"]
)

calendar_df["date"] = pd.to_datetime(
    calendar_df["date"]
)

festival_df["date"] = pd.to_datetime(
    festival_df["date"]
)

weather_df["date"] = pd.to_datetime(
    weather_df["date"]
)


# ============================================================
# 3. SELECT REQUIRED SALES COLUMNS
# ============================================================

required_sales_columns = [
    "date",
    "item_id",
    "store_id",
    "sales",
    "cat_id"
]

# If cat_id is not present, create category from item information
if "cat_id" not in sales_df.columns:

    print(
        "\nWARNING: cat_id not found."
    )

    sales_df["product_category"] = (
        sales_df["item_id"]
        .str.split("_")
        .str[0]
    )

else:

    sales_df["product_category"] = (
        sales_df["cat_id"]
    )


# ============================================================
# 4. SORT DATA
# ============================================================

sales_df = sales_df.sort_values(
    by=[
        "item_id",
        "store_id",
        "date"
    ]
).reset_index(drop=True)


# ============================================================
# 5. ADD INDIAN FESTIVALS
# ============================================================

festival_columns = [
    "date",
    "festival",
    "category",
    "importance"
]

festival_available = [
    col
    for col in festival_columns
    if col in festival_df.columns
]

sales_df = sales_df.merge(
    festival_df[festival_available].drop_duplicates(
        subset=["date"]
    ),
    on="date",
    how="left"
)

sales_df["festival_flag"] = (
    sales_df["festival"]
    .notna()
    .astype(int)
)


# ============================================================
# 6. ADD FESTIVAL PRODUCT IMPACT
# ============================================================

if (
    "festival" in sales_df.columns
    and "festival" in mapping_df.columns
):

    mapping_columns = [
        "festival",
        "product_category",
        "expected_impact"
    ]

    mapping_available = [
        col
        for col in mapping_columns
        if col in mapping_df.columns
    ]

    if len(mapping_available) == 3:

        sales_df = sales_df.merge(
            mapping_df[
                mapping_available
            ].drop_duplicates(),
            on=[
                "festival",
                "product_category"
            ],
            how="left"
        )

else:

    sales_df["expected_impact"] = "None"


sales_df["expected_impact"] = (
    sales_df["expected_impact"]
    .fillna("None")
)


impact_mapping = {
    "None": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3
}


sales_df["festival_impact"] = (
    sales_df["expected_impact"]
    .map(impact_mapping)
    .fillna(0)
)


# ============================================================
# 7. ADD WEATHER
# ============================================================

weather_columns = [
    "date",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain"
]

weather_available = [
    col
    for col in weather_columns
    if col in weather_df.columns
]


sales_df = sales_df.merge(
    weather_df[
        weather_available
    ].drop_duplicates(
        subset=["date"]
    ),
    on="date",
    how="left"
)


# ============================================================
# 8. WEATHER FEATURES
# ============================================================

if "rain" in sales_df.columns:

    sales_df["rain"] = (
        pd.to_numeric(
            sales_df["rain"],
            errors="coerce"
        )
        .fillna(0)
    )

    sales_df["rain_flag"] = (
        sales_df["rain"] > 0
    ).astype(int)

    sales_df["heavy_rain_flag"] = (
        sales_df["rain"] >= 10
    ).astype(int)

else:

    sales_df["rain"] = 0
    sales_df["rain_flag"] = 0
    sales_df["heavy_rain_flag"] = 0


# ============================================================
# 9. WEEKDAY ENCODING
# ============================================================

if "weekday" in sales_df.columns:

    weekday_mapping = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    sales_df["weekday_code"] = (
        sales_df["weekday"]
        .map(weekday_mapping)
    )

else:

    sales_df["weekday_code"] = (
        sales_df["date"]
        .dt.dayofweek
    )


# ============================================================
# 10. CALENDAR FEATURES
# ============================================================

sales_df["month"] = (
    sales_df["date"].dt.month
)

sales_df["year"] = (
    sales_df["date"].dt.year
)

sales_df["day_of_week"] = (
    sales_df["date"].dt.dayofweek
)

sales_df["week_of_year"] = (
    sales_df["date"]
    .dt.isocalendar()
    .week
    .astype(int)
)


# ============================================================
# 11. GROUP-WISE LAG FEATURES
# ============================================================

group_columns = [
    "item_id",
    "store_id"
]

sales_df["lag_1"] = (
    sales_df
    .groupby(group_columns)["sales"]
    .shift(1)
)

sales_df["lag_7"] = (
    sales_df
    .groupby(group_columns)["sales"]
    .shift(7)
)


# ============================================================
# 12. GROUP-WISE ROLLING SALES
# ============================================================

sales_df["rolling_7"] = (
    sales_df
    .groupby(group_columns)["sales"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(
            window=7,
            min_periods=1
        )
        .mean()
    )
)


sales_df["rolling_30"] = (
    sales_df
    .groupby(group_columns)["sales"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(
            window=30,
            min_periods=1
        )
        .mean()
    )
)


# ============================================================
# 13. CLEAN NUMERIC FEATURES
# ============================================================

numeric_columns = [
    "sales",
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_30",
    "festival_impact",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain"
]

for column in numeric_columns:

    if column in sales_df.columns:

        sales_df[column] = pd.to_numeric(
            sales_df[column],
            errors="coerce"
        )


# ============================================================
# 14. SAVE FINAL INTEGRATED DATASET
# ============================================================

output_file = (
    "data/m5_multi_product_context.csv"
)


sales_df.to_csv(
    output_file,
    index=False
)


# ============================================================
# 15. FINAL REPORT
# ============================================================

print("\n========================================")
print("   INTEGRATION COMPLETE")
print("========================================")

print(
    "Total rows:",
    len(sales_df)
)

print(
    "Products:",
    sales_df["item_id"].nunique()
)

print(
    "Stores:",
    sales_df["store_id"].nunique()
)

print(
    "Product-Store combinations:",
    sales_df[
        ["item_id", "store_id"]
    ]
    .drop_duplicates()
    .shape[0]
)

print(
    "Start date:",
    sales_df["date"].min()
)

print(
    "End date:",
    sales_df["date"].max()
)

print(
    "Festival days:",
    sales_df["festival_flag"].sum()
)

print(
    "Rainy rows:",
    sales_df["rain_flag"].sum()
)

print(
    "Heavy rain rows:",
    sales_df["heavy_rain_flag"].sum()
)

print("\nColumns:")

print(
    sales_df.columns.tolist()
)

print("\nSample data:")

print(
    sales_df[
        [
            "date",
            "item_id",
            "store_id",
            "sales",
            "festival_flag",
            "festival_impact",
            "temperature_mean",
            "rain",
            "lag_1",
            "lag_7",
            "rolling_7"
        ]
    ].tail(10).to_string(
        index=False
    )
)

print("\n========================================")
print("Integrated dataset saved successfully!")
print("File:", output_file)
print("========================================")