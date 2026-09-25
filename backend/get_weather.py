import requests
import pandas as pd

# ========================================
# CALIFORNIA WEATHER
# ========================================

latitude = 36.7783
longitude = -119.4179

start_date = "2011-01-29"
end_date = "2016-06-19"

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": start_date,
    "end_date": end_date,
    "daily": [
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "rain_sum"
    ],
    "timezone": "America/Los_Angeles"
}

print("Fetching historical weather data...")

response = requests.get(
    url,
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()

# ========================================
# CONVERT TO DATAFRAME
# ========================================

weather_df = pd.DataFrame(data["daily"])

weather_df = weather_df.rename(
    columns={
        "time": "date",
        "temperature_2m_mean": "temperature_mean",
        "temperature_2m_max": "temperature_max",
        "temperature_2m_min": "temperature_min",
        "precipitation_sum": "precipitation",
        "rain_sum": "rain"
    }
)

weather_df["date"] = pd.to_datetime(
    weather_df["date"]
)

# ========================================
# SAVE
# ========================================

output_file = "data/weather_historical.csv"

weather_df.to_csv(
    output_file,
    index=False
)

print("\n========================================")
print("      WEATHER DATA DOWNLOADED")
print("========================================")

print("Location: California, USA")

print(
    "Date Range:",
    weather_df["date"].min().date(),
    "to",
    weather_df["date"].max().date()
)

print(
    "Total records:",
    len(weather_df)
)

print("\nSample Weather Data:")

print(
    weather_df.head(10)
    .to_string(index=False)
)

print(
    "\nWeather file saved successfully:",
    output_file
)