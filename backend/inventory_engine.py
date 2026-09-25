import os
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor


# =========================================================
# STORE LOCATIONS
# =========================================================

STORE_LOCATIONS = {
    "CA_1": {
        "latitude": 36.7783,
        "longitude": -119.4179,
        "location": "California"
    },
    "CA_2": {
        "latitude": 36.7783,
        "longitude": -119.4179,
        "location": "California"
    },
    "CA_3": {
        "latitude": 36.7783,
        "longitude": -119.4179,
        "location": "California"
    },
    "CA_4": {
        "latitude": 36.7783,
        "longitude": -119.4179,
        "location": "California"
    },
    "CA_5": {
        "latitude": 36.7783,
        "longitude": -119.4179,
        "location": "California"
    }
}


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# =========================================================
# CONSTANTS
# =========================================================

DATA_PATH = os.path.join(DATA_DIR, "retail_context_integrated.csv")
INVENTORY_PATH = os.path.join(DATA_DIR, "inventory.csv")
FESTIVALS_PATH = os.path.join(DATA_DIR, "indian_festivals.csv")
MAPPING_PATH = os.path.join(DATA_DIR, "festival_product_mapping.csv")
TRENDS_PATH = os.path.join(DATA_DIR, "online_trends.csv")
PROMOTIONS_PATH = os.path.join(DATA_DIR, "promotions.csv")

FEATURES = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "month",
    "weekday_code",
    "festival_flag",
    "festival_impact",
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag",
    "promotion_flag",
    "discount_percentage",
    "trend_index"
]


# =========================================================
# GLOBAL CACHE
# =========================================================
#
# These dictionaries keep models, weather and recommendations
# in memory so that they are not calculated again and again.
# =========================================================

MODEL_CACHE = {}
WEATHER_CACHE = {}
RECOMMENDATION_CACHE = {}


# =========================================================
# LOAD DATA ONCE
# =========================================================
#
# Previously pd.read_csv() was called every time
# get_recommendation() was called.
#
# Now files are loaded only once when backend starts.
# =========================================================

print("Loading retail AI data...")


sales_df = pd.read_csv(DATA_PATH)

inventory_df = pd.read_csv(INVENTORY_PATH)

festivals_df = pd.read_csv(FESTIVALS_PATH)

mapping_df = pd.read_csv(MAPPING_PATH)

trend_df = pd.read_csv(TRENDS_PATH)

promotions_df = pd.read_csv(PROMOTIONS_PATH)


# =========================================================
# DATE CONVERSION ONCE
# =========================================================

sales_df["date"] = pd.to_datetime(
    sales_df["date"]
)

festivals_df["date"] = pd.to_datetime(
    festivals_df["date"]
)

trend_df["date"] = pd.to_datetime(
    trend_df["date"]
)

promotions_df["date"] = pd.to_datetime(
    promotions_df["date"]
)


# =========================================================
# NUMERIC CONVERSION
# =========================================================

sales_df["sales"] = pd.to_numeric(
    sales_df["sales"],
    errors="coerce"
).fillna(0)


# =========================================================
# FESTIVAL FEATURES
# =========================================================

sales_df["festival_flag"] = pd.to_numeric(
    sales_df["festival_flag"],
    errors="coerce"
).fillna(0)


sales_df["festival_impact"] = pd.to_numeric(
    sales_df["festival_impact"],
    errors="coerce"
).fillna(0)


# =========================================================
# WEATHER FEATURES
# =========================================================

weather_columns = [
    "temperature_mean",
    "temperature_max",
    "temperature_min",
    "precipitation",
    "rain",
    "rain_flag",
    "heavy_rain_flag"
]


for col in weather_columns:

    if col in sales_df.columns:

        sales_df[col] = pd.to_numeric(
            sales_df[col],
            errors="coerce"
        )

        sales_df[col] = (
            sales_df[col]
            .fillna(sales_df[col].median())
            .fillna(0)
        )


