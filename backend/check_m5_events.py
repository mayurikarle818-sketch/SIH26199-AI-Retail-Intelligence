import pandas as pd

calendar_df = pd.read_csv("data/calendar.csv")

events = calendar_df[
    ["date", "event_name_1", "event_type_1"]
].dropna(subset=["event_name_1"])

print("\n========================================")
print("          M5 EVENTS")
print("========================================")

print(events.to_string(index=False))

print("\nTotal Event Records:", len(events))