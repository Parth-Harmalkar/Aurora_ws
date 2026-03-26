#!/bin/bash

# 💻 Aurora Laptop Setup Script (GTX 1650)
# Run this on your laptop to prepare for AI offloading.

echo "📦 Installing Python dependencies..."
pip install faster-whisper sounddevice numpy scipy rclpy

echo "🔧 ROS 2 Humble Check:"
if [ -f /opt/ros/humble/setup.bash ]; then
    echo "✅ ROS 2 Humble found."
else
    echo "❌ ROS 2 Humble NOT FOUND. Please install it first."
    exit 1
fi

echo "🚀 To start offloading, follow these steps IN ORDER:"
echo ""
echo "1. Set Network Environment:"
echo "   export ROS_DOMAIN_ID=42"
echo "   export RMW_IMPLEMENTATION=rmw_fastrtps_cpp"
echo ""
echo "2. Start Ollama with remote access:"
echo "   export OLLAMA_HOST=0.0.0.0"
echo "   ollama serve"
echo ""
echo "3. Run the Remote Whisper Node (this machine):"
echo "   # In a new terminal (after sourcing ROS 2 and your workspace):"
echo "   ros2 run aurora_ai_bridge whisper_node --ros-args -p mode:=consumer"
echo ""
echo "------------------------------------------------"
echo "💡 IMPORTANT: On the Jetson, you must set:"
echo "   export LAPTOP_IP=$(hostname -I | awk '{print $1}')"
echo "   export AURORA_OLLAMA_URL=http://\$LAPTOP_IP:11434"
