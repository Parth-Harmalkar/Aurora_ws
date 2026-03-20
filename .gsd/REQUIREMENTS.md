# REQUIREMENTS.md (Finalized)

## Control & Arbitration
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-01 | **EKF Alignment**: `robot_localization` must publish directly to `/odom`. | Arch Fix 1 | Pending |
| REQ-02 | **Twist Mux**: Implement `twist_mux` for velocity arbitration (Nav2 vs AI vs Safety). | Arch Fix 2 | Pending |
| REQ-03 | **Motor Output**: `aurora_motor_driver` subscribes to the muxed `/cmd_vel`. | Arch Fix 2 | Pending |

## Sensor & Perception
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-04 | **US Conversion**: Node to convert I2C ultrasonic data to `sensor_msgs/Range`. | Arch Fix 3 | Pending |
| REQ-05 | **Costmap Integration**: Nav2 local costmap includes a `Range` layer for US data. | Arch Fix 3 | Pending |
| REQ-06 | **Edge AI**: OAK-D Lite performs on-device object detection (YOLOv8n). | Arch Fix 4 | Pending |

## Intelligence & Behavioral Layer
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-07 | **Asynchronous AI**: Ollama reasoning runs outside the real-time control loop. | Arch Fix 5 | Pending |
| REQ-11 | **Behavior Tree**: Extend Nav2 Behavior Tree to handle "AI-Triggered" goals. | Arch Fix 6 | Pending |
| REQ-12 | **Semantic Store**: Load/Save system for `semantic_tags.yaml` with a "tag" service. | Arch Fix 7 | Pending |

## Core Hardware (arjuna2_ws)
| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| REQ-08 | **Ticks**: Port `Arjuna_Ticks_Pub.py` (Topic: `left_ticks`, `right_ticks`). | arjuna2_ws | Pending |
| REQ-09 | **Odom Source**: Port `EKF_data_pub.cpp` for wheel-odometry generation. | arjuna2_ws | Pending |
| REQ-10 | **IMU/Lidar**: Verified driver launch with correctly mapped device paths. | arjuna2_ws | Pending |
