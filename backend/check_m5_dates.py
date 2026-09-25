import pandas as pd

calendar_df = pd.read_csv("data/calendar.csv")

calendar_df["date"] = pd.to_datetime(calendar_df["date"])

print("M5 Dataset Date Range:")
print("Start Date:", calendar_df["date"].min().date())
print("End Date:", calendar_df["date"].max().date())

print("\nLast 10 Dates:")
print(calendar_df[["d", "date"]].tail(10).to_string(index=False))