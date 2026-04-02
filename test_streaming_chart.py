#!/usr/bin/env python3
"""
Test script to validate streaming endpoint with chart generation.
"""
import requests
import json
import time
import pandas as pd

BASE_URL = "http://localhost:8000"

def test_streaming_chart():
    """Test streaming endpoint with chart request (uses test_datetime.csv from previous test)."""
    filename = "test_datetime.csv"
    print(f"Testing streaming endpoint with chart request for file: {filename}")
    
    payload = {
        "message": "Create a line chart showing value over date",
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
    chart_received = False
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix
                try:
                    event = json.loads(data_str)
                    print(f"  Event: {event.get('status')} - {event.get('message', '')}")
                    
                    # Check for chart configuration
                    if event.get('status') == 'chart':
                        chart_received = True
                        config = event.get('config', {})
                        if config:
                            print(f"    Chart type: {config.get('type', 'unknown')}")
                            print(f"    Chart title: {config.get('title', config.get('option', {}).get('title', {}).get('text', 'N/A'))}")
                            # Try to serialize to verify it's JSON-safe
                            json.dumps(config)
                            print(f"    ✓ Chart config is JSON serializable")
                    elif event.get('status') == 'error':
                        error_count += 1
                        print(f"    ERROR: {event.get('message')}")
                except json.JSONDecodeError as e:
                    print(f"  (Error parsing JSON: {e})")
                    error_count += 1
    
    return error_count == 0 and chart_received

if __name__ == "__main__":
    time.sleep(1)
    success = test_streaming_chart()
    
    if success:
        print("\n✓ Chart Test PASSED - Chart config is JSON serializable!")
    else:
        print("\n✗ Chart Test FAILED - Chart generation or serialization error")
