import pandas as pd


# ============================================================
# AI RECOMMENDATION ENGINE
# ============================================================

# -----------------------------
# 1. Load Data
# -----------------------------
sales = pd.read_csv("data/retail_context_integrated.csv")
inventory = pd.read_csv("data/inventory.csv")
mapping = pd.read_csv("data/festival_product_mapping.csv")
festivals = pd.read_csv("data/indian_festivals.csv")

sales["date"] = pd.to_datetime(sales["date"])
festivals["date"] = pd.to_datetime(festivals["date"])


# ============================================================
# 2. Product and Store
# ============================================================

item_id = "FOODS_3_090"
store_id = "CA_1"

forecast_date = pd.Timestamp("2026-09-14")


# ============================================================
# 3. Get Inventory
# ============================================================

inventory_row = inventory[
    (inventory["item_id"] == item_id) &
    (inventory["store_id"] == store_id)
]

if inventory_row.empty:

    print("Inventory information not found.")

    exit()

current_stock = int(
    inventory_row.iloc[0]["current_stock"]
)

incoming_stock = int(
    inventory_row.iloc[0]["incoming_stock"]
)

lead_time = int(
    inventory_row.iloc[0]["lead_time_days"]
)


# ============================================================
# 4. Recent Sales
# ============================================================

product_sales = sales[
    (sales["item_id"] == item_id) &
    (sales["store_id"] == store_id)
].sort_values("date")


recent_sales = product_sales.tail(7)["sales"]

recent_daily_demand = recent_sales.mean()


# ============================================================
# 5. Festival Context
# ============================================================

festival_match = festivals[
    festivals["date"] == forecast_date
]

if festival_match.empty:

    festival_name = "No Festival"

else:

    festival_name = festival_match.iloc[0]["festival"]


# ============================================================
# 6. Festival Impact
# ============================================================

festival_impact = "Low"

if festival_name != "No Festival":

    festival_mapping = mapping[
        (mapping["festival"] == festival_name) &
        (mapping["product_category"] == "FOODS")
    ]

    if not festival_mapping.empty:

        festival_impact = festival_mapping.iloc[0][
            "expected_impact"
        ]


# ============================================================
# 7. Weather Context
# ============================================================

# Current forecast values
rain_mm = 1.2
temperature = 24.6


if rain_mm > 10:

    weather_impact = "High"

elif rain_mm > 0:

    weather_impact = "Medium"

else:

    weather_impact = "Low"


# ============================================================
# 8. Context Adjustment
# ============================================================

predicted_demand = recent_daily_demand


# Festival adjustment
if festival_impact == "High":

    predicted_demand *= 1.20

elif festival_impact == "Medium":

    predicted_demand *= 1.10


# Weather adjustment
if weather_impact == "High":

    predicted_demand *= 1.10

elif weather_impact == "Medium":

    predicted_demand *= 1.05


predicted_demand = round(predicted_demand)


# ============================================================
# 9. Safety Stock
# ============================================================

sales_std = product_sales.tail(30)["sales"].std()

if pd.isna(sales_std):

    safety_stock = 0

else:

    safety_stock = round(sales_std * 0.5)


# ============================================================
# 10. Available Stock
# ============================================================

available_stock = (
    current_stock +
    incoming_stock
)


# ============================================================
# 11. Reorder Quantity
# ============================================================

reorder_quantity = max(
    0,
    predicted_demand +
    safety_stock -
    available_stock
)


# ============================================================
# 12. Stock Cover
# ============================================================

if recent_daily_demand > 0:

    stock_cover = (
        available_stock /
        recent_daily_demand
    )

else:

    stock_cover = 0


stock_cover = round(stock_cover, 1)


# ============================================================
# 13. Risk Level
# ============================================================

if stock_cover < lead_time:

    risk_level = "HIGH"

elif stock_cover < lead_time + 2:

    risk_level = "MEDIUM"

else:

    risk_level = "LOW"


# ============================================================
# 14. Recommendation
# ============================================================

if reorder_quantity > 0:

    recommendation = (
        f"Increase stock by "
        f"{reorder_quantity} units"
    )

else:

    recommendation = "Stock level is healthy"


# ============================================================
# 15. AI Explanation
# ============================================================

reasons = []

if festival_impact == "High":

    reasons.append(
        f"{festival_name} may increase demand"
    )

elif festival_impact == "Medium":

    reasons.append(
        f"{festival_name} may moderately increase demand"
    )


if weather_impact == "High":

    reasons.append(
        "High rainfall may affect product demand"
    )

elif weather_impact == "Medium":

    reasons.append(
        "Rain is expected"
    )


if current_stock < predicted_demand:

    reasons.append(
        "Current stock is below predicted demand"
    )


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 55)
print("             AI RECOMMENDATION ENGINE")
print("=" * 55)

print()

print("Product:", item_id)
print("Store:", store_id)
print("Forecast Date:", forecast_date.strftime("%Y-%m-%d"))

print()

print("----- INVENTORY -----")

print("Current Stock:", current_stock)
print("Incoming Stock:", incoming_stock)
print("Lead Time:", lead_time, "days")

print()

print("----- CONTEXT -----")

print("Festival:", festival_name)
print("Festival Impact:", festival_impact)

print("Temperature:", temperature, "°C")
print("Rain:", rain_mm, "mm")
print("Weather Impact:", weather_impact)

print()

print("----- AI ANALYSIS -----")

print(
    "Recent Daily Demand:",
    round(recent_daily_demand, 2)
)

print(
    "Predicted Demand:",
    predicted_demand
)

print(
    "Safety Stock:",
    safety_stock
)

print(
    "Available Stock:",
    available_stock
)

print(
    "Stock Cover:",
    stock_cover,
    "days"
)

print()

print("Risk Level:", risk_level)

print(
    "Recommended Action:",
    recommendation
)

print()

print("----- WHY AI RECOMMENDS THIS -----")

if reasons:

    for reason in reasons:

        print("•", reason)

else:

    print("No major context signals detected.")

print()

print("=" * 55)