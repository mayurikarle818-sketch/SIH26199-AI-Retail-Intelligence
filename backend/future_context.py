import pandas as pd
import requests

# ==========================================
# FORECAST DATE
# ==========================================

forecast_date = "2026-09-14"

# ==========================================
# 1. INDIAN FESTIVAL
# ==========================================

festivals = pd.read_csv(
    "data/indian_festivals.csv"
)

festivals["date"] = pd.to_datetime(
    festivals["date"]
)

festival_match = festivals[
    festivals["date"] == forecast_date
]

if not festival_match.empty:

    festival_name = festival_match.iloc[0]["festival"]
    festival_category = festival_match.iloc[0]["category"]
    festival_importance = festival_match.iloc[0]["importance"]

else:

    festival_name = "No Festival"
    festival_category = "None"
    festival_importance = "None"


# ==========================================
# 2. WEATHER
# ==========================================

# Pune coordinates for Indian retail MVP
latitude = 18.5204
longitude = 73.8567

url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={latitude}"
    f"&longitude={longitude}"
    f"&daily=temperature_2m_mean,"
    f"temperature_2m_max,"
    f"temperature_2m_min,"
    f"precipitation_sum,"
    f"rain_sum"
    f"&start_date={forecast_date}"
    f"&end_date={forecast_date}"
    f"&timezone=Asia%2FKolkata"
)

response = requests.get(url, timeout=20)

weather = response.json()

if "daily" in weather and len(weather["daily"]["time"]) > 0:

    temperature = weather["daily"]["temperature_2m_mean"][0]
    temperature_max = weather["daily"]["temperature_2m_max"][0]
    temperature_min = weather["daily"]["temperature_2m_min"][0]
    precipitation = weather["daily"]["precipitation_sum"][0]
    rain = weather["daily"]["rain_sum"][0]

else:

    temperature = None
    temperature_max = None
    temperature_min = None
    precipitation = None
    rain = None


# ==========================================
# 3. WEATHER INTERPRETATION
# ==========================================

if rain is not None and rain > 10:

    weather_condition = "Heavy Rain"

elif rain is not None and rain > 0:

    weather_condition = "Rain Expected"

else:

    weather_condition = "No Significant Rain"


# ==========================================
# 4. PROMOTION
# ==========================================

promotion_name = "No Promotion"
discount = 0

promotions = pd.read_csv(
    "data/promotions.csv"
)

promotions["date"] = pd.to_datetime(
    promotions["date"]
)

promotion_match = promotions[
    promotions["date"] == forecast_date
]

if not promotion_match.empty:

    promotion_name = promotion_match.iloc[0]["promotion_name"]

    discount = promotion_match.iloc[0][
        "discount_percentage"
    ]


# ==========================================
# 5. FINAL CONTEXT
# ==========================================

print("\n========================================")
print("        FUTURE RETAIL CONTEXT")
print("========================================")

print(
    "Forecast Date:",
    forecast_date
)

print(
    "Festival:",
    festival_name
)

print(
    "Festival Category:",
    festival_category
)

print(
    "Festival Importance:",
    festival_importance
)

print(
    "Weather:",
    weather_condition
)

print(
    "Temperature:",
    temperature,
    "°C"
)

print(
    "Rain:",
    rain,
    "mm"
)

print(
    "Promotion:",
    promotion_name
)

print(
    "Discount:",
    discount,
    "%"
)

print("\n========================================")
print("       CONTEXT SUMMARY")
print("========================================")

if festival_name != "No Festival":

    print(
        f"Festival signal detected: "
        f"{festival_name}"
    )

if rain is not None and rain > 0:

    print(
        "Weather signal detected: "
        "rain expected."
    )

if promotion_name != "No Promotion":

    print(
        f"Promotion signal detected: "
        f"{promotion_name}"
    )