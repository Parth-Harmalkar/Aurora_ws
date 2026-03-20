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

### Phase 4: Visual SLAM & Scene Understanding (The Camera) 🚧
**Objective:** Add rich 3D vision and depth to enable object recognition and feature-rich localization.
- **Hardware:** OAK-D Lite (DepthAI).
- **Tasks:**
  - Integrate OAK-D Lite ROS2 drivers into the stack.
  - Enable onboard VPU inference (Object Detection / Scene Understanding).
  - Combine Lidar SLAM with Visual SLAM for robust localization under changing layouts.
  - Feed object classifications (camera spatial inputs) directly into the ROS2 framework for the AI reasoning layer to perceive ("What do you see?").

### Phase 5: Semantic Mapping & Persistent Memory
**Objective:** Long-term episodic and spatial memory enabling the robot to understand *what* a location is.
- **Technology:** ChromaDB (Local Vector Database).
- **Tasks:**
  - Store interaction history and spatial map coordinates persistently.
  - Enable explicit spatial learning ("This is the kitchen", "This is the charging station").
  - Enable object-level spatial memory by remembering the last Nav2 coordinate where an object was seen by the OAK-D Lite.
  - Retrieve Nav2 waypoints dynamically from semantic NLP requests ("Go to the couch").

### Phase 6: Autonomous Personality & Follower Interactions
**Objective:** True companion behaviors and proactive AI presence.
- **Tasks:**
  - Implement Text-to-Speech (TTS) for natural, conversational audio responses.
  - Develop a semantic "Follow Me" capability: Combine OAK-D Lite person-tracking bounding boxes with Nav2 dynamic waypoints to chase a human safely.
  - Evolve the LangGraph reasoner into a continuous background loop to act proactively (e.g. initiate conversation if battery is low), maintaining a consistent behavior style/personality.

### Phase 7: Optimization & Real-Time Safety Guarantee
**Objective:** Finalize the 8GB Jetson constraint limits.
- **Tasks:**
  - Guarantee real-time safe execution: Ensure Nav2 and motor controllers are strictly isolated from LLM latency drops.
  - Profile GPU/CPU load to balance OAK-D inference, Lidar SLAM, and Ollama reasoning simultaneously.
  - Final stress testing across dynamic, completely unmapped environments.
