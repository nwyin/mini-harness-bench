import pandas as pd

df = pd.read_csv("input.csv")
df = df[df["quantity"] > 0]
df["total"] = df["price"] * df["quantity"]
result = (
    df.groupby("category")
    .agg(
        total_revenue=("total", "sum"),
        num_orders=("total", "count"),
        avg_price=("price", "mean"),
    )
    .reset_index()
)
result = result.sort_values("total_revenue", ascending=False)
result.to_csv("output.csv", index=False)
