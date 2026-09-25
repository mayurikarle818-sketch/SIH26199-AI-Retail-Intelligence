import pandas as pd

# Load calendar data
calendar_df = pd.read_csv("data/calendar.csv")

print("Calendar data loaded successfully!")

print("\nColumns:")
print(calendar_df.columns.tolist())

print("\nFirst 5 rows:")
print(calendar_df.head())