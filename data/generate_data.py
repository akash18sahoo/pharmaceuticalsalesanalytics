"""
Pharmaceutical Sales Data Generator
====================================
Generates a realistic synthetic dataset of 5,000 pharma sales transactions
across 5 years (2020–2024), 5 regions, 10 drugs, and 20 sales reps.

Run this script once to create:
  - data/pharma_sales.csv   → the raw dataset
  - data/pharma_sales.db    → SQLite database (fact_sales table)
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import date, timedelta

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── Drug Master ──────────────────────────────────────────────────────────────
DRUGS = {
    'Metformin':          {'class': 'Diabetes',           'price_range': (200, 350)},
    'Insulin Glargine':   {'class': 'Diabetes',           'price_range': (800, 1200)},
    'Atorvastatin':       {'class': 'Cardiovascular',     'price_range': (150, 300)},
    'Amlodipine':         {'class': 'Cardiovascular',     'price_range': (100, 200)},
    'Aspirin':            {'class': 'Cardiovascular',     'price_range': (50,  100)},
    'Sertraline':         {'class': 'CNS',                'price_range': (300, 600)},
    'Amoxicillin':        {'class': 'Anti-infective',     'price_range': (120, 250)},
    'Ciprofloxacin':      {'class': 'Anti-infective',     'price_range': (180, 350)},
    'Omeprazole':         {'class': 'Gastrointestinal',   'price_range': (90,  180)},
    'Ibuprofen':          {'class': 'Pain & Inflammation','price_range': (60,  130)},
}

# ── Region & Rep Master ───────────────────────────────────────────────────────
REPS = {
    'North':   ['Ravi Kumar',    'Priya Sharma',  'Anjali Singh',  'Rahul Verma'],
    'South':   ['Suresh Nair',   'Meena Pillai',  'Karthik Raj',   'Divya Menon'],
    'East':    ['Arnab Das',     'Sunita Ghosh',  'Debashish Roy', 'Pooja Bose'],
    'West':    ['Nikhil Joshi',  'Sneha Patil',   'Vikram Shah',   'Kavita Desai'],
    'Central': ['Deepak Gupta',  'Asha Tiwari',   'Rohit Mishra',  'Nisha Yadav'],
}

MANAGERS = {
    'North':   'Amit Srivastava',
    'South':   'Lakshmi Iyer',
    'East':    'Subrata Chatterjee',
    'West':    'Rajesh Mehta',
    'Central': 'Anita Pandey',
}

# ── Business Multipliers ──────────────────────────────────────────────────────
# Regional performance variance (North best, South worst)
REGION_MULT = {
    'North': 1.20, 'West': 1.10, 'East': 1.00,
    'Central': 0.90, 'South': 0.80
}

# Seasonal demand by drug class (monthly index 1–12)
SEASONAL_MULT = {
    'Cardiovascular':     {1:1.2, 2:1.2, 3:1.0, 4:0.9, 5:0.9, 6:0.8, 7:0.8, 8:0.9, 9:1.0, 10:1.1, 11:1.2, 12:1.3},
    'Diabetes':           {1:1.0, 2:1.0, 3:1.0, 4:1.0, 5:1.0, 6:1.0, 7:1.1, 8:1.1, 9:1.0, 10:1.0, 11:1.0, 12:1.0},
    'CNS':                {1:0.9, 2:0.9, 3:1.0, 4:1.0, 5:1.0, 6:1.1, 7:1.0, 8:1.0, 9:1.0, 10:1.1, 11:1.2, 12:1.3},
    'Anti-infective':     {1:1.3, 2:1.2, 3:1.1, 4:0.9, 5:0.8, 6:0.8, 7:0.8, 8:0.8, 9:0.9, 10:1.0, 11:1.2, 12:1.3},
    'Gastrointestinal':   {1:1.0, 2:1.0, 3:1.0, 4:1.1, 5:1.1, 6:1.0, 7:1.0, 8:1.0, 9:1.0, 10:1.0, 11:1.0, 12:1.0},
    'Pain & Inflammation':{1:1.2, 2:1.1, 3:1.0, 4:0.9, 5:0.9, 6:0.9, 7:0.9, 8:0.9, 9:1.0, 10:1.0, 11:1.1, 12:1.2},
}

# Year-over-year growth (~10% per year)
YOY_GROWTH = {2020: 1.00, 2021: 1.09, 2022: 1.18, 2023: 1.28, 2024: 1.40}

# Rep performance tiers — Pareto effect (top rep = 1.5x, bottom = 0.7x)
REP_TIER = {}
for region, reps in REPS.items():
    for i, rep in enumerate(reps):
        if i == 0:
            REP_TIER[rep] = 1.5   # Star performer
        elif i == len(reps) - 1:
            REP_TIER[rep] = 0.70  # Underperformer
        else:
            REP_TIER[rep] = 1.00  # Average


# ── Data Generation ───────────────────────────────────────────────────────────
def generate_pharma_sales(n_rows=5000):
    """Generate n_rows of synthetic pharma sales transactions."""

    start_date = date(2020, 1, 1)
    end_date   = date(2024, 12, 31)
    date_range = (end_date - start_date).days

    drug_names  = list(DRUGS.keys())
    regions     = list(REPS.keys())

    rows = []

    for i in range(n_rows):
        # Random sale date
        txn_date = start_date + timedelta(days=int(np.random.randint(0, date_range)))
        year     = txn_date.year
        month    = txn_date.month
        quarter  = f"Q{(month - 1) // 3 + 1}"

        # Drug selection
        drug_name  = np.random.choice(drug_names)
        drug_class = DRUGS[drug_name]['class']
        price_min, price_max = DRUGS[drug_name]['price_range']

        # Region & Rep
        region   = np.random.choice(regions)
        rep_name = np.random.choice(REPS[region])
        manager  = MANAGERS[region]

        # Channel (Hospital 40%, Pharmacy 60%)
        channel = np.random.choice(['Hospital', 'Pharmacy'], p=[0.4, 0.6])

        # Units sold with all multipliers applied
        base_units     = max(10, int(np.random.normal(100, 30)))
        seasonal_factor = SEASONAL_MULT[drug_class][month]
        region_factor   = REGION_MULT[region]
        rep_factor      = REP_TIER[rep_name]
        growth_factor   = YOY_GROWTH[year]
        noise           = np.random.uniform(0.85, 1.15)

        units_sold = int(base_units * seasonal_factor * region_factor
                         * rep_factor * growth_factor * noise)
        units_sold = max(5, units_sold)

        # Price & revenue
        unit_price = round(np.random.uniform(price_min, price_max), 2)
        revenue    = round(units_sold * unit_price, 2)

        # Target: top reps get harder targets, bottom reps get easier targets
        if REP_TIER[rep_name] >= 1.5:
            target_mult = 0.95   # Top reps usually beat target
        elif REP_TIER[rep_name] <= 0.7:
            target_mult = 1.15   # Struggling reps miss target
        else:
            target_mult = 1.05   # Average reps nearly hit target

        target_revenue = round(revenue * target_mult * np.random.uniform(0.92, 1.08), 2)

        rows.append({
            'sale_id':        f'TXN-{i+1:05d}',
            'date':           txn_date.strftime('%Y-%m-%d'),
            'year':           year,
            'month':          month,
            'quarter':        quarter,
            'drug_name':      drug_name,
            'drug_class':     drug_class,
            'region':         region,
            'channel':        channel,
            'rep_name':       rep_name,
            'manager':        manager,
            'units_sold':     units_sold,
            'unit_price':     unit_price,
            'revenue':        revenue,
            'target_revenue': target_revenue,
        })

    return pd.DataFrame(rows)


def introduce_dirty_data(df):
    """
    Intentionally introduce data quality issues for the cleaning exercise.
    - 20 rows: missing units_sold
    - 15 rows: missing unit_price
    -  5 rows: extreme outliers in units_sold
    - 10 rows: duplicate transactions
    """
    rng = np.random.default_rng(seed=99)
    idx = rng.choice(df.index, size=50, replace=False)

    df.loc[idx[:20], 'units_sold']  = np.nan   # Missing values
    df.loc[idx[20:35], 'unit_price'] = np.nan   # Missing values
    df.loc[idx[35:40], 'units_sold'] = rng.integers(6000, 9000, 5)  # Outliers

    # Duplicate 10 rows
    duplicates = df.iloc[idx[40:50]].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  Pharma Sales Data Generator")
    print("=" * 55)

    # Step 1: Generate clean data
    print("\n[1/4] Generating 5,000 sales transactions...")
    df = generate_pharma_sales(n_rows=5000)
    print(f"      Generated {len(df):,} rows x {len(df.columns)} columns")

    # Step 2: Introduce dirty data
    print("\n[2/4] Introducing data quality issues (nulls, outliers, duplicates)...")
    df = introduce_dirty_data(df)
    print(f"      Final shape: {df.shape[0]:,} rows (includes 10 duplicates)")

    # Step 3: Save CSV
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/pharma_sales.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n[3/4] Saved CSV  → {csv_path}")

    # Step 4: Load into SQLite
    db_path = 'data/pharma_sales.db'
    conn = sqlite3.connect(db_path)
    df.to_sql('fact_sales', conn, if_exists='replace', index=False)
    conn.close()
    print(f"[4/4] Saved DB   → {db_path}")

    # Summary
    clean_df = df.dropna(subset=['units_sold', 'unit_price'])
    print("\n" + "=" * 55)
    print("  Dataset Summary")
    print("=" * 55)
    print(f"  Total Rows      : {len(df):,}")
    print(f"  Columns         : {len(df.columns)}")
    print(f"  Date Range      : {df['date'].min()}  to  {df['date'].max()}")
    print(f"  Regions         : {sorted(df['region'].dropna().unique())}")
    print(f"  Drug Classes    : {sorted(df['drug_class'].dropna().unique())}")
    print(f"  Sales Reps      : {df['rep_name'].nunique()}")
    print(f"  Missing (units) : {df['units_sold'].isna().sum()}")
    print(f"  Missing (price) : {df['unit_price'].isna().sum()}")
    print(f"  Duplicates      : 10 (intentional)")
    print(f"  Total Revenue   : INR {clean_df['revenue'].sum():,.0f}")
    print("=" * 55)
    print("\n  Done! Open notebooks/01_data_generation.ipynb to explore.\n")
