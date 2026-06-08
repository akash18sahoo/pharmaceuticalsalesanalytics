-- ============================================================
--  Query 4: Sales Rep Target Achievement (SFE)
--  Business Question: Which reps are meeting their targets?
--  SQL Concepts: GROUP BY, CASE WHEN, percentage calculation,
--                RANK() window function
--  Note: SFE (Sales Force Effectiveness) is a core ZS concept
-- ============================================================

WITH rep_summary AS (
    -- Step 1: Aggregate each rep's actual vs target revenue
    SELECT
        rep_name,
        manager,
        region,
        COUNT(sale_id)              AS total_transactions,
        ROUND(SUM(revenue), 2)      AS actual_revenue,
        ROUND(SUM(target_revenue),2) AS target_revenue
    FROM fact_sales_clean
    GROUP BY rep_name, manager, region
),

rep_performance AS (
    -- Step 2: Calculate achievement % and rank within region
    SELECT
        rep_name,
        manager,
        region,
        total_transactions,
        actual_revenue,
        target_revenue,
        ROUND(actual_revenue * 100.0 / target_revenue, 1) AS achievement_pct,
        RANK() OVER (
            PARTITION BY region
            ORDER BY actual_revenue DESC
        ) AS rank_in_region
    FROM rep_summary
)

-- Step 3: Add performance bucket using CASE WHEN
SELECT
    rank_in_region          AS rank,
    rep_name,
    manager,
    region,
    actual_revenue,
    target_revenue,
    achievement_pct,
    CASE
        WHEN achievement_pct >= 100 THEN 'Target Met'
        WHEN achievement_pct >= 85  THEN 'Near Target'
        ELSE                             'Below Target'
    END AS performance_status
FROM rep_performance
ORDER BY achievement_pct DESC;
