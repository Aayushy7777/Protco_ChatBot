#!/usr/bin/env python3
"""
Test if agent.py imports correctly.
"""
import sys
sys.path.insert(0, "c:\\Users\\redqu\\OneDrive\\Desktop\\CSV CHAT AGENT\\BACKEND")

try:
    from agent import CSVChatAgent
    print("[OK] agent.py imported successfully")
    
    # Try to inspect the _classify method
    import inspect
    source = inspect.getsource(CSVChatAgent._classify)
    print("\n_classify method source (first 500 chars):")
    print(source[:500])
except Exception as e:
    print(f"[ERROR] Failed to import agent: {e}")
