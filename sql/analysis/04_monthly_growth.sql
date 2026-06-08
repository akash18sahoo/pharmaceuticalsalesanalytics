-- ============================================================
--  Query 3: Month-over-Month Revenue Growth
--  Business Question: Is revenue growing month over month?
--  SQL Concepts: CTE, LAG() window function, growth % formula
-- ============================================================

WITH monthly_revenue AS (
    -- Step 1: Sum revenue for each year-month combination
    SELECT
        year,
        month,
        ROUND(SUM(revenue), 2)   AS monthly_revenue,
        COUNT(sale_id)           AS transactions
    FROM fact_sales_clean
    GROUP BY year, month
),

growth_calc AS (
    -- Step 2: Use LAG() to get previous month's revenue
    --         LAG(col) OVER (ORDER BY ...) looks at the row above
    SELECT
        year,
        month,
        monthly_revenue,
        transactions,
        LAG(monthly_revenue) OVER (
            ORDER BY year, month
        ) AS prev_month_revenue
    FROM monthly_revenue
)

-- Step 3: Calculate growth percentage
SELECT
    year,
    month,
    monthly_revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL THEN NULL
        ELSE ROUND(
            (monthly_revenue - prev_month_revenue)
            * 100.0 / prev_month_revenue, 2
        )
    END AS mom_growth_pct,
    transactions
FROM growth_calc
ORDER BY year, month;
