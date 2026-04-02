#!/usr/bin/env python3
"""
Test script to validate streaming endpoint with date columns.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def upload_test_file():
    """Upload test CSV with date column."""
    csv_content = """date,value,category
2024-01-01,100,A
2024-01-02,150,B
2024-01-03,120,A
2024-01-04,200,B
"""
    
    files = {'files': ('test_dates.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    print(f"Upload status: {response.status_code}")
    print(f"Upload response: {response.json()}")
    return "test_dates.csv"

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
                except json.JSONDecodeError as e:
                    print(f"  (Error parsing JSON: {e})")

if __name__ == "__main__":
    # Upload test file
    filename = upload_test_file()
    
    time.sleep(1)  # Wait for file to be processed
    
    # Test streaming
    test_streaming_table(filename)
    
    print("\nTest completed!")
