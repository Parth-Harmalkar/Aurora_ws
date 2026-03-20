# REQUIREMENTS.md (Embodied AI Agent)

## 0. Phase 0: Memory Hardening (MANDATORY)
| ID | Requirement | Detail | Status |
|----|-------------|--------|--------|
| REQ-00 | **NVMe Swap**: 16GB NVMe-based swap file initialized. | Fix 1 | Pending |

## 1. Digital & AI Agent Requirements
| ID | Requirement | Detail | Status |
|----|-------------|--------|--------|
| REQ-02 | **ai_bridge_node**: ROS2 Node to sync Robot State <-> LangGraph. | Fix 2 | Pending |
| REQ-03 | **LangGraph Agent**: State-machine logic for multi-domain tasks. | Tool | Pending |
| REQ-04 | **Digital Tools**: Shell, File System, and Playwright integration. | Tool | Pending |

## 2. Voice & Emotion Requirements
| ID | Requirement | Detail | Status |
|----|-------------|--------|--------|
| REQ-05 | **Whisper-TRT**: TensorRT-optimized STT for low latency. | Voice | Pending |
| REQ-06 | **XTTS Streaming**: Emotional speech with <1s latency. | Voice | Pending |

## 3. Robotics & Physical Requirements
| ID | Requirement | Detail | Status |
|----|-------------|--------|--------|
| REQ-07 | **Arjuna Core**: Port and verify ticks/odom/IMU/Lidar. | arjuna2 | Pending |
| REQ-08 | **twist_mux**: Velocity arbitration with priority layers. | Control | Pending |
| REQ-09 | **Nav2 range_layer**: Integrate US sensors for inflation. | Perception| Pending |
