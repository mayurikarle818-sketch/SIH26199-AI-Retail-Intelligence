import pandas as pd

mapping = pd.DataFrame([
    ["Ganesh Chaturthi", "FOODS", "High"],
    ["Ganesh Chaturthi", "HOBBIES", "Medium"],
    ["Ganesh Chaturthi", "HOUSEHOLD", "Medium"],

    ["Diwali", "FOODS", "High"],
    ["Diwali", "HOBBIES", "Medium"],
    ["Diwali", "HOUSEHOLD", "Medium"],

    ["Dussehra", "FOODS", "High"],
    ["Dussehra", "HOBBIES", "Medium"],

    ["Holi", "FOODS", "High"],
    ["Holi", "HOBBIES", "Medium"],

    ["Eid al-Adha", "FOODS", "High"],
    ["Eid al-Adha", "HOUSEHOLD", "Medium"],

    ["Christmas", "FOODS", "High"],
    ["Christmas", "HOBBIES", "Medium"],
    ["Christmas", "HOUSEHOLD", "Medium"],
], columns=["festival", "product_category", "expected_impact"])

mapping.to_csv("data/festival_product_mapping.csv", index=False)

print("Festival-Product mapping updated successfully!")
print("\n", mapping.to_string(index=False))
print("\nTotal mappings:", len(mapping))