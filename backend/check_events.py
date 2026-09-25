import pandas as pd

# Load calendar
calendar_df = pd.read_csv("data/calendar.csv")

# Get all available events
events = calendar_df[
    ["event_name_1", "event_type_1"]
].dropna().drop_duplicates()

print("\nAvailable Events:")
print(events.to_string(index=False))

print("\nTotal unique events:", len(events))
