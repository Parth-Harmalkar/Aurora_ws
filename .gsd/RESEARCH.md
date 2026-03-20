# RESEARCH.md — Project Research & Recommendations

## 1. Nav2 + SLAM Integration
**Existing Source of Truth**: `/home/aurora/arjuna2_ws/src/odometry` (EKF_data_pub.cpp).
-   **Topic Alignment**:
    -   Odometry: `/odom` (nav_msgs/Odometry) published by `ekf_odom_pub` node.
    -   Lidar: `/scan` (sensor_msgs/LaserScan) published by `sllidar_node`.
    -   IMU: `/imu/data` (sensor_msgs/Imu) - confirm if `aurora_imu` or `ros-imu-bno055` is used.
-   **SLAM Choice**: **SLAM Toolbox (Asynchronous)**.
    -   *Rationale*: More robust than Gmapping for dynamic environments and provides better map-saving/loading as a service. Asynchronous mode prevents blocking Real-Time ROS2 threads on the Orin Nano.
-   **Tuning Strategy**:
    -   **DDS**: Switch to `Cyclone DDS` for better stability with high-bandwidth Lidar/Vision data.
    -   **Transforms**: Ensure `static_transform_publisher` covers `base_link` -> `laser` and `base_link` -> `imu`.

## 2. OAK-D Lite on Jetson Orin Nano
-   **Driver**: Use `depthai_ros_driver` (Component-based).
-   **Optimization**:
    -   **Resolution**: Set RGB/Depth to 400p/480p to minimize Jetson CPU/Bus load.
    -   **Hardware Acceleration**: Leverage DepthAI's internal VPU for edge inference (YOLOv8-node) to offload the Jetson GPU for Global LLM reasoning.
    -   **Transport**: Use `compressed` image transport if visualizing remotely, otherwise use intra-process for local perception nodes.

## 3. Ollama on Jetson Orin Nano (8GB)
-   **Feasibility**: High.
-   **Model Recommendations**:
    -   **Primary**: `Llama-3.2-3B` or `Phi-3-mini (3.8B)` (Quantized INT4).
    -   *Rationale*: 8GB is tight. A 3B model leaves ~5.5GB for ROS2/Navigation/Perception. An 8B model would consume ~6GB+, which is risky for real-time robotics.
-   **Storage**: Ensure models are stored on an NVMe SSD (boot drive or mount).
-   **Performance**: Expected 15-25 tokens/sec, sufficient for command reasoning.

## 4. ROS2 + AI Integration Architecture
-   **Proposed Pipeline**:
    `Human (Command) -> Whisper (Text-to-Speech, Optional) -> "Intelligence Node" -> Ollama (Reasoning) -> Nav2 Goal / Velocity Commands`
-   **Semantic Mapping**:
    -   Maintain a simple JSON lookup: `{"kitchen": [x, y, z, w], "door": [...]}`.
    -   The LLM will be given this context in its System Prompt to resolve "go to kitchen" into coordinates.
-   **Latency Strategy**:
    -   **Async reasoning**: The robot should NOT stop while thinking. The LLM should update/override goals asynchronously.
    -   **Local Bridge**: Use a Python-based bridge node using `ollama-python` library or `llama_ros`.

## Final Subsystem Decisions
1. **Move `odometry` package**: Transfer `odometry` from `arjuna2_ws` to `aurora_ws/ros2_ws/src`.
2. **Unified Launch**: Create `aurora_bringup` to launch hardware, then `aurora_nav` for SLAM/Nav2.
3. **Dedicated AI Package**: Create `aurora_ai` to handle Ollama communication and command dispatch.
