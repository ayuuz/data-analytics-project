"""
run_all.py
----------
Orchestrator — runs the full analytics pipeline in order.

Modules called (in order):
    1. clean.py        → load, clean, and export the dataset
    2. eda.py          → exploratory data analysis charts
    3. funnel.py       → funnel metrics and charts
    4. segmentation.py → customer segmentation charts
    5. dashboard.py    → management dashboard visuals
    6. report.py       → compile final PDF report

"""

import sys, os, time

# Ensure src/ is on the path so sibling imports work when called from root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clean
import eda
import funnel
import segmentation
import dashboard
import report

def main():
    start = time.time()
    print('=' * 60)
    print('  E-COMMERCE ANALYTICS — FULL PIPELINE')
    print('=' * 60)

    # Step 1 — clean (returns DataFrame so we avoid re-reading CSV downstream)
    df = clean.run()

    # Steps 2–5 — analysis modules (each accepts the df directly)
    eda.run(df)
    funnel.run(df)
    segmentation.run(df)
    dashboard.run(df)

    # Step 6 — PDF report (reads from outputs/*.json, no df needed)
    report.run()

    elapsed = time.time() - start
    print(f'\n{"=" * 60}')
    print(f'  Pipeline complete in {elapsed:.1f}s')
    print(f'{"=" * 60}')
    print('\n  Outputs:')
    print('    outputs/events_cleaned.csv')
    print('    outputs/user_segments.csv')
    print('    outputs/project_summary.json')
    print('    images/eda/          (10 charts)')
    print('    images/funnel/       (3 charts)')
    print('    images/segmentation/ (3 charts)')
    print('    images/dashboard/    (2 dashboards)')
    print('    reports/final_report.pdf')


if __name__ == '__main__':
    main()
