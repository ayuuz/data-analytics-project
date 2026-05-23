"""
clean.py
--------
Step 1 — Load the raw events CSV, apply all cleaning steps, engineer
derived columns, and persist the cleaned dataset to outputs/.

Returns:         cleaned pd.DataFrame (used by run_all.py to pass forward)
"""

import json
import pandas as pd
from config import RAW_CSV, CLEAN_CSV, OUT_DIR


def run() -> pd.DataFrame:
    print('\n── Step 1: Data Cleaning ─────────────────────────────────────')

    # 1. Load
    df = pd.read_csv(RAW_CSV)
    print(f'  Raw rows     : {len(df):,}')

    # 2. Parse timestamps
    df['event_time'] = pd.to_datetime(df['event_time'], utc=True)

    # 3. Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f'  Duplicates   : {before - len(df):,} removed')

    # 4. Remove zero / negative prices
    df = df[df['price'] > 0]

    # 5. Fill missing text fields
    df['brand']         = df['brand'].fillna('Unknown')
    df['category_code'] = df['category_code'].fillna('Unknown')
    print(f'  Missing brand filled     : {(df["brand"] == "Unknown").sum():,}')
    print(f'  Missing category filled  : {(df["category_code"] == "Unknown").sum():,}')

    # 6. Derived time columns
    df['month']     = df['event_time'].dt.month
    df['day']       = df['event_time'].dt.day
    df['hour']      = df['event_time'].dt.hour
    df['weekday']   = df['event_time'].dt.day_name()
    df['date']      = df['event_time'].dt.date
    df['month_str'] = df['event_time'].dt.to_period('M').astype(str)

    # 7. Top-level category (e.g. "computers" from "computers.components.cpu")
    df['top_category'] = df['category_code'].apply(
        lambda x: x.split('.')[0] if x != 'Unknown' else 'Unknown'
    )

    print(f'  Clean rows   : {len(df):,}')
    print(f'  Date range   : {df["event_time"].min().date()} → {df["event_time"].max().date()}')
    print(f'  Unique users : {df["user_id"].nunique():,}')
    print(f'  Unique prods : {df["product_id"].nunique():,}')

    # 8. Persist
    df.to_csv(CLEAN_CSV, index=False)

    # 9. Save cleaning summary
    views     = df[df['event_type'] == 'view']
    carts     = df[df['event_type'] == 'cart']
    purchases = df[df['event_type'] == 'purchase']

    summary = {
        'raw_rows':               int(before),
        'clean_rows':             int(len(df)),
        'duplicates_removed':     int(before - len(df)),
        'missing_brand_filled':   int((df['brand'] == 'Unknown').sum()),
        'missing_category_filled':int((df['category_code'] == 'Unknown').sum()),
        'date_range_start':       str(df['event_time'].min().date()),
        'date_range_end':         str(df['event_time'].max().date()),
        'unique_users':           int(df['user_id'].nunique()),
        'unique_products':        int(df['product_id'].nunique()),
        'total_views':            int(len(views)),
        'total_carts':            int(len(carts)),
        'total_purchases':        int(len(purchases)),
    }
    with open(f'{OUT_DIR}/cleaning_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print('  Saved → outputs/events_cleaned.csv')
    return df


if __name__ == '__main__':
    run()
