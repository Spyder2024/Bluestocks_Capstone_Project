# Data Dictionary — Bluestock MF Analytics Platform

**Project:** Bluestock Fintech Mutual Fund Analytics Capstone  
**Database:** bluestock_mf.db (SQLite)  
**Last Updated:** Day 2  

---

## Dimension Tables

### dim_fund
Master reference table for all 40 mutual fund schemes.

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| amfi_code | TEXT (PK) | AMFI unique scheme code (e.g., 125497) | 01_fund_master.csv |
| fund_house | TEXT | AMC name (e.g., SBI Mutual Fund) | 01_fund_master.csv |
| scheme_name | TEXT | Full official AMFI scheme name | 01_fund_master.csv |
| category | TEXT | Equity / Debt / Hybrid | 01_fund_master.csv |
| sub_category | TEXT | Large Cap / Mid Cap / Small Cap / Liquid etc. | 01_fund_master.csv |
| plan | TEXT | Regular or Direct | 01_fund_master.csv |
| launch_date | DATE | Fund launch date (YYYY-MM-DD) | 01_fund_master.csv |
| benchmark | TEXT | Official benchmark index name | 01_fund_master.csv |
| expense_ratio_pct | REAL | Annual expense ratio in % (range: 0.1–2.5) | 01_fund_master.csv |
| exit_load_pct | REAL | Exit load % (0 for Liquid/Index funds) | 01_fund_master.csv |
| fund_manager | TEXT | Primary fund manager name | 01_fund_master.csv |
| risk_category | TEXT | SEBI risk: Low / Moderate / High / Very High | 01_fund_master.csv |
| sebi_category_code | TEXT | SEBI internal code (e.g., EC01=LargeCap) | 01_fund_master.csv |

### dim_date
Calendar dimension spanning the full NAV date range.

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| date_id | INTEGER (PK) | YYYYMMDD format (e.g., 20250610) | Generated |
| date | DATE | Full date | Generated from nav_history range |
| year | INTEGER | Year (e.g., 2025) | Generated |
| month | INTEGER | Month number (1–12) | Generated |
| month_name | TEXT | Month name (e.g., January) | Generated |
| quarter | INTEGER | Quarter (1–4) | Generated |
| day_of_week | INTEGER | Day of week (0=Monday, 6=Sunday) | Generated |
| is_weekday | INTEGER | 1 if Mon–Fri, 0 if Sat–Sun | Generated |
| is_month_end | INTEGER | 1 if last business day of month | Generated from nav data |

---

## Fact Tables

