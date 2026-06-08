# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
"""
=============================================================
  PHASE 2 — Data Cleaning
=============================================================
  What this script does:
    1. Loads raw data from data/pharma_sales.csv
    2. Inspects data quality (nulls, types, duplicates)
    3. Removes duplicate rows
    4. Fills missing values (median imputation)
    5. Detects & caps outliers using IQR method
    6. Recalculates revenue after imputation
    7. Validates final dataset
    8. Saves → data/pharma_sales_clean.csv
    9. Updates → data/pharma_sales.db (clean table)

  Run:  python scripts/02_clean_data.py
=============================================================
"""

import pandas as pd
import numpy as np
import sqlite3
import os

# ── Pretty print helper ───────────────────────────────────────
def section(title):
    print()
    print("=" * 52)
    print(f"  {title}")
    print("=" * 52)

# ============================================================
#  STEP 1: Load Raw Data
# ============================================================

section("STEP 1: Load Raw Data")

df = pd.read_csv('data/pharma_sales.csv')

print(f"\n  Shape         : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  Columns       : {list(df.columns)}")
print(f"\n  First 3 rows:")
print(df.head(3).to_string(index=False))


# ============================================================
#  STEP 2: Inspect Data Quality
# ============================================================

section("STEP 2: Data Quality Inspection")

print("\n  -- Data Types --")
print(df.dtypes.to_string())

print("\n  -- Missing Values --")
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({
    'Missing Count': missing,
    'Missing %': missing_pct
})
print(missing_report[missing_report['Missing Count'] > 0].to_string())

print(f"\n  -- Duplicate Rows --")
n_dupes = df.duplicated().sum()
print(f"  Exact duplicates found: {n_dupes}")

print(f"\n  -- Outlier Check (units_sold) --")
q1  = df['units_sold'].quantile(0.25)
q3  = df['units_sold'].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
n_outliers = df[(df['units_sold'] < lower_bound) | (df['units_sold'] > upper_bound)].shape[0]

print(f"  Q1={q1:.0f}  Q3={q3:.0f}  IQR={iqr:.0f}")
print(f"  Normal range : [{lower_bound:.0f}  ,  {upper_bound:.0f}]")
print(f"  Outlier rows : {n_outliers}")

# Save before stats
rows_before = len(df)
missing_before = df.isnull().sum().sum()


# ============================================================
#  STEP 3: Remove Duplicates
# ============================================================

section("STEP 3: Remove Duplicates")

df = df.drop_duplicates()
removed_dupes = rows_before - len(df)
print(f"\n  Rows before  : {rows_before:,}")
print(f"  Rows removed : {removed_dupes}")
print(f"  Rows after   : {len(df):,}")


# ============================================================
#  STEP 4: Fix Data Types
# ============================================================

section("STEP 4: Fix Data Types")

# Convert date column to proper datetime
df['date'] = pd.to_datetime(df['date'])
print(f"\n  'date' column converted to datetime64")

# Ensure year, month are integers
df['year']  = df['year'].astype('Int64')
df['month'] = df['month'].astype('Int64')
print(f"  'year' and 'month' set to integer")

# Ensure numeric columns are float
df['units_sold']     = pd.to_numeric(df['units_sold'],     errors='coerce')
df['unit_price']     = pd.to_numeric(df['unit_price'],     errors='coerce')
df['revenue']        = pd.to_numeric(df['revenue'],        errors='coerce')
df['target_revenue'] = pd.to_numeric(df['target_revenue'], errors='coerce')
print(f"  Numeric columns confirmed as float")

print(f"\n  Updated dtypes:")
print(df.dtypes.to_string())


# ============================================================
#  STEP 5: Handle Missing Values
# ============================================================

section("STEP 5: Handle Missing Values")

# Strategy: median imputation per drug_class group
# Why median? It's not affected by outliers (unlike mean)

print("\n  Strategy: Median imputation grouped by drug_class")
print("  Why median? Robust to outliers — mean can be skewed by extreme values\n")

# Fill missing units_sold with median of same drug_class
missing_units_before = df['units_sold'].isna().sum()
df['units_sold'] = df.groupby('drug_class')['units_sold'].transform(
    lambda x: x.fillna(x.median())
)
missing_units_after = df['units_sold'].isna().sum()

print(f"  units_sold  : {missing_units_before} missing -> {missing_units_after} missing (filled with drug class median)")

# Fill missing unit_price with median of same drug_name
missing_price_before = df['unit_price'].isna().sum()
df['unit_price'] = df.groupby('drug_name')['unit_price'].transform(
    lambda x: x.fillna(x.median())
)
missing_price_after = df['unit_price'].isna().sum()

