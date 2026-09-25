import pandas as pd

# Load festival-product mapping
mapping = pd.read_csv("data/festival_product_mapping.csv")

print("Festival-Product Mapping loaded successfully!")

print("\nMapping:")
print(mapping.to_string(index=False))

print("\nTotal mappings:", len(mapping))