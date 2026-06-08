-- ============================================================
--  Query 2: Top 3 Drugs per Region
--  Business Question: Which drug leads sales in each region?
--  SQL Concepts: CTE, DENSE_RANK() window function,
--                PARTITION BY, subquery filter
-- ============================================================

WITH drug_revenue AS (
    -- Step 1: Aggregate total revenue by region + drug
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
    -- Step 2: Rank drugs within each region by revenue
    SELECT
        region,
        drug_name,
        drug_class,
        total_revenue,
        total_units,
        DENSE_RANK() OVER (
            PARTITION BY region
            ORDER BY total_revenue DESC
        ) AS rank_in_region
    FROM drug_revenue
)

-- Step 3: Filter to top 3 per region only
SELECT
    region,
    rank_in_region  AS rank,
    drug_name,
    drug_class,
    total_revenue,
    total_units
FROM ranked_drugs
WHERE rank_in_region <= 3
ORDER BY region, rank_in_region;
