import pandas as pd

festivals = pd.read_csv("data/indian_festivals.csv")

print("Indian Festival Calendar loaded successfully!")

print("\nFestivals:")
print(festivals.to_string(index=False))

print("\nTotal festivals:", len(festivals))