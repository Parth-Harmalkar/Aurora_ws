# 🚀 Project Roadmap: Intelligent Autonomous Mobile Robot (AMR)

**North Star:** 
An intelligent mobile agent that perceives, maps, understands, remembers, and acts autonomously in dynamic environments without pre-loaded maps, running exclusively on a Jetson Orin Nano (8GB).

---

## 🎯 Engineering Objectives
1. **Explore Unknown Spaces:** Perform real-time SLAM & dynamic updates.
2. **Scene Understanding:** Combine Lidar & OAK-D Lite Vision to identify free space and objects.
3. **Natural Language Interaction:** Command parsing ("Go to kitchen", "Follow me") and conversational personality.
4. **Persistent Memory:** Remember semantic locations ("charging station") and object-level memory ("chair near table").
5. **Real-time Safe:** Navigation and obstacle avoidance MUST NOT bottleneck on LLM latency.
6. **Mandatory Base:** Extend `arjuna2_ws`. Reuse existing motor control, odometry, and Lidar drivers.

---

## 📅 Execution Phases

### Phase 1: Hardware Foundation & Low-Level Control ✅
**Objective:** Establish the reliable base ROS2 hardware stack.
- **Hardware:** Jetson Orin Nano, Waveshare Motor Driver, BNO055 IMU.
- **Tasks:**
  - Port existing `arjuna2_ws`.
  - Integrate motor control, encoder ticks, and IMU.
  - Implement `twist_mux` for velocity command arbitration.

### Phase 2: Dynamic Mapping & Short-Range Perception ✅
**Objective:** Real-time Lidar SLAM for unknown environments and immediate obstacle avoidance.
- **Hardware:** RPLidar C1, ESP32 Ultrasonic Array.
- **Tasks:**
  - Configure Async SLAM Toolbox for dynamic map updating without preloaded maps.
  - Implement Nav2 for autonomous navigation.
  - Integrate ultrasonic sensors as a Nav2 `range_layer` to detect low/invisible obstacles.
  - Handle moving obstacles and sensor noise via costmap inflations.

### Phase 3: The Intelligence Bridge (Local AI Base) ✅
**Objective:** Hardware-to-AI translation and basic natural language processing.
- **Hardware:** USB Microphone.
- **Tasks:**
  - Implement `ai_bridge_node` (ROS2 ↔ LangGraph).
  - Integrate local LLM (Ollama 3B-7B) for fast reasoning.
  - Deploy Whisper for local STT (Speech-to-Text) with robust VAD (Voice Activity Detection).
  - Convert high-level semantic intents ("Stop", "Turn left") into actionable `/cmd_vel` goals.

### ✅ Phase 4: Visual SLAM & Scene Understanding (OAK-D Lite)
- Integrate DepthAI tools for the OAK-D Lite camera. *(Completed)*
- Overlay Camera Vision / Depth Maps (RTAB-Map / Target Tracking) alongside Lidar. *(Completed)*
- Connect Semantic Object Detection natively to internal ROS topics. *(Completed)*
- **Hardware:** OAK-D Lite (DepthAI).
- **Tasks:**
  - Integrate OAK-D Lite ROS2 drivers into the stack.
  - Enable onboard VPU inference (Object Detection / Scene Understanding).
  - Combine Lidar SLAM with Visual SLAM for robust localization under changing layouts.
  - Feed object classifications (camera spatial inputs) directly into the ROS2 framework for the AI reasoning layer to perceive ("What do you see?").

### Phase 5: Semantic Mapping & Persistent Memory
**Objective:** Long-term episodic and spatial memory enabling the robot to understand *what* a location is.
- **Technology:** ChromaDB Lite / Spatial Registry.
- **Tasks:**
  - [NEW] Implement a persistent "Spatial Registry" to store coordinates for named rooms ("kitchen", "bedroom").
  - [NEW] Enable object-level "Event Memory" to remember where a specific object (person, bottle, chair) was last seen by the OAK-D.
  - Integrate retrieval into LangGraph so the AI can say "I last saw the bottle in the kitchen."

### Phase 6: Proactive Interaction & Voice (TTS)
**Objective:** Give Aurora a physical voice and a proactive personality.
- **Tasks:**
  - [NEW] **Voice Integration:** Add a local TTS node (Piper/espeak-ng) to convert `ai_status` text into audio.
  - [NEW] **Proactive Awareness:** Trigger spontaneous interactions when the OAK-D sees a person while the robot is idle ( greeting, perking up).
  - [NEW] **Follow Me:** Use person-tracking from OAK-D to actively follow the user.

### Phase 7: Optimization & "Vitals" Monitoring
**Objective:** Finalize the 8GB Jetson performance and add self-awareness of health.
- **Tasks:**
  - [NEW] **Vitals Node:** Monitor Battery Voltage and SoC Thermal status.
  - [NEW] **Self-Awareness:** Teach the AI to factor "energy levels" into its personality (e.g., getting "sleepy" when low battery).
  - Profile GPU/CPU load and ensure Nav2 has priority over LLM background tasks.

### Phase 8: Embodied AI Companion ✅
**Objective:** Basic conversational companion with safety reflexes.
- **Completed:** Velocity clamping, Real-time obstacle reflexes, Conversational NLU, Personality/Idle curiosity movements.

### Phase 9: System Reliability & Build Pipeline ✅
**Objective:** Fix technical debt and environment issues.
- **Completed:** `find_packages` exclusions, unified `aurora_env` shebang patching.

### Phase 10: Interactive Terminal Dashboard (TUI) ✅
**Objective:** Replace cluttered launch logs with a beautiful, live AI dashboard.
- **Completed:** Standalone `status_monitor` tool, Log silencing, 16GB NVMe swap strategy, 8-sector Lidar spatial awareness.

### Phase 11: Multi-Machine Offloading & GPU Optimization
**Objective:** Offload heavy AI tasks to a secondary PC to achieve sub-1s reasoning.
- **Tasks:**
  - [NEW] **Network Sync:** Configure `ROS_DOMAIN_ID` and multicast for Jetson-to-PC discovery.
  - [NEW] **Brain Offload:** Move `whisper_node` and `ollama` reasoning to a high-power PC.
  - [NEW] **Hybrid Perception:** Feed Jetson Lidar/Vision into the PC-based AI over the network.
  - [NEW] **Latency Mastery:** Restore large context (512+ tokens) with near-instant GPU response.
