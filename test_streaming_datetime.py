#!/usr/bin/env python3
"""
Test script to validate streaming endpoint with actual datetime columns.
"""
import requests
import json
import time
import pandas as pd
import io

BASE_URL = "http://localhost:8000"

def upload_test_file_with_datetime():
    """Upload test CSV with actual datetime column."""
    # Create a DataFrame with datetime
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=4),
        'value': [100, 150, 120, 200],
        'category': ['A', 'B', 'A', 'B']
    })
    
    # Save to CSV string
    csv_string = df.to_csv(index=False)
    
    files = {'files': ('test_datetime.csv', csv_string, 'text/csv')}
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    print(f"Upload status: {response.status_code}")
    upload_data = response.json()
    print(f"Upload response: {json.dumps(upload_data, indent=2)}")
    return "test_datetime.csv"

def test_streaming_table(filename):
    """Test streaming endpoint with table request."""
    print(f"\nTesting streaming endpoint with file: {filename}")
    
    payload = {
        "message": "Show me the data as a table",
        "active_file": filename,
        "conversation_history": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        stream=True
    )
    
    print(f"Stream status: {response.status_code}")
    print("Stream events:")
    
    error_count = 0
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix
                try:
                    event = json.loads(data_str)
                    print(f"  Event: {event.get('status')} - {event.get('message', '')}")
                    
                    # Check for data that might have Timestamps
                    if event.get('status') == 'table':
                        print(f"    Table data received: {len(event.get('data', []))} rows")
                        if event.get('data'):
                            print(f"    First row: {event['data'][0]}")
                            print(f"    Column types: {[type(v).__name__ for v in event['data'][0].values()]}")
                    elif event.get('status') == 'error':
                        error_count += 1
                        print(f"    ERROR: {event.get('message')}")
                except json.JSONDecodeError as e:
                    print(f"  (Error parsing JSON: {e})")
                    error_count += 1
    
    return error_count == 0

if __name__ == "__main__":
    # Upload test file
    filename = upload_test_file_with_datetime()
    
    time.sleep(1)  # Wait for file to be processed
    
    # Test streaming
    success = test_streaming_table(filename)
    
    if success:
        print("\n✓ Test PASSED - JSON serialization working correctly!")
    else:
        print("\n✗ Test FAILED - Errors occurred during streaming")
