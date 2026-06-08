-- ============================================================
--  Query 1: Region-wise Revenue Analysis
--  Business Question: Which regions drive the most revenue?
--  SQL Concepts: GROUP BY, ORDER BY, aggregate functions
-- ============================================================

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