# =========================================================
# PROMOTION FEATURES
# =========================================================

sales_df["promotion_flag"] = pd.to_numeric(
    sales_df["promotion_flag"],
    errors="coerce"
).fillna(0)


sales_df["discount_percentage"] = pd.to_numeric(
    sales_df["discount_percentage"],
    errors="coerce"
).fillna(0)


# =========================================================
# WEEKDAY MAPPING
# =========================================================

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


# =========================================================
# ONLINE TREND INTEGRATION
# =========================================================
#
# Trend data is merged only once.
# Previously this happened for every API request.
# =========================================================

trend_merge = trend_df[
    [
        "date",
        "product_category",
        "trend_index"
    ]
].copy()


trend_merge["trend_index"] = pd.to_numeric(
    trend_merge["trend_index"],
    errors="coerce"
).fillna(0)


sales_df = sales_df.merge(
    trend_merge,
    on=[
        "date",
        "product_category"
    ],
    how="left"
)


sales_df["trend_index"] = pd.to_numeric(
    sales_df["trend_index"],
    errors="coerce"
).fillna(0)


print(
    f"Retail AI data loaded successfully: "
    f"{len(sales_df)} sales records"
)


# =========================================================
# WEATHER FUNCTION
# =========================================================

def get_weather_forecast(
    forecast_date,
    store_id
):

    # -----------------------------------------------------
    # Create cache key
    # -----------------------------------------------------

    date_key = str(
        pd.Timestamp(forecast_date).date()
    )

    cache_key = (
        date_key,
        store_id
    )


    # -----------------------------------------------------
    # Return cached weather if available
    # -----------------------------------------------------

    if cache_key in WEATHER_CACHE:

        return WEATHER_CACHE[cache_key]


    # -----------------------------------------------------
    # Get store location
    # -----------------------------------------------------

    location = STORE_LOCATIONS.get(
        store_id
    )


    if location is None:

        location = {
            "latitude": 36.7783,
            "longitude": -119.4179,
            "location": "California"
        }


    # -----------------------------------------------------
    # Open-Meteo
    # -----------------------------------------------------

    url = (
        "https://api.open-meteo.com/v1/forecast"
    )


    params = {

        "latitude":
            location["latitude"],

        "longitude":
            location["longitude"],

        "daily":
            ",".join([
                "temperature_2m_mean",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum"
            ]),

        "timezone":
            "auto",

        "start_date":
            date_key,

        "end_date":
            date_key
    }


    try:

        response = requests.get(
            url,
            params=params,
            timeout=5
        )


        response.raise_for_status()


        data = response.json()


        daily = data.get(
            "daily",
            {}
        )


        if not daily.get("time"):

            result = {

                "temperature_mean": 0,

                "temperature_max": 0,

                "temperature_min": 0,

                "precipitation": 0,

                "rain": 0,

                "rain_flag": 0,

                "heavy_rain_flag": 0,

                "weather_source":
                    "Unavailable"
            }


            WEATHER_CACHE[cache_key] = result

            return result


        temperature_mean = float(
            daily["temperature_2m_mean"][0]
        )


        temperature_max = float(
            daily["temperature_2m_max"][0]
        )


        temperature_min = float(
            daily["temperature_2m_min"][0]
        )


        precipitation = float(
            daily["precipitation_sum"][0]
        )


        rain = float(
            daily["rain_sum"][0]
        )


        rain_flag = (
            1 if rain > 0 else 0
        )


        heavy_rain_flag = (
            1 if rain > 10 else 0
        )


        result = {

            "temperature_mean":
                temperature_mean,

            "temperature_max":
                temperature_max,

            "temperature_min":
                temperature_min,

            "precipitation":
                precipitation,

            "rain":
                rain,

            "rain_flag":
                rain_flag,

            "heavy_rain_flag":
                heavy_rain_flag,

            "weather_source":
                "Open-Meteo"
        }


        # -------------------------------------------------
        # Save weather in cache
        # -------------------------------------------------

        WEATHER_CACHE[cache_key] = result


        return result


    except Exception as e:

        print(
            "Weather API error:",
            e
        )


        result = {

            "temperature_mean": 0,

            "temperature_max": 0,

            "temperature_min": 0,

            "precipitation": 0,

            "rain": 0,

            "rain_flag": 0,

            "heavy_rain_flag": 0,

            "weather_source":
                "Unavailable"
        }


        WEATHER_CACHE[cache_key] = result


        return result


