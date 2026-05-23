"""
eda.py
------
Step 2 — Exploratory Data Analysis.
Produces 10 charts saved to images/eda/.

Accepts:         cleaned pd.DataFrame  (loaded from CSV if not passed in)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from config import (
    CLEAN_CSV, IMG_EDA,
    BLUE, RED, GREEN, ORANGE, PURPLE,
    save,
)

WEEKDAY_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']


def run(df: pd.DataFrame = None) -> None:
    if df is None:
        df = pd.read_csv(CLEAN_CSV, parse_dates=['event_time'])

    print('\n── Step 2: EDA ───────────────────────────────────────────────')

    views     = df[df['event_type'] == 'view']
    carts     = df[df['event_type'] == 'cart']
    purchases = df[df['event_type'] == 'purchase']

    _event_distribution(df)
    _monthly_trends(df)
    _hourly_patterns(df)
    _weekday_patterns(df)
    _top_brands(views, purchases)
    _top_categories(df)
    _revenue_analysis(purchases)
    _price_distribution(purchases)
    _high_view_low_purchase(views, purchases)
    _user_activity(df)

    print('  EDA complete.')


# ── Individual chart functions ────────────────────────────────────────────────

def _event_distribution(df):
    counts = df['event_type'].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [BLUE, ORANGE, GREEN]
    bars = ax.bar(counts.index, counts.values, color=colors, width=0.55,
                  edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
                f'{val:,}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    pct = [f'{v/len(df)*100:.1f}%' for v in counts.values]
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels([f'{e.capitalize()}\n({p})' for e, p in zip(counts.index, pct)])
    ax.set_title('Event Type Distribution\nUsers Browse Heavily but Few Convert to Purchase', pad=15)
    ax.set_ylabel('Number of Events')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    save(fig, os.path.join(IMG_EDA, '01_event_distribution.png'))


def _monthly_trends(df):
    monthly = df.groupby(['month_str', 'event_type']).size().unstack(fill_value=0)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for et, color in zip(['view', 'cart', 'purchase'], [BLUE, ORANGE, GREEN]):
        if et in monthly.columns:
            axes[0].plot(monthly.index, monthly[et], marker='o', label=et.capitalize(),
                         color=color, linewidth=2.2, markersize=6)
    axes[0].set_title('Monthly Event Trends')
    axes[0].set_ylabel('Event Count')
    axes[0].tick_params(axis='x', rotation=35)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    axes[0].legend()
    if 'purchase' in monthly.columns:
        axes[1].bar(monthly.index, monthly['purchase'], color=GREEN, edgecolor='white')
        axes[1].set_title('Monthly Purchases')
        axes[1].set_ylabel('Purchase Events')
        axes[1].tick_params(axis='x', rotation=35)
        axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    save(fig, os.path.join(IMG_EDA, '02_monthly_trends.png'))


def _hourly_patterns(df):
    hourly = df.groupby(['hour', 'event_type']).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 5))
    for et, color in zip(['view', 'cart', 'purchase'], [BLUE, ORANGE, GREEN]):
        if et in hourly.columns:
            ax.plot(hourly.index, hourly[et], marker='o', label=et.capitalize(),
                    color=color, linewidth=2.2, markersize=5)
    ax.axvspan(10, 14, alpha=0.08, color=GREEN, label='Mid-day peak')
    ax.axvspan(19, 22, alpha=0.08, color=ORANGE, label='Evening peak')
    ax.set_title('Hourly Activity Patterns\nWhen Are Users Most Active?')
    ax.set_ylabel('Event Count')
    ax.set_xlabel('Hour of Day (UTC)')
    ax.set_xticks(range(0, 24))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax.legend()
    save(fig, os.path.join(IMG_EDA, '03_hourly_patterns.png'))


def _weekday_patterns(df):
    wk = df.groupby(['weekday', 'event_type']).size().unstack(fill_value=0)
    wk = wk.reindex(WEEKDAY_ORDER)
    fig, ax = plt.subplots(figsize=(10, 5))
    x, w = np.arange(len(WEEKDAY_ORDER)), 0.25
    for i, (et, color) in enumerate(zip(['view', 'cart', 'purchase'], [BLUE, ORANGE, GREEN])):
        if et in wk.columns:
            ax.bar(x + i*w, wk[et], width=w, label=et.capitalize(),
                   color=color, edgecolor='white')
    ax.set_xticks(x + w)
    ax.set_xticklabels(WEEKDAY_ORDER, rotation=25)
    ax.set_title('Events by Day of Week\nWeekday vs Weekend Behavior')
    ax.set_ylabel('Event Count')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax.legend()
    save(fig, os.path.join(IMG_EDA, '04_weekday_patterns.png'))


def _top_brands(views, purchases):
    top_v = views[views['brand'] != 'Unknown']['brand'].value_counts().head(15)
    top_p = purchases[purchases['brand'] != 'Unknown']['brand'].value_counts().head(15)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].barh(top_v.index[::-1], top_v.values[::-1], color=BLUE, edgecolor='white')
    axes[0].set_title('Top 15 Brands by Views')
    axes[0].set_xlabel('View Count')
    axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    for i, v in enumerate(top_v.values[::-1]):
        axes[0].text(v + 200, i, f'{v:,}', va='center', fontsize=8)
    axes[1].barh(top_p.index[::-1], top_p.values[::-1], color=GREEN, edgecolor='white')
    axes[1].set_title('Top 15 Brands by Purchases')
    axes[1].set_xlabel('Purchase Count')
    for i, v in enumerate(top_p.values[::-1]):
        axes[1].text(v + 5, i, f'{v:,}', va='center', fontsize=8)
    save(fig, os.path.join(IMG_EDA, '05_top_brands.png'))


def _top_categories(df):
    cat = (df[df['top_category'] != 'Unknown']
           .groupby(['top_category', 'event_type'])
           .size().unstack(fill_value=0))
    cat['total'] = cat.sum(axis=1)
    cat = cat.sort_values('total', ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(11, 6))
    x, w = np.arange(len(cat)), 0.25
    for i, (et, color) in enumerate(zip(['view', 'cart', 'purchase'], [BLUE, ORANGE, GREEN])):
        if et in cat.columns:
            ax.bar(x + i*w, cat[et], width=w, label=et.capitalize(),
                   color=color, edgecolor='white')
    ax.set_xticks(x + w)
    ax.set_xticklabels(cat.index, rotation=30, ha='right')
    ax.set_title('Events by Top Category\nElectronics & Computers Dominate')
    ax.set_ylabel('Event Count')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax.legend()
    save(fig, os.path.join(IMG_EDA, '06_top_categories.png'))


def _revenue_analysis(purchases):
    rev_monthly = purchases.groupby('month_str')['price'].sum()
    rev_cat = (purchases[purchases['top_category'] != 'Unknown']
               .groupby('top_category')['price'].sum()
               .sort_values(ascending=False).head(8))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].bar(rev_monthly.index, rev_monthly.values, color=BLUE, edgecolor='white')
    axes[0].set_title('Monthly Revenue from Purchases')
    axes[0].set_ylabel('Revenue (USD)')
    axes[0].tick_params(axis='x', rotation=35)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
    for i, v in enumerate(rev_monthly.values):
        axes[0].text(i, v + 1000, f'${v/1000:.1f}K', ha='center', fontsize=8, fontweight='bold')
    axes[1].barh(rev_cat.index[::-1], rev_cat.values[::-1], color=GREEN, edgecolor='white')
    axes[1].set_title('Revenue by Category')
    axes[1].set_xlabel('Revenue (USD)')
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'))
    save(fig, os.path.join(IMG_EDA, '07_revenue_analysis.png'))


def _price_distribution(purchases):
    p99 = purchases['price'].quantile(0.99)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].hist(purchases[purchases['price'] <= p99]['price'], bins=50,
                 color=GREEN, edgecolor='white', alpha=0.85)
    axes[0].axvline(purchases['price'].median(), color=RED,    linestyle='--', linewidth=1.8,
                    label=f'Median: ${purchases["price"].median():.2f}')
    axes[0].axvline(purchases['price'].mean(),   color=ORANGE, linestyle='--', linewidth=1.8,
                    label=f'Mean: ${purchases["price"].mean():.2f}')
    axes[0].set_title('Purchase Price Distribution')
    axes[0].set_xlabel('Price (USD)')
    axes[0].set_ylabel('Count')
    axes[0].legend()
    bins   = [0, 20, 50, 100, 200, 500, 10000]
    labels = ['<$20', '$20–50', '$50–100', '$100–200', '$200–500', '>$500']
    pc = purchases.copy()
    pc['price_range'] = pd.cut(pc['price'], bins=bins, labels=labels)
    prc = pc['price_range'].value_counts().sort_index()
    axes[1].bar(prc.index, prc.values, color=BLUE, edgecolor='white')
    axes[1].set_title('Purchases by Price Range')
    axes[1].set_xlabel('Price Range')
    axes[1].set_ylabel('Number of Purchases')
    for i, v in enumerate(prc.values):
        axes[1].text(i, v + 10, f'{v:,}', ha='center', fontsize=8)
    save(fig, os.path.join(IMG_EDA, '08_price_distribution.png'))


def _high_view_low_purchase(views, purchases):
    prod_v = views.groupby('product_id').size().rename('views')
    prod_p = purchases.groupby('product_id').size().rename('purchases')
    prod   = pd.concat([prod_v, prod_p], axis=1).fillna(0)
    prod['conv_rate'] = prod['purchases'] / prod['views']
    hvlp = prod[prod['views'] >= 100].sort_values('conv_rate').head(15)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(range(len(hvlp)), hvlp['views'].values,     color=RED,   alpha=0.75,
            label='Views', edgecolor='white')
    ax.barh(range(len(hvlp)), hvlp['purchases'].values, color=GREEN,
            label='Purchases', edgecolor='white')
    ax.set_yticks(range(len(hvlp)))
    ax.set_yticklabels([f'Product {str(pid)[:6]}…' for pid in hvlp.index], fontsize=8)
    ax.set_title('High-View, Low-Purchase Products\nProducts That Attract Attention but Fail to Convert')
    ax.set_xlabel('Event Count')
    ax.legend()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    save(fig, os.path.join(IMG_EDA, '09_high_view_low_purchase.png'))


def _user_activity(df):
    user_total     = df.groupby('user_id').size()
    sessions_per_u = df.groupby('user_id')['user_session'].nunique()
    returning      = (sessions_per_u > 1).sum()
    onetime        = (sessions_per_u == 1).sum()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    cap = user_total[user_total <= user_total.quantile(0.95)]
    axes[0].hist(cap, bins=40, color=BLUE, edgecolor='white', alpha=0.85)
    axes[0].set_title('User Event Count Distribution\n(Up to 95th Percentile)')
    axes[0].set_xlabel('Total Events per User')
    axes[0].set_ylabel('Number of Users')
    axes[1].pie([onetime, returning],
                labels=['One-Session Users', 'Returning Users'],
                colors=[ORANGE, BLUE], autopct='%1.1f%%', startangle=90,
                wedgeprops=dict(edgecolor='white', linewidth=2))
    axes[1].set_title('Returning vs One-Session Users')
    save(fig, os.path.join(IMG_EDA, '10_user_activity.png'))


if __name__ == '__main__':
    run()
