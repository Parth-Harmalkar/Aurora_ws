# Phase 2 Research: Mapping & Short-Range Perception

## 1. SLAM Toolbox (Async Mode)
For the Jetson Orin Nano 8GB, **Asynchronous mode** is highly recommended for real-time operation.
- **Key Parameters**:
    - `mode: async`
    - `use_scan_matching: true`
    - `minimum_travel_distance: 0.1`
    - `minimum_travel_heading: 0.1`
    - `map_update_interval: 5.0` (Reduce frequency to save CPU/Memory)
    - `resolution: 0.05`

## 2. Navigation2 (Low RAM Optimization)
To keep memory usage under 1GB:
- **Use Composition**: Run all Nav2 servers in a single process (`use_composition: true`).
- **Costmap Layers**:
    - Static Layer (Map)
    - Obstacle Layer (Lidar + Ultrasonic Range)
    - Inflation Layer (Keep footprint simple)
- **Controller/Planner**: Use `RPP` (Regulated Pure Pursuit) or `DWB` with minimal plugins.

## 3. Short-Range Perception (Ultrasonic)
- **Bridge**: Convert `Float32MultiArray` to `sensor_msgs/Range`.
- **Nav2 Integration**: Add `RangeSensorLayer` to both Global and Local Costmaps.
- **FOV**: Set field of view and range min/max based on HC-SR04 specs (approx 30deg, 0.02m - 4.0m).

## 4. Hardware/Dependencies
- **Install**: `ros-humble-slam-toolbox`, `ros-humble-navigation2`, `ros-humble-nav2-bringup`.
- **System**: NVMe Swap (16GB) must be active.
