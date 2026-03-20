# RESEARCH.md — Project Research & Recommendations (Finalized)

## 1. Hardware & Control Architecture
-   **Topic Remapping**: The `robot_localization` (EKF) node must remap its output from `/odometry/filtered` to the standard `/odom` topic. This ensures Nav2 has a direct, fused source of truth without drunk behavior.
-   **Velocity Arbitration (`twist_mux`)**: Mandatory. All velocity sources (Nav2, AI, Manual, Safety) must pipe through a `twist_mux` node.
    -   **Priorities**:
        1. Safety/Obstacle Stop: 100
        2. Teleop (Manual): 50
        3. Nav2 (Autonomous): 10
        4. AI (Semantic Commands): 5
    -   **Output**: The multiplexer outputs to `/cmd_vel` which the `aurora_motor_driver` subscribes to.

## 2. Sensor Integration Strategy
-   **Ultrasonic (US)**: Convert `ultrasonic_distances` (Float32MultiArray) to `sensor_msgs/Range` or `sensor_msgs/LaserScan` (simulated).
    -   *Recommendation*: `Range` sensorsintegrated into Nav2 costmaps as `range` layers for near-field obstacle inflation.
-   **OAK-D Lite**: Implement **On-Device Inference**.
    -   *Model*: YOLOv8n or MobileNet-SSD running on the OAK's Myriad X VPU.
    -   *Rationale*: Frees up Jetson Orin Nano GPU/CPU for the high-level LLM and heavy Nav2 calculations.

## 3. High-Level AI Layer (Intelligence)
-   **Decoupled Control Loop**:
    -   **Real-Time Layer**: ROS2 Nav2 + SLAM + EKF (Safety/Motion).
    -   **Strategic Layer**: LLM (Ollama) as a "Goal Dispatcher".
    -   *Flow*: `User -> LLM -> Semantic Resolve -> Nav2 Goal (Action)`.
-   **Behavioral State Machine**: Use a Behavior Tree (Nav2 native) or a lightweight State Machine (e.g., SMPY) to manage robot modes (IDLE, NAVIGATING, FOLLOWING, ERROR).

## 4. Semantic Mapping & Memory
-   **Storage Strategy**: Store labeled poses in `.gsd/maps/semantic_tags.yaml`.
-   **Format**:
    ```yaml
    kitchen:
      position: {x: 1.2, y: 3.4, z: 0.0}
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    ```
-   **Update Protocol**: Provide a CLI service to "Tag Current Pose" during manual mapping.

## Final Decision Summary
1.  **EKF Output**: Remapped to `/odom`.
2.  **Motion Control**: `twist_mux` installed and configured.
3.  **Vision**: On-device inference enforced.
4.  **AI**: Decoupled from real-time loop; Goal-oriented only.
5.  **Behavior**: Nav2 Behavior Tree customized for AI triggers.
