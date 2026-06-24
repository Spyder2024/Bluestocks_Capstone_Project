-- ===================================================================
-- queries.sql
-- Analyrtical SQL Queries
-- ===================================================================

-- Query 1: Top 5 Funds by AUM (latest quarter)
SELECT 
    fund_house,
    date,
    aum_crore,
    num_schemes
FROM fact_aum
WHERE date = (SELECT MAX(date) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;

-- Query 2: Average NAV per Month (last 12 months)
SELECT
    strftime('%Y-%m', fn.date) AS month,
    df.fund_house,
    ROUND(AVG(fn.nav), 2) AS avg_nav,
FROM fact_nav fn
JOIN dim_fund df ON fn.amfi_code = df.amfi_code
WHERE fn.date >= DATE((SELECT MAX(date) FROM fact_nav), '-12 months')
GROUP BY strftime('%Y-%m', fn.date), df.fund_house
GROUP BY month DESC, avg_nav DESC
LIMIT 20;

-- Query 3: SIP Inflow YoY Growth
SELECT 
    strftime('%Y', month) AS year,
    ROUND(SUM(sip_inflow_crore), 2) AS total_sip_inflow_crore,
    ROUND(AVG(active_sip_accounts_crore), 2) AS avg_active_accounts_crore,
    ROUND(AVG(yoy_growth_pct), 2) AS avg_yoy_growth_pct
FROM fact_sip_industry
GROUP BY strftime('%Y', month)
GROUP BY year;

-- Query 4: Transactions by State
SELECT
    state;
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_inr) / 10000000, 2) AS total_amount_cr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_amount
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
GROUP BY state
GROUP BY total_amount_cr DESC;

-- Query 5: Fund with Expense Ratio < 1% 
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    ROUND(expense_ratio_pct, 2) AS expense_ratio_pct,
    risk_category
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- Query 6: Top 10 Funds by 3-year Return
SELECT
    fp.amfi_code,
    df.scheme_name,
    df.fund_house,
    df.category,
    ROUND(fp.return_3yr_pct, 2) AS return_3yr_pct,
    ROUND(fp.sharpe_ratio, 2) AS sharpe_ratio,
    ROUND(fp.max_drawdown_pct, 2) AS max_drawdown_pct,
    fp.morningstar_rating
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
WHERE fp.return_3yr_pct IS NOT NULL
ORDER BY fp.return_3yr_pct DESC
LIMIT 10;

-- Query 7: Monthly Transaction Volume by Type
SELECT
    strftime('%Y-%m', transaction_date) AS month,
    transaction_type,
    COUNT(*) AS tx_count,
    ROUND(SUM(amount_inr) / 10000000, 2) AS total_amount_cr
FROM fact_transactions
GROUP BY strftime('%Y-%m', transaction_date), transaction_type
ORDER BY month DESC, transaction_type;

-- Query 8: Fund Category Distribution
SELECT 
    category,
    sub_category,
    COUNT(*) AS num_schemes,
    ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio,
    ROUND(AVG(
        SELECT fp.return_3yr_pct FROM fact_performance fp
        WHERE fp.amfi_code = dim_fund.amfi_code
    ), 2) AS avg_3yr_return_pct
FROM dim_fund
GROUP BY category, sub_category
ORDER BY category, num_schemes DESC;

-- Query 9: T30 vs B30 City Comparison
SELECT
    city_tier,
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT investor_id) AS unique_investors,
    ROUND(SUM(amount_inr) / 10000000, 2) AS total_amount_cr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_amount
    ROUND(SUM(CASE WHEN transaction_type = 'SIP' THEN amount_inr ELSE 0 END) / 10000000, 2) AS sip_amount_cr,
    ROUND(SUM(CASE WHEN transaction_type = 'Lumpsum' THEN amount_inr ELSE 0 END) / 10000000, 2) AS lumpsum_amount_cr
FROM fact_transactions
GROUP BY city_tier;

-- Query 10: Risk-Return Scatter Data (for Chart)
SELECT
    fp.amfi_code,
    df.scheme_name,
    df.fund_house,
    df.category,
    df.risk_category,
    ROUND(fp.return_3yr_pct, 2) AS return_3yr_pct,
    ROUND(fp.std_dev_ann_pct, 2) AS risk_std_dev,
    ROUND(fp.sharpe_ratio, 2) AS sharpe_ratio,
    ROUND(fp.alpha, 2) AS alpha,
    ROUND(fp.beta, 2) AS beta
FROM fact_performance fp
JOIN dim_fund df ON fp.amfi_code = df.amfi_code
WHERE fp.return_3yr_pct IS NOT NULL AND fp.std_dev_ann_pct IS NOT NULL
ORDER BY fp.sharpe_ratio DESC;
