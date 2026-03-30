# 🚀 Project Roadmap: Intelligent Autonomous Mobile Robot (AMR)

> **Current Milestone**: Autonomous Navigation & Mapping
> **Goal**: Transform Aurora from a teleoperated platform into a fully autonomous exploration, detection, and navigation system that can map unknown environments, detect and remember objects, and navigate intelligently — all without human intervention.

---

## 🎯 Engineering Objectives
1. **Explore Unknown Spaces:** Perform real-time SLAM & dynamic updates.
2. **Scene Understanding:** Combine Lidar & OAK-D Lite Vision to identify free space and objects.
3. **Natural Language Interaction:** Command parsing ("Go to kitchen", "Follow me") and conversational personality.
4. **Persistent Memory:** Remember semantic locations ("charging station") and object-level memory ("chair near table").
5. **Real-time Safe:** Navigation and obstacle avoidance MUST NOT bottleneck on LLM latency.
6. **Mandatory Base:** Extend `arjuna2_ws`. Reuse existing motor control, odometry, and Lidar drivers.

---

## ✅ Completed Phases (Previous Milestone: Intelligent AMR)

### Phase 1: Hardware Foundation & Low-Level Control ✅
**Objective:** Establish the reliable base ROS2 hardware stack.
- **Hardware:** Jetson Orin Nano, Waveshare Motor Driver, BNO055 IMU.
- Ported existing `arjuna2_ws`, integrated motor control, encoder ticks, IMU, `twist_mux`.

### Phase 2: Dynamic Mapping & Short-Range Perception ✅
**Objective:** Real-time Lidar SLAM for unknown environments and immediate obstacle avoidance.
- **Hardware:** RPLidar C1, ESP32 Ultrasonic Array.
- RTAB-Map SLAM, Nav2 basic setup, ultrasonic range_layer.

### Phase 3: The Intelligence Bridge (Local AI Base) ✅
**Objective:** Hardware-to-AI translation and basic natural language processing.
- `ai_bridge_node`, local LLM (Ollama), Whisper STT.

### Phase 4: Visual SLAM & Scene Understanding (OAK-D) ✅
**Objective:** Integrate OAK-D Pro with hybrid SLAM.
- DepthAI driver, depth+RGB streaming, camera IMU, RTAB-Map hybrid SLAM.

### Phase 8: Embodied AI Companion ✅
- Velocity clamping, real-time obstacle reflexes, conversational NLU.

### Phase 9: System Reliability & Build Pipeline ✅
- `find_packages` exclusions, unified `aurora_env` shebang patching.

### Phase 10: Interactive Terminal Dashboard (TUI) ✅
- Status monitor, log silencing, 16GB NVMe swap, 8-sector Lidar spatial awareness.

---

## 📅 Current Milestone: Autonomous Navigation & Mapping

### Must-Haves
- [ ] Robot autonomously explores unknown environments (frontier exploration)
- [ ] Real-time object detection on OAK-D VPU (zero Jetson CPU cost)
- [ ] Persistent map storage (survives restarts)
- [ ] Semantic spatial database (remember where objects are)
- [ ] Proper path planning (Smac2D, not NavFn) with tuned controller
- [ ] Depth camera integrated into costmaps for obstacle avoidance
- [ ] Single launch command for full autonomous operation

### Nice-to-Haves
- [ ] Patrol mode (revisit areas after exploration complete)
- [ ] Multi-floor map support
- [ ] Dynamic obstacle tracking with prediction

---

### Phase 1: Nav2 Foundation Overhaul
**Status**: ✅ Complete
**Objective**: Replace the weak NavFn planner with Smac2D, tune RPP controller for Aurora's chassis, fix the critical RTAB-Map/Nav2 TF conflict, and harden recovery behaviors.

