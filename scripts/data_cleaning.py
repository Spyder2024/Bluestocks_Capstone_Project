""" 
data_cleaning.py
"""

import pandas as pd
import numpy as np
import os

# Project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)


# Task 1: Cleaning nav_history.csv
def clean_nav_history():
    """ 
    Clean NAV history: parse dates, sort, ffill, dedup, validate. 
    """
    print("=" * 60)
    print("Cleaning nav_history.csv")
    print("=" * 60)
    
    df = pd.read_csv(os.path.join(RAW_DATA_DIR, '02_nav_history.csv'))
    print(f" Raw Shape: {df.shape}")
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Parse data columns to datetime
    df['date'] = pd.to_datetime(df['date'], format = "mixed", dayfirst = True)
    
    # Ensure NAV is numeric
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    
    # Sort by amfi_code + date
    df = df.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
    
    # Remove exact duplicates (save code + same date)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['amfi_code', 'date'], keep='last')
    print(f" Duplicates removed: {before_dedup - len(df)}")
    
    # Forward-fill missing NAV for each scheme
    null_before = df['nav'].isnull().sum()
    df['nav'] = df.groupby('amfi_code')['nav'].ffill()  
    df['nav'] = df.groupby('amfi_code')['nav'].bfill()  # Backward fill if needed
    null_after = df['nav'].isnull().sum()
    print(f"Nulls before ffill: {null_before}")
    print(f"Nulls after ffill: {null_after}")  
    
    # Validate NAV > 0
    invalid_nav = (df['nav'] <= 0).sum()
    df = df[df['nav'] > 0].reset_index(drop=True)
    print(f"Invalid NAV entries removed: {invalid_nav}")
    
    # Compute Daily return percentage
    df['daily_return'] = df.groupby('amfi_code')['nav'].pct_change() * 100
    
    print(f" Cleaned Shape: {df.shape}")
    print(f" Date range: {df['date'].min()} to {df['date'].max()}")
    print(f" Unique schemes: {df['amfi_code'].nunique()}")
    
    output_path = os.path.join(PROCESSED_DATA_DIR, 'nav_history_cleaned.csv')
    df.to_csv(output_path, index=False)
    print(f" Cleaned data saved to: {output_path}\n")
    
    return df 


