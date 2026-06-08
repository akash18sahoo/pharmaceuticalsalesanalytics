# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
"""
=============================================================
  PHASE 4 — Visualizations
=============================================================
  What this script does:
    Loads clean data and generates 6 business charts using
    Matplotlib and Seaborn. All charts saved to reports/figures/

  Charts:
    Chart 1 : Revenue by Region         (horizontal bar)
    Chart 2 : Monthly Revenue Trend     (multi-year line)
    Chart 3 : Top 10 Drugs by Revenue   (bar chart)
    Chart 4 : Drug Class Breakdown      (pie chart)
    Chart 5 : Sales Rep Achievement %   (color-coded bar)
    Chart 6 : Year-over-Year Growth     (bar + line combo)

  Run:  python scripts/04_visualizations.py
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import os

os.makedirs('reports/figures', exist_ok=True)

# ── Global Style ──────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor':  '#F7F9FC',
    'axes.facecolor':    '#F7F9FC',
    'axes.edgecolor':    '#CCCCCC',
    'axes.grid':         True,
    'grid.color':        '#E0E0E0',
    'grid.linestyle':    '--',
    'grid.linewidth':    0.6,
    'font.family':       'DejaVu Sans',
    'font.size':         10,
    'axes.titlesize':    13,
    'axes.titleweight':  'bold',
    'axes.labelsize':    10,
    'xtick.labelsize':   9,
    'ytick.labelsize':   9,
    'legend.fontsize':   9,
})

# Color palette
BLUE    = '#1A6FA6'
TEAL    = '#2E9E8F'
ORANGE  = '#E07B39'
RED     = '#C0392B'
GREEN   = '#27AE60'
PURPLE  = '#7D3C98'
GRAY    = '#7F8C8D'

REGION_COLORS = [BLUE, TEAL, ORANGE, PURPLE, GRAY]
CLASS_COLORS  = [BLUE, TEAL, ORANGE, RED, GREEN, PURPLE]


# ── Helper: save figure ───────────────────────────────────────
def save_fig(fig, filename):
    path = f'reports/figures/{filename}'
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Load Data ─────────────────────────────────────────────────
conn = sqlite3.connect('data/pharma_sales.db')
df   = pd.read_sql_query("SELECT * FROM fact_sales_clean", conn)
conn.close()

df['date']    = pd.to_datetime(df['date'])
df['year']    = df['year'].astype(int)
df['month']   = df['month'].astype(int)
df['revenue'] = df['revenue'].astype(float)

print(f"\n  Loaded {len(df):,} rows from fact_sales_clean")
print(f"  Generating 6 charts...\n")


# ============================================================
#  CHART 1: Revenue by Region (Horizontal Bar)
# ============================================================

print("[1/6] Revenue by Region...")

region_rev = (df.groupby('region')['revenue']
                .sum()
                .sort_values(ascending=True))  # ascending for horizontal bar

fig, ax = plt.subplots(figsize=(9, 5))

bars = ax.barh(region_rev.index, region_rev.values / 1e6,
               color=REGION_COLORS[::-1], edgecolor='white', linewidth=0.8)

# Value labels on bars
for bar, val in zip(bars, region_rev.values):
    ax.text(val / 1e6 + 0.3, bar.get_y() + bar.get_height() / 2,
            f'INR {val/1e6:.1f}M', va='center', fontsize=9, color='#333333')

ax.set_xlabel('Total Revenue (INR Millions)')
ax.set_title('Revenue by Region (2020–2024)', pad=15)
ax.set_xlim(0, region_rev.max() / 1e6 * 1.22)
ax.axvline(region_rev.mean() / 1e6, color=ORANGE, linestyle='--',
           linewidth=1.2, label=f'Avg: INR {region_rev.mean()/1e6:.1f}M')
ax.legend()
ax.grid(axis='x', alpha=0.7)
ax.grid(axis='y', alpha=0)

fig.text(0.12, -0.04,
         'Insight: North region leads with the highest revenue share. '
         'South region is the weakest — potential coaching area.',
         fontsize=8, color='#555555', style='italic')

save_fig(fig, 'chart1_revenue_by_region.png')


# ============================================================
#  CHART 2: Monthly Revenue Trend — All Years (Line Chart)
# ============================================================

print("[2/6] Monthly Revenue Trend...")

monthly = (df.groupby(['year', 'month'])['revenue']
             .sum()
             .reset_index())

year_colors = {2020: GRAY, 2021: PURPLE, 2022: TEAL, 2023: BLUE, 2024: ORANGE}

fig, ax = plt.subplots(figsize=(11, 5))

for year in sorted(monthly['year'].unique()):
    yd = monthly[monthly['year'] == year].sort_values('month')
    ax.plot(yd['month'], yd['revenue'] / 1e6,
            marker='o', markersize=4, linewidth=2,
            color=year_colors[year], label=str(year))

month_labels = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']
ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_labels)
ax.set_xlabel('Month')
ax.set_ylabel('Revenue (INR Millions)')
ax.set_title('Monthly Revenue Trend by Year (2020–2024)', pad=15)
ax.legend(title='Year', loc='upper left')

# Highlight Q4 peak
ax.axvspan(9.5, 12.5, alpha=0.08, color=ORANGE, label='Q4 Season')
ax.text(10.8, monthly['revenue'].max() * 0.95 / 1e6, 'Q4\nPeak',
        fontsize=8, color=ORANGE, ha='center')

fig.text(0.12, -0.04,
         'Insight: Revenue shows a consistent Q4 spike across all years. '
         'Anti-infective and Cardiovascular drugs drive winter seasonality.',
         fontsize=8, color='#555555', style='italic')

save_fig(fig, 'chart2_monthly_trend.png')


# ============================================================
#  CHART 3: Top 10 Drugs by Revenue (Vertical Bar)
# ============================================================

print("[3/6] Top 10 Drugs by Revenue...")

drug_rev = (df.groupby(['drug_name', 'drug_class'])['revenue']
              .sum()
              .reset_index()
              .sort_values('revenue', ascending=False)
              .head(10))

# Color by drug class
class_color_map = {c: CLASS_COLORS[i]
                   for i, c in enumerate(drug_rev['drug_class'].unique())}
bar_colors = drug_rev['drug_class'].map(class_color_map).tolist()

fig, ax = plt.subplots(figsize=(11, 5))

bars = ax.bar(range(len(drug_rev)), drug_rev['revenue'] / 1e6,
              color=bar_colors, edgecolor='white', linewidth=0.8, width=0.65)

# Value labels
for bar, val in zip(bars, drug_rev['revenue']):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
            f'{val/1e6:.1f}M', ha='center', va='bottom', fontsize=8)

ax.set_xticks(range(len(drug_rev)))
ax.set_xticklabels(drug_rev['drug_name'], rotation=25, ha='right')
ax.set_ylabel('Total Revenue (INR Millions)')
ax.set_title('Top 10 Drugs by Revenue (2020–2024)', pad=15)

# Legend for drug class
legend_patches = [mpatches.Patch(color=col, label=cls)
                  for cls, col in class_color_map.items()]
ax.legend(handles=legend_patches, title='Drug Class',
          loc='upper right', fontsize=8)

fig.text(0.12, -0.06,
         'Insight: Cardiovascular and Diabetes drugs dominate revenue. '
         'High unit price drives Insulin Glargine performance despite lower volumes.',
         fontsize=8, color='#555555', style='italic')

save_fig(fig, 'chart3_top_drugs.png')


# ============================================================
#  CHART 4: Drug Class Revenue Breakdown (Pie Chart)
# ============================================================

print("[4/6] Drug Class Breakdown...")

class_rev = (df.groupby('drug_class')['revenue']
               .sum()
               .sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(8, 6))

wedges, texts, autotexts = ax.pie(
    class_rev.values,
    labels=None,
    autopct='%1.1f%%',
    startangle=140,
    colors=CLASS_COLORS[:len(class_rev)],
    pctdistance=0.78,
    wedgeprops=dict(edgecolor='white', linewidth=1.8)
)

for at in autotexts:
    at.set_fontsize(9)
    at.set_color('white')
    at.set_fontweight('bold')

# Legend with INR values
legend_labels = [f"{cls}  —  INR {rev/1e6:.1f}M"
                 for cls, rev in zip(class_rev.index, class_rev.values)]
ax.legend(wedges, legend_labels,
          title='Drug Class', loc='lower center',
          bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9)

ax.set_title('Revenue Breakdown by Drug Class (2020–2024)', pad=20)

fig.text(0.5, -0.08,
         'Insight: Cardiovascular drugs form the largest revenue share '
         'due to chronic usage and higher prescription rates.',
         fontsize=8, color='#555555', style='italic', ha='center')

save_fig(fig, 'chart4_drug_class_pie.png')


# ============================================================
#  CHART 5: Sales Rep Achievement % (Color-Coded Bar)
# ============================================================

print("[5/6] Sales Rep Achievement %...")

rep_data = (df.groupby(['rep_name', 'region'])
              .agg(actual=('revenue', 'sum'),
                   target=('target_revenue', 'sum'))
              .reset_index())
rep_data['achievement_pct'] = (rep_data['actual'] / rep_data['target'] * 100).round(1)
rep_data = rep_data.sort_values('achievement_pct', ascending=True)

# Color based on performance
def rep_color(pct):
    if pct >= 100:
        return GREEN
    elif pct >= 85:
        return ORANGE
    else:
        return RED

bar_colors = [rep_color(p) for p in rep_data['achievement_pct']]

fig, ax = plt.subplots(figsize=(10, 7))

bars = ax.barh(rep_data['rep_name'], rep_data['achievement_pct'],
               color=bar_colors, edgecolor='white', linewidth=0.6)

# Value labels
for bar, val in zip(bars, rep_data['achievement_pct']):
    ax.text(val + 0.4, bar.get_y() + bar.get_height() / 2,
            f'{val:.1f}%', va='center', fontsize=8.5)

# Reference lines
ax.axvline(100, color=GREEN,  linestyle='--', linewidth=1.5,
           label='Target (100%)')
ax.axvline(85,  color=ORANGE, linestyle=':',  linewidth=1.2,
           label='Near Target (85%)')

ax.set_xlabel('Achievement % (Actual / Target Revenue)')
ax.set_title('Sales Rep Target Achievement — SFE Analysis', pad=15)
ax.set_xlim(0, rep_data['achievement_pct'].max() * 1.12)

# Legend for status
legend_patches = [
    mpatches.Patch(color=GREEN,  label='Target Met  (>=100%)'),
    mpatches.Patch(color=ORANGE, label='Near Target (85–99%)'),
    mpatches.Patch(color=RED,    label='Below Target (<85%)'),
]
ax.legend(handles=legend_patches + [
    mpatches.Patch(color=GREEN,  alpha=0, label=''),  # spacer
], loc='lower right', fontsize=8)

fig.text(0.12, -0.03,
         'Insight: Top reps (Rank 1 per region) consistently beat their targets. '
         'Rank 4 reps in each region need performance coaching.',
         fontsize=8, color='#555555', style='italic')

save_fig(fig, 'chart5_rep_achievement.png')


# ============================================================
#  CHART 6: Year-over-Year Revenue Growth (Bar + Line)
# ============================================================

print("[6/6] Year-over-Year Revenue Growth...")

yearly = (df.groupby('year')['revenue']
            .sum()
            .reset_index()
            .rename(columns={'revenue': 'total_revenue'}))

yearly['yoy_growth_pct'] = yearly['total_revenue'].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(9, 5))

# Bar: absolute revenue
bars = ax1.bar(yearly['year'], yearly['total_revenue'] / 1e6,
               color=[BLUE, TEAL, ORANGE, PURPLE, '#E74C3C'],
               edgecolor='white', linewidth=0.8, width=0.55, alpha=0.9)

for bar, val in zip(bars, yearly['total_revenue']):
    ax1.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.3,
             f'INR {val/1e6:.1f}M', ha='center', va='bottom',
             fontsize=9, fontweight='bold')

ax1.set_xlabel('Year')
ax1.set_ylabel('Total Revenue (INR Millions)', color='#333333')
ax1.set_title('Year-over-Year Revenue & Growth Rate (2020–2024)', pad=15)
ax1.set_xticks(yearly['year'])

# Line: YoY growth % on secondary axis
ax2 = ax1.twinx()
ax2.plot(yearly['year'], yearly['yoy_growth_pct'],
         color=ORANGE, marker='D', markersize=7,
         linewidth=2.2, linestyle='--', label='YoY Growth %')

for x, y in zip(yearly['year'], yearly['yoy_growth_pct']):
    if not np.isnan(y):
        ax2.text(x, y + 0.8, f'+{y:.1f}%',
                 ha='center', fontsize=8.5, color=ORANGE, fontweight='bold')

ax2.set_ylabel('YoY Growth (%)', color=ORANGE)
ax2.tick_params(axis='y', labelcolor=ORANGE)
ax2.set_ylim(-5, yearly['yoy_growth_pct'].max() * 2)
ax2.grid(False)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    mpatches.Patch(facecolor=BLUE,   label='Annual Revenue'),
    Line2D([0], [0], color=ORANGE, marker='D', linestyle='--',
           markersize=6, label='YoY Growth %')
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=9)

fig.text(0.12, -0.04,
         'Insight: Consistent ~7-10% YoY growth reflects a healthy, '
         'growing pharma portfolio. 2024 growth slows — watch Q4 performance.',
         fontsize=8, color='#555555', style='italic')

save_fig(fig, 'chart6_yoy_growth.png')


# ============================================================
#  DONE
# ============================================================

print()
print("=" * 52)
print("  ALL 6 CHARTS SAVED")
print("=" * 52)

charts = [
    ('chart1_revenue_by_region.png',  'Revenue by Region'),
    ('chart2_monthly_trend.png',      'Monthly Revenue Trend'),
    ('chart3_top_drugs.png',          'Top 10 Drugs by Revenue'),
    ('chart4_drug_class_pie.png',     'Drug Class Breakdown'),
    ('chart5_rep_achievement.png',    'Sales Rep Achievement %'),
    ('chart6_yoy_growth.png',         'Year-over-Year Growth'),
]
for fname, title in charts:
    size_kb = os.path.getsize(f'reports/figures/{fname}') // 1024
    print(f"  {title:<30} -> reports/figures/{fname}  ({size_kb} KB)")

print(f"""
  Phase 4 complete!
  Open reports/figures/ to view all charts.

  PROJECT COMPLETE — All 4 phases done:
    Phase 1 : Data Generation   -> data/pharma_sales.csv + .db
    Phase 2 : Data Cleaning     -> data/pharma_sales_clean.csv
    Phase 3 : SQL Analysis      -> sql/analysis/*.sql
    Phase 4 : Visualizations    -> reports/figures/*.png
""")
