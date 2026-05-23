"""
segmentation.py
---------------
Step 4 — Behavioural customer segmentation.
Classifies every user into: Viewer Only, Cart Abandoner, Purchaser, Repeat Buyer.
Produces 3 charts saved to images/segmentation/.

Accepts:         cleaned pd.DataFrame  (loaded from CSV if not passed in)
Returns:         dict of segment KPIs
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    CLEAN_CSV, IMG_SEG, OUT_DIR,
    BLUE, RED, GREEN, ORANGE, PURPLE, TEAL,
    save,
)

SEG_COLORS = {
    'Viewer Only':    BLUE,
    'Cart Abandoner': ORANGE,
    'Purchaser':      GREEN,
    'Repeat Buyer':   PURPLE,
}


def run(df: pd.DataFrame = None) -> dict:
    if df is None:
        df = pd.read_csv(CLEAN_CSV, parse_dates=['event_time'])

    print('\n── Step 4: Customer Segmentation ────────────────────────────')

    purchases = df[df['event_type'] == 'purchase']

    # Build user-level segment labels
    user_seg = _build_segments(df, purchases)

    seg_counts = user_seg['segment'].value_counts()
    for seg, cnt in seg_counts.items():
        print(f'  {seg:<20}: {cnt:,} users ({cnt/len(user_seg)*100:.1f}%)')

    # Revenue by segment
    user_rev = purchases.groupby('user_id')['price'].sum().rename('revenue')
    seg_rev  = (user_seg.merge(user_rev, on='user_id', how='left')
                         .fillna(0)
                         .groupby('segment')['revenue']
                         .agg(['sum', 'mean'])
                         .reset_index())

    kpis = {}
    for seg in seg_counts.index:
        row = seg_rev[seg_rev['segment'] == seg]
        kpis[seg] = {
            'user_count':    int(seg_counts[seg]),
            'pct_of_users':  round(seg_counts[seg] / len(user_seg) * 100, 1),
            'total_revenue': round(float(row['sum'].values[0])  if len(row) else 0, 2),
            'avg_revenue':   round(float(row['mean'].values[0]) if len(row) else 0, 2),
        }

    with open(os.path.join(OUT_DIR, 'segment_kpis.json'), 'w') as f:
        json.dump(kpis, f, indent=2)
    user_seg.to_csv(os.path.join(OUT_DIR, 'user_segments.csv'), index=False)

    _segment_overview(user_seg, seg_counts, seg_rev)
    _behavior_heatmap(df, user_seg)
    _repeat_vs_onetimee(purchases)

    print('  Segmentation complete.')
    return kpis


# ── Segment builder ───────────────────────────────────────────────────────────

def _build_segments(df: pd.DataFrame, purchases: pd.DataFrame) -> pd.DataFrame:
    user_events = (df.groupby('user_id')['event_type']
                     .apply(set)
                     .reset_index()
                     .rename(columns={'event_type': 'event_set'}))

    def label(event_set):
        if 'purchase' in event_set:
            return 'Purchaser'
        if 'cart' in event_set:
            return 'Cart Abandoner'
        return 'Viewer Only'

    user_events['segment'] = user_events['event_set'].apply(label)

    # Upgrade single-purchasers who bought more than once to Repeat Buyer
    repeat_ids = purchases.groupby('user_id').size()
    repeat_ids = repeat_ids[repeat_ids > 1].index
    mask = user_events['user_id'].isin(repeat_ids) & (user_events['segment'] == 'Purchaser')
    user_events.loc[mask, 'segment'] = 'Repeat Buyer'

    return user_events.drop(columns=['event_set'])


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _segment_overview(user_seg, seg_counts, seg_rev):
    colors_list = [SEG_COLORS.get(s, '#999') for s in seg_counts.index]
    fig, axes   = plt.subplots(1, 2, figsize=(14, 6))

    # Pie: user count
    axes[0].pie(seg_counts.values, labels=seg_counts.index, colors=colors_list,
                autopct='%1.1f%%', startangle=90,
                wedgeprops=dict(edgecolor='white', linewidth=2.5))
    axes[0].set_title('User Segments\nWho Are Our Customers?', pad=15)

    # Bar: revenue
    rev_sorted = seg_rev.sort_values('sum', ascending=False)
    bar_colors = [SEG_COLORS.get(s, '#999') for s in rev_sorted['segment']]
    axes[1].bar(rev_sorted['segment'], rev_sorted['sum'], color=bar_colors, edgecolor='white')
    axes[1].set_title('Revenue by Segment\nWhere Does Revenue Come From?')
    axes[1].set_ylabel('Total Revenue (USD)')
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
    axes[1].tick_params(axis='x', rotation=20)
    for i, row in enumerate(rev_sorted.itertuples()):
        axes[1].text(i, row.sum + 500, f'${row.sum/1000:.1f}K',
                     ha='center', fontsize=9, fontweight='bold')

    save(fig, os.path.join(IMG_SEG, '01_customer_segments.png'))


def _behavior_heatmap(df, user_seg):
    merged    = df.merge(user_seg[['user_id', 'segment']], on='user_id', how='left')
    seg_hour  = merged.groupby(['segment', 'hour']).size().unstack(fill_value=0)
    seg_norm  = seg_hour.div(seg_hour.sum(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(seg_norm, cmap='Blues', ax=ax,
                linewidths=0.5, linecolor='white',
                cbar_kws={'label': 'Proportion of Segment Activity'})
    ax.set_title('Hourly Activity by Customer Segment\nWhen Does Each Segment Shop?')
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Segment')
    save(fig, os.path.join(IMG_SEG, '02_segment_behavior_heatmap.png'))


def _repeat_vs_onetimee(purchases):
    purch_count = purchases.groupby('user_id').size().rename('n_purchases')
    buyer_df    = purch_count.reset_index()
    buyer_df['type'] = buyer_df['n_purchases'].apply(
        lambda x: 'Repeat Buyer' if x > 1 else 'One-Time Buyer'
    )
    rev = purchases.groupby('user_id')['price'].sum().rename('revenue').reset_index()
    buyer_df = buyer_df.merge(rev, on='user_id', how='left')
    agg = buyer_df.groupby('type').agg(
        user_count=('user_id',  'count'),
        total_rev= ('revenue',  'sum'),
        avg_rev=   ('revenue',  'mean'),
    ).reset_index()

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    cols = [('user_count', 'Number of Users', '{:,.0f}'),
            ('total_rev',  'Total Revenue (USD)', '${:,.0f}'),
            ('avg_rev',    'Avg Revenue / User (USD)', '${:,.2f}')]
    for ax, (col, title, fmt) in zip(axes, cols):
        bar_colors = [GREEN if t == 'Repeat Buyer' else BLUE for t in agg['type']]
        bars = ax.bar(agg['type'], agg[col], color=bar_colors, edgecolor='white')
        ax.set_title(title)
        for bar, val in zip(bars, agg[col].values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.02,
                    fmt.format(val), ha='center', fontsize=9, fontweight='bold')
    fig.suptitle('Repeat vs One-Time Buyers\nBusiness Impact of Customer Retention',
                 fontsize=13, fontweight='bold')
    save(fig, os.path.join(IMG_SEG, '03_repeat_vs_onetimebyer.png'))


if __name__ == '__main__':
    run()
