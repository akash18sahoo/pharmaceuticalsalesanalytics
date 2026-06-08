# Pharmaceutical Sales Analytics — ZS BTSA Interview Prep Guide

> **How to use this guide**: Read it section by section. For every concept, understand the *what*, the *why*, and the *how to explain it*. The "Interview Q&A" blocks tell you exactly what to say.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [ZS BTSA Role Context](#2-zs-btsa-role-context)
3. [Dataset Design](#3-dataset-design)
4. [Phase 1 — Data Generation](#4-phase-1--data-generation)
5. [Phase 2 — Data Cleaning](#5-phase-2--data-cleaning)
6. [Phase 3 — SQL Analysis](#6-phase-3--sql-analysis)
7. [Phase 4 — Visualizations](#7-phase-4--visualizations)
8. [Pharma Domain Knowledge](#8-pharma-domain-knowledge)
9. [Master Interview Story](#9-master-interview-story)
10. [Likely Interview Questions & Answers](#10-likely-interview-questions--answers)

---

## 1. Project Overview

### What is this project?

An **end-to-end pharmaceutical sales analytics solution** that simulates the kind of work ZS Associates does for pharma clients every day.

### The pipeline

```
[Raw Data Generation] → [Data Cleaning] → [SQL Analysis] → [Visualizations]
       Phase 1                Phase 2           Phase 3           Phase 4
  generate_data.py        clean_data.py      sql_analysis.py  visualizations.py
```

### Files at a glance

```
pharmaceuticalsalesanalytics/
├── data/
│   ├── generate_data.py          ← generates synthetic dataset
│   ├── pharma_sales.csv          ← raw data (5,010 rows, has dirty data)
│   ├── pharma_sales_clean.csv    ← cleaned data (5,000 rows)
│   └── pharma_sales.db           ← SQLite database (2 tables)
│
├── scripts/
│   ├── 01_generate_data.py       ← Phase 1
│   ├── 02_clean_data.py          ← Phase 2
│   ├── 03_sql_analysis.py        ← Phase 3
│   └── 04_visualizations.py      ← Phase 4
│
├── sql/
│   ├── schema/01_create_tables.sql
│   └── analysis/
│       ├── 02_region_sales.sql   ← GROUP BY + aggregate
│       ├── 03_top_drugs.sql      ← CTE + DENSE_RANK()
│       ├── 04_monthly_growth.sql ← CTE + LAG()
│       ├── 05_rep_performance.sql← CTE + CASE WHEN + RANK()
│       └── 06_quarterly_summary.sql ← CTE + SUM() OVER()
│
└── reports/figures/
    ├── chart1_revenue_by_region.png
    ├── chart2_monthly_trend.png
    ├── chart3_top_drugs.png
    ├── chart4_drug_class_pie.png
    ├── chart5_rep_achievement.png
    └── chart6_yoy_growth.png
```

---

## 2. ZS BTSA Role Context

### What does BTSA stand for?
**Business Technology Solutions Associate** — ZS's technical consulting track.

### What does a BTSA actually do?
- Works with pharma clients to build **data-driven technology solutions**
- Designs databases, writes SQL queries, builds dashboards
- Translates **business problems** into **technical solutions**
- Takes **end-to-end ownership** of a deliverable — from raw data to insights

### Why does this project fit the BTSA role?

| BTSA Responsibility | How This Project Demonstrates It |
|---------------------|----------------------------------|
| Solution design | Star schema DB + ETL pipeline |
| SQL mastery | 5 queries using CTEs, window functions |
| Data cleaning | Handling nulls, outliers, duplicates |
| Business insight | SFE analysis, regional performance, growth metrics |
| Stakeholder output | 6 charts ready for business presentations |

### Key ZS interview focus areas:
1. **SQL** — CTEs, window functions, complex joins
2. **Python** — Pandas, NumPy, data manipulation
3. **Domain** — Pharma KPIs (SFE, TRx, NRx, territory)
4. **Problem-solving** — Structure, logic, business context

---

## 3. Dataset Design

### Why synthetic data?

- No Kaggle access needed — fully self-contained
- You control every variable — you can explain every pattern
- Realistic business rules baked in — just like a real client dataset

### Dataset columns explained

| Column | Type | Description | Why Included |
|--------|------|-------------|--------------|
| `sale_id` | TEXT | TXN-00001 format | Unique identifier — primary key |
| `date` | DATE | 2020-01-01 to 2024-12-30 | 5 years of data for trend analysis |
| `year` | INT | 2020–2024 | Pre-extracted for easy SQL GROUP BY |
| `month` | INT | 1–12 | Pre-extracted for seasonal analysis |
| `quarter` | TEXT | Q1–Q4 | Pre-extracted for quarterly reporting |
| `drug_name` | TEXT | 10 real drug names | Drug performance analysis |
| `drug_class` | TEXT | 6 ATC categories | Class-level market share |
| `region` | TEXT | North/South/East/West/Central | Territory analysis |
| `channel` | TEXT | Hospital / Pharmacy | Channel effectiveness |
| `rep_name` | TEXT | 20 sales reps | Sales Force Effectiveness (SFE) |
| `manager` | TEXT | 5 regional managers | Team-level rollup |
| `units_sold` | FLOAT | Units per transaction | Volume analysis |
| `unit_price` | FLOAT | Price in INR | Pricing analysis |
| `revenue` | FLOAT | units × price | Core KPI |
| `target_revenue` | FLOAT | Monthly target for rep | SFE: actual vs target |

### The 10 drugs and their classes

| Drug | Class | Price Range (INR) | Interview Note |
|------|-------|-------------------|----------------|
| Insulin Glargine | Diabetes | 800–1200 | Highest price → highest revenue despite fewer units |
| Metformin | Diabetes | 200–350 | High volume, moderate price |
| Atorvastatin | Cardiovascular | 150–300 | Cholesterol drug — very common |
| Amlodipine | Cardiovascular | 100–200 | Blood pressure — chronic use |
| Aspirin | Cardiovascular | 50–100 | Lowest price, high volume |
| Sertraline | CNS | 300–600 | Antidepressant — high price, steady demand |
| Amoxicillin | Anti-infective | 120–250 | Seasonal peak in winter |
| Ciprofloxacin | Anti-infective | 180–350 | Antibiotic — seasonal |
| Omeprazole | Gastrointestinal | 90–180 | Acid reflux — consistent demand |
| Ibuprofen | Pain & Inflammation | 60–130 | OTC-style drug, price sensitive |

---

## 4. Phase 1 — Data Generation

**Script**: `scripts/01_generate_data.py`

### What it does (step by step)

#### Step 1: Configuration setup
Defined dictionaries for drugs, regions, reps, managers — this is the "master data" or reference data, equivalent to dimension tables in a data warehouse.

#### Step 2: Business multipliers

This is what makes the data realistic. Four multipliers are applied to every transaction:

**Regional multiplier** — North sells more than South:
```python
REGION_MULT = {
    'North': 1.20,   # 20% above average
    'West':  1.10,   # 10% above average
    'East':  1.00,   # baseline
    'Central': 0.90, # 10% below
    'South': 0.80,   # 20% below — weakest territory
}
```

**Seasonal multiplier** — Demand varies by drug class and month:
```python
# Anti-infectives peak in Jan (winter infections)
'Anti-infective': {1: 1.3, 2: 1.2, ..., 12: 1.3}

# Cardiovascular peaks in winter (cold weather, heart strain)
'Cardiovascular': {1: 1.2, 2: 1.2, ..., 12: 1.3}
```

**Year-over-year growth** — ~10% annual growth baked in:
```python
YOY_GROWTH = {2020: 1.00, 2021: 1.09, 2022: 1.18, 2023: 1.28, 2024: 1.40}
```

**Rep performance tier (Pareto Effect)** — Top reps sell 1.5x more:
```python
REP_TIER = {
    'Ravi Kumar': 1.50,    # Star performer (1st rep in each region)
    'Priya Sharma': 1.00,  # Average
    'Anjali Singh': 1.00,  # Average
    'Rahul Verma': 0.70,   # Underperformer (last rep in each region)
}
```

#### Step 3: Units sold formula

```python
units_sold = int(
    base_units              # ~100 units (normal distribution)
    * seasonal_factor       # 0.8 to 1.3
    * region_factor         # 0.8 to 1.2
    * rep_factor            # 0.7 to 1.5
    * growth_factor         # 1.0 to 1.4
    * np.random.uniform(0.85, 1.15)  # random noise
)
```

#### Step 4: Target revenue logic

This is important for SFE analysis:
- **Star reps** get a target slightly BELOW their actual (target × 0.95) → they beat target easily
- **Average reps** get target slightly ABOVE actual (target × 1.05) → they nearly hit target
- **Underperformers** get target well above actual (target × 1.15) → they consistently miss target

This creates a realistic SFE distribution.

#### Step 5: Dirty data (for Phase 2)

Intentionally introduced:
```python
df.loc[idx[:20], 'units_sold']   = np.nan   # 20 missing values
df.loc[idx[20:35], 'unit_price'] = np.nan   # 15 missing values
df.loc[idx[35:40], 'units_sold'] = np.random.randint(6000, 9000, 5)  # 5 outliers
duplicates = df.iloc[idx[40:50]].copy()     # 10 duplicate rows
```

### Interview Q&A — Phase 1

**Q: Why did you use `np.random.seed(42)`?**

> "Setting a random seed ensures reproducibility — every time I run the script, I get the exact same dataset. This is critical in data science so that your results are consistent and shareable. It's a standard best practice."

**Q: Why synthetic data instead of real data?**

> "I chose synthetic data for three reasons: First, I could control the complexity and ensure it covered all the analytical scenarios I wanted to demonstrate. Second, it avoids data privacy concerns — real pharma sales data is often proprietary. Third, I could engineer realistic patterns like seasonality, regional variance, and Pareto distribution of rep performance that you'd see in actual pharma datasets."

**Q: What is the Pareto effect you mentioned?**

> "In sales, the Pareto principle — or 80/20 rule — means roughly 20% of sales reps drive 80% of revenue. I modeled this by assigning 1.5x performance to the top rep in each region and 0.7x to the bottom rep. The resulting data shows the top 5 reps (25% of 20) contributing disproportionately to total revenue, which matches real-world pharma sales patterns."

---

## 5. Phase 2 — Data Cleaning

**Script**: `scripts/02_clean_data.py`

### The 5 cleaning steps

#### Step 1: Inspect data quality

Always inspect before touching anything:

```python
df.isnull().sum()      # count nulls per column
df.dtypes              # check data types
df.duplicated().sum()  # count exact duplicates
```

**What we found:**
- 20 missing `units_sold` values (0.4%)
- 15 missing `unit_price` values (0.3%)
- 10 duplicate rows
- 5 outlier rows (units_sold = 6,000–9,000 vs. normal range of 5–274)

#### Step 2: Remove duplicates

```python
df = df.drop_duplicates()
# 5,010 rows → 5,000 rows (10 removed)
```

**Why**: Duplicate transactions would double-count revenue in SQL aggregations — a classic data quality issue.

#### Step 3: Fix data types

```python
df['date']  = pd.to_datetime(df['date'])   # string → datetime
df['year']  = df['year'].astype('Int64')   # ensure integer
df['month'] = df['month'].astype('Int64')
```

**Why**: SQL and Pandas operations on dates require proper datetime types. String '2022-01-15' can't be used in date arithmetic.

#### Step 4: Handle missing values — Median Imputation

```python
# Fill missing units_sold with median of same drug_class
df['units_sold'] = df.groupby('drug_class')['units_sold'].transform(
    lambda x: x.fillna(x.median())
)

# Fill missing unit_price with median of same drug_name
df['unit_price'] = df.groupby('drug_name')['unit_price'].transform(
    lambda x: x.fillna(x.median())
)
```

**Why median and not mean?**
The mean is sensitive to outliers. If one row has units_sold = 8,000 (an outlier), it pulls the mean up significantly. The median is the middle value, unaffected by extremes.

**Why group by drug_class/drug_name?**
Missing units for an Insulin Glargine transaction should be filled with the median of other Insulin Glargine transactions — not the median of all drugs. Context-aware imputation is more accurate.

#### Step 5: Handle outliers — IQR Capping (Winsorization)

```python
q1  = df['units_sold'].quantile(0.25)  # 25th percentile
q3  = df['units_sold'].quantile(0.75)  # 75th percentile
iqr = q3 - q1                          # interquartile range

lower = q1 - 1.5 * iqr  # anything below this = outlier
upper = q3 + 1.5 * iqr  # anything above this = outlier

df['units_sold'] = np.clip(df['units_sold'], lower, upper)
```

**What is IQR?**
IQR (Interquartile Range) = Q3 − Q1 = the spread of the middle 50% of data. The 1.5×IQR rule is the standard statistical definition of an outlier (used in box plots).

**Why cap instead of delete?**
We use `np.clip()` (Winsorization) — this caps values at the boundary rather than deleting the row. We keep the transaction, just correct the unrealistic value. Deleting rows loses information; capping preserves the data point.

### Interview Q&A — Phase 2

**Q: What is imputation? Why did you choose median?**

> "Imputation means filling missing values with estimated values instead of deleting the rows. I chose median imputation because median is resistant to outliers — it represents the typical value better than the mean when the data has extreme values. I also grouped by drug class or drug name, so the fill value is context-appropriate. For example, a missing price for Insulin Glargine is filled with the median price of other Insulin Glargine sales — not the median of all drugs."

**Q: What is Winsorization?**

> "Winsorization is a technique for handling outliers where instead of deleting the outlier row, you cap its value at a defined boundary. In my project, I used the IQR method to find the upper bound, then used NumPy's `clip()` function to set any value above that bound equal to the bound. This way I keep all 5,000 rows but remove the distorting effect of outliers like a units_sold value of 8,000 when the normal range is 5–274."

**Q: How did you detect outliers?**

> "I used the IQR method: Q1 is the 25th percentile, Q3 is the 75th percentile, and IQR = Q3 − Q1. Any value below Q1 − 1.5×IQR or above Q3 + 1.5×IQR is classified as an outlier. This is the same rule used in box-and-whisker plots. For units_sold, Q1 was 80, Q3 was 159, giving IQR = 79, so anything above 274 was an outlier."

**Q: Why did you recalculate revenue after imputation?**

> "After filling missing units_sold and unit_price, the existing revenue column was stale — it was calculated from the original (now incorrect) values. So I recalculated revenue as units_sold × unit_price to ensure consistency across all three columns."

---

## 6. Phase 3 — SQL Analysis

**Script**: `scripts/03_sql_analysis.py`  
**SQL files**: `sql/analysis/`  
**Database**: `data/pharma_sales.db` → table: `fact_sales_clean`

### How SQL runs from Python

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/pharma_sales.db')

# Read SQL file and execute it
with open('sql/analysis/02_region_sales.sql', 'r') as f:
    sql = f.read()

df = pd.read_sql_query(sql, conn)
conn.close()
```

`sqlite3` is Python's built-in library — no installation needed. `pd.read_sql_query()` runs the SQL and returns the result directly as a Pandas DataFrame.

---

### Query 1 — Region-wise Revenue

**File**: `sql/analysis/02_region_sales.sql`  
**Business Question**: Which regions drive the most revenue?

```sql
SELECT
    region,
    COUNT(sale_id)                              AS total_transactions,
    SUM(units_sold)                             AS total_units,
    ROUND(SUM(revenue), 2)                      AS total_revenue,
    ROUND(AVG(revenue), 2)                      AS avg_revenue_per_sale,
    ROUND(SUM(revenue) * 100.0
          / (SELECT SUM(revenue) FROM fact_sales_clean), 2) AS revenue_share_pct
FROM fact_sales_clean
GROUP BY region
ORDER BY total_revenue DESC;
```

**Explain line by line:**

| Part | What it does |
|------|-------------|
| `COUNT(sale_id)` | Counts rows per region = total transactions |
| `SUM(revenue)` | Adds up all revenue for that region |
| `AVG(revenue)` | Average revenue per single sale |
| `SUM(revenue) * 100.0 / (SELECT SUM(...))` | Subquery calculates total revenue once, then divides to get % share |
| `GROUP BY region` | Creates one row per region |
| `ORDER BY total_revenue DESC` | Highest revenue first |

**Result:**
```
region   | total_revenue | revenue_share_pct
North    | 43,456,076    | 24.7%
West     | 37,033,892    | 21.1%
East     | 35,108,732    | 20.0%
Central  | 33,145,894    | 18.9%
South    | 26,936,516    | 15.3%
```

**Business Insight**: North has 24.7% of revenue. South is the weakest at 15.3% — a ZS client would ask: "Should we reallocate sales reps from Central to South?"

---

### Query 2 — Top 3 Drugs per Region (CTE + DENSE_RANK)

**File**: `sql/analysis/03_top_drugs.sql`  
**Business Question**: Which drug is the top seller in each region?

```sql
WITH drug_revenue AS (
    SELECT
        region,
        drug_name,
        drug_class,
        ROUND(SUM(revenue), 2)   AS total_revenue,
        SUM(units_sold)          AS total_units
    FROM fact_sales_clean
    GROUP BY region, drug_name, drug_class
),
ranked_drugs AS (
    SELECT *,
        DENSE_RANK() OVER (
            PARTITION BY region
            ORDER BY total_revenue DESC
        ) AS rank_in_region
    FROM drug_revenue
)
SELECT region, rank_in_region AS rank, drug_name, drug_class, total_revenue
FROM ranked_drugs
WHERE rank_in_region <= 3
ORDER BY region, rank_in_region;
```

**Understanding CTEs:**

A CTE (Common Table Expression) is a named temporary result set, defined with `WITH name AS (...)`. Think of it as giving a subquery a name so you can refer to it cleanly.

```
Without CTE (hard to read):          With CTE (clear and readable):
SELECT * FROM (                      WITH drug_revenue AS (
  SELECT *, DENSE_RANK()...              SELECT region, SUM(revenue)...
  FROM (                             )
    SELECT region, SUM(revenue)...   SELECT * FROM drug_revenue...
  )
) WHERE rank <= 3
```

**Understanding DENSE_RANK():**

A window function that ranks rows within a partition without collapsing them.

```
DENSE_RANK() OVER (PARTITION BY region ORDER BY total_revenue DESC)
              ↑                  ↑                  ↑
       window function    reset rank       sort within each group
                          per region       (highest revenue = rank 1)
```

**RANK vs DENSE_RANK:**

| Function | If two drugs tie at 2nd place... |
|----------|----------------------------------|
| `RANK()` | Both get rank 2, next gets rank 4 (gap) |
| `DENSE_RANK()` | Both get rank 2, next gets rank 3 (no gap) |

We use `DENSE_RANK()` so we always get exactly top 3 even if there are ties.

---

### Query 3 — Month-over-Month Growth (CTE + LAG)

**File**: `sql/analysis/04_monthly_growth.sql`  
**Business Question**: Is revenue growing or declining month over month?

```sql
WITH monthly_revenue AS (
    SELECT year, month,
        ROUND(SUM(revenue), 2) AS monthly_revenue
    FROM fact_sales_clean
    GROUP BY year, month
),
growth_calc AS (
    SELECT *,
        LAG(monthly_revenue) OVER (
            ORDER BY year, month
        ) AS prev_month_revenue
    FROM monthly_revenue
)
SELECT
    year, month, monthly_revenue, prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL THEN NULL
        ELSE ROUND(
            (monthly_revenue - prev_month_revenue)
            * 100.0 / prev_month_revenue, 2
        )
    END AS mom_growth_pct
FROM growth_calc
ORDER BY year, month;
```

**Understanding LAG():**

`LAG(column)` is a window function that returns the value from the **previous row** in the defined order.

```
Without LAG (requires self-join):     With LAG (elegant, one pass):
SELECT a.month, a.revenue,            SELECT month, revenue,
       b.revenue AS prev_revenue      LAG(revenue) OVER
FROM monthly a                            (ORDER BY year, month)
JOIN monthly b ON a.month = b.month+1     AS prev_revenue
                                      FROM monthly
```

LAG() is more efficient — no self-join, reads the table once.

**Growth formula:**
```
mom_growth_pct = (this_month - last_month) / last_month × 100
```

**Result insight**: Average MoM growth is +4.2%, with the best month at +124.6% (likely a seasonal spike) and worst at -36.5%.

---

### Query 4 — Sales Rep SFE (CTE + CASE WHEN + RANK)

**File**: `sql/analysis/05_rep_performance.sql`  
**Business Question**: Which reps are hitting their targets? (SFE analysis)

```sql
WITH rep_summary AS (
    SELECT rep_name, manager, region,
        COUNT(sale_id)               AS total_transactions,
        ROUND(SUM(revenue), 2)       AS actual_revenue,
        ROUND(SUM(target_revenue),2) AS target_revenue
    FROM fact_sales_clean
    GROUP BY rep_name, manager, region
),
rep_performance AS (
    SELECT *,
        ROUND(actual_revenue * 100.0 / target_revenue, 1) AS achievement_pct,
        RANK() OVER (
            PARTITION BY region
            ORDER BY actual_revenue DESC
        ) AS rank_in_region
    FROM rep_summary
)
SELECT rank_in_region AS rank, rep_name, manager, region,
       actual_revenue, target_revenue, achievement_pct,
    CASE
        WHEN achievement_pct >= 100 THEN 'Target Met'
        WHEN achievement_pct >= 85  THEN 'Near Target'
        ELSE                             'Below Target'
    END AS performance_status
FROM rep_performance
ORDER BY achievement_pct DESC;
```

**Why two CTEs?**

- CTE 1 (`rep_summary`): aggregates raw transactions into one row per rep
- CTE 2 (`rep_performance`): calculates achievement % and rank ON TOP of the summary

You can't use a window function on the same SELECT where you define a GROUP BY — CTEs let you layer the logic cleanly.

**CASE WHEN** is SQL's if-else:
```sql
CASE
    WHEN condition1 THEN result1
    WHEN condition2 THEN result2
    ELSE default_result
END
```

**SFE result (key talking point for ZS):**

```
Top performers (Target Met): Suresh Nair 105.5%, Deepak Gupta 104.3%,
                              Arnab Das 103.2%, Ravi Kumar 101.8%,
                              Nikhil Joshi 101.7%
Near Target (85–99%)       : 15 reps
Below Target (<85%)         : 0 reps
```

---

### Query 5 — Quarterly Cumulative Revenue (CTE + SUM OVER)

**File**: `sql/analysis/06_quarterly_summary.sql`  
**Business Question**: Are we on track to hit annual revenue targets?

```sql
WITH quarterly_revenue AS (
    SELECT year, quarter,
        ROUND(SUM(revenue), 2)   AS quarterly_revenue,
        COUNT(sale_id)           AS transactions
    FROM fact_sales_clean
    GROUP BY year, quarter
)
SELECT *,
    ROUND(
        SUM(quarterly_revenue) OVER (
            PARTITION BY year
            ORDER BY quarter
        ), 2
    ) AS cumulative_revenue_ytd,
    ROUND(
        quarterly_revenue * 100.0 /
        SUM(quarterly_revenue) OVER (PARTITION BY year)
    , 1) AS pct_of_annual_revenue
FROM quarterly_revenue
ORDER BY year, quarter;
```

**Understanding `SUM() OVER (PARTITION BY year ORDER BY quarter)`:**

This is a **running/cumulative sum** that resets each year.

```
year | quarter | revenue | cumulative_ytd
2022 |   Q1    |  6.9M   |     6.9M      ← starts fresh
2022 |   Q2    |  7.4M   |    14.3M      ← Q1 + Q2
2022 |   Q3    |  9.3M   |    23.6M      ← Q1+Q2+Q3
2022 |   Q4    | 11.7M   |    35.2M      ← full year total
2023 |   Q1    |  9.4M   |     9.4M      ← RESETS because year changed
```

**Key difference from GROUP BY:**
- `GROUP BY` collapses rows → one row per group
- `SUM() OVER()` keeps all rows and adds a running total column

**YoY Revenue:**
```
2020: INR 29.8M (baseline)
2021: INR 32.9M (+10.3%)
2022: INR 35.2M (+7.0%)
2023: INR 38.4M (+9.1%)
2024: INR 39.3M (+2.3%)
```

### Interview Q&A — Phase 3

**Q: What is a CTE and why use it over a subquery?**

> "A CTE, or Common Table Expression, is a named temporary result set defined at the start of a query using the WITH keyword. I prefer CTEs over subqueries for three reasons. First, readability — you name each intermediate step, so the query reads like a story. Second, reusability — you can reference the same CTE multiple times in one query without repeating code. Third, debugging — you can test each CTE independently by just running that block."

**Q: Explain window functions. How are they different from GROUP BY?**

> "GROUP BY collapses multiple rows into one row per group — you lose the individual row data. Window functions perform calculations ACROSS rows related to the current row but keep all the original rows intact. For example, when I use `RANK() OVER (PARTITION BY region ORDER BY revenue DESC)`, every row keeps its original data AND gets an additional rank column. GROUP BY would give me one row per region; RANK() gives me one row per rep with their rank added."

**Q: When would you use RANK vs DENSE_RANK vs ROW_NUMBER?**

> "All three are ranking window functions but differ in how they handle ties. ROW_NUMBER always gives a unique number even if rows are identical — good for deduplication. RANK gives the same rank to ties but skips numbers — so if two reps tie at rank 2, the next rank is 4. DENSE_RANK also gives same rank to ties but never skips — the next rank after two reps tied at 2 would be 3. I used DENSE_RANK for drug rankings because I wanted a clean 1, 2, 3 sequence without gaps."

**Q: What is LAG and why is it better than a self-join for growth calculations?**

> "LAG is a window function that accesses the value from a previous row in the same result set, based on the ORDER BY clause I define. For month-over-month growth, the alternative would be a self-join — joining the monthly table to itself on month = previous month. That's less efficient because it requires two table scans. LAG reads the data in one pass and looks back at the previous row directly, making it cleaner and faster."

---

## 7. Phase 4 — Visualizations

**Script**: `scripts/04_visualizations.py`  
**Output**: `reports/figures/` (6 PNG files)

### Chart 1 — Revenue by Region (Horizontal Bar)

**What it shows**: Revenue comparison across 5 regions with average line.

**Key code concepts:**
```python
ax.barh(region_rev.index, region_rev.values / 1e6, color=REGION_COLORS)
ax.axvline(region_rev.mean() / 1e6, linestyle='--', label='Avg')
```

- `barh` = horizontal bar (better for labeled categories)
- Dividing by `1e6` converts INR to millions for readability
- Average line gives a reference point

**Business Insight**: North leads at INR 43.5M; South is 38% below North.

---

### Chart 2 — Monthly Revenue Trend (Multi-Year Line)

**What it shows**: All 5 years overlaid on same month axis to spot seasonality.

**Key code concepts:**
```python
for year in sorted(monthly['year'].unique()):
    yd = monthly[monthly['year'] == year]
    ax.plot(yd['month'], yd['revenue'] / 1e6, label=str(year))
ax.axvspan(9.5, 12.5, alpha=0.08, color=ORANGE)  # highlight Q4
```

- Loop over years to plot each as a separate line
- `axvspan` shades the Q4 region (Oct–Dec)
- Each year gets a distinct color

**Business Insight**: Q4 (Oct–Dec) spikes consistently across all years — driven by Anti-infective and Cardiovascular seasonal demand.

---

### Chart 3 — Top 10 Drugs by Revenue (Bar Chart)

**What it shows**: Drug rankings colored by drug class.

**Key code concepts:**
```python
class_color_map = {cls: COLOR for cls in drug_rev['drug_class'].unique()}
bar_colors = drug_rev['drug_class'].map(class_color_map).tolist()
ax.bar(range(len(drug_rev)), drug_rev['revenue'] / 1e6, color=bar_colors)
```

- Mapping drug class to color makes the legend meaningful
- `.map()` applies the dictionary to the column to get a color per bar

**Business Insight**: Insulin Glargine (INR 61M) leads despite not being the highest-volume drug — its price range (INR 800–1,200) makes it the revenue champion. This is a useful insight: volume ≠ revenue.

---

### Chart 4 — Drug Class Pie Chart

**What it shows**: Market share by drug category.

**Key code concepts:**
```python
ax.pie(class_rev.values, autopct='%1.1f%%', startangle=140,
       wedgeprops=dict(edgecolor='white', linewidth=1.8))
```

- `autopct` shows percentage on each slice
- `startangle=140` rotates the pie for better readability
- White edge between slices for clean separation

---

### Chart 5 — Sales Rep Achievement % (Color-Coded Bar)

**What it shows**: All 20 reps ranked by target achievement, green/orange by status.

**Key code concepts:**
```python
def rep_color(pct):
    if pct >= 100: return GREEN
    elif pct >= 85: return ORANGE
    else: return RED

bar_colors = [rep_color(p) for p in rep_data['achievement_pct']]
ax.axvline(100, color=GREEN, linestyle='--', label='Target (100%)')
```

- List comprehension applies color function to every rep
- Two reference lines make the threshold visually clear

**Business Insight**: This chart is exactly what a ZS SFE dashboard shows a sales manager. Top 5 reps (green) = Rank 1 in each region.

---

### Chart 6 — Year-over-Year Growth (Dual Axis)

**What it shows**: Revenue bars + YoY growth % line on secondary axis.

**Key code concepts:**
```python
ax1 = fig.subplots()            # primary axis for bars
ax2 = ax1.twinx()               # secondary axis shares X, has own Y
ax2.plot(yearly['year'], yearly['yoy_growth_pct'], color=ORANGE)
ax2.grid(False)                 # avoid double grid lines
```

- `twinx()` creates a second Y-axis on the right sharing the same X-axis
- Turning off grid on ax2 avoids a messy overlapping grid

**Business Insight**: YoY growth slows in 2024 (+2.3% vs 10.3% in 2021) — a ZS analyst would flag this and investigate whether it's a market saturation issue or a data issue.

### Interview Q&A — Phase 4

**Q: Why did you use horizontal bar charts for regions instead of vertical?**

> "Horizontal bar charts are better when the category labels are long text strings like region names or rep names. In a vertical bar chart, long labels either overlap or need to be rotated diagonally, which reduces readability. Horizontal charts give each label its own clear row, making it much easier to compare."

**Q: What does `twinx()` do in Matplotlib?**

> "twinx() creates a second Y-axis on the right side that shares the same X-axis with the original. This lets me plot two different units on the same chart — in my YoY growth chart, the left Y-axis shows absolute revenue in millions of INR (bars), while the right Y-axis shows growth percentage (line). Without twinx(), the two scales would be incompatible."

**Q: Why save charts as PNG files instead of just showing them?**

> "In a business context, charts need to be shared — in PowerPoint presentations, reports, emails. By saving them as PNG files with `fig.savefig()`, the charts can be used anywhere without needing to re-run the Python script. I set `dpi=150` for high resolution and `bbox_inches='tight'` so labels aren't cut off at the edges."

---

## 8. Pharma Domain Knowledge

This section is what separates a ZS candidate from a generic data analyst candidate.

### Key Pharma Metrics

| Metric | Full Name | What It Means |
|--------|-----------|---------------|
| **TRx** | Total Prescriptions | Total number of prescriptions written by doctors for a drug |
| **NRx** | New Prescriptions | Prescriptions written for patients starting the drug for the first time |
| **Refill Rx** | Refill Prescriptions | TRx − NRx = patients who are continuing the drug |
| **Market Share** | — | % of total category prescriptions that your drug captures |
| **SFE** | Sales Force Effectiveness | How well sales reps perform against their revenue/call targets |
| **HCP** | Healthcare Professional | Doctors, pharmacists, nurses — the people reps call on |
| **KOL** | Key Opinion Leader | High-influence doctors who shape prescribing behavior |
| **Launch** | Product Launch | When a new drug enters the market |

### Why TRx and NRx matter

- **High NRx, Low TRx**: Doctors are prescribing the drug to new patients, but patients aren't continuing → side effect or adherence problem
- **Low NRx, High TRx**: Few new patients, but existing patients are staying → drug has a loyal base but isn't growing
- **High both**: Drug is growing and patients are staying → healthy product

In my dataset, I used `new_patients` and `repeat_patients` as proxies for NRx and TRx.

### Drug Classes (ATC System)

ATC = Anatomical Therapeutic Chemical classification. This is the WHO's standard for classifying drugs.

| Class | Examples | Market Characteristics |
|-------|----------|----------------------|
| Cardiovascular | Atorvastatin, Amlodipine, Aspirin | Chronic use, large patient base |
| Diabetes | Metformin, Insulin Glargine | Growing market (diabetes epidemic) |
| CNS | Sertraline | Mental health awareness driving growth |
| Anti-infective | Amoxicillin, Ciprofloxacin | Seasonal peaks in winter |
| Gastrointestinal | Omeprazole | Chronic use, price-competitive |
| Pain & Inflammation | Ibuprofen | OTC competition, price sensitive |

### Sales Channels

| Channel | Characteristics |
|---------|----------------|
| Hospital | Higher-value drugs, specialty care, controlled environment |
| Retail Pharmacy | OTC and chronic-use drugs, consumer-facing |
| Specialty Clinic | Oncology, neurology — high-cost, targeted drugs |

In my dataset: Hospital = 40%, Pharmacy = 60% (typical split for a mixed portfolio).

### What is Sales Force Effectiveness (SFE)?

SFE is one of ZS's core service areas. It answers:
- Are reps calling on the right doctors?
- Are they spending enough time with high-value HCPs?
- Are they meeting their revenue and call targets?
- Which territory needs more/fewer reps?

My Query 4 (rep target achievement) and Chart 5 directly model SFE analysis.

---

## 9. Master Interview Story

Memorize this 2-minute project walkthrough. Say it confidently.

---

> "I built a pharmaceutical sales analytics project to simulate the kind of end-to-end solution delivery that ZS does for pharma clients.
>
> **The Data**: Since I didn't have access to real proprietary data, I designed and generated a synthetic dataset of 5,000 transactions spanning five years, ten drugs across six ATC drug classes, and twenty sales reps across five regions. I built in realistic business patterns — seasonal demand shifts, year-over-year growth of around 10%, and a Pareto distribution for rep performance where the top reps significantly outperform the rest.
>
> **Data Cleaning**: I intentionally introduced dirty data — missing values, duplicates, and outliers — to demonstrate a real cleaning pipeline. I used median imputation grouped by drug class for missing values, because median is robust to outliers. I used IQR-based Winsorization to cap outliers rather than delete them, preserving all rows.
>
> **SQL Analysis**: I wrote five SQL queries covering the full range of concepts — GROUP BY aggregations, CTEs, and window functions including DENSE_RANK for drug rankings, LAG for month-over-month growth, RANK for rep leaderboards, and cumulative SUM OVER for year-to-date tracking. All queries run against a SQLite database from Python via the sqlite3 library.
>
> **Visualizations**: I created six business charts in Matplotlib — regional revenue comparison, a multi-year seasonal trend chart, drug performance rankings, drug class market share, a color-coded SFE rep achievement dashboard, and a dual-axis year-over-year growth chart.
>
> **The ZS angle**: This project directly mirrors what BTSA does — I owned the full pipeline from data architecture to stakeholder-ready output. The SFE analysis in particular is a core ZS offering, and being able to discuss sales force effectiveness, territory management, and pharma KPIs like TRx and NRx gives me the domain context to match the technical skills."

---

## 10. Likely Interview Questions & Answers

### Technical — Python

**Q: How does `groupby().transform()` work?**

> "`.transform()` is like `.apply()` but it returns a result with the same index as the original DataFrame, keeping the number of rows intact. I used it to fill missing values — `df.groupby('drug_class')['units_sold'].transform(lambda x: x.fillna(x.median()))`. This computes the median per drug class group and fills nulls in that group, but returns a full-length series that I can assign back to the column. If I used `.agg()` instead, I'd get one row per group — not what I want for filling."

**Q: What is `np.clip()`?**

> "np.clip() restricts all values in an array to be within a specified range. `np.clip(arr, lower, upper)` — any value below lower becomes lower, any value above upper becomes upper, values in between stay unchanged. I used it for outlier capping — setting units_sold values above 274 to exactly 274."

**Q: What is `pd.to_datetime()` and why do we need it?**

> "pd.to_datetime() converts a column from string format (like '2022-03-15') to Python's datetime64 type. Once it's a proper datetime, you can extract `.dt.year`, `.dt.month`, `.dt.quarter`, perform date arithmetic like finding the number of days between two dates, sort chronologically, and use it in time-series resampling. String dates look like dates but behave like text — Python wouldn't know '2022-03-15' comes after '2021-12-31' without the conversion."

**Q: How does `pd.read_sql_query()` work?**

> "pd.read_sql_query() takes a SQL string and a database connection object, executes the SQL against the database, and returns the result as a Pandas DataFrame. I used it with a sqlite3 connection — `pd.read_sql_query(sql_string, conn)`. It's the bridge between SQL and Python, letting you do the heavy aggregation in SQL and then use Pandas for any Python-specific processing or visualization."

---

### Technical — SQL

**Q: What's the difference between WHERE and HAVING?**

> "WHERE filters rows before aggregation; HAVING filters groups after aggregation. For example, `WHERE revenue > 10000` filters individual transactions, while `HAVING SUM(revenue) > 1000000` filters groups after GROUP BY. You can't use aggregate functions like SUM() in a WHERE clause — that's what HAVING is for."

**Q: Can you explain PARTITION BY?**

> "PARTITION BY in a window function is like GROUP BY but without collapsing rows. It defines the groups within which the window function operates. So `RANK() OVER (PARTITION BY region ORDER BY revenue DESC)` restarts the rank at 1 for each new region. Without PARTITION BY, it would rank all reps across all regions as one big group."

**Q: When would you use a CTE vs a subquery vs a view?**

> "A subquery is embedded inside the main query — useful for simple one-time logic but hard to read when nested deeply. A CTE is a named subquery at the top of the query — better for readability and for logic you want to reference multiple times in the same query. A view is a saved query in the database — useful when the same aggregation is needed repeatedly across many queries or by multiple users. I used CTEs in my project because each query's logic is self-contained and I wanted maximum readability."

---

### Behavioral

**Q: Why are you interested in ZS Associates?**

> "ZS sits at the intersection of three things I'm interested in: data analytics, technology consulting, and the healthcare/pharma domain. The BTSA role specifically appeals to me because it's not just analysis — it's building production-quality solutions. The idea of owning a deliverable end-to-end, from data architecture to a dashboard a business user can interact with, is exactly the kind of work that gets me excited. Plus, pharma is a domain where the data really matters — better analytics can lead to better drug distribution, better rep coverage, and ultimately better patient outcomes."

**Q: Walk me through a challenge in this project.**

> "The most interesting challenge was designing the synthetic data to be realistic enough to produce meaningful analysis. I had to think carefully about what patterns actually exist in pharma sales — for example, that anti-infectives spike in winter due to respiratory infections, or that the top 20% of reps drive a disproportionate share of revenue. Getting the seasonal multipliers and the Pareto rep tier distribution right required research into real pharma industry patterns. The payoff was that every chart and SQL result tells a believable business story — there are real insights to discuss, not random noise."

**Q: What would you add to this project if you had more time?**

> "Three things. First, I'd add a Power BI dashboard — connecting the clean CSV to Power BI and building an interactive report with slicers for year, region, and drug class, so a business stakeholder could explore the data without touching code. Second, I'd add a simple revenue forecast using NumPy's polyfit for linear trend extrapolation — showing next year's projected revenue based on the historical growth rate. Third, I'd add a territory optimization analysis — looking at revenue per rep per region and suggesting whether any territory needs headcount changes. All three are things ZS actually builds for clients."

---

## Quick Reference Card (For Last-Minute Review)

```
PROJECT FACTS
  Dataset      : 5,010 rows → 5,000 after cleaning
  Columns      : 15
  Date range   : 2020-01-01 to 2024-12-30
  Drugs        : 10 (across 6 ATC classes)
  Regions      : 5 (North, South, East, West, Central)
  Sales Reps   : 20 (4 per region)
  Total Revenue: INR 17.57 Crore

CLEANING FACTS
  Duplicates removed : 10
  Nulls filled       : 35 (median imputation)
  Outliers capped    : 5 (IQR Winsorization)
  Method for nulls   : Grouped median (not global median)
  Method for outliers: np.clip() to IQR boundary

SQL CONCEPTS USED
  Query 1: GROUP BY, COUNT, SUM, AVG, subquery
  Query 2: CTE × 2, DENSE_RANK() OVER (PARTITION BY)
  Query 3: CTE × 2, LAG() OVER (ORDER BY year, month)
  Query 4: CTE × 2, CASE WHEN, RANK() OVER (PARTITION BY)
  Query 5: CTE × 1, SUM() OVER (PARTITION BY year ORDER BY quarter)

KEY RESULTS
  Top region    : North (INR 43.5M, 24.7% share)
  Weakest region: South (INR 26.9M, 15.3% share)
  Top drug      : Insulin Glargine (INR 61M)
  Top rep       : Suresh Nair (105.5% achievement)
  YoY growth    : ~7-10% per year (realistic pharma)
  Q4 peak       : Consistent across all years (seasonality)

PHARMA TERMS
  TRx = Total Prescriptions
  NRx = New Prescriptions
  SFE = Sales Force Effectiveness
  HCP = Healthcare Professional
  ATC = Anatomical Therapeutic Chemical (drug classification)
  KOL = Key Opinion Leader
```

---

*Good luck with your ZS BTSA interview! You built this project — you can defend every line of it.*