# =========================================================
# PREPARE PRODUCT DATA
# =========================================================

def prepare_product_data(
    item_id,
    store_id
):

    product_sales = sales_df[
        (sales_df["item_id"] == item_id)
        &
        (sales_df["store_id"] == store_id)
    ].copy()


    if product_sales.empty:

        return None


    product_sales = (
        product_sales
        .sort_values("date")
        .reset_index(drop=True)
    )


    # -----------------------------------------------------
    # Lag features
    # -----------------------------------------------------

    product_sales["lag_1"] = (
        product_sales["sales"]
        .shift(1)
    )


    product_sales["lag_7"] = (
        product_sales["sales"]
        .shift(7)
    )


    product_sales["rolling_7"] = (
        product_sales["sales"]
        .shift(1)
        .rolling(7)
        .mean()
    )


    product_sales = (
        product_sales
        .dropna(
            subset=[
                "lag_1",
                "lag_7",
                "rolling_7",
                "weekday_code"
            ]
        )
        .reset_index(drop=True)
    )


    return product_sales


# =========================================================
# GET / CACHE RANDOM FOREST MODEL
# =========================================================

def get_product_model(
    item_id,
    store_id
):

    cache_key = (
        item_id,
        store_id
    )


    # -----------------------------------------------------
    # If model already exists, return it
    # -----------------------------------------------------

    if cache_key in MODEL_CACHE:

        return MODEL_CACHE[cache_key]


    print(
        f"Training AI model for "
        f"{item_id} / {store_id}..."
    )


    # -----------------------------------------------------
    # Prepare product data
    # -----------------------------------------------------

    product_sales_model = prepare_product_data(
        item_id,
        store_id
    )


    if product_sales_model is None:

        return None


    if len(product_sales_model) < 20:

        return None


    # -----------------------------------------------------
    # Features
    # -----------------------------------------------------

    X = product_sales_model[
        FEATURES
    ]


    y = product_sales_model[
        "sales"
    ]


    # -----------------------------------------------------
    # Random Forest
    # -----------------------------------------------------

    model = RandomForestRegressor(

        n_estimators=200,

        random_state=42,

        n_jobs=-1

    )


    model.fit(
        X,
        y
    )


    # -----------------------------------------------------
    # Save model in cache
    # -----------------------------------------------------

    MODEL_CACHE[cache_key] = {

        "model": model,

        "product_sales":
            product_sales_model
    }


    print(
        f"AI model cached for "
        f"{item_id} / {store_id}"
    )


    return MODEL_CACHE[cache_key]


# =========================================================
# MAIN RECOMMENDATION ENGINE
# =========================================================

