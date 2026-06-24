""" 
live_nav_fetch.py
Fetch live NAV data from mfapi.in for HDFC Top 100 + 5 key bluechip schemes. Save as raw CSVs.
"""

import requests
import pandas as pd
import json
import os
import time
import sys

# Path Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw')
os.makedirs(RAW_DATA_PATH, exist_ok=True)

# Scheme definitions
SCHEMES = {
    125497: "HDFC_Top_100_Direct",
    119551: "SBI_Bluechip_Direct",
    120503: "ICICI_Bluechip_Direct",
    118632: "Nippon_Large_Cap_Direct",
    119092: "Axis_Bluechip_Direct",
    120841: "Kotak_Bluechip_Direct",
}

BASE_URL = "https://api.mfapi.in/mf"

def fetch_nav(scheme_code, scheme_name):
    """ 
    Fetch historical NAV for a single scheme from mfapi.in 
    """
    url = f"{BASE_URL}/{scheme_code}"
    print(f"Fetching {scheme_name} (Code: {scheme_code}) ...", end="", flush=True)
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        meta = data.get("meta", {})
        nav_data = data.get("data", [])
        
        if not nav_data:
            print("No data returned.")
            return None
        
        records = []
        for row in nav_data:
            if isinstance(row, dict):
                date_val = row.get("date")
                nav_val = row.get("nav")
            elif isinstance(row, (list, tuple)) and len(row) >= 2:
                date_val, nav_val = row[0], row[1]
            else:
                continue
            
            if date_val and nav_val:
                records.append({"date": date_val, "nav": nav_val})
                
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"] = pd.to_numeric(df["nav"], errors='coerce')
        df = df.dropna(subset=["nav"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # Add Scheme info
        df["amfi_code"] = scheme_code
        df["scheme_name"] = meta.get("scheme_name", scheme_name)
        df["fund_house"] = meta.get("fund_house", "Unknown")
        
        df = df[["amfi_code", "scheme_name", "fund_house", "date", "nav"]]
        
        print(f" {len(df):,} rows | Latest NAV: {df['nav'].iloc[-1]:.4f} ({df['date'].iloc[-1].strftime('%Y-%m-%d')})")
        
        return df 
    
    except requests.exceptions.Timeout:
        print("Request timed out.")
        return None 
    except requests.exceptions.HTTPError as e:
        print(f"HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"{type(e).__name__}: {e}")
        return None
    

def main():
    print(" DAY 1: LIVE NAV FETCH")
    
    all_dfs = {}
    success_count = 0
    failure_count = 0
    
    for code, name in SCHEMES.items():
        df = fetch_nav(code, name)
        if df is not None:
            out_path = os.path.join(RAW_DATA_PATH, f"live_nav_{code}_{name}.csv")
            df.to_csv(out_path, index=False)
            all_dfs[name] = df
            success_count += 1
        else:
            failure_count += 1
        
        time.sleep(1)  # To avoid hitting API rate limits
        
    if all_dfs:
        combined = pd.concat(all_dfs.values(), ignore_index=True)
        combined_path = os.path.join(RAW_DATA_PATH, "live_nav_combined.csv")
        combined.to_csv(combined_path, index=False)
        print(f"\n Combined CSV saved: {combined.shape[0]:,} total rows")
        
    print(f"\n{'='*60}")
    print(f"Successful fetches: {success_count}")
    print(f"Failed fetches: {failure_count}")
    print(f"Output folder: {RAW_DATA_PATH}")
    print(f"\n{'='*60}")
    
    if failure_count > 0:
        print("Some fetches failed. Please check the logs above for details.")
        
    else:
        print("live_nav_fetch.py completed successfully. All NAVs fetched and saved.")
    

if __name__ == "__main__":
    main()