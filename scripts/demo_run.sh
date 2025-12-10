#!/bin/bash
#
# Demo run script for CrowdStrike AI Pipeline Health Monitor
# This script demonstrates the full monitoring and remediation flow
#

set -e

API_BASE="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo "================================================"
echo "🚀 CrowdStrike AI Pipeline Health Monitor Demo"
echo "================================================"
echo ""

# Check if services are running
echo "🔍 Checking services..."
if ! curl -s "$API_BASE/health" > /dev/null 2>&1; then
    echo "❌ Backend not running. Start with: docker-compose up"
    exit 1
fi
echo "✅ Backend is running"

# Show initial state
echo ""
echo "📊 Initial Health Check Status:"
curl -s "$API_BASE/healthchecks/run-all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"  Total: {data['total']}, Passed: {data['passed']}, Failed: {data['failed']}\")
"

# Wait for user
echo ""
echo "Press Enter to inject a latency failure..."
read

# Inject failure
echo ""
echo "💉 Injecting high latency failure..."
python3 scripts/inject_failure.py --type latency --severity high

# Run checks to detect failure
echo ""
echo "🔍 Running health checks to detect failure..."
curl -s -X POST "$API_BASE/healthchecks/run-all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('📊 Check Results:')
for r in data['results']:
    status = '✅' if r['passed'] else '❌'
    print(f\"  {status} {r['check_name']}\")
"

# Show the dashboard
echo ""
echo "🌐 Open the dashboard to see the failure:"
echo "   $FRONTEND_URL"
echo ""
echo "Press Enter to trigger auto-remediation..."
read

# Clear the failure (simulating remediation)
echo ""
echo "🔧 Executing remediation (restart_service)..."
python3 scripts/inject_failure.py --clear

# Verify fix
echo ""
echo "✅ Running verification checks..."
curl -s -X POST "$API_BASE/healthchecks/run-all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('📊 Verification Results:')
for r in data['results']:
    status = '✅' if r['passed'] else '❌'
    print(f\"  {status} {r['check_name']}\")
print()
print(f\"🎉 All checks passing: {data['passed'] == data['total']}\")
"

echo ""
echo "================================================"
echo "✨ Demo Complete!"
echo "================================================"
echo ""
echo "Key demo points:"
echo "  1. Health checks detected the latency issue"
echo "  2. Auto-remediation could be triggered"
echo "  3. Verification confirmed the fix"
echo ""
echo "Try other failure types:"
echo "  python3 scripts/inject_failure.py --type correctness --severity medium"
echo "  python3 scripts/inject_failure.py --type drift"
echo "  python3 scripts/inject_failure.py --type error --severity high"
