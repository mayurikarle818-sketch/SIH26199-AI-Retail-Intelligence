import pandas as pd

promotions = pd.read_csv(
    "data/promotions.csv"
)

promotions["date"] = pd.to_datetime(
    promotions["date"]
)

print("\n========================================")
print("       PROMOTION DATA")
print("========================================")

print("Total Promotions:", len(promotions))

print("\nPromotion Data:")

print(
    promotions.to_string(index=False)
)