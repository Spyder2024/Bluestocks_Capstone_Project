""" 
load_to_sqlite.py
Execute schema.sql and load all 10 cleaned CSV files into a SQLite database.
"""

import pandas as pd
import sqlite3
import os

# Project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
SQL_DIR = os.path.join(PROJECT_ROOT, "sql")
DB_DIR = os.path.join(PROJECT_ROOT, "data", "db")
DB_PATH = os.path.join(DB_DIR, "bluestocks_mf.db")

os.makedirs(DB_DIR, exist_ok=True)

# create schema
def create_schema(conn):
    """ 
    Execute schema.sql to create the databse tables.
    """
    schema_path = os.path.join(SQL_DIR, "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    print("Database schema created successfully.")
    
def generate_dim_date(conn, nav_df):
    """ 
    Generate dim_date from the full date range ini nav_history. 
    """
    min_date = nav_df['date'].min()
    max_date = nav_df['date'].max()
    dates = pd.date_range(min_date, max_date, freq='D')
    
    dim = pd.DataFrame({'date': dates})
    dim['date_id'] = dim['date'].dt.strftime('%Y%m%d').astype(int)
    dim['year'] = dim['date'].dt.year
    dim['month'] = dim['date'].dt.month
    dim['month_name'] = dim['date'].dt.strftime('%B')
    dim['quarter'] = dim['date'].dt.quarter
    dim['day_of_week'] = dim['date'].dt.dayofweek
    dim['is_weekday'] = (dim['day_of_week'] < 5).astype(int)
    
    nav_month_ends = (
        nav_df.groupby(nav_df['date'].dt.to_period('M'))['date'].max().dt.normalize()
    )
    dim['is_month_end'] = dim['date'].isin(nav_month_ends).astype(int)
    
    dim.to_sql('dim_date', conn, if_exists='replace', index=False)
    print(f"dim_date: {len(dim):,} rows ({min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}).")
    
    
def load_table(conn, csv_name, table_name, if_exists='replace'):
    """ 
    Load a cleaned CSV into a SQLite table.
    """
    filepath = os.path.join(PROCESSED_DATA_DIR, csv_name)
    df = pd.read_csv(filepath)
    
    # parse date columns back to avoid SQLite string issues
    for col in df.columns:
        if 'date' in col or 'month' in col or 'launch' in col:
            df[col] = pd.to_datetime(df[col], format='mixed', dayfirst=True, errors='coerce')
            
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    
    return len(df)

def verify_counts(conn, expected):
    """ 
    Verify SQLite row counts match expected CSV row counts.
    """
    print(f"\n {'Table':<30}{'Expected':>10} {'Actual':>10} {'Match':>8}")
    print("-" * 60)
    
    all_match = True
    for table, exp_count in expected.items():
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        actual = cur.fetchone()[0]
        match = "Yes" if actual == exp_count else "No"
        if actual != exp_count:
            all_match = False
        print(f" {table:<30} {exp_count:>10,} {actual:>10,} {match:>8}")
        
    return all_match


def main():
    print(" DAY 2: LOAD TO SQLITE")
    
    # remove old db if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old database: {DB_PATH}\n")
        
    conn = sqlite3.connect(DB_PATH)
    
    # Create Schema
    print("="*60)
    print("Creating database schema...")
    print("="*60)
    create_schema(conn)
    
    # Generate dim_date from nav_history
    print("="*60)
    print("Generating dim_date from nav_history...")
    print("="*60)
    nav_df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "nav_history_cleaned.csv"))
    nav_df['date'] = pd.to_datetime(nav_df['date'], format='mixed', dayfirst=True)
    generate_dim_date(conn, nav_df)
    
    # load all fact/dim tables
    print("\n" + "="*60)
    print("Loading cleaned CSV files into SQLite...")
    print("="*60)
    
    expected = {}
    
    # dim_fund
    expected['dim_fund'] = load_table(conn, "fund_master_cleaned.csv", "dim_fund")
    print(f"dim_fund: {expected['dim_fund']:,} rows loaded.")
    
    # fact_nav
    expected['fact_nav'] = load_table(conn, "nav_history_cleaned.csv", "fact_nav")
    print(f"fact_nav: {expected['fact_nav']:,} rows loaded.")
    
    # fact_transactions
    expected['fact_transactions'] = load_table(conn, "investor_transactions_cleaned.csv", "fact_transactions")
    print(f"fact_transactions: {expected['fact_transactions']:,} rows loaded.")
    
    # fact_performance
    expected['fact_performance'] = load_table(conn, "scheme_performance_cleaned.csv", "fact_performance")
    print(f"fact_performance: {expected['fact_performance']:,} rows loaded.")
    
    # fact_aum
    expected['fact_aum'] = load_table(conn, "aum_by_fund_house_cleaned.csv", "fact_aum")
    print(f"fact_aum: {expected['fact_aum']:,} rows loaded.")
    
    # fact_sip_industry
    expected['fact_sip_industry'] = load_table(conn, "monthly_sip_inflows_cleaned.csv", "fact_sip_industry")
    print(f"fact_sip_industry: {expected['fact_sip_industry']:,} rows loaded.")
    
    # fact_portfolio
    expected['fact_portfolio'] = load_table(conn, "portfolio_holdings_cleaned.csv", "fact_portfolio")
    print(f"fact_portfolio: {expected['fact_portfolio']:,} rows loaded.")
    
    # verify row counts
    print("\n" + "="*60)
    print("Verifying row counts...")
    print("="*60)
    all_match = verify_counts(conn, expected)
    
    conn.close()
    print(f"\n Database created successfully: {DB_PATH}")
    if all_match:
        print(f" All row counds match. Database is consistent.")
    else:
        print(f" Row counts do not match. Please check the logs above for details.")
        
        
if __name__ == "__main__":
    main()