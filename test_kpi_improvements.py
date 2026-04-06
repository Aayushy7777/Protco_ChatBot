import os
import requests

# Test with existing upload
upload_dir = r"c:\Users\redqu\OneDrive\Desktop\CSV CHAT AGENT\ai-dashboard-generator\backend\uploads"
csv_files = [f for f in os.listdir(upload_dir) if f.endswith('.csv')]

if csv_files:
    test_file = csv_files[0]
    test_path = os.path.join(upload_dir, test_file)
    
    print(f"Testing with uploaded file: {test_file}")
    
    # Upload it
    with open(test_path, 'rb') as f:
        files = {'file': (test_file, f, 'text/csv')}
        response = requests.post('http://localhost:8011/upload', files=files, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Upload successful - {data['rows']} rows")
        
        # Get dashboard with improvements
        dash_response = requests.get('http://localhost:8011/dashboard', timeout=30)
        if dash_response.status_code == 200:
            html = dash_response.text
            kpi_count = html.count('class="kpi-card"')
            print(f"✓ Dashboard generated with {kpi_count} KPI cards")
            print(f"  - Has improved colors: {'style=\"color:' in html}")
            print(f"  - KPI details: {'kpi-detail' in html}")
            
            # Save
            with open(r"c:\Users\redqu\OneDrive\Desktop\CSV CHAT AGENT\dashboard_improved.html", 'w') as f:
                f.write(html)
            print("✓ Saved to dashboard_improved.html")
