import pandas as pd

sales_df = pd.read_csv("data/sales_train_validation.csv")

print("\nProduct Categories:")
print(
    sales_df[
        ["item_id", "dept_id", "cat_id"]
    ].drop_duplicates().head(30).to_string(index=False)
)

print("\nUnique Categories:")
print(sales_df["cat_id"].unique())

print("\nUnique Departments:")
print(sales_df["dept_id"].unique())