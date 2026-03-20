# SPEC.md [FINALIZED] — Project Specification (Embodied AI Agent)

## Vision
Build an **Embodied General-Purpose AI Agent** that acts as both a physical autonomous mobile robot and a digital assistant. The system features emotional voice interaction, OS-level task execution, and persistent contextual memory, running locally on a Jetson Orin Nano 8GB.

## Goals
1. **Memory Hardening**: Achieve system stability on 8GB RAM via 16GB NVMe swap.
2. **Physical Autonomy**: SLAM, Nav2, and obstacle avoidance using `arjuna2_ws` hardware layer + `twist_mux`.
3. **Cognitive Intelligence**: High-level reasoning using **LangGraph** and an **ai_bridge_node** for ROS2 synchronization.
4. **Emotional Interaction**: Human-like speech using TensorRT-optimized Whisper (STT) and XTTS v2 (TTS).
5. **Digital Agency**: OS-level control (File system, Web, Productivity) via shell/python tool execution.

## Constraints & Targets
- **Memory**: Peak physical RAM usage < 7GB.
- **Latency**: Navigation must be real-time; Voice response < 1.5s (STT + LLM + TTS).
- **Hardware**: Shared 8GB RAM requires aggressive optimization (NVMe Swap enabled).

## Success Criteria
- [ ] System remains stable with all components active (Memory < 100% with Swap).
- [ ] Robot executes a cross-domain task (e.g., "Find recipe on web and go to the kitchen").
- [ ] Voice interaction reflects emotional tone based on context.
