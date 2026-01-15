#!/bin/bash
# Auto-run full system test

set -e

cd /Users/wangjunhui/playcode/zen_ai

echo "Installing dependencies..."
pip3 install -q aiohttp 2>/dev/null || pip install -q aiohttp 2>/dev/null || true

echo "Running full system test..."
python3 tests/full_system_test.py data/test_inputs.jsonl \
  --output reports/full_test_report.json \
  --verbose

echo "Test completed!"
