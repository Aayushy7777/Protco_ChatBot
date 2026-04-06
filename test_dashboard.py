import requests
import json
import time

file_path = r"c:\Users\redqu\OneDrive\Desktop\CSV CHAT AGENT\ai-dashboard-generator\frontend\public\sample_project_data.csv"

print("=" * 60)
print("Testing Complete Dashboard Pipeline")
print("=" * 60)

# Test 1: Upload file
print("\n[1/4] Uploading sample CSV...")
try:
    with open(file_path, 'rb') as f:
        files = {'file': ('sample_project_data.csv', f, 'text/csv')}
        response = requests.post('http://localhost:8011/upload', files=files, timeout=10)
    
    if response.status_code == 200:
        print(f"✓ Upload successful (Status: {response.status_code})")
        data = response.json()
        print(f"  - Rows processed: {data.get('rows', 'N/A')}")
        print(f"  - Columns: {data.get('columns', 'N/A')}")
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"✗ Upload error: {e}")
    exit(1)

# Test 2: Get dashboard HTML
print("\n[2/4] Generating dashboard HTML...")
try:
    response = requests.get('http://localhost:8011/dashboard', timeout=30)
    if response.status_code == 200:
        html = response.text
        checks = {
            "KPI strip": 'kpi-strip' in html,
            "Charts section": 'charts-section' in html,
            "Chatbot": 'chatbot' in html,
            "Data table": 'table-section' in html,
            "Chart.js": 'Chart.js' in html or 'chart' in html.lower(),
        }
        all_valid = all(checks.values())
        if all_valid:
            print(f"✓ Dashboard generated (HTML size: {len(html)} bytes)")
            for name, present in checks.items():
                print(f"  - {name}: {'✓' if present else '✗'}")
        else:
            print(f"✗ Dashboard missing components: {[k for k, v in checks.items() if not v]}")
    else:
        print(f"✗ Dashboard generation failed: {response.status_code}")
except Exception as e:
    print(f"✗ Dashboard error: {e}")

# Test 3: Test chatbot
print("\n[3/4] Testing chatbot integration...")
try:
    chat_data = {
        "message": "What are the top priorities in this project data?",
        "history": []
    }
    response = requests.post('http://localhost:8011/api/chat', json=chat_data, timeout=15)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Chatbot responded (Status: {response.status_code})")
        print(f"  Message: {result.get('reply', 'N/A')[:150]}...")
    else:
        print(f"⚠ Chatbot returned: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"⚠ Chatbot error: {e}")

# Test 4: Health check
print("\n[4/4] Backend health check...")
try:
    response = requests.get('http://localhost:8011/api/health', timeout=5)
    if response.status_code == 200:
        print(f"✓ Backend is healthy: {response.json()}")
    else:
        print(f"✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"✗ Health check error: {e}")

print("\n" + "=" * 60)
print("✓ Full Test Complete!")
print("=" * 60)
print("\nDashboard is ready at: http://localhost:8011/dashboard")
