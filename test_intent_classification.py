#!/usr/bin/env python3
"""
Test script to validate intent classification and response descriptions.
Demonstrates:
1. CHAT: List queries → text-only with proper descriptions
2. CHART: Analysis queries → detailed charts with explanations
3. TABLE: Raw data → table with descriptions
4. STATS: Metrics → detailed statistics
"""
import requests
import json
import time
import pandas as pd

BASE_URL = "http://localhost:8000"

def create_and_upload_test_data():
    """Create a test dataset with banking/payment data."""
    data = {
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005', 'C006', 'C007', 'C008'],
        'customer_name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry'],
        'bank': ['HDFC', 'ICICI', 'HDFC', 'SBI', 'HDFC', 'AXIS', 'HDFC', 'ICICI'],
        'amount': [5000, 8000, 6500, 3000, 9500, 4500, 7000, 5500],
        'date': pd.date_range('2024-01-01', periods=8),
        'status': ['Completed', 'Completed', 'Pending', 'Completed', 'Failed', 'Completed', 'Completed', 'Pending']
    }
    
    df = pd.DataFrame(data)
    csv_string = df.to_csv(index=False)
    
    files = {'files': ('payment_data.csv', csv_string, 'text/csv')}
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    if response.status_code == 200:
        print("[OK] Test data uploaded successfully")
        return True
    return False

def test_intent_and_response(query, expected_intent):
    """Test a query and verify the response type."""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"Expected Intent: {expected_intent}")
    print('='*70)
    
    payload = {
        "message": query,
        "active_file": "payment_data.csv",
        "conversation_history": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        stream=True
    )
    
    detected_intent = None
    response_data = {}
    answer = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                try:
                    event = json.loads(data_str)
                    
                    if event.get('status') == 'table':
                        detected_intent = 'TABLE'
                        response_data = {
                            'rows': len(event.get('data', [])),
                            'columns': event.get('columns', [])
                        }
                    elif event.get('status') == 'chart':
                        detected_intent = 'CHART'
                        config = event.get('config', {})
                        response_data = {
                            'chart_type': config.get('type'),
                            'x_axis': config.get('xKey'),
                            'y_axis': config.get('yKey')
                        }
                    elif event.get('status') == 'token':
                        answer += event.get('token', '')
                    elif event.get('status') == 'done':
                        if not detected_intent:
                            detected_intent = 'CHAT'
                except:
                    pass
    
    # Print results
    if not detected_intent:
        detected_intent = 'CHAT'
    
    print(f"\n[OK] Detected Intent: {detected_intent}")
    if response_data:
        print(f"  Response Details: {response_data}")
    
    print(f"\n[TEXT] Response Text ({len(answer)} chars):")
    print(f"  {answer[:150]}..." if len(answer) > 150 else f"  {answer}")
    
    # Validate
    if detected_intent == expected_intent:
        print(f"\n[PASS] Intent classification correct!")
    else:
        print(f"\n[FAIL] Expected {expected_intent} but got {detected_intent}")
    
    return detected_intent == expected_intent

if __name__ == "__main__":
    print("Starting Intent Classification and Response Description Tests...\n")
    
    # Step 1: Upload test data
    if not create_and_upload_test_data():
        print("[ERROR] Failed to upload test data")
        exit(1)
    
    time.sleep(2)
    
    # Test cases: (query, expected_intent)
    test_cases = [
        ("Give me the list of customers who have payment through HDFC bank", "CHAT"),
        ("Show me an analysis of payment distribution by bank", "CHART"),
        ("Display the raw payment records sorted by amount", "TABLE"),
        ("What is the total amount and average payment value?", "STATS"),
        ("Which customers made payments and their details", "CHAT"),
        ("Create a bar chart comparing amounts by bank", "CHART"),
        ("Show me statistics on payment status", "STATS"),
    ]
    
    results = []
    for query, expected_intent in test_cases:
        passed = test_intent_and_response(query, expected_intent)
        results.append((query[:50], expected_intent, passed))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    passed_count = sum(1 for _, _, p in results if p)
    total_count = len(results)
    
    for query, expected, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {query:<50} -> {expected}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    if passed_count == total_count:
        print("[OK] All tests passed!")
    else:
        print(f"[ERROR] {total_count - passed_count} tests failed")
