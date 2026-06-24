""" 
data_ingestion.py
Day 1 Task
"""

import pandas as pd
import os
import sys

# Path Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw')
PROCESSED_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed')

os.makedirs(RAW_DATA_PATH, exist_ok=True)

# Dataset registry 
DATASETS = {
    "01_fund_master.csv": "fund_master",
    "02_nav_history.csv": "nav_history",
    "03_aum_by_fund_house.csv": "aum_fund_house",
    "04_monthly_sip_inflows.csv": "monthly_sip",
    "05_category_inflows.csv": "category_inflows",
    "06_industry_folio_count.csv": "industry_folio",
    "07_scheme_performance.csv": "scheme_performance",
    "08_investor_transactions.csv": "investor_transactions",
    "09_portfolio_holdings.csv": "portfolio_holdings",
    "10_benchmark_indices.csv": "benchmark_indices",
}

# Load all 10 CSV files
def load_and_profile_all():
    """ 
    Load every CSV, print shape/dtypes/head, store in a dictionary
    """
    data = {}
    anomalies = []
    
    for filename, var_name in DATASETS.items():
        filepath = os.path.join(RAW_DATA_PATH, filename)
        
        if not os.path.exists(filepath):
            print(f"MISSING: {filename}")
            anomalies.append(f"{filename} not found in data/raw/")
            continue
        
        try:
            df = pd.read_csv(filepath)
            data[var_name] = df
            
            print(f"\n{'='*60}")
            print(f"{filename} -> var: {var_name}")
            print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
            print(f"Dtypes:\n{df.dtypes.to_string()}")
            print(f"Head:\n{df.head(3).to_string()}")
            
            # Auto detect anomalies: missing values, duplicates, etc.
            null_pct = (df.isnull().sum() / len(df) * 100)
            high_null_cols = null_pct[null_pct > 10].index.tolist()
            if high_null_cols:
                anomalies.append(f"{filename} has columns with >10% nulls: {high_null_cols}")
                
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                anomalies.append(f"{filename} has {dup_count} duplicate rows")
                
        except Exception as e:
            anomalies.append(f"Error loading {filename}: {str(e)}")
            print(f"Error loading {filename}: {str(e)}")
    
    return data, anomalies

# Explore fund_master dataset
def explore_fund_master(df):
    """ 
    Print unique values for key categorical columns.
    """
    print(f"\n{'='*60}")
    print("FUND MASTER DATASET EXPLORATION")
    print(f"\n{'='*60}")
    
    print(f"\n Unique Fund Houses: {df['fund_house'].nunique()}:")
    for fh in sorted(df['fund_house'].unique()):
        print(f" - {fh}")
        
    print(f"\n Unique Categories: {df['category'].nunique()}:")
    for cat in sorted(df['category'].unique()):
        print(f" - {cat}")
    
    if 'sub_category' in df.columns:
        print(f"\n Unique Sub-Categories: {df['sub_category'].nunique()}:")
        for sub_cat in sorted(df['sub_category'].dropna().unique()):
            print(f" - {sub_cat}")
            
    if 'risk_category' in df.columns:
        print(f"\n Unique Risk Categories: {df['risk_category'].nunique()}:")
        for risk_cat in sorted(df['risk_category'].dropna().unique()):
            print(f" - {risk_cat}")
            
    if 'plan' in df.columns:
        print(f"\n Plan Distribution:")
        print(df['plan'].value_counts().to_string())
        
    return


# Validate AMFI Codes
def validate_amfi_codes(fund_master, nav_history):
    """ 
    Check every code in fund_master exists in nav_history.
    """
    print(f"\n{'='*60}")
    print("AMFI CODE VALIDATION")
    print(f"\n{'='*60}")
    
    master_codes = set(fund_master['amfi_code'].unique())
    nav_codes = set(nav_history['amfi_code'].unique())
    
    in_master_not_nav = master_codes - nav_codes
    in_nav_not_master = nav_codes - master_codes
    
    print(f"\n Fund Master unique AMFI codes: {len(master_codes)}")
    print(f" NAV history unique AMFI codes: {len(nav_codes)}")
    print(f" Common AMFI codes: {len(master_codes & nav_codes)}")
    
    if in_master_not_nav:
        print(f"\n Codes in fund_master but not in nav_history: {len(in_master_not_nav)}")
        for code in sorted(in_master_not_nav):
            name = fund_master[fund_master['amfi_code'] == code]['scheme_name'].values
            name_str = name[0] if len(name) > 0 else "Unknown"
            print(f" - {code}: {name_str}")
    else:
        print("\n All fund_master AMFI codes are present in nav_history.")
        
    if in_nav_not_master:
        print(f"\n Codes in nav_history but not in fund_master: {len(in_nav_not_master)}")
        for code in sorted(in_nav_not_master):
            print(f" - {code}")
    else:
        print("\n All nav_history AMFI codes are present in fund_master.")
        
    all_valid = (len(in_master_not_nav) == 0) and (len(in_nav_not_master) == 0)
    
    return all_valid 

# Data Quality Summary
def print_quality_summary(anomalies, validation_passed):
    """ 
    Print final data quality summary.
    """
    print(f"\n{'='*60}")
    print("DATA QUALITY SUMMARY")
    print(f"\n{'='*60}")
    
    if not anomalies:
        print("No anomalies detected in datasets.")
    else:
        print(f"{len(anomalies)} anomaly(ies) detected:")
        for a in anomalies:
            print(f" - {a}")
            
    print(f"\n AMFI Code Validation: {'PASSED' if validation_passed else 'FAILED'}")
    
    status = 'CLEAN - ready for analysis' if (not anomalies and validation_passed) else 'ISSUES DETECTED - review above'
    
    print(f"\n Overall Data Quality Status: {status}")
    print(f"\n{'='*60}")
    
    
# Main Execution
if __name__ == "__main__":
    
    print("DAY 1: DATA INGESTION AND QUALITY CHECKS")
    print("Bluestocks Fintech MF Analytics Capstone Project")
    
    data, anomalies = load_and_profile_all()
    
    if 'fund_master' in data:
        explore_fund_master(data['fund_master'])
        
    validation_passed = False
    if 'fund_master' in data and 'nav_history' in data:
        validation_passed = validate_amfi_codes(data['fund_master'], data['nav_history'])
    else:
        anomalies.append("Cannot validate AMFI codes: fund_master or nav_history dataset missing.")
    
    print_quality_summary(anomalies, validation_passed)
    
    print("data_ingestion.py execution completed.\n")
    