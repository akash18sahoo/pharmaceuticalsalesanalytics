# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
"""
=============================================================
  PHASE 3 — SQL Analysis
=============================================================
  What this script does:
    Connects to data/pharma_sales.db and runs all 5 SQL
    queries against the clean table (fact_sales_clean).
    Results are printed as formatted tables with insights.

  SQL Concepts covered:
    Query 1 : GROUP BY + aggregate functions
    Query 2 : CTE + DENSE_RANK() window function
    Query 3 : CTE + LAG() window function
    Query 4 : CTE + CASE WHEN + RANK() window function
    Query 5 : CTE + SUM() OVER() cumulative window

  Run:  python scripts/03_sql_analysis.py
=============================================================
"""

import sqlite3
import pandas as pd
import os

pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 120)
pd.set_option('display.float_format', '{:,.2f}'.format)


# ── Helpers ───────────────────────────────────────────────────

def section(title, subtitle=''):
    print()
    print("=" * 62)
    print(f"  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print("=" * 62)

def run_query(conn, sql_file):
    """Read a .sql file and execute it, return a DataFrame."""
    with open(sql_file, 'r') as f:
        sql = f.read()
    return pd.read_sql_query(sql, conn)

def insight(text):
    print(f"\n  >> INSIGHT: {text}")


# ============================================================
#  Connect to Database
# ============================================================

db_path = 'data/pharma_sales.db'
if not os.path.exists(db_path):
    print("ERROR: Database not found. Run Phase 1 first.")
    sys.exit(1)

conn = sqlite3.connect(db_path)

# Verify clean table exists
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table'", conn
)
print(f"\n  Connected to: {db_path}")
print(f"  Tables available: {tables['name'].tolist()}")


# ============================================================
#  QUERY 1: Region-wise Revenue
# ============================================================

section(
    "QUERY 1 — Region-wise Revenue Analysis",
    "SQL: GROUP BY, SUM, AVG, COUNT, subquery for % share"
)

df_region = run_query(conn, 'sql/analysis/02_region_sales.sql')
print(f"\n{df_region.to_string(index=False)}")

top_region  = df_region.iloc[0]['region']
top_revenue = df_region.iloc[0]['total_revenue']
top_share   = df_region.iloc[0]['revenue_share_pct']
low_region  = df_region.iloc[-1]['region']

insight(f"'{top_region}' is the highest-revenue region contributing "
        f"{top_share}% of total revenue (INR {top_revenue:,.0f}).")
insight(f"'{low_region}' is the weakest region — potential area for "
        f"sales team intervention.")


# ============================================================
#  QUERY 2: Top 3 Drugs per Region
# ============================================================

section(
    "QUERY 2 — Top 3 Drugs per Region",
    "SQL: CTE + DENSE_RANK() OVER (PARTITION BY region ORDER BY revenue DESC)"
)

df_drugs = run_query(conn, 'sql/analysis/03_top_drugs.sql')
print(f"\n{df_drugs.to_string(index=False)}")

# Find the #1 drug overall across all regions
top_drug = (df_drugs[df_drugs['rank'] == 1]
            .groupby('drug_name')['total_revenue']
            .sum()
            .idxmax())

insight(f"'{top_drug}' appears as the #1 drug in the most regions.")
insight("DENSE_RANK() was used here instead of RANK() to avoid "
        "gaps in ranking when two drugs tie in revenue.")


# ============================================================
#  QUERY 3: Month-over-Month Growth
# ============================================================

section(
    "QUERY 3 — Month-over-Month Revenue Growth",
    "SQL: CTE + LAG() OVER (ORDER BY year, month)"
)

df_growth = run_query(conn, 'sql/analysis/04_monthly_growth.sql')

# Show only last 18 months for readability
print(f"\n  Showing last 18 months (full dataset has {len(df_growth)} months):\n")
print(df_growth.tail(18).to_string(index=False))

