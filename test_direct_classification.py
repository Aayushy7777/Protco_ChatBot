#!/usr/bin/env python3
"""
Direct test of classification logic without streaming.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

test_queries = [
    ("What is the total amount and average payment value?", "STATS"),
   ("Show me a breakdown of payments by status", "TABLE"),
]

for query, expected in test_queries:
    payload = {
        "message": query,
        "active_file": "payment_data.csv",
        "conversation_history": []
    }
    
    # Get one quick event to see intent
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        stream=True,
        timeout=30
    )
   
    detected_intent = None
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            if line_str.startswith('data: '):
                try:
                    event = json.loads(line_str[6:])
                    if event.get('status') in ['table', 'chart']:
                        detected_intent = event['status'].upper()
                        break
                    elif event.get('status') == 'token':
                        break
                except:
                    pass
        if detected_intent:
            break
    
    if not detected_intent:
        detected_intent = 'CHAT'
    
    status = "[PASS]" if detected_intent == expected else "[FAIL]"
    print(f"{status} | Query: {query[:40]:<40} | Expected: {expected:<6} | Got: {detected_intent}")
