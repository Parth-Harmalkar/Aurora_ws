# REQUIREMENTS.md

## Hardware Integration (Brownfield)
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-01 | Reuse `aurora_motor_driver` for `/cmd_vel` to motor command conversion. | SPEC Goal 4 | Pending |
| REQ-02 | Integrate `odometry` package to publish `/odom` from encoder/IMU fusion. | SPEC Goal 4 | Pending |
| REQ-03 | Ensure RPLidar C1 publishes 360° `LaserScan` on `/scan`. | SPEC Goal 4 | Pending |

## Navigation & SLAM
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-04 | Configure SLAM Toolbox in asynchronous mode for real-time mapping. | SPEC Goal 1 | Pending |
| REQ-05 | Implement Nav2 stack with Global/Local planners tuned for differential drive. | SPEC Goal 1 | Pending |
| REQ-06 | Provide a service to save and load static maps for localized navigation. | SPEC Goal 1 | Pending |

## Vision & Perception
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-07 | Integrate OAK-D Lite using `depthai_ros_driver` for RGB-D data. | SPEC Goal 3 | Pending |
| REQ-08 | Implement real-time object detection (e.g., YOLOv8) on OAK hardware. | SPEC Goal 3 | Pending |
| REQ-09 | Publish detected objects as persistent semantic landmarks in a local database. | SPEC Goal 3 | Pending |

## Intelligence Layer (AI)
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-10 | Run Ollama locally on Jetson Orin Nano with `llama3.2:3b` model. | SPEC Goal 2 | Pending |
| REQ-11 | Develop a ROS2 Intelligence Node to bridge LLM reasoning with Nav2 Actions. | SPEC Goal 2 | Pending |
| REQ-12 | Parse natural language commands into JSON-structured robot instructions. | SPEC Goal 2 | Pending |