def get_recommendation(

    item_id="FOODS_3_090",

    store_id="CA_1",

    forecast_date="2026-09-14"

):

    # =====================================================
    # 1. FORECAST DATE
    # =====================================================

    forecast_date = pd.Timestamp(
        forecast_date
    )


    # =====================================================
    # 2. RESULT CACHE
    # =====================================================
    #
    # If exactly the same recommendation is requested again,
    # return it immediately.
    # =====================================================

    recommendation_key = (

        item_id,

        store_id,

        str(
            forecast_date.date()
        )

    )


    if recommendation_key in RECOMMENDATION_CACHE:

        return RECOMMENDATION_CACHE[
            recommendation_key
        ]


    # =====================================================
    # 3. PRODUCT SALES
    # =====================================================

    product_sales = sales_df[

        (sales_df["item_id"] == item_id)

        &

        (sales_df["store_id"] == store_id)

    ].copy()


    if product_sales.empty:

        return {

            "status": "error",

            "message":
                "Product or store data not found"

        }


    product_sales = (
        product_sales
        .sort_values("date")
        .reset_index(drop=True)
    )


    # =====================================================
    # 4. PRODUCT CATEGORY
    # =====================================================

    if "product_category" in product_sales.columns:

        product_category = str(
            product_sales.iloc[0][
                "product_category"
            ]
        )

    else:

        product_category = "FOODS"


    # =====================================================
    # 5. MODEL
    # =====================================================

    model_data = get_product_model(

        item_id,

        store_id

    )


    if model_data is None:

        return {

            "status": "error",

            "message":
                "Not enough historical data "
                "for ML prediction"

        }


    model = model_data[
        "model"
    ]


    product_sales_model = model_data[
        "product_sales"
    ]


    # =====================================================
    # 6. FESTIVAL CONTEXT
    # =====================================================

    festival_match = festivals_df[

        festivals_df["date"]
        == forecast_date

    ]


    if festival_match.empty:

        festival_name = "No Festival"

        festival_flag = 0

        festival_impact_value = 0

        festival_importance = "None"


    else:

        festival_row = (
            festival_match.iloc[0]
        )


        festival_name = str(
            festival_row["festival"]
        )


        festival_flag = 1


        festival_importance = str(
            festival_row["importance"]
        )


        product_mapping = mapping_df[

            (mapping_df["festival"]
             == festival_name)

            &

            (
                mapping_df[
                    "product_category"
                ]
                == product_category
            )

        ]


        if product_mapping.empty:

            festival_impact_value = 0


        else:

            impact_text = str(
                product_mapping.iloc[0][
                    "expected_impact"
                ]
            )


            if impact_text == "High":

                festival_impact_value = 2


            elif impact_text == "Medium":

                festival_impact_value = 1


            else:

                festival_impact_value = 0


    # =====================================================
    # 7. WEATHER CONTEXT
    # =====================================================

    weather = get_weather_forecast(

        forecast_date,

        store_id

    )


    temperature_mean = weather[
        "temperature_mean"
    ]


    temperature_max = weather[
        "temperature_max"
    ]


    temperature_min = weather[
        "temperature_min"
    ]


    precipitation = weather[
        "precipitation"
    ]


    rain = weather[
        "rain"
    ]


    rain_flag = weather[
        "rain_flag"
    ]


    heavy_rain_flag = weather[
        "heavy_rain_flag"
    ]


    weather_source = weather[
        "weather_source"
    ]


    # =====================================================
    # 8. PROMOTION CONTEXT
    # =====================================================

    promotion_match = promotions_df[

        promotions_df["date"]
        == forecast_date

    ]


    if promotion_match.empty:

        promotion_flag = 0

        discount_percentage = 0

        promotion_name = "No Promotion"


    else:

        promotion_row = (
            promotion_match.iloc[0]
        )


        promotion_flag = 1


        discount_percentage = float(
            promotion_row[
                "discount_percentage"
            ]
        )


        if "promotion_name" in promotions_df.columns:

            promotion_name = str(
                promotion_row[
                    "promotion_name"
                ]
            )


        elif "promotion" in promotions_df.columns:

            promotion_name = str(
                promotion_row[
                    "promotion"
                ]
            )


        else:

            promotion_name = (
                "Promotion Active"
            )


    # =====================================================
    # 9. ONLINE TREND CONTEXT
    # =====================================================

    future_trend = trend_df[

        (trend_df["date"]
         == forecast_date)

        &

        (
            trend_df[
                "product_category"
            ]
            == product_category
        )

    ]


    if future_trend.empty:

        trend_index = 0

        trend_direction = "No Data"


    else:

        trend_index = float(

            future_trend.iloc[0][
                "trend_index"
            ]

        )


        trend_direction = str(

            future_trend.iloc[0][
                "trend_direction"
            ]

        )


    # =====================================================
    # 10. CREATE ML INPUT
    # =====================================================

    if len(product_sales) < 7:

        return {

            "status": "error",

            "message":
                "Not enough sales history"

        }


    last_row = (
        product_sales.iloc[-1]
    )


    rolling_7_value = (

        product_sales[
            "sales"
        ]
        .tail(7)
        .mean()

    )


    next_input = pd.DataFrame([{

        "lag_1":
            float(
                last_row["sales"]
            ),

        "lag_7":
            float(
                product_sales.iloc[-7][
                    "sales"
                ]
            ),

        "rolling_7":
            float(
                rolling_7_value
            ),

        "month":
            forecast_date.month,

        "weekday_code":
            forecast_date.weekday(),

        "festival_flag":
            festival_flag,

        "festival_impact":
            festival_impact_value,

        "temperature_mean":
            temperature_mean,

        "temperature_max":
            temperature_max,

        "temperature_min":
            temperature_min,

        "precipitation":
            precipitation,

        "rain":
            rain,

        "rain_flag":
            rain_flag,

        "heavy_rain_flag":
            heavy_rain_flag,

        "promotion_flag":
            promotion_flag,

        "discount_percentage":
            discount_percentage,

        "trend_index":
            trend_index

    }])


    # =====================================================
    # 11. ML PREDICTION
    # =====================================================

    predicted_demand = model.predict(

        next_input[
            FEATURES
        ]

    )[0]


    predicted_demand = max(

        0,

        round(
            float(
                predicted_demand
            )
        )

    )


    # =====================================================
    # 12. INVENTORY
    # =====================================================

    inventory_match = inventory_df[

        (inventory_df["item_id"]
         == item_id)

        &

        (inventory_df["store_id"]
         == store_id)

    ]


    if inventory_match.empty:

        return {

            "status": "error",

            "message":
                "Inventory data not found"

        }


    inventory = (
        inventory_match.iloc[0]
    )


    current_stock = int(
        inventory["current_stock"]
    )


    incoming_stock = int(
        inventory["incoming_stock"]
    )


    lead_time_days = int(
        inventory["lead_time_days"]
    )


    # =====================================================
    # 13. SAFETY STOCK
    # =====================================================

    sales_std = (

        product_sales[
            "sales"
        ]
        .tail(30)
        .std()

    )


    if pd.isna(sales_std):

        safety_stock = 0

    else:

        safety_stock = max(

            0,

            round(
                float(
                    sales_std
                ) * 0.5
            )

        )


    # =====================================================
    # 14. AVAILABLE STOCK
    # =====================================================

    available_stock = (

        current_stock

        +

        incoming_stock

    )


    # =====================================================
    # 15. REORDER POINT
    # =====================================================

    reorder_point = max(

        0,

        round(

            (
                predicted_demand
                *
                lead_time_days
            )

            +

            safety_stock

        )

    )


    # =====================================================
    # 16. REORDER QUANTITY
    # =====================================================

    reorder_quantity = max(

        0,

        reorder_point
        -
        available_stock

    )


    # =====================================================
    # 17. STOCK COVER
    # =====================================================

    recent_demand = float(

        product_sales[
            "sales"
        ]
        .tail(7)
        .mean()

    )


    if recent_demand > 0:

        stock_cover_days = round(

            float(
                available_stock
                /
                recent_demand
            ),

            1

        )

    else:

        stock_cover_days = 0.0


    # =====================================================
    # 18. RISK
    # =====================================================

    if available_stock == 0:

        risk = "CRITICAL"


    elif stock_cover_days < lead_time_days:

        risk = "HIGH"


    elif stock_cover_days < (
        lead_time_days + 2
    ):

        risk = "MEDIUM"


    else:

        risk = "LOW"


    # =====================================================
    # 19. RECOMMENDATION
    # =====================================================

    if risk == "CRITICAL":

        recommendation = (
            "Immediate Reorder"
        )


    elif risk == "HIGH":

        recommendation = (
            "Increase Stock"
        )


    elif risk == "MEDIUM":

        recommendation = (
            "Monitor Inventory"
        )


    else:

        recommendation = (
            "Stock Level Healthy"
        )


    # =====================================================
    # 20. TREND SIGNAL
    # =====================================================

    if trend_index >= 70:

        trend_signal = (
            "Strong Rising"
        )


    elif trend_index >= 50:

        trend_signal = (
            "Rising"
        )


    elif trend_index > 0:

        trend_signal = (
            "Stable"
        )


    else:

        trend_signal = (
            "No Data"
        )


    # =====================================================
    # 21. CONTEXT SIGNALS
    # =====================================================

    context_signals = []


    if festival_flag == 1:

        context_signals.append(

            f"{festival_name} detected"

        )


    if festival_impact_value == 2:

        context_signals.append(

            f"High festival impact for "
            f"{product_category}"

        )


    elif festival_impact_value == 1:

        context_signals.append(

            f"Medium festival impact for "
            f"{product_category}"

        )


    if rain_flag == 1:

        context_signals.append(

            f"Rain expected "
            f"({round(rain, 1)} mm)"

        )


    if promotion_flag == 1:

        context_signals.append(

            f"Promotion active: "
            f"{promotion_name}"

        )


    if trend_index >= 70:

        context_signals.append(

            f"Strong online trend detected "
            f"({int(trend_index)}/100)"

        )


    elif trend_index >= 50:

        context_signals.append(

            f"Rising online trend detected "
            f"({int(trend_index)}/100)"

        )


    # =====================================================
    # 22. FINAL RESULT
    # =====================================================

    result = {

        "status":
            "success",

        "product":
            item_id,

        "store":
            store_id,

        "forecast_date":
            str(
                forecast_date.date()
            ),

        "predicted_demand":
            predicted_demand,

        "current_stock":
            current_stock,

        "incoming_stock":
            incoming_stock,

        "available_stock":
            available_stock,

        "lead_time_days":
            lead_time_days,

        "safety_stock":
            safety_stock,

        "reorder_point":
            reorder_point,

        "stock_cover_days":
            float(
                stock_cover_days
            ),

        "risk":
            risk,

        "recommendation":
            recommendation,

        "recommended_order":
            reorder_quantity,

        "festival":
            festival_name,

        "festival_importance":
            festival_importance,

        "festival_impact":

            (
                "High"

                if festival_impact_value == 2

                else

                "Medium"

                if festival_impact_value == 1

                else

                "Low"
            ),

        "temperature":
            round(
                temperature_mean,
                1
            ),

        "rain":
            round(
                rain,
                1
            ),

        "weather_source":
            weather_source,

        "promotion":
            promotion_name,

        "promotion_active":
            bool(
                promotion_flag
            ),

        "discount_percentage":
            round(
                discount_percentage,
                1
            ),

        "trend_index":
            round(
                trend_index
            ),

        "trend_direction":
            trend_direction,

        "online_trend":
            trend_signal,

        "context_signals":
            context_signals

    }


    # =====================================================
    # 23. SAVE RESULT IN CACHE
    # =====================================================

    RECOMMENDATION_CACHE[
        recommendation_key
    ] = result


    return result


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print()
    print(
        "======================================"
    )

    print(
        "AI RETAIL RECOMMENDATION TEST"
    )

    print(
        "======================================"
    )

    print()


    result = get_recommendation()


    for key, value in result.items():

        print(
            f"{key}: {value}"
        )


    print()