### fact_nav
Daily NAV for all 40 schemes (~46,000 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| id | INTEGER (PK) | Auto-increment row ID | System |
| amfi_code | TEXT (FK) | FK to dim_fund | 02_nav_history.csv |
| date | DATE | NAV date (business days) | 02_nav_history.csv |
| nav | REAL | NAV in ₹ (e.g., 892.4560) | 02_nav_history.csv |
| daily_return_pct | REAL | Daily % change from previous NAV | Computed: (nav_t / nav_t-1 - 1) × 100 |

*Cleaning applied:* Duplicates removed, holidays forward-filled, NAV > 0 validated.

### fact_transactions
Simulated investor transactions (~32,000 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| tx_id | INTEGER (PK) | Auto-increment transaction ID | System |
| investor_id | TEXT | Unique investor (INV000001–INV005000) | 08_investor_transactions.csv |
| amfi_code | TEXT (FK) | FK to dim_fund | 08_investor_transactions.csv |
| transaction_date | DATE | Date of transaction | 08_investor_transactions.csv |
| transaction_type | TEXT | SIP / Lumpsum / Redemption | 08_investor_transactions.csv (standardised) |
| amount_inr | REAL | Transaction amount in ₹ (validated > 0) | 08_investor_transactions.csv |
| state | TEXT | Investor's state (12 states covered) | 08_investor_transactions.csv |
| city | TEXT | Investor's city | 08_investor_transactions.csv |
| city_tier | TEXT | T30 (Top 30) or B30 (Beyond Top 30) | 08_investor_transactions.csv |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ | 08_investor_transactions.csv |
| gender | TEXT | Male / Female | 08_investor_transactions.csv |
| annual_income_lakh | REAL | Annual income in ₹ lakh | 08_investor_transactions.csv |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque | 08_investor_transactions.csv |
| kyc_status | TEXT | Verified (92%) / Pending (8%) | 08_investor_transactions.csv (standardised) |

*Cleaning applied:* transaction_type standardised, amount > 0, KYC enum validated, date formats fixed.

### fact_performance
Risk-return metrics per scheme (40 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| id | INTEGER (PK) | Auto-increment | System |
| amfi_code | TEXT (FK) | FK to dim_fund | 07_scheme_performance.csv |
| as_of_date | DATE | Date metrics computed | 07_scheme_performance.csv |
| return_1yr_pct | REAL | 1-year absolute return % | 07_scheme_performance.csv |
| return_3yr_pct | REAL | 3-year CAGR % | 07_scheme_performance.csv |
| return_5yr_pct | REAL | 5-year CAGR % | 07_scheme_performance.csv |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR % | 07_scheme_performance.csv |
| alpha | REAL | Excess return vs benchmark (3yr) | 07_scheme_performance.csv |
| beta | REAL | Market sensitivity (1.0 = market) | 07_scheme_performance.csv |
| sharpe_ratio | REAL | Risk-adjusted return (>1 is good) | 07_scheme_performance.csv |
| sortino_ratio | REAL | Downside-risk-adjusted return | 07_scheme_performance.csv |
| std_dev_ann_pct | REAL | Annualised standard deviation % | 07_scheme_performance.csv |
| max_drawdown_pct | REAL | Worst peak-to-trough decline % | 07_scheme_performance.csv |
| morningstar_rating | INTEGER | 1–5 star rating (simulated) | 07_scheme_performance.csv |

*Cleaning applied:* Numeric validation, expense ratio range check (0.1–2.5%), negative Sharpe flagged.

### fact_aum
Quarterly AUM by fund house (~90 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| id | INTEGER (PK) | Auto-increment | System |
| fund_house | TEXT | AMC name | 03_aum_by_fund_house.csv |
| date | DATE | Quarter-end date | 03_aum_by_fund_house.csv |
| aum_crore | REAL | AUM in ₹ crore | 03_aum_by_fund_house.csv |
| num_schemes | INTEGER | Number of schemes under that AMC | 03_aum_by_fund_house.csv |

### fact_sip_industry
Monthly SIP industry data (48 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| id | INTEGER (PK) | Auto-increment | System |
| month | DATE | Month (YYYY-MM-DD, first day) | 04_monthly_sip_inflows.csv |
| sip_inflow_crore | REAL | Total SIP inflows in ₹ crore | 04_monthly_sip_inflows.csv |
| active_sip_accounts_crore | REAL | Active SIP accounts in crore | 04_monthly_sip_inflows.csv |
| new_sip_accounts_lakh | REAL | New SIP registrations (lakh) | 04_monthly_sip_inflows.csv |
| sip_aum_lakh_crore | REAL | SIP AUM in ₹ lakh crore | 04_monthly_sip_inflows.csv |
| yoy_growth_pct | REAL | YoY growth % in SIP inflows | 04_monthly_sip_inflows.csv |

### fact_portfolio
Top equity holdings per fund (~320 rows).

| Column | Data Type | Description | Source |
| :--- | :--- | :--- | :--- |
| id | INTEGER (PK) | Auto-increment | System |
| amfi_code | TEXT (FK) | FK to dim_fund | 09_portfolio_holdings.csv |
| stock_symbol | TEXT | Stock ticker (e.g., RELIANCE) | 09_portfolio_holdings.csv |
| weight_pct | REAL | Holding weight % | 09_portfolio_holdings.csv |
| sector | TEXT | Sector name (e.g., Banking) | 09_portfolio_holdings.csv |
| date | DATE | As-of date for holdings | 09_portfolio_holdings.csv |

---

## Computed Fields Reference

| Field | Formula | Used In |
| :--- | :--- | :--- |
| **daily_return_pct** | (nav_t / nav_t-1 - 1) × 100 | fact_nav |
| **CAGR** | (NAV_end / NAV_start)^(1/n) - 1 | Day 4 computation |
| **Sharpe Ratio** | (Rp - Rf) / Std(Rp) × √252 where Rf = 6.5% | Day 4 computation |
| **Sortino Ratio** | (Rp - Rf) / Downside_Std × √252 | Day 4 computation |
| **Alpha** | OLS intercept × 252 (vs Nifty 100) | Day 4 computation |
| **Beta** | OLS slope (fund returns vs Nifty 100) | Day 4 computation |
| **Max Drawdown** | min(NAV / cummax(NAV) - 1) | Day 4 computation |
| **HHI** | Σ(weight_i²) for sector weights | Day 6 computation |

---

## Data Sources

| Source | URL | Data Type | Frequency |
| :--- | :--- | :--- | :--- |
| **AMFI India** | amfiindia.com | NAV, AUM, Folio, SIP | Daily / Monthly |
| **mfapi.in** | api.mfapi.in/mf/{code} | Historical NAV (JSON) | Daily |
| **NSE India** | nseindia.com/reports | Benchmark Index Prices | Daily |
| **BSE India** | bseindia.com | BSE SmallCap Index | Daily |

> *All data is sourced from publicly available AMFI India data and open APIs. This project is for educational purposes only and does not constitute financial advice.*
