#!/bin/bash

# QA Multi-Agent System - Test Script
# Triggers a test execution

set -e

echo "🧪 Testing QA Multi-Agent System..."
echo ""

# Check if runner is up
if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "❌ Runner service is not running"
    echo "   Start the system first: ./scripts/start.sh"
    exit 1
fi

echo "✅ Runner service is healthy"
echo ""

# Trigger a test execution
echo "📬 Triggering QA pipeline..."
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "pull_request",
    "repo_url": "https://github.com/test/repo",
    "branch": "feature/test",
    "commit_sha": "abc123def456",
    "pull_request_id": "1",
    "author": "test_user"
  }')

echo "📥 Response:"
echo "$RESPONSE" | python3 -m json.tool || echo "$RESPONSE"
echo ""

# Extract execution_id
EXECUTION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['execution_id'])" 2>/dev/null || echo "")

if [ -n "$EXECUTION_ID" ]; then
    echo "✅ Pipeline triggered successfully!"
    echo "   Execution ID: $EXECUTION_ID"
    echo ""
    echo "⏳ Waiting for execution to complete (15 seconds)..."
    sleep 15
    echo ""

    echo "📊 Fetching results..."
    curl -s "http://localhost:8000/status/$EXECUTION_ID" | python3 -m json.tool
    echo ""

    echo "✅ Test complete!"
    echo ""
    echo "View full results:"
    echo "   curl http://localhost:8000/status/$EXECUTION_ID | jq"
else
    echo "❌ Failed to trigger pipeline"
    exit 1
fi
