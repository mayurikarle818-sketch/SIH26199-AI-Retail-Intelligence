import pandas as pd


# ============================================================
# CONTEXT IMPACT ENGINE
# ============================================================

# -----------------------------
# 1. Load Festival Data
# -----------------------------
festivals = pd.read_csv("data/indian_festivals.csv")
festivals["date"] = pd.to_datetime(festivals["date"])


# -----------------------------
# 2. Load Festival-Product Mapping
# -----------------------------
mapping = pd.read_csv("data/festival_product_mapping.csv")


# -----------------------------
# 3. Forecast Date
# -----------------------------
forecast_date = pd.Timestamp("2026-09-14")


# -----------------------------
# 4. Find Festival
# -----------------------------
festival_match = festivals[
    festivals["date"] == forecast_date
]

if festival_match.empty:
    festival_name = "No Festival"
    festival_category = ""
    festival_importance = ""
else:
    festival_name = festival_match.iloc[0]["festival"]
    festival_category = festival_match.iloc[0]["category"]
    festival_importance = festival_match.iloc[0]["importance"]


# -----------------------------
# 5. Find Product Category Impact
# -----------------------------
if festival_name != "No Festival":

    festival_mapping = mapping[
        mapping["festival"] == festival_name
    ]

else:

    festival_mapping = pd.DataFrame()


# -----------------------------
# 6. Weather Information
# -----------------------------
# These values are currently coming
# from the future weather forecast.

rain_mm = 1.2
temperature = 24.6


# -----------------------------
# 7. Calculate Weather Impact
# -----------------------------
if rain_mm > 10:

    weather_impact = "High"

elif rain_mm > 0:

    weather_impact = "Medium"

else:

    weather_impact = "Low"


# -----------------------------
# 8. Weather Impact by Category
# -----------------------------
weather_category_impact = {

    "FOODS": "Medium",

    "HOUSEHOLD": "Medium",

    "HOBBIES": "Low"

}


# ============================================================
# OUTPUT
# ============================================================

print()
print("==============================================")
print("           CONTEXT IMPACT ENGINE")
print("==============================================")

print()

print("Forecast Date:", forecast_date.strftime("%Y-%m-%d"))

print("Festival:", festival_name)

if festival_name != "No Festival":

    print("Festival Category:", festival_category)

    print("Festival Importance:", festival_importance)

print("Temperature:", temperature, "°C")

print("Rain:", rain_mm, "mm")

print("Weather Impact:", weather_impact)


# ============================================================
# CATEGORY IMPACT
# ============================================================

print()
print("==============================================")
print("              CATEGORY IMPACT")
print("==============================================")

print()


if festival_mapping.empty:

    print("No festival-specific category impact.")

else:

    for _, row in festival_mapping.iterrows():

        # IMPORTANT:
        # Actual CSV column names are:
        # festival
        # product_category
        # expected_impact

        category = row["product_category"]

        festival_impact = row["expected_impact"]

        weather_impact_category = weather_category_impact.get(
            category,
            "Low"
        )

        print(
            f"{category}: "
            f"Festival={festival_impact}, "
            f"Weather={weather_impact_category}"
        )


# ============================================================
# FINAL CONTEXT SUMMARY
# ============================================================

print()
print("==============================================")
print("             CONTEXT SUMMARY")
print("==============================================")

print()

if festival_name != "No Festival":

    print(
        "Festival signal detected:",
        festival_name
    )

    print(
        "Festival importance:",
        festival_importance
    )

else:

    print("No festival signal detected.")


if weather_impact == "High":

    print(
        "Weather signal detected: "
        "High rain impact."
    )

elif weather_impact == "Medium":

    print(
        "Weather signal detected: "
        "Rain expected."
    )

else:

    print(
        "Weather signal detected: "
        "No significant rain."
    )


print()
print("Context analysis completed successfully.")
print()