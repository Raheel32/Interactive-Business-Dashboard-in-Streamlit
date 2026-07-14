"""
Generates a synthetic dataset that mirrors the schema of the
'Global Superstore' dataset (Kaggle) since the original CSV was not
supplied with this task. Replace data/Global_Superstore.csv with the
real file (same column names) to use actual data -- no code changes
needed elsewhere.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)
N = 4000

regions = ["East", "West", "Central", "South"]
region_states = {
    "East": ["New York", "Pennsylvania", "New Jersey", "Massachusetts", "Virginia"],
    "West": ["California", "Washington", "Oregon", "Nevada", "Arizona"],
    "Central": ["Texas", "Illinois", "Michigan", "Ohio", "Wisconsin"],
    "South": ["Florida", "Georgia", "North Carolina", "Alabama", "Tennessee"],
}
categories = {
    "Furniture": ["Bookcases", "Chairs", "Furnishings", "Tables"],
    "Office Supplies": ["Appliances", "Art", "Binders", "Envelopes", "Labels", "Paper", "Storage", "Supplies"],
    "Technology": ["Accessories", "Copiers", "Machines", "Phones"],
}
segments = ["Consumer", "Corporate", "Home Office"]
ship_modes = ["Standard Class", "Second Class", "First Class", "Same Day"]

first_names = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda","David","Elizabeth",
               "William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen"]
last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
              "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]
customers = [f"{rng.choice(first_names)} {rng.choice(last_names)}" for _ in range(300)]

start_date = datetime(2022, 1, 1)

rows = []
for i in range(N):
    region = rng.choice(regions)
    state = rng.choice(region_states[region])
    category = rng.choice(list(categories.keys()), p=[0.2, 0.55, 0.25])
    sub_category = rng.choice(categories[category])
    order_date = start_date + timedelta(days=int(rng.integers(0, 1000)))
    ship_date = order_date + timedelta(days=int(rng.integers(1, 8)))
    quantity = int(rng.integers(1, 10))
    base_price = {"Furniture": 250, "Office Supplies": 40, "Technology": 400}[category]
    sales = round(float(np.abs(rng.normal(base_price, base_price * 0.5))) * quantity / 3 + 5, 2)
    discount = float(rng.choice([0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5], p=[0.35,0.2,0.15,0.15,0.08,0.04,0.03]))
    margin_rate = {"Furniture": 0.05, "Office Supplies": 0.18, "Technology": 0.12}[category]
    profit = round(sales * (margin_rate - discount * 0.6) + rng.normal(0, sales * 0.05), 2)

    rows.append({
        "Order ID": f"US-{order_date.year}-{100000+i}",
        "Order Date": order_date.strftime("%Y-%m-%d"),
        "Ship Date": ship_date.strftime("%Y-%m-%d"),
        "Ship Mode": rng.choice(ship_modes, p=[0.55, 0.2, 0.18, 0.07]),
        "Customer Name": rng.choice(customers),
        "Segment": rng.choice(segments, p=[0.5, 0.3, 0.2]),
        "Country": "United States",
        "State": state,
        "Region": region,
        "Category": category,
        "Sub-Category": sub_category,
        "Sales": sales,
        "Quantity": quantity,
        "Discount": discount,
        "Profit": profit,
    })

df = pd.DataFrame(rows)

# inject a few messy/realistic issues for the cleaning step to handle
dup_idx = rng.choice(df.index, size=15, replace=False)
df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)          # duplicates
null_idx = rng.choice(df.index, size=20, replace=False)
df.loc[null_idx, "Customer Name"] = np.nan                         # missing values
df.loc[rng.choice(df.index, size=8, replace=False), "Sales"] = -df.loc[rng.choice(df.index, size=8, replace=False), "Sales"].abs()  # bad negative sales

df.to_csv("data/Global_Superstore.csv", index=False)
print("Sample dataset written:", df.shape)
