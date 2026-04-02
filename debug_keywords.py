#!/usr/bin/env python3
"""
Quick debug test for intent classification.
"""

# Test the keyword matching logic locally
def test_keyword_matching():
    messages = [
        ("What is the total amount and average payment value?", "STATS"),
        ("Show me statistics on payment status", "STATS"),
    ]
    
    for msg, expected in messages:
        m = msg.lower()
        
        stats_keywords = ["total ", "average ", "statistics", "how much", "how many", " sum ", 
                         " count ", "aggregate", "metrics", "median ", "maximum ", "minimum ",
                         "standard deviation", "variance"]
        
        matches = [kw for kw in stats_keywords if kw in m]
        
        print(f"\nQuery: {msg}")
        print(f"Expected: {expected}")
        print(f"Matching keywords: {matches}")
        print(f"Should match: {'YES' if matches else 'NO'}")

if __name__ == "__main__":
    test_keyword_matching()
