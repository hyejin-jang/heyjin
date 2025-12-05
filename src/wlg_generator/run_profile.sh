#!/bin/bash
# WLG Profile Test Runner
# Usage: ./run_profile.sh <profile_num> <capacity>
# Example: ./run_profile.sh 1 64TB

PROFILE_NUM=$1
CAPACITY=$2

if [ -z "$PROFILE_NUM" ] || [ -z "$CAPACITY" ]; then
    echo "Usage: ./run_profile.sh <profile_num> <capacity>"
    echo "Example: ./run_profile.sh 1 64TB"
    exit 1
fi

CONFIG_FILE="config/profile_${PROFILE_NUM}.json"
JOB_LIST="profile_${PROFILE_NUM}_${CAPACITY}_jobs.txt"

echo "=========================================="
echo "WLG Profile Test Runner"
echo "=========================================="
echo "Profile: $PROFILE_NUM"
echo "Capacity: $CAPACITY"
echo "Config: $CONFIG_FILE"
echo "=========================================="
echo ""

# Step 1: Generate FIO jobs
echo "📝 Step 1: Generating FIO jobs..."
python3 generator.py "$CONFIG_FILE" "$CAPACITY"

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate FIO jobs"
    exit 1
fi

echo "✅ FIO jobs generated"
echo ""

# Step 2: Run jobs
echo "🚀 Step 2: Running tests..."
echo "⚠️  This will take ${RUNTIME_HOURS:-168} hours"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

python3 orchestrator.py "$JOB_LIST"

if [ $? -ne 0 ]; then
    echo "❌ Test execution failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Test completed successfully"
echo "=========================================="