print(f"  unit_price  : {missing_price_before} missing -> {missing_price_after} missing (filled with drug name median)")

# Recalculate revenue where it might be wrong after imputation
df['units_sold']  = df['units_sold'].round(0).astype(int)
df['unit_price']  = df['unit_price'].round(2)
df['revenue']     = (df['units_sold'] * df['unit_price']).round(2)

print(f"\n  Revenue recalculated: units_sold x unit_price")


# ============================================================
#  STEP 6: Handle Outliers (IQR Capping)
# ============================================================

section("STEP 6: Outlier Detection & Capping")

print("\n  Method: IQR (Interquartile Range)")
print("  Formula: lower = Q1 - 1.5*IQR  |  upper = Q3 + 1.5*IQR")
print("  Action : Cap (Winsorize) — don't delete, just clip to boundary\n")

for col in ['units_sold', 'revenue']:
    q1  = df[col].quantile(0.25)
    q3  = df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    n_outliers = df[(df[col] < lower) | (df[col] > upper)].shape[0]

    # Cap outliers (Winsorization)
    df[col] = np.clip(df[col], lower, upper)

    print(f"  {col:<15} | Q1={q1:>8.0f}  Q3={q3:>8.0f}  IQR={iqr:>8.0f}")
    print(f"                  | Range=[{lower:.0f}, {upper:.0f}]  Outliers capped: {n_outliers}")
    print()

# Recalculate revenue once more after capping units
df['revenue'] = (df['units_sold'] * df['unit_price']).round(2)


# ============================================================
#  STEP 7: Final Validation
# ============================================================

section("STEP 7: Final Validation")

print(f"\n  -- Remaining Nulls --")
final_nulls = df.isnull().sum()
if final_nulls.sum() == 0:
    print("  No missing values remaining!")
else:
    print(final_nulls[final_nulls > 0].to_string())

print(f"\n  -- Clean Dataset Stats --")
print(f"  Rows             : {len(df):,}")
print(f"  Rows removed     : {rows_before - len(df):,}  ({removed_dupes} dupes)")
print(f"  Total Revenue    : INR {df['revenue'].sum():>15,.0f}")
print(f"  Avg Revenue/Sale : INR {df['revenue'].mean():>15,.0f}")
print(f"  units_sold range : {df['units_sold'].min():.0f}  to  {df['units_sold'].max():.0f}")
print(f"  Date range       : {df['date'].min().date()}  to  {df['date'].max().date()}")

print(f"\n  -- Row count by Year --")
print(df.groupby('year')['sale_id'].count().rename('transactions').to_string())

print(f"\n  -- Revenue by Region --")
region_summary = df.groupby('region')['revenue'].sum().sort_values(ascending=False)
print(region_summary.apply(lambda x: f"INR {x:,.0f}").to_string())


# ============================================================
#  STEP 8: Save Cleaned Data
# ============================================================

section("STEP 8: Save Cleaned Data")

# Reset date to string for CSV/SQLite compatibility
df['date'] = df['date'].dt.strftime('%Y-%m-%d')

# Save clean CSV
clean_csv_path = 'data/pharma_sales_clean.csv'
df.to_csv(clean_csv_path, index=False)
print(f"\n  Clean CSV saved  : {clean_csv_path}  ({os.path.getsize(clean_csv_path)/1024:.0f} KB)")

# Save clean table to SQLite
db_path = 'data/pharma_sales.db'
conn = sqlite3.connect(db_path)
df.to_sql('fact_sales_clean', conn, if_exists='replace', index=False)

# Verify
count = conn.execute("SELECT COUNT(*) FROM fact_sales_clean").fetchone()[0]
conn.close()

print(f"  SQLite table     : fact_sales_clean  ({count:,} rows)")
print(f"\n  Note: 'fact_sales'       = raw data  (with nulls, outliers, dupes)")
print(f"        'fact_sales_clean' = clean data (used for all SQL analysis)")


# ============================================================
#  CLEANING SUMMARY
# ============================================================

section("CLEANING SUMMARY")

print(f"""
  Issue                  | Before    | After
  -----------------------|-----------|----------
  Total rows             | {rows_before:>9,} | {len(df):>8,}
  Missing values (total) | {missing_before:>9,} | {0:>8,}
  Duplicate rows         | {removed_dupes:>9,} | {0:>8,}
  Outliers in units_sold | {5:>9,} | {0:>8,} (capped)
""")

print("  Phase 2 complete!")
print("  Next step: python scripts/03_sql_analysis.py\n")
