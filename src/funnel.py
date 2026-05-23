"""
funnel.py
---------
Step 3 — Purchase funnel analysis.
Calculates conversion rates and produces 3 charts saved to images/funnel/.

Accepts:         cleaned pd.DataFrame  (loaded from CSV if not passed in)
Returns:         dict of funnel KPIs
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt

from config import CLEAN_CSV, IMG_FUN, OUT_DIR, BLUE, RED, GREEN, ORANGE, save


def run(df=None) -> dict:
    if df is None:
        import pandas as pd
        df = pd.read_csv(CLEAN_CSV, parse_dates=['event_time'])

    print('\n── Step 3: Funnel Analysis ───────────────────────────────────')

    views     = df[df['event_type'] == 'view']
    carts     = df[df['event_type'] == 'cart']
    purchases = df[df['event_type'] == 'purchase']

    n_views     = len(views)
    n_carts     = len(carts)
    n_purchases = len(purchases)

    # Event-level rates
    v2c_pct  = n_carts     / n_views     * 100
    c2p_pct  = n_purchases / n_carts     * 100
    v2p_pct  = n_purchases / n_views     * 100
    abandon  = 100 - c2p_pct

    # User-level rates
    view_users  = set(views['user_id'])
    cart_users  = set(carts['user_id']) & view_users
    purch_users = set(purchases['user_id']) & view_users
    u_v2c  = len(cart_users)  / len(view_users) * 100
    u_v2p  = len(purch_users) / len(view_users) * 100

    print(f'  Views:                  {n_views:,}')
    print(f'  Carts:                  {n_carts:,}')
    print(f'  Purchases:              {n_purchases:,}')
    print(f'  View → Cart rate:       {v2c_pct:.2f}%')
    print(f'  Cart → Purchase rate:   {c2p_pct:.2f}%')
    print(f'  Overall conversion:     {v2p_pct:.2f}%')
    print(f'  Cart abandonment rate:  {abandon:.1f}%')

    kpis = {
        'total_views':             int(n_views),
        'total_carts':             int(n_carts),
        'total_purchases':         int(n_purchases),
        'view_to_cart_pct':        round(v2c_pct,  2),
        'cart_to_purchase_pct':    round(c2p_pct,  2),
        'overall_conversion_pct':  round(v2p_pct,  2),
        'user_view_to_cart_pct':   round(u_v2c,    2),
        'user_overall_conv_pct':   round(u_v2p,    2),
        'cart_abandonment_rate':   round(abandon,   2),
    }
    with open(os.path.join(OUT_DIR, 'funnel_kpis.json'), 'w') as f:
        json.dump(kpis, f, indent=2)

    _funnel_chart(n_views, n_carts, n_purchases, v2c_pct, c2p_pct, v2p_pct)
    _monthly_conversion(df)
    _dropoff_chart(n_views, n_carts, n_purchases)

    print('  Funnel analysis complete.')
    return kpis


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _funnel_chart(n_views, n_carts, n_purchases, v2c, c2p, v2p):
    stages = ['View', 'Add to Cart', 'Purchase']
    counts = [n_views, n_carts, n_purchases]
    colors = [BLUE, ORANGE, GREEN]
    max_w  = 0.85

    fig, ax = plt.subplots(figsize=(10, 7))
    for i, (stage, count, color) in enumerate(zip(stages, counts, colors)):
        width = max_w * (count / n_views)
        rect  = plt.Rectangle(
            (0.5 - width/2, 2 - i - 0.4), width, 0.7,
            facecolor=color, edgecolor='white', linewidth=2, alpha=0.9
        )
        ax.add_patch(rect)
        ax.text(0.5, 2-i, f'{stage}\n{count:,}',
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        if i > 0:
            pct = counts[i] / counts[i-1] * 100
            ax.text(0.5 + max_w/2 + 0.03, 2-i + 0.1, f'{pct:.1f}%',
                    fontsize=10, color=color, fontweight='bold')
            ax.text(0.5 + max_w/2 + 0.03, 2-i - 0.1, 'conversion', fontsize=8, color='#888')

    ax.set_xlim(0, 1.2); ax.set_ylim(-0.5, 3); ax.axis('off')
    ax.set_title('Customer Purchase Funnel', fontsize=15, fontweight='bold', pad=20)
    fig.text(0.5, 0.02,
        f'Biggest drop-off: View → Cart ({v2c:.1f}%). '
        f'Cart abandonment: {100-c2p:.1f}%. '
        f'Overall conversion: {v2p:.2f}%.',
        ha='center', fontsize=9, style='italic', color='#555')
    save(fig, os.path.join(IMG_FUN, '01_conversion_funnel.png'))


def _monthly_conversion(df):
    mf = df.groupby(['month_str', 'event_type']).size().unstack(fill_value=0)
    mf['v2c']     = mf.get('cart',     0) / mf.get('view', 1) * 100
    mf['c2p']     = mf.get('purchase', 0) / mf.get('cart', 1) * 100
    mf['overall'] = mf.get('purchase', 0) / mf.get('view', 1) * 100

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (col, title, color) in zip(axes, [
        ('v2c',     'View→Cart Rate (%)',        BLUE),
        ('c2p',     'Cart→Purchase Rate (%)',    ORANGE),
        ('overall', 'Overall Conversion (%)',    GREEN),
    ]):
        ax.plot(mf.index, mf[col], marker='o', color=color, linewidth=2.5, markersize=8)
        ax.fill_between(range(len(mf)), mf[col], alpha=0.12, color=color)
        ax.set_title(title)
        ax.set_ylabel('%')
        ax.tick_params(axis='x', rotation=35)
        ax.set_xticks(range(len(mf)))
        ax.set_xticklabels(mf.index)
    fig.suptitle('Conversion Rates Over Time', fontsize=14, fontweight='bold', y=1.02)
    save(fig, os.path.join(IMG_FUN, '02_monthly_conversion_rates.png'))


def _dropoff_chart(n_views, n_carts, n_purchases):
    cart_no_buy  = n_carts - n_purchases
    view_no_act  = n_views - n_carts - n_purchases
    labels = ['Viewed Only', 'Added to Cart', 'Purchased', 'Dropped at Cart']
    vals   = [view_no_act, n_carts, n_purchases, cart_no_buy]
    colors = [BLUE, ORANGE, GREEN, RED]

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (lbl, val, color) in enumerate(zip(labels, vals, colors)):
        hatch = '//' if lbl == 'Dropped at Cart' else None
        ax.bar(lbl, val, color=color, edgecolor='white', linewidth=1.5, hatch=hatch)
        ax.text(i, val + 2000, f'{val:,}', ha='center', fontsize=9, fontweight='bold')
    ax.set_title('Customer Drop-Off Analysis\nWhere Are We Losing Customers?')
    ax.set_ylabel('Number of Events')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    save(fig, os.path.join(IMG_FUN, '03_dropoff_analysis.png'))


if __name__ == '__main__':
    run()