# Stats
avg_growth = df_growth['mom_growth_pct'].dropna().mean()
best_month = df_growth.loc[df_growth['mom_growth_pct'].idxmax()]
worst_month = df_growth.loc[df_growth['mom_growth_pct'].idxmin()]

insight(f"Average MoM growth across all months: {avg_growth:.1f}%")
insight(f"Best month  : Year {int(best_month['year'])}, "
        f"Month {int(best_month['month'])} "
        f"(+{best_month['mom_growth_pct']:.1f}%)")
insight(f"Worst month : Year {int(worst_month['year'])}, "
        f"Month {int(worst_month['month'])} "
        f"({worst_month['mom_growth_pct']:.1f}%)")
insight("LAG() looks at the previous row's value without collapsing "
        "rows — unlike a self-join, no duplicate scans needed.")


# ============================================================
#  QUERY 4: Sales Rep Target Achievement (SFE)
# ============================================================

section(
    "QUERY 4 — Sales Rep Performance vs Target (SFE)",
    "SQL: CTE + CASE WHEN + RANK() OVER (PARTITION BY region)"
)

df_rep = run_query(conn, 'sql/analysis/05_rep_performance.sql')
print(f"\n{df_rep.to_string(index=False)}")

# Summary by performance bucket
bucket_counts = df_rep['performance_status'].value_counts()
print(f"\n  -- Performance Bucket Summary --")
for status, count in bucket_counts.items():
    pct = count / len(df_rep) * 100
    print(f"  {status:<15} : {count} reps  ({pct:.0f}%)")

best_rep  = df_rep.iloc[0]['rep_name']
best_pct  = df_rep.iloc[0]['achievement_pct']
worst_rep = df_rep.iloc[-1]['rep_name']
worst_pct = df_rep.iloc[-1]['achievement_pct']

insight(f"Top performer: {best_rep} at {best_pct:.1f}% target achievement.")
insight(f"Needs coaching: {worst_rep} at {worst_pct:.1f}% target achievement.")
insight("SFE (Sales Force Effectiveness) is a core ZS consulting area — "
        "this query directly mimics what ZS builds for pharma clients.")


# ============================================================
#  QUERY 5: Quarterly Cumulative Revenue
# ============================================================

section(
    "QUERY 5 — Quarterly Cumulative Revenue (YTD)",
    "SQL: CTE + SUM() OVER (PARTITION BY year ORDER BY quarter)"
)

df_qtly = run_query(conn, 'sql/analysis/06_quarterly_summary.sql')
print(f"\n{df_qtly.to_string(index=False)}")

# YoY revenue comparison
yearly = df_qtly.groupby('year')['quarterly_revenue'].sum()
print(f"\n  -- Year-over-Year Revenue --")
prev = None
for yr, rev in yearly.items():
    if prev is not None:
        yoy_pct = (rev - prev) / prev * 100
        print(f"  {yr}: INR {rev:>15,.0f}   (YoY growth: +{yoy_pct:.1f}%)")
    else:
        print(f"  {yr}: INR {rev:>15,.0f}   (baseline year)")
    prev = rev

insight("PARTITION BY year resets the cumulative sum at the start "
        "of each new year — this gives year-to-date (YTD) tracking.")
insight("The % of annual revenue column shows which quarter "
        "contributes most — useful for seasonal planning.")


# ============================================================
#  Close connection
# ============================================================

conn.close()

print()
print("=" * 62)
print("  ALL 5 QUERIES COMPLETE")
print("=" * 62)
print(f"""
  SQL concepts demonstrated:
    Query 1 : GROUP BY, SUM, AVG, COUNT, subquery
    Query 2 : CTE (2 levels) + DENSE_RANK() window
    Query 3 : CTE + LAG() window function
    Query 4 : CTE (2 levels) + CASE WHEN + RANK() window
    Query 5 : CTE + SUM() OVER() cumulative + PARTITION BY

  Phase 3 complete!
  Next step: python scripts/04_visualizations.py
""")
