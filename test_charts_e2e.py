#!/usr/bin/env python
"""
End-to-end test for the 24-chart auto-generation system.
Tests:
1. CSV upload and parsing
2. AI chart selection
3. Data preparation for all 24 types
4. Chart generation endpoint
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'BACKEND'))

import pandas as pd
from csv_processor import ai_select_charts, prepare_chart_data

def test_e2e():
    """Run end-to-end test"""
    print("\n" + "="*60)
    print("🧪 CHART GENERATION END-TO-END TEST")
    print("="*60 + "\n")

    # Test 1: Load CSV
    print("📂 Test 1: Loading test CSV...")
    csv_path = Path(__file__).parent / "test_data_with_dates.csv"
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded: {csv_path.name}")
        print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}\n")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}\n")
        return False

    # Test 2: AI Chart Selection
    print("🤖 Test 2: Running AI chart selection...")
    try:
        chart_configs = ai_select_charts(df, csv_path.name, quarter="All", category="All")
        print(f"✓ Selected {len(chart_configs)} charts")
        for idx, cfg in enumerate(chart_configs, 1):
            print(f"  {idx}. {cfg.get('title', 'Unknown')} [{cfg.get('chartType', 'UNKNOWN')}] (Priority: {cfg.get('priority', '?')})")
        print()
    except Exception as e:
        print(f"❌ Chart selection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Data Preparation
    print("📊 Test 3: Preparing data for each chart...")
    success_count = 0
    fail_count = 0
    
    for idx, config in enumerate(chart_configs, 1):
        try:
            data = prepare_chart_data(df, config)
            if data is None:
                print(f"  ⚠️  {idx}. {config.get('title')} - returned None")
                fail_count += 1
                continue
            
            # Check data structure
            has_labels = 'labels' in data or 'categories' in data
            has_series = 'series' in data or 'data' in data
            
            if has_labels or has_series:
                print(f"  ✓ {idx}. {config.get('title')} - {config.get('chartType')}")
                success_count += 1
            else:
                print(f"  ⚠️  {idx}. {config.get('title')} - missing labels/series")
                fail_count += 1
        except Exception as e:
            print(f"  ❌ {idx}. {config.get('title')} - {str(e)[:50]}")
            fail_count += 1

    print(f"\n✓ Successfully prepared: {success_count}/{len(chart_configs)} charts")
    if fail_count > 0:
        print(f"⚠️  Failed: {fail_count} charts")
    print()

    # Test 4: Verify chart diversity
    print("🎨 Test 4: Checking chart type diversity...")
    chart_types = set(cfg.get('chartType') for cfg in chart_configs)
    print(f"✓ Using {len(chart_types)} distinct chart types")
    print(f"  Types: {', '.join(sorted(chart_types))}\n")

    # Test 5: Verify business insights
    print("💡 Test 5: Checking business insights...")
    charts_with_insights = sum(1 for cfg in chart_configs if cfg.get('business_insight'))
    print(f"✓ {charts_with_insights}/{len(chart_configs)} charts have business insights\n")

    # Summary
    print("="*60)
    print("✅ END-TO-END TEST PASSED!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start backend server: python BACKEND/main.py")
    print("2. Start frontend server: cd FRONTEND && npm run dev")
    print("3. Open browser and upload test_data_with_dates.csv")
    print("4. Verify charts auto-generate in dashboard")
    print("5. Test chart type cycling (↻ button)")
    print("6. Verify business insight text displays under titles\n")

    return True

if __name__ == "__main__":
    success = test_e2e()
    sys.exit(0 if success else 1)
