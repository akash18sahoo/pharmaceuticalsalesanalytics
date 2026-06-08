-- ============================================================
--  Pharmaceutical Sales Analytics — SQLite Schema
--  File   : sql/schema/01_create_tables.sql
--  Purpose: Create the fact_sales table and indexes
-- ============================================================

-- Drop if exists (safe re-run)
DROP TABLE IF EXISTS fact_sales;

-- ── Main Fact Table ──────────────────────────────────────────
CREATE TABLE fact_sales (
    sale_id         TEXT,           -- Unique transaction ID (TXN-00001)
    date            TEXT NOT NULL,  -- Sale date (YYYY-MM-DD)
    year            INTEGER,        -- Extracted year
    month           INTEGER,        -- Extracted month (1–12)
    quarter         TEXT,           -- Q1 / Q2 / Q3 / Q4
    drug_name       TEXT,           -- Drug brand name
    drug_class      TEXT,           -- ATC category
    region          TEXT,           -- Sales region
    channel         TEXT,           -- Hospital / Pharmacy
    rep_name        TEXT,           -- Sales representative name
    manager         TEXT,           -- Regional manager
    units_sold      REAL,           -- Units sold (may have nulls — raw data)
    unit_price      REAL,           -- Price per unit in INR
    revenue         REAL,           -- Total revenue (units × price)
    target_revenue  REAL            -- Monthly revenue target for rep
);

-- ── Indexes for faster query performance ─────────────────────
CREATE INDEX idx_region   ON fact_sales(region);
CREATE INDEX idx_drug     ON fact_sales(drug_name);
CREATE INDEX idx_class    ON fact_sales(drug_class);
CREATE INDEX idx_rep      ON fact_sales(rep_name);
CREATE INDEX idx_year     ON fact_sales(year);
CREATE INDEX idx_quarter  ON fact_sales(quarter);
CREATE INDEX idx_channel  ON fact_sales(channel);

-- ── Quick verification query ─────────────────────────────────
-- Run this after loading data to confirm row counts:
-- SELECT COUNT(*) AS total_rows FROM fact_sales;
-- SELECT year, COUNT(*) AS rows FROM fact_sales GROUP BY year ORDER BY year;
