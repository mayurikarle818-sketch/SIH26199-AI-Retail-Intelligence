import pandas as pd
import os


# ========================================
# 1. FILE PATHS
# ========================================

sales_file = "data/sales_train_validation.csv"

calendar_file = "data/calendar.csv"

output_file = "data/m5_multi_product_sales.csv"


# ========================================
# 2. LOAD M5 DATA
# ========================================

print("\n========================================")
print("     M5 MULTI-PRODUCT DATA PREPARATION")
print("========================================")

print("\nLoading M5 sales data...")

sales_df = pd.read_csv(
    sales_file
)

calendar_df = pd.read_csv(
    calendar_file
)

print(
    "Original rows:",
    len(sales_df)
)


# ========================================
# 3. IDENTIFY DAILY SALES COLUMNS
# ========================================

sales_columns = [

    col
    for col in sales_df.columns
    if col.startswith("d_")

]

print(
    "Daily sales columns:",
    len(sales_columns)
)


# ========================================
# 4. IDENTIFY ALL STORES
# ========================================

stores = sorted(
    sales_df["store_id"].unique()
)

print(
    "\nStores found:",
    len(stores)
)

print(
    "Stores:",
    stores
)


# ========================================
# 5. SELECT TOP PRODUCTS PER STORE
# ========================================

TOP_PRODUCTS_PER_STORE = 10


selected_store_data = []


print(
    "\nSelecting top",
    TOP_PRODUCTS_PER_STORE,
    "real products per store..."
)


for store in stores:

    print(
        "\nProcessing store:",
        store
    )

    store_df = sales_df[
        sales_df["store_id"] == store
    ].copy()


    # Calculate total historical sales
    store_df["total_sales"] = (

        store_df[sales_columns]
        .sum(axis=1)

    )


    # Select top products
    top_products = (

        store_df
        .sort_values(
            "total_sales",
            ascending=False
        )
        .head(
            TOP_PRODUCTS_PER_STORE
        )

    )


    selected_store_data.append(
        top_products
    )


# Combine selected products
selected = pd.concat(
    selected_store_data,
    ignore_index=True
)


# ========================================
# 6. DISPLAY SELECTED DATA
# ========================================

print(
    "\n========================================"
)

print(
    "       SELECTED PRODUCT SUMMARY"
)

print(
    "========================================"
)


print(
    "Selected rows:",
    len(selected)
)


print(
    "Unique products:",
    selected["item_id"].nunique()
)


print(
    "Unique stores:",
    selected["store_id"].nunique()
)


print(
    "Product-store combinations:",
    len(
        selected[
            ["item_id", "store_id"]
        ].drop_duplicates()
    )
)


print(
    "\nSelected products:"
)


print(

    selected[
        [
            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "total_sales"
        ]
    ]
    .sort_values(
        ["store_id", "total_sales"],
        ascending=[True, False]
    )
    .to_string(index=False)

)


# ========================================
# 7. CONVERT WIDE → LONG
# ========================================

print(
    "\n========================================"
)

print(
    "      CONVERTING WIDE DATA TO LONG"
)

print(
    "========================================"
)


long_df = selected.melt(

    id_vars=[

        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id"

    ],

    value_vars=sales_columns,

    var_name="d",

    value_name="sales"

)


print(
    "Long-format rows:",
    len(long_df)
)


# ========================================
# 8. MERGE CALENDAR DATA
# ========================================

print(
    "\nMerging calendar data..."
)


calendar_columns = [

    "date",
    "d",
    "weekday",
    "wday",
    "month",
    "year",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2"

]


long_df = long_df.merge(

    calendar_df[
        calendar_columns
    ],

    on="d",

    how="left"

)


# ========================================
# 9. DATA CLEANING
# ========================================

print(
    "Cleaning data..."
)


long_df["date"] = pd.to_datetime(
    long_df["date"]
)


long_df["sales"] = pd.to_numeric(

    long_df["sales"],

    errors="coerce"

).fillna(0)


# Sort correctly for time-series processing
long_df = long_df.sort_values(

    [
        "item_id",
        "store_id",
        "date"
    ]

).reset_index(
    drop=True
)


# ========================================
# 10. REMOVE DUPLICATES
# ========================================

long_df = long_df.drop_duplicates(

    subset=[
        "item_id",
        "store_id",
        "date"
    ]

)


# ========================================
# 11. SAVE FINAL DATASET
# ========================================

os.makedirs(
    "data",
    exist_ok=True
)


long_df.to_csv(

    output_file,

    index=False

)


# ========================================
# 12. FINAL REPORT
# ========================================

print(
    "\n========================================"
)

print(
    "             SUCCESS"
)

print(
    "========================================"
)


print(
    "Output file:",
    output_file
)


print(
    "Rows:",
    len(long_df)
)


print(
    "Products:",
    long_df["item_id"].nunique()
)


print(
    "Stores:",
    long_df["store_id"].nunique()
)


print(
    "Product-Store combinations:",

    len(
        long_df[
            [
                "item_id",
                "store_id"
            ]
        ]
        .drop_duplicates()
    )

)


print(
    "Start date:",
    long_df["date"].min().date()
)


print(
    "End date:",
    long_df["date"].max().date()
)


print(
    "\nSample data:"
)


print(

    long_df.head(10)
    .to_string(index=False)

)


print(
    "\nM5 multi-product dataset preparation completed."
)