"""
=============================================================
  PHASE 1 — Data Generation & Database Setup
=============================================================
  What this script does:
    1. Generates 5,000 realistic pharma sales transactions
    2. Applies seasonal trends, regional variance, rep tiers
    3. Adds intentional dirty data (nulls, outliers, duplicates)
    4. Saves → data/pharma_sales.csv
    5. Loads → data/pharma_sales.db (SQLite)

  Run:  python scripts/01_generate_data.py
=============================================================
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import date, timedelta

# ── Reproducibility ──────────────────────────────────────────
np.random.seed(42)


# ============================================================
#  SECTION 1: Master Configuration
# ============================================================

DRUGS = {
    'Metformin':         {'class': 'Diabetes',           'price_range': (200,  350)},
    'Insulin Glargine':  {'class': 'Diabetes',           'price_range': (800, 1200)},
    'Atorvastatin':      {'class': 'Cardiovascular',     'price_range': (150,  300)},
    'Amlodipine':        {'class': 'Cardiovascular',     'price_range': (100,  200)},
    'Aspirin':           {'class': 'Cardiovascular',     'price_range': ( 50,  100)},
    'Sertraline':        {'class': 'CNS',                'price_range': (300,  600)},
    'Amoxicillin':       {'class': 'Anti-infective',     'price_range': (120,  250)},
    'Ciprofloxacin':     {'class': 'Anti-infective',     'price_range': (180,  350)},
    'Omeprazole':        {'class': 'Gastrointestinal',   'price_range': ( 90,  180)},
    'Ibuprofen':         {'class': 'Pain & Inflammation','price_range': ( 60,  130)},
}

REPS = {
    'North':   ['Ravi Kumar',   'Priya Sharma',  'Anjali Singh',  'Rahul Verma'],
    'South':   ['Suresh Nair',  'Meena Pillai',  'Karthik Raj',   'Divya Menon'],
    'East':    ['Arnab Das',    'Sunita Ghosh',  'Debashish Roy', 'Pooja Bose'],
    'West':    ['Nikhil Joshi', 'Sneha Patil',   'Vikram Shah',   'Kavita Desai'],
    'Central': ['Deepak Gupta', 'Asha Tiwari',   'Rohit Mishra',  'Nisha Yadav'],
}

MANAGERS = {
    'North':   'Amit Srivastava',
    'South':   'Lakshmi Iyer',
    'East':    'Subrata Chatterjee',
    'West':    'Rajesh Mehta',
    'Central': 'Anita Pandey',
}


# ============================================================
#  SECTION 2: Business Multipliers
#  (These create realistic patterns in the data)
# ============================================================

# North sells 20% more than average, South 20% less
REGION_MULT = {
    'North': 1.20, 'West': 1.10, 'East': 1.00,
    'Central': 0.90, 'South': 0.80,
}

# Demand varies by drug class per month (e.g. Anti-infectives peak in winter)
SEASONAL_MULT = {
    'Cardiovascular':      {1:1.2, 2:1.2, 3:1.0, 4:0.9, 5:0.9, 6:0.8, 7:0.8, 8:0.9, 9:1.0, 10:1.1, 11:1.2, 12:1.3},
    'Diabetes':            {1:1.0, 2:1.0, 3:1.0, 4:1.0, 5:1.0, 6:1.0, 7:1.1, 8:1.1, 9:1.0, 10:1.0, 11:1.0, 12:1.0},
    'CNS':                 {1:0.9, 2:0.9, 3:1.0, 4:1.0, 5:1.0, 6:1.1, 7:1.0, 8:1.0, 9:1.0, 10:1.1, 11:1.2, 12:1.3},
    'Anti-infective':      {1:1.3, 2:1.2, 3:1.1, 4:0.9, 5:0.8, 6:0.8, 7:0.8, 8:0.8, 9:0.9, 10:1.0, 11:1.2, 12:1.3},
    'Gastrointestinal':    {1:1.0, 2:1.0, 3:1.0, 4:1.1, 5:1.1, 6:1.0, 7:1.0, 8:1.0, 9:1.0, 10:1.0, 11:1.0, 12:1.0},
    'Pain & Inflammation': {1:1.2, 2:1.1, 3:1.0, 4:0.9, 5:0.9, 6:0.9, 7:0.9, 8:0.9, 9:1.0, 10:1.0, 11:1.1, 12:1.2},
}

# ~10% YoY growth in units
YOY_GROWTH = {2020: 1.00, 2021: 1.09, 2022: 1.18, 2023: 1.28, 2024: 1.40}

# Pareto effect: top rep sells 1.5x, bottom sells 0.7x (first rep in each region = star)
REP_TIER = {}
for region, reps in REPS.items():
    for i, rep in enumerate(reps):
        if i == 0:
            REP_TIER[rep] = 1.50   # Star performer
        elif i == len(reps) - 1:
            REP_TIER[rep] = 0.70   # Underperformer
        else:
            REP_TIER[rep] = 1.00   # Average


# ============================================================
#  SECTION 3: Generate Transactions
# ============================================================

def generate_pharma_sales(n_rows=5000):
    """
    Generate n_rows synthetic pharma sales transactions.
    Each row = one sale event by a rep for a drug in a region.
    """
    start_date = date(2020, 1, 1)
    end_date   = date(2024, 12, 31)
    total_days = (end_date - start_date).days

    drug_names = list(DRUGS.keys())
    regions    = list(REPS.keys())
    rows       = []

    for i in range(n_rows):
        # Random date in 5-year range
        txn_date = start_date + timedelta(days=int(np.random.randint(0, total_days)))
        year     = txn_date.year
        month    = txn_date.month
        quarter  = f"Q{(month - 1) // 3 + 1}"

        # Drug
        drug_name  = np.random.choice(drug_names)
        drug_class = DRUGS[drug_name]['class']
        p_min, p_max = DRUGS[drug_name]['price_range']

        # Rep & Region
        region   = np.random.choice(regions)
        rep_name = np.random.choice(REPS[region])
        manager  = MANAGERS[region]
        channel  = np.random.choice(['Hospital', 'Pharmacy'], p=[0.4, 0.6])

        # Units sold — base 100 units, then multiply all factors
        base_units = max(10, int(np.random.normal(100, 30)))

        units_sold = int(
            base_units
            * SEASONAL_MULT[drug_class][month]
            * REGION_MULT[region]
            * REP_TIER[rep_name]
            * YOY_GROWTH[year]
            * np.random.uniform(0.85, 1.15)   # random noise
        )
        units_sold = max(5, units_sold)

        # Price & revenue
        unit_price = round(np.random.uniform(p_min, p_max), 2)
        revenue    = round(units_sold * unit_price, 2)

        # Target: star reps get tougher targets (they usually still beat them),
        # struggling reps get easier targets (they still miss them)
        if REP_TIER[rep_name] >= 1.50:
            t_mult = 0.95   # target < actual  → rep beats target
        elif REP_TIER[rep_name] <= 0.70:
            t_mult = 1.15   # target > actual  → rep misses target
        else:
            t_mult = 1.05   # target slightly above → near-miss

        target_revenue = round(revenue * t_mult * np.random.uniform(0.92, 1.08), 2)

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


# ============================================================
#  SECTION 4: Add Dirty Data (for Phase 2 cleaning demo)
# ============================================================

def add_dirty_data(df):
    """
    Introduce realistic data quality issues:
      - 20 rows: missing units_sold
      - 15 rows: missing unit_price
      -  5 rows: extreme outlier units_sold (data entry errors)
      - 10 rows: duplicate transactions
    """
    rng = np.random.default_rng(seed=99)
    idx = rng.choice(df.index, size=50, replace=False)

    df.loc[idx[:20], 'units_sold']   = np.nan            # Missing
    df.loc[idx[20:35], 'unit_price'] = np.nan            # Missing
    df.loc[idx[35:40], 'units_sold'] = rng.integers(6000, 9000, 5)  # Outliers

    duplicates = df.iloc[idx[40:50]].copy()
    df = pd.concat([df, duplicates], ignore_index=True)  # Duplicates

    return df


# ============================================================
#  SECTION 5: Save CSV and Load into SQLite
# ============================================================

def save_to_csv(df, path='data/pharma_sales.csv'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  CSV saved    : {path}  ({os.path.getsize(path)/1024:.0f} KB)")

def load_to_sqlite(df, db_path='data/pharma_sales.db'):
    conn = sqlite3.connect(db_path)
    df.to_sql('fact_sales', conn, if_exists='replace', index=False)

    # Apply indexes for query speed
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_region  ON fact_sales(region)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drug    ON fact_sales(drug_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rep     ON fact_sales(rep_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year    ON fact_sales(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel ON fact_sales(channel)")
    conn.commit()

    # Verify
    count = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    conn.close()
    print(f"  SQLite saved : {db_path}  ({count:,} rows loaded)")

def print_summary(df):
    clean = df.dropna(subset=['units_sold', 'unit_price'])
    print()
    print("=" * 50)
    print("  DATASET SUMMARY")
    print("=" * 50)
    print(f"  Total rows       : {len(df):,}")
    print(f"  Columns          : {len(df.columns)}")
    print(f"  Date range       : {df['date'].min()}  to  {df['date'].max()}")
    print(f"  Regions          : {', '.join(sorted(df['region'].dropna().unique()))}")
    print(f"  Drug classes     : {df['drug_class'].nunique()}")
    print(f"  Drugs            : {df['drug_name'].nunique()}")
    print(f"  Sales reps       : {df['rep_name'].nunique()}")
    print(f"  Channels         : {', '.join(df['channel'].dropna().unique())}")
    print()
    print("  -- Data Quality Issues (for Phase 2) --")
    print(f"  Missing units    : {df['units_sold'].isna().sum()}")
    print(f"  Missing price    : {df['unit_price'].isna().sum()}")
    print(f"  Duplicates added : 10")
    print(f"  Outlier rows     : 5")
    print()
    print(f"  Total Revenue    : INR {clean['revenue'].sum():>15,.0f}")
    print(f"  Avg Revenue/Sale : INR {clean['revenue'].mean():>15,.0f}")
    print("=" * 50)


# ============================================================
#  MAIN
# ============================================================

if __name__ == '__main__':
    print()
    print("=" * 50)
    print("  PHASE 1 — Data Generation")
    print("=" * 50)

    print("\n[Step 1/4]  Generating 5,000 transactions...")
    df = generate_pharma_sales(n_rows=5000)

    print("[Step 2/4]  Adding dirty data for cleaning exercise...")
    df = add_dirty_data(df)

    print("[Step 3/4]  Saving to CSV...")
    save_to_csv(df)

    print("[Step 4/4]  Loading into SQLite database...")
    load_to_sqlite(df)

    print_summary(df)

    print("\n  Phase 1 complete!")
    print("  Next step: python scripts/02_clean_data.py\n")
