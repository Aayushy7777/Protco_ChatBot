#!/usr/bin/env python
"""Test the refactored architecture."""
from file_processor import read_file, clean_and_type, profile
from pathlib import Path

print("=" * 60)
print("Testing refactored AI Dashboard architecture")
print("=" * 60)

# Try multiple paths
test_paths = [
    ('../../uploads', '*.csv'),
    ('../../../uploads', '*.csv'),
    ('../../', '*.csv'),
    ('../frontend/public', '*.csv'),
]

test_file = None
for base_path, pattern in test_paths:
    try:
        test_files = list(Path(base_path).glob(pattern))
        if test_files:
            test_file = test_files[0]
            break
    except:
        pass

if test_file:
    filepath = str(test_file)
    print(f"\nTest file: {test_file.name}")
    
    # Test file reading
    df = read_file(filepath)
    print(f"✓ File read successfully: {df.shape[0]} rows")
    
    # Test type cleaning
    df = clean_and_type(df)
    print(f"✓ Types detected and cleaned")
    
    # Test profiling
    p = profile(df, test_file.name)
    print(f"\nProfile Summary:")
    print(f"  Rows: {p['rows']}")
    print(f"  Columns: {len(p['columns'])}")
    print(f"  Chart datasets generated: {len(p['charts'])}")
    print(f"  KPI cards generated: {len(p['kpis'])}")
    print(f"  LLM context size: {len(p['context'])} characters")
    
    # Show auto-detected columns
    if p['auto']:
        print(f"\nAuto-detected columns:")
        for key, val in p['auto'].items():
            print(f"  {key}: {val}")
    
    # Show KPIs
    if p['kpis']:
        print(f"\nKPI cards (first 3):")
        for kpi in p['kpis'][:3]:
            print(f"  [{kpi['color']}] {kpi['label']}: {kpi['value']}")
    
    # Show charts
    if p['charts']:
        print(f"\nChart configs (first 3):")
        for chart in p['charts'][:3]:
            print(f"  [{chart['type']}] {chart['title']}")
    
    print("\n" + "=" * 60)
    print("ARCHITECTURE TEST: PASS")
    print("=" * 60)
    print("\nBackend refactoring is complete and working!")
else:
    print("ERROR: No CSV files found in test paths")
    print("Try uploading a CSV or Excel file through the web interface first.")