**Key deliverables:**
- Smac2D planner configuration
- RPP controller tuned for indoor differential drive (0.22m radius)
- AMCL disabled in SLAM mode (RTAB-Map owns map→odom)
- map_server disabled when SLAM is providing /map
- Recovery behaviors with proper timeouts

---

### Phase 2: Sensor-Enhanced Costmaps
**Status**: ✅ Complete
**Objective**: Add depth camera data to Nav2 costmaps using `depth_image_proc` (CPU-efficient), creating a multi-sensor obstacle detection layer.

**Key deliverables:**
- `depth_image_proc` point_cloud_xyz node integration
- Depth camera obstacle layer in local + global costmaps
- Verified obstacle detection from camera (glass, thin objects), lidar, and ultrasonics
- Costmap tuning for all three sensor types working together

---

### Phase 3: Map Persistence & Management
**Status**: ✅ Complete
**Objective**: Make maps survive restarts by persisting RTAB-Map database and providing map save/load services.

**Key deliverables:**
- Persistent RTAB-Map database at `~/.aurora/rtabmap.db`
- `delete_db_on_start` launch argument for clean starts
- Map saver node: PGM + YAML export for Nav2
- Auto-save every 5 minutes + manual save service
- `SaveMap.srv` service definition in `aurora_msgs`

---

### Phase 4: Object Detection Pipeline
**Status**: ⬜ Not Started
**Objective**: Run real-time object detection on the OAK-D's Movidius VPU using MobileNet-SSD, publishing 3D object positions.

**Key deliverables:**
- MobileNet-SSD neural network in DepthAI pipeline (VPU inference)
- `Detection2DArray` publishing on `/camera/detections`
- TF-correct 3D position computation (using detection timestamp)
- RViz visualization markers for detected objects
- Confidence filtering and deduplication

---

### Phase 5: Semantic Spatial Database
**Status**: ⬜ Not Started
**Objective**: Build a persistent spatial memory system that stores where objects were detected in map coordinates.

**Key deliverables:**
- SQLite-backed object database at `~/.aurora/spatial_objects.db`
- TF-correct map-frame coordinate projection with timestamp-based lookup
- `QueryObject.srv` and `ListObjects.srv` services
- Exponential moving average for position updates
- Persistent RViz markers on `/semantic_map`

---

### Phase 6: Autonomous Frontier Exploration
**Status**: ⬜ Not Started
**Objective**: Build the autonomous decision-making brain that identifies unexplored areas and drives to them.

**Key deliverables:**
- Frontier detection via BFS on OccupancyGrid
- State machine: `IDLE → EXPLORING → NAVIGATING → RECOVERY → COMPLETE`
- Stale map guard (skip if map timestamp too old)
- Goal timeout (30s) + retry limit (3) + distance threshold + blacklist
- Completion conditions: no frontiers OR coverage >95% OR time limit
- Debug topics: `/exploration_state`, `/current_goal`, `/failed_frontiers`

---

### Phase 7: Unified Autonomous Launch & Integration
**Status**: ⬜ Not Started
**Objective**: Bring everything together into a single launch command and validate end-to-end autonomous operation.

**Key deliverables:**
- `autonomous.launch.py` — one command for full autonomy
- Integration testing of all components
- RViz configuration for autonomous visualization
- End-to-end validation: robot explores, detects, saves map, remembers objects

---

## 🔮 Future Milestones (Backlog)

### Phase 5 (Original): Semantic Mapping & Persistent Memory
- ChromaDB Lite / Spatial Registry for named room storage
- Event Memory for last-seen object tracking
- LangGraph retrieval integration

### Phase 6 (Original): Proactive Interaction & Voice (TTS)
- Piper/espeak-ng TTS, proactive awareness, Follow Me mode

### Phase 7 (Original): Optimization & Vitals Monitoring
- Battery/thermal monitoring, GPU/CPU profiling

### Phase 11: Multi-Machine Offloading & GPU Optimization
- Network sync, brain offload, hybrid perception, latency mastery
