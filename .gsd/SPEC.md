# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision
Build an AI-powered Autonomous Mobile Robot (AMR) using ROS2 and local intelligence (Ollama) on a Jetson Orin Nano, capable of navigating autonomously and executing high-level semantic commands like "go to kitchen" or "follow a person".

## Goals
1. **Autonomous Navigation**: Implement SLAM and Nav2 using existing Lidar, IMU, and Odometry data.
2. **AI Intelligence Layer**: Integrate Ollama for local reasoning to translate natural language commands into robot actions.
3. **Vision Perception**: Integrate OAK-D Lite for object detection and scene understanding.
4. **Hardware Reuse**: Leverage existing `aurora_motor_driver`, `aurora_lidar`, and other hardware packages without modification.

## Non-Goals (Out of Scope)
- Re-implementing existing hardware drivers or low-level nodes.
- Custom mechanical design or hardware assembly.
- External cloud-based reasoning (priority is local AI on Jetson).

## Users
- Robotics developers/researchers looking for an intelligent, interactive mobile platform.

## Constraints
- **Hardware**: Jetson Orin Nano Super 8GB, OAK-D Lite, RPLidar, IMU.
- **Software**: ROS2, Ollama (Local AI), Nav2, SLAM Toolbox.
- **Timeline**: Rapid prototype for AI-navigation integration.

## Success Criteria
- [ ] Robot can generate a map of the environment using SLAM.
- [ ] Robot can navigate to a target pose using Nav2.
- [ ] AI Layer successfully parses a command (e.g., "go to [X]") and triggers the appropriate Nav2 goal.
- [ ] Vision system identifies at least 3 common household objects/scenes.
