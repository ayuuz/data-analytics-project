"""
config.py
---------
Shared constants: file paths, colour palette, matplotlib theme, and the
save() helper used by every other module.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Base paths ───────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
IMG_EDA  = os.path.join(BASE, 'images', 'eda')
IMG_FUN  = os.path.join(BASE, 'images', 'funnel')
IMG_SEG  = os.path.join(BASE, 'images', 'segmentation')
IMG_DASH = os.path.join(BASE, 'images', 'dashboard')
OUT_DIR  = os.path.join(BASE, 'outputs')
RPT_DIR  = os.path.join(BASE, 'reports')

RAW_CSV     = os.path.join(DATA_DIR, 'events.csv')
CLEAN_CSV   = os.path.join(OUT_DIR,  'events_cleaned.csv')
SUMMARY_JSON = os.path.join(OUT_DIR, 'project_summary.json')

# ── Colour palette ───────────────────────────────────────────────────────────
PALETTE = ['#2C3E50', '#E74C3C', '#3498DB', '#27AE60', '#F39C12',
           '#8E44AD', '#16A085', '#D35400', '#2980B9', '#C0392B']

BLUE   = '#2C3E50'
RED    = '#E74C3C'
GREEN  = '#27AE60'
ORANGE = '#F39C12'
PURPLE = '#8E44AD'
TEAL   = '#16A085'
LIGHT_BG = '#F8F9FA'

# ── Matplotlib global theme ──────────────────────────────────────────────────
import seaborn as sns
sns.set_theme(style='whitegrid', palette=PALETTE)
plt.rcParams.update({
    'figure.dpi':        150,
    'savefig.dpi':       150,
    'font.family':       'DejaVu Sans',
    'axes.titlesize':    14,
    'axes.titleweight':  'bold',
    'axes.labelsize':    11,
    'xtick.labelsize':   9,
    'ytick.labelsize':   9,
    'legend.fontsize':   9,
    'figure.facecolor':  'white',
    'axes.facecolor':    '#FAFAFA',
    'axes.edgecolor':    '#CCCCCC',
    'grid.color':        '#E5E5E5',
    'axes.spines.top':   False,
    'axes.spines.right': False,
})

# ── Helper ───────────────────────────────────────────────────────────────────
def save(fig, path):
    """Save figure, close it, and print a confirmation line."""
    fig.tight_layout()
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✓ {os.path.basename(path)}')
