"""
dashboard.py
------------
Step 5 — Management dashboards.
Produces 2 multi-panel dashboard images saved to images/dashboard/.

Accepts:         cleaned pd.DataFrame  (loaded from CSV if not passed in)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

from config import (
    CLEAN_CSV, IMG_DASH,
    BLUE, RED, GREEN, ORANGE, PURPLE, TEAL, LIGHT_BG,
    save,
)

WEEKDAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
SEG_COLORS = {
    'Viewer Only':    BLUE,
    'Cart Abandoner': ORANGE,
    'Purchaser':      GREEN,
    'Repeat Buyer':   PURPLE,
}


def run(df: pd.DataFrame = None) -> None:
    if df is None:
        df = pd.read_csv(CLEAN_CSV, parse_dates=['event_time'])

    print('\n── Step 5: Dashboard ─────────────────────────────────────────')

    views     = df[df['event_type'] == 'view']
    carts     = df[df['event_type'] == 'cart']
    purchases = df[df['event_type'] == 'purchase']

    # Core KPIs
    total_rev   = purchases['price'].sum()
    n_purchases = len(purchases)
    n_buyers    = purchases['user_id'].nunique()
    aov         = purchases['price'].mean()
    conv        = n_purchases / len(views) * 100
    abandon     = (1 - n_purchases / len(carts)) * 100
    v2c         = len(carts)     / len(views) * 100
    c2p         = n_purchases    / len(carts) * 100

    print(f'  Revenue:          ${total_rev:,.2f}')
    print(f'  Conversion rate:  {conv:.2f}%')
    print(f'  Cart abandonment: {abandon:.1f}%')

    # Segment summary (recompute lightweight version)
    user_events = df.groupby('user_id')['event_type'].apply(set)
    purch_count = purchases.groupby('user_id').size()
    repeat_ids  = purch_count[purch_count > 1].index

    def seg_label(es):
        if 'purchase' in es:
            return 'Repeat Buyer' if es == es  else 'Purchaser'
        if 'cart' in es:
            return 'Cart Abandoner'
        return 'Viewer Only'

    # Simpler inline segmentation for dashboard use
    seg_series = pd.Series({
        uid: (
            'Repeat Buyer'   if uid in repeat_ids else
            'Purchaser'      if 'purchase' in es   else
            'Cart Abandoner' if 'cart'     in es   else
            'Viewer Only'
        )
        for uid, es in user_events.items()
    }, name='segment')
    seg_counts = seg_series.value_counts()

    _main_dashboard(df, purchases, views, carts,
                    total_rev, n_purchases, n_buyers, aov,
                    conv, abandon, v2c, c2p, seg_counts)

    _conversion_dashboard(df, purchases, views, carts,
                          conv, abandon, v2c, c2p)

    print('  Dashboard complete.')


# ── Dashboard 1 ───────────────────────────────────────────────────────────────

def _main_dashboard(df, purchases, views, carts,
                    total_rev, n_purchases, n_buyers, aov,
                    conv, abandon, v2c, c2p, seg_counts):

    rev_monthly = purchases.groupby('month_str')['price'].sum()
    top_brands  = (purchases[purchases['brand'] != 'Unknown']['brand']
                   .value_counts().head(10))

    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor(LIGHT_BG)
    gs  = gridspec.GridSpec(3, 4, figure=fig, hspace=0.5, wspace=0.4)

    # Row 0 — KPI cards
    kpi_cards = [
        (f'${total_rev:,.0f}', 'Total Revenue',   BLUE),
        (f'{n_purchases:,}',   'Purchases',        GREEN),
        (f'{n_buyers:,}',      'Unique Buyers',    PURPLE),
        (f'${aov:.2f}',        'Avg Order Value',  ORANGE),
    ]
    for idx, (val, lbl, color) in enumerate(kpi_cards):
        ax = fig.add_subplot(gs[0, idx])
        ax.set_facecolor(color)
        ax.text(0.5, 0.65, val,  ha='center', va='center', fontsize=16,
                fontweight='bold', color='white', transform=ax.transAxes)
        ax.text(0.5, 0.25, lbl,  ha='center', va='center', fontsize=9,
                color='white', alpha=0.9, transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)

    # Row 1 — Revenue trend (cols 0–1)
    ax_rev = fig.add_subplot(gs[1, 0:2])
    ax_rev.plot(rev_monthly.index, rev_monthly.values, marker='o', color=BLUE, linewidth=2)
    ax_rev.fill_between(range(len(rev_monthly)), rev_monthly.values, alpha=0.15, color=BLUE)
    ax_rev.set_title('Monthly Revenue', fontsize=11)
    ax_rev.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
    ax_rev.tick_params(axis='x', rotation=30)
    ax_rev.set_xticks(range(len(rev_monthly)))
    ax_rev.set_xticklabels(rev_monthly.index)

    # Row 1 — Funnel (cols 2–3)
    ax_fun = fig.add_subplot(gs[1, 2:4])
    n_v, n_c, n_p = len(views), len(carts), n_purchases
    bars = ax_fun.barh(['Views', 'Carts', 'Purchases'], [n_v, n_c, n_p],
                       color=[BLUE, ORANGE, GREEN], edgecolor='white', height=0.5)
    for bar, val in zip(bars, [n_v, n_c, n_p]):
        ax_fun.text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
                    f'{val:,}', va='center', fontsize=9, fontweight='bold')
    ax_fun.set_title('Purchase Funnel', fontsize=11)
    ax_fun.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))

    # Row 2 — Top brands (cols 0–1)
    ax_br = fig.add_subplot(gs[2, 0:2])
    ax_br.barh(top_brands.index[::-1], top_brands.values[::-1], color=BLUE, edgecolor='white')
    ax_br.set_title('Top 10 Brands by Purchases', fontsize=11)
    ax_br.set_xlabel('Purchases')

    # Row 2 — Segments (cols 2–3)
    ax_sg = fig.add_subplot(gs[2, 2:4])
    colors_seg = [SEG_COLORS.get(s, '#999') for s in seg_counts.index]
    ax_sg.pie(seg_counts.values, labels=seg_counts.index, colors=colors_seg,
              autopct='%1.0f%%', startangle=90,
              wedgeprops=dict(edgecolor='white', linewidth=1.5))
    ax_sg.set_title('Customer Segments', fontsize=11)

    fig.suptitle('E-Commerce Analytics Dashboard\nElectronics Store — Sep 2020 to Feb 2021',
                 fontsize=16, fontweight='bold', y=1.01, color=BLUE)
    save(fig, os.path.join(IMG_DASH, '01_main_dashboard.png'))


# ── Dashboard 2 ───────────────────────────────────────────────────────────────

def _conversion_dashboard(df, purchases, views, carts, conv, abandon, v2c, c2p):
    daily_purch = purchases.groupby('date').size()
    rev_weekday = purchases.groupby('weekday')['price'].sum().reindex(WEEKDAY_ORDER)
    hourly_conv = (df.groupby(['hour', 'event_type']).size().unstack(fill_value=0))
    hourly_conv['conv_rate'] = hourly_conv.get('purchase', 0) / hourly_conv.get('view', 1) * 100
    cat_conv = (df[df['top_category'] != 'Unknown']
                .groupby(['top_category', 'event_type']).size().unstack(fill_value=0))
    cat_conv['conv'] = cat_conv.get('purchase', 0) / cat_conv.get('view', 1) * 100
    top_cat_conv = cat_conv['conv'].sort_values(ascending=False).head(8)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.patch.set_facecolor(LIGHT_BG)

    def _gauge(ax, value, max_val, label, color):
        theta = np.linspace(0, np.pi, 200)
        ax.plot(np.cos(theta), np.sin(theta), color='#DDDDDD', linewidth=20, solid_capstyle='round')
        angle = np.pi * (1 - min(value / max_val, 1))
        ax.annotate('', xy=(np.cos(angle)*0.7, np.sin(angle)*0.7), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color=color, lw=3))
        ax.text(0,  -0.2,  f'{value:.2f}%', ha='center', fontsize=20, fontweight='bold', color=color)
        ax.text(0,  -0.45, label, ha='center', fontsize=10, color='#555')
        ax.set_xlim(-1.2, 1.2); ax.set_ylim(-0.6, 1.2); ax.axis('off')

    _gauge(axes[0][0], conv,   10,  'Overall Conversion', RED)
    axes[0][0].set_title('Overall Conversion Rate', fontsize=11, fontweight='bold')

    _gauge(axes[0][1], abandon, 100, 'Cart Abandonment',   ORANGE)
    axes[0][1].set_title('Cart Abandonment Rate', fontsize=11, fontweight='bold')

    # Daily purchases
    axes[0][2].plot(range(len(daily_purch)), daily_purch.values, color=GREEN, linewidth=1.5, alpha=0.8)
    axes[0][2].fill_between(range(len(daily_purch)), daily_purch.values, alpha=0.2, color=GREEN)
    axes[0][2].set_title('Daily Purchase Volume', fontsize=11, fontweight='bold')
    axes[0][2].set_xlabel('Days'); axes[0][2].set_ylabel('Purchases')

    # Conversion by hour
    axes[1][0].plot(hourly_conv.index, hourly_conv['conv_rate'], marker='o',
                    color=BLUE, linewidth=2, markersize=5)
    axes[1][0].set_title('Conversion Rate by Hour', fontsize=11, fontweight='bold')
    axes[1][0].set_xlabel('Hour of Day'); axes[1][0].set_ylabel('Conv Rate (%)')
    axes[1][0].set_xticks(range(0, 24, 2))

    # Top categories by conversion
    axes[1][1].barh(top_cat_conv.index[::-1], top_cat_conv.values[::-1], color=GREEN, edgecolor='white')
    axes[1][1].set_title('Categories by Conversion Rate', fontsize=11, fontweight='bold')
    axes[1][1].set_xlabel('Conversion Rate (%)')

    # Revenue by weekday
    axes[1][2].bar(range(len(WEEKDAY_ORDER)), rev_weekday.values, color=BLUE, edgecolor='white')
    axes[1][2].set_title('Revenue by Weekday', fontsize=11, fontweight='bold')
    axes[1][2].set_xticks(range(len(WEEKDAY_ORDER)))
    axes[1][2].set_xticklabels([d[:3] for d in WEEKDAY_ORDER], rotation=30)
    axes[1][2].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))

    fig.suptitle('Conversion & Revenue Deep Dive Dashboard',
                 fontsize=15, fontweight='bold', y=1.01)
    save(fig, os.path.join(IMG_DASH, '02_conversion_dashboard.png'))


if __name__ == '__main__':
    run()
