#!/usr/bin/env python
"""
Quick verification script for OpenClaw + RAG setup.
Run this to validate the production architecture is correctly installed.
"""

import sys
from pathlib import Path

def check_structure():
    """Verify folder structure."""
    print("📁 Checking folder structure...")
    required_dirs = [
        "BACKEND/app/core",
        "BACKEND/app/db",
        "BACKEND/app/services",
        "BACKEND/app/routes",
        "BACKEND/app/models",
        "BACKEND/openclaw",
        "BACKEND/data/raw",
        "BACKEND/data/vector_store",
        "BACKEND/logs",
        "docker",
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (MISSING)")
            return False
    return True

def check_dependencies():
    """Check if all dependencies are installed."""
    print("\n📦 Checking dependencies...")
    try:
        import fastapi
        print("  ✅ fastapi")
    except ImportError:
        print("  ❌ fastapi (MISSING)")
        return False
    
    try:
        import chromadb
        print("  ✅ chromadb")
    except ImportError:
        print("  ❌ chromadb (MISSING)")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("  ✅ sentence-transformers")
    except ImportError:
        print("  ❌ sentence-transformers (MISSING)")
        return False
    
    try:
        import langchain
        print("  ✅ langchain")
    except ImportError:
        print("  ❌ langchain (MISSING)")
        return False
    
    try:
        import ollama
        print("  ✅ ollama")
    except ImportError:
        print("  ❌ ollama (MISSING)")
        return False
    
    return True

def check_configs():
    """Check configuration files."""
    print("\n⚙️  Checking configuration files...")
    required_files = [
        "BACKEND/.env",
        "BACKEND/openclaw/agent_config.yaml",
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (MISSING)")
            return False
    return True

def check_imports():
    """Check if modules can be imported."""
    print("\n🔌 Checking module imports...")
    try:
        from app.core.config import settings
        print("  ✅ app.core.config")
    except Exception as e:
        print(f"  ❌ app.core.config: {e}")
        return False
    
    try:
        from app.db.vector_store import get_vector_store
        print("  ✅ app.db.vector_store")
    except Exception as e:
        print(f"  ❌ app.db.vector_store: {e}")
        return False
    
    try:
        from app.services.embeddings import get_embeddings_service
        print("  ✅ app.services.embeddings")
    except Exception as e:
        print(f"  ❌ app.services.embeddings: {e}")
        return False
    
    try:
        from app.services.rag_pipeline import get_rag_pipeline
        print("  ✅ app.services.rag_pipeline")
    except Exception as e:
        print(f"  ❌ app.services.rag_pipeline: {e}")
        return False
    
    try:
        from app.services.openclaw_agent import get_agent
        print("  ✅ app.services.openclaw_agent")
    except Exception as e:
        print(f"  ❌ app.services.openclaw_agent: {e}")
        return False
    
    return True

def main():
    """Run all checks."""
    print("=" * 60)
    print("🚀 OpenClaw + RAG Architecture Verification")
    print("=" * 60)
    
    checks = [
        ("Folder Structure", check_structure),
        ("Dependencies", check_dependencies),
        ("Configuration Files", check_configs),
        ("Module Imports", check_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! Ready to start.")
        print("\nNext steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Start backend: python -m uvicorn app.main:app --reload")
        print("3. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