# Task 2: Cleaning investor_transactions.csv
def clean_investor_transactions():
    """ 
    Clean transactions: standardise types, validate amounts, fix dates, KYC.
    """
    print("=" * 60)
    print("Cleaning investor_transactions.csv")
    print("=" * 60)
    
    df = pd.read_csv(os.path.join(RAW_DATA_DIR, '08_investor_transactions.csv'))
    print(f" Raw Shape: {df.shape}")
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Parse transaction_date to datetime
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format = "mixed", dayfirst = True)
    
    # Standardize transaction types
    df['transaction_type'] = (df['transaction_type'].str.strip().str.title())
    
    # Map common variations to canonical values
    type_mapping = {
        'Sip': 'SIP',
        'Lumpsum': 'Lumpsum',
        'Redemption': 'Redemption',
        'Purchase': 'Lumpsum',
    }
    df['transaction_type'] = df['transaction_type'].map(type_mapping).fillna(df['transaction_type'])
    
    valid_types = {'SIP', 'Lumpsum', 'Redemption'}
    invalid_types = set(df['transaction_type'].unique()) - valid_types
    if invalid_types:
        print(f" Unexpected transaction types found: {invalid_types}")
    else:
        print(f"Transaction types: {sorted(valid_types)}")
        
    # Validate transaction_amount > 0
    df['amount_inr'] = pd.to_numeric(df['amount_inr'], errors='coerce')
    invalid_amounts = (df['amount_inr'] <= 0).sum()
    null_amounts = df['amount_inr'].isnull().sum()
    df = df[df['amount_inr'] > 0].reset_index(drop=True)
    print(f" Invalid transaction amounts removed: {invalid_amounts}")
    print(f" Null transaction amounts removed: {null_amounts}")
    
    # Standardize KYC status
    df['kyc_status'] = df['kyc_status'].str.strip().str.title()
    valid_kyc = {'Verified', 'Pending'}
    invalid_kyc = set(df['kyc_status'].dropna().unique()) - valid_kyc
    if invalid_kyc:
        print(f" Unexpected KYC statuses found: {invalid_kyc}")
    else:
        print(f"KYC statuses: {sorted(valid_kyc)}")
        
    # Standardise city_tier
    df['city_tier'] = df['city_tier'].str.strip().str.upper()
    print(f"City tiers: {sorted(df['city_tier'].dropna().unique())}")
    
    # Remove exact duplicates (same investor + same date + same amount)
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f" Duplicates removed: {before - len(df)}")
    
    print(f" Cleaned Shape: {df.shape}")
    print(f" Date range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
    print(f" Unique investors: {df['investor_id'].nunique()}")
    
    output_path = os.path.join(PROCESSED_DATA_DIR, 'investor_transactions_cleaned.csv')
    df.to_csv(output_path, index=False)
    print(f" Cleaned data saved to: {output_path}\n")
    
    return df


# Task 3: Cleaning scheme_performance.csv
def clean_scheme_performance():
    """ 
    Clean performance: numeric validation, flag anomalies, expense ratio check.
    """
    print("=" * 60)
    print("Cleaning scheme_performance.csv")
    print("=" * 60)
    
    df = pd.read_csv(os.path.join(RAW_DATA_DIR, '07_scheme_performance.csv'))
    print(f" Raw Shape: {df.shape}")
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Identify numeric return/risk columns
    numeric_cols = [
        'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 
        'benchmark_3yr_pct', 'alpha', 'beta',
        'sharpe_ratio', 'sortino_ratio', 
        'std_dev_ann_pct', 'max_drawdown_pct', 'expense_ratio_pct',
        'exit_load_pct', 'morningstar_rating'
    ]
    
    # only keep columns that exist in the dataframe
    numeric_cols = [col for col in numeric_cols if col in df.columns]
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # flag anomalies in return values
    return_cols = [c for c in numeric_cols if 'return' in c and c != 'morningstar_rating']
    anomalies = []
    for col in return_cols:
        nulls = df[col].isnull().sum()
        if nulls > 0:
            anomalies.append(f"{col}: {nulls} nulls")
            
        # flag unrealistic values
        unrealistic = ((df[col] > 200 | (df[col] < -90))).sum()
        if unrealistic > 0:
            anomalies.append(f"{col}: {unrealistic} unrealistic values")
            
    if anomalies:
        print("Anomalies flagged: ")
        for anomaly in anomalies:
            print(f"  - {anomaly}")
    else:
        print("No anomalies detected")
        
    # Validate expense_ratio_pct range
    if 'expense_ratio_pct' in df.columns:
        out_of_range = df[
            (df['expense_ratio_pct'].notna()) & 
            ((df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5))
        ]
        if len(out_of_range) > 0:
            print(f"Expense ratio out of expected range (0.1% - 2.5%): {len(out_of_range)} entries")
            for _, row in out_of_range.iterrows():
                print(f"  - Scheme: {row.get('amfi_code', '?')} -> {row['expense_ratio_pct']:.2f}%")
        else:
            print("All expense ratios within expected range (0.1% - 2.5%)")
            
    # flag negative sharpe ratios
    if 'sharpe_ratio' in df.columns:
        neg_sharpe = (df['sharpe_ratio'] < 0).sum()
        print(f"Negative Sharpe ratios: {neg_sharpe}")
        
    # remove exact duplicates (same scheme + same date)
    before = len(df)
    df = df.drop_duplicates(subset=['amfi_code'], keep='last').reset_index(drop=True)
    print(f" Duplicates removed: {before - len(df)}")
    
    print(f" Cleaned Shape: {df.shape}")
    
    output_path = os.path.join(PROCESSED_DATA_DIR, 'scheme_performance_cleaned.csv')
    df.to_csv(output_path, index=False)
    print(f" Cleaned data saved to: {output_path}\n")
    
    return df
    

# Light-clean all datasets for database loading
def light_clean_all(filename, output_path):
    """ 
    Minimal Clean
    """
    df = pd.read_csv(filename)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # auto parse
    for col in df.columns:
        if 'date' in col or 'month' in col:
            df[col] = pd.to_datetime(df[col], format='mixed', errors='coerce', dayfirst=True)
            
    output_path = os.path.join(PROCESSED_DATA_DIR, output_path)
    df.to_csv(output_path, index=False)
    print(f"Light cleaned data saved to: {output_path}\n")
    
    return df
    

# main execution
if __name__ == "__main__":
    print("DAY 2: DATA CLEANING")
    
    nav_df = clean_nav_history()
    tx_df = clean_investor_transactions()
    perf_df = clean_scheme_performance()
    
    print("=" * 60)
    print("Light cleaning all datasets for database loading")
    print("=" * 60)
    
    fund_master_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '01_fund_master.csv'),
        'fund_master_cleaned.csv'
    )
    aum_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '03_aum_by_fund_house.csv'),
        'aum_by_fund_house_cleaned.csv'
    )
    sip_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '04_monthly_sip_inflows.csv'),
        'monthly_sip_inflows_cleaned.csv'
    )
    cat_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '05_category_inflows.csv'),
        'category_inflows_cleaned.csv'
    )
    folio_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '06_industry_folio_count.csv'),
        'industry_folio_count_cleaned.csv'
    )
    portfolio_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '09_portfolio_holdings.csv'),
        'portfolio_holdings_cleaned.csv'
    )
    benchmark_df = light_clean_all(
        os.path.join(RAW_DATA_DIR, '10_benchmark_indices.csv'),
        'benchmark_indices_cleaned.csv'
    )
    
    print(f"\n{"=" * 60}")
    print("Data cleaning completed. All cleaned datasets saved to data/processed/")
    processed_files = os.listdir(PROCESSED_DATA_DIR)
    for f in sorted(processed_files):
        if f.endswith('.csv'):
            fpath = os.path.join(PROCESSED_DATA_DIR, f)
            rows = sum(1 for _ in open(fpath)) - 1
            print(f" - {f:<45} {rows:>7,} rows")
    print("=" * 60)
    
    