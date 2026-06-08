-- ============================================================
--  Query 5: Quarterly Cumulative Revenue Summary
--  Business Question: Are we on track for annual revenue targets?
--  SQL Concepts: CTE, SUM() OVER() cumulative window function,
--                PARTITION BY year (resets each year)
-- ============================================================

WITH quarterly_revenue AS (
    -- Step 1: Aggregate by year and quarter
    SELECT
        year,
        quarter,
        ROUND(SUM(revenue), 2)        AS quarterly_revenue,
        COUNT(sale_id)                AS transactions,
        COUNT(DISTINCT rep_name)      AS active_reps,
        ROUND(AVG(revenue), 2)        AS avg_deal_size
    FROM fact_sales_clean
    GROUP BY year, quarter
)

-- Step 2: Add year-to-date cumulative revenue
--         PARTITION BY year means the running total resets each year
SELECT
    year,
    quarter,
    quarterly_revenue,
    transactions,
    active_reps,
    avg_deal_size,
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
