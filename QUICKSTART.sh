#!/usr/bin/env bash
# QUICK START - CSV Chat Agent with 24-Chart Auto-Generation
# 
# This script starts both backend and frontend servers
# You'll need 2 terminals for this to work properly

echo "🚀 CSV Chat Agent - Quick Start Guide"
echo "======================================"
echo ""
echo "To start the complete system, open 2 terminals and run:"
echo ""
echo "TERMINAL 1 - Backend Server:"
echo "  $ cd /path/to/CSV\ CHAT\ AGENT"
echo "  $ .venv/Scripts/activate"
echo "  $ python BACKEND/main.py"
echo ""
echo "TERMINAL 2 - Frontend Server:"
echo "  $ cd /path/to/CSV\ CHAT\ AGENT/FRONTEND"
echo "  $ npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "USAGE:"
echo "  1. Click 'Upload CSV' button"
echo "  2. Select test_data_with_dates.csv (or any quarterly invoice CSV)"
echo "  3. Watch as 8-12 charts auto-generate automatically!"
echo "  4. Click '↻ Cycle' to switch between chart types"
echo "  5. Click '✕ Remove' to delete charts"
echo ""
echo "VERIFICATION:"
echo "  $ python test_charts_e2e.py"
echo ""
echo "For detailed docs, see: IMPLEMENTATION_SUMMARY.md"
