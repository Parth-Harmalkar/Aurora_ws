# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0 — "Intelligent Navigator"

## Must-Haves (from SPEC)
- [ ] Autonomous Navigation (SLAM + Nav2)
- [ ] Local AI Reasoner (Ollama)
- [ ] Vision-based Perception (OAK-D Lite)
- [ ] Semantic Command Execution ("Go to X")

## Phases

### Phase 1: Foundation & Navigation
**Status**: ⬜ Not Started
**Objective**: Enable the robot to map its environment and navigate autonomously using Nav2.
**Deliverables**:
- SLAM Toolbox configuration for RPLidar + IMU + Odom.
- Nav2 launch configuration for autonomous path planning.
- Static map of the test environment.

### Phase 2: Vision & Perception
**Status**: ⬜ Not Started
**Objective**: Integrate the OAK-D Lite camera for real-time object detection and scene understanding.
**Deliverables**:
- OAK-D Lite ROS2 driver integration.
- Object detection node (YOLO or similar) running locally.
- Scene description/labeling module.

### Phase 3: Intelligence Layer (Ollama)
**Status**: ⬜ Not Started
**Objective**: Connect the robot to a local LLM (Ollama) to interpret natural language commands.
**Deliverables**:
- Ollama service running on Jetson Orin Nano.
- Command parser bridge (text/speech → Nav2 goal/Action).
- Reasoning engine for multi-step tasks.

### Phase 4: Semantic Navigation & Integration
**Status**: ⬜ Not Started
**Objective**: Bridge the gap between AI reasoning and physical robot motion.
**Deliverables**:
- Semantic map link (Location Label → Coordinates).
- "Follow a person" implementation using vision-based tracking.
- End-to-end integration test of "Go to [Location]".

### Phase 5: Refinement & Human-Robot Interaction
**Status**: ⬜ Not Started
**Objective**: Polish behaviors and improve the robot's "intelligence" feel.
**Deliverables**:
- Improved obstacle avoidance using vision.
- Basic voice/text feedback from robot.
- Final system performance audit on Jetson.
