#!/bin/bash

# 🚀 Aurora Multi-Machine Network Setup
# This script configures the ROS 2 environment for Jetson <-> Laptop communication.

export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

echo "📢 ROS_DOMAIN_ID set to $ROS_DOMAIN_ID"
echo "📢 RMW_IMPLEMENTATION set to $RMW_IMPLEMENTATION"

# Function to check connectivity
check_laptop() {
    if [ -z "$LAPTOP_IP" ]; then
        echo "❌ Error: LAPTOP_IP environment variable is not set."
        echo "Example: export LAPTOP_IP=192.168.1.10"
        return 1
    fi

    echo "🔍 Pinging Laptop at $LAPTOP_IP..."
    if ping -c 1 $LAPTOP_IP > /dev/null 2>&1; then
        echo "✅ Laptop is reachable!"
    else
        echo "❌ Laptop is UNREACHABLE. Check ethernet/cables."
        return 1
    fi
}

if [ "$1" == "--check" ]; then
    check_laptop
fi

echo "✨ Network environment ready."
echo "💡 Source this script: 'source scripts/setup_network.sh'"
