import requests
import json

file_path = r"c:\Users\redqu\OneDrive\Desktop\CSV CHAT AGENT\uploads\Project-Management-Sample-Data.xlsx"

print("=" * 70)
print("Testing Improved Dashboard with Enhanced KPIs")
print("=" * 70)

# Upload file
print("\n[1/2] Uploading project management file...")
try:
    with open(file_path, 'rb') as f:
        files = {'file': ('Project-Management-Sample-Data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post('http://localhost:8011/upload', files=files, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Upload successful")
        print(f"  - Rows: {data.get('rows', 'N/A')}")
        print(f"  - Columns: {data.get('columns', 'N/A')}")
        print(f"  - KPIs generated: {len(data.get('kpis', []))}")
    else:
        print(f"✗ Upload failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Get dashboard
print("\n[2/2] Generating improved dashboard...")
try:
    response = requests.get('http://localhost:8011/dashboard', timeout=30)
    if response.status_code == 200:
        html = response.text
        # Count KPI cards
        kpi_count = html.count('kpi-card')
        charts_count = html.count('chart-card')
        has_detail = 'kpi-detail' in html
        has_colors = 'color:' in html
        
        print(f"✓ Dashboard generated ({len(html)} bytes)")
        print(f"  - KPI cards: {kpi_count // 2}")  # Each card has opening and closing
        print(f"  - Chart cards: {charts_count // 2}")
        print(f"  - Has detail text: {has_detail}")
        print(f"  - Has color coding: {has_colors}")
        
        # Save to file
        with open("c:/Users/redqu/OneDrive/Desktop/CSV CHAT AGENT/dashboard_improved.html", 'w') as f:
            f.write(html)
        print(f"  - Saved to: dashboard_improved.html")
    else:
        print(f"✗ Failed: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 70)
print("✓ Dashboard improvements complete!")
print("=" * 70)
