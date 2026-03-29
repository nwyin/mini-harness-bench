#!/usr/bin/env python3
"""Transform nested user/order JSON data into a summary report."""

import json


def main():
    with open("data.json") as f:
        data = json.load(f)

    summary = []
    total_revenue = 0.0

    for user in data["users"]:
        orders = user["orders"]
        total_spent = sum(o["amount"] for o in orders)
        total_revenue += total_spent
        most_expensive = max(orders, key=lambda o: o["amount"])

        summary.append(
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "total_spent": round(total_spent, 2),
                "order_count": len(orders),
                "most_expensive_order": {
                    "order_id": most_expensive["order_id"],
                    "amount": most_expensive["amount"],
                    "product": most_expensive["product"],
                },
            }
        )

    summary.sort(key=lambda x: x["total_spent"], reverse=True)
    top_spender = summary[0]["name"]

    output = {
        "summary": summary,
        "total_revenue": round(total_revenue, 2),
        "top_spender": top_spender,
    }

    with open("output.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
