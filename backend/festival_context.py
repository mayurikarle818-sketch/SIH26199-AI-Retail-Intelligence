import pandas as pd

# ============================================================
# 1. LOAD INDIAN FESTIVAL DATA
# ============================================================

festivals = pd.read_csv("data/indian_festivals.csv")

# Convert date column to datetime
festivals["date"] = pd.to_datetime(festivals["date"])


# ============================================================
# 2. GET TODAY'S DATE
# ============================================================

today = pd.Timestamp.today().normalize()

print("Today:", today.date())


# ============================================================
# 3. FIND UPCOMING FESTIVALS
# ============================================================

upcoming = festivals[
    festivals["date"] >= today
].copy()


# ============================================================
# 4. CALCULATE DAYS UNTIL FESTIVAL
# ============================================================

upcoming["days_until"] = (
    upcoming["date"] - today
).dt.days


# ============================================================
# 5. SORT BY NEAREST FESTIVAL
# ============================================================

upcoming = upcoming.sort_values(
    by="date"
)


# ============================================================
# 6. DISPLAY UPCOMING FESTIVALS
# ============================================================

print("\n========================================")
print("       UPCOMING INDIAN FESTIVALS")
print("========================================")

print(
    upcoming[
        [
            "date",
            "festival",
            "category",
            "importance",
            "days_until"
        ]
    ].head(5).to_string(index=False)
)


# ============================================================
# 7. NEXT FESTIVAL
# ============================================================

if len(upcoming) > 0:

    next_festival = upcoming.iloc[0]

    print("\n========================================")
    print("          NEXT FESTIVAL")
    print("========================================")

    print("Festival:", next_festival["festival"])
    print("Date:", next_festival["date"].date())
    print("Category:", next_festival["category"])
    print("Importance:", next_festival["importance"])
    print("Days Until:", next_festival["days_until"])

else:

    print("\nNo upcoming festivals found.")
    