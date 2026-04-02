#!/usr/bin/env python3
"""
Demonstrate the chatbot providing appropriate responses to different types of queries:
1. List/Filter queries -> Text responses with detailed descriptions
2. Analysis/Dashboard queries -> Charts with detailed explanations  
3. Statistics queries -> Detailed metrics and calculations
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def demonstrate_query(query, query_type):
    """Send a query and demonstrate the response."""
    print(f"\n{'='*80}")
    print(f"QUERY TYPE: {query_type}")
    print(f"USER ASKS: {query}")
    print('='*80)
    
    payload = {
        "message": query,
        "active_file": "payment_data.csv",
        "conversation_history": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        stream=True,
        timeout=60
    )
    
    intent_detected = None
    response_text = ""
    has_chart = False
    has_table = False
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                try:
                    event = json.loads(line_str[6:])
                    status = event.get('status')
                    
                    if status == 'table':
                        has_table = True
                        rows = event.get('data', [])
                        print(f"\n[RESPONSE TYPE: TABLE]")
                        print(f"Showing {len(rows)} records...")
                        if rows:
                            print(f"Sample record: {rows[0]}")
                    elif status == 'chart':
                        has_chart = True
                        config = event.get('config', {})
                        print(f"\n[RESPONSE TYPE: CHART]")
                        print(f"Chart type: {config.get('type')}")
                        print(f"X-axis: {config.get('xKey')} | Y-axis: {config.get('yKey')}")
                    elif status == 'token':
                        response_text += event.get('token', '')
                    elif status == 'classifying':
                        print(f"\n[Processing] {event.get('message')}")
                    elif status == 'loading':
                        print(f"[{event.get('step')}] {event.get('message')}")
                    elif status == 'generating':
                        print(f"[{event.get('step')}] {event.get('message')}")
                except:
                    pass
    
    if response_text:
        print(f"\n[RESPONSE TEXT]")
        print(f"{response_text[:400]}..." if len(response_text) > 400 else response_text)
    
    if has_chart:
        print("\n✓ SUCCESS: Chart visualization provided with detailed explanation")
    elif has_table:
        print("\n✓ SUCCESS: Table data provided with detailed description")  
    elif response_text:
        print("\n✓ SUCCESS: Text response with detailed information")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CSV CHAT AGENT - RESPONSE DEMONSTRATION")
    print("="*80)
    
    time.sleep(1)
    
    # Test 1: List/Filter Query (should return CHAT with description)
    demonstrate_query(
        "Give me the list of customers who have payment through HDFC bank",
        "LIST/FILTER QUERY"
    )
    
    time.sleep(2)
    
    # Test 2: Analysis Query (should return CHART with explanation)
    demonstrate_query(
        "Show me how payment amounts are distributed across different banks",
        "ANALYSIS QUERY"
    )
    
    time.sleep(2)
    
    # Test 3: Statistics Query (should return detailed metrics)
    demonstrate_query(
        "What is the total amount and average payment value across all transactions?",
        "STATISTICS QUERY"
    )
    
    time.sleep(2)
    
    # Test 4: Dashboard Query (should return CHART)
    demonstrate_query(
        "Analyze the payment trends - show me a dashboard visualization",
        "DASHBOARD QUERY"
    )
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
