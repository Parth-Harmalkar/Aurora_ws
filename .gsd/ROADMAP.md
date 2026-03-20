# ROADMAP.md (Refined Architecture)

> **Current Phase**: Research (Phase 1 Refinement)
> **Goal**: 100% Reliable Autonomous Assistant on 8GB Memory

## Phases

### Phase 1: Foundation (Hardware + Navigation)
- Port `arjuna2_ws` drivers.
- **Add**: `twist_mux`, emergency stop layer, and odom remapping.
- **Goal**: Basic Teleop + Fused Odom.

### Phase 2: Mapping & Short-Range Perception
- Configure SLAM Toolbox (Async) & Nav2.
- **Add**: Ultrasonic-to-Range integration for short-range protection.
- **Goal**: Mapping an unknown environment and basic navigation.

### Phase 3: Intelligence Layer (Experimental)
- Implement **ai_bridge_node** (ROS2 <-> LangGraph).
- Integrate **Ollama (3B INT4)** for high-level reasoning.
- **Add**: Basic voice input (**Whisper**) + Text/Console response.
- **Optimization**: Memory profiling and ZRAM setup.

### Phase 4: OS-Level Agent (The Assistant)
- Tool wrappers for Shell, File System, and Python.
- Lightweight Browser agent (Playwright).
- **Goal**: Execute digital tasks via voice/chat.

### Phase 5: Voice & Emotion (The Personality)
- Add **Coqui XTTS v2** for emotional speech output.
- Implement emotion tagging based on intent/context.
- **Goal**: Human-like interaction with expressive tone.

### Phase 6: Memory & Context
- **ChromaDB** for interaction history and semantic spatial tags.
- Persistent location memory ("Go home", "Kitchen").

### Phase 7: Optimization & Stress Test
- GPU/CPU profiling.
- Node-level latency tracking.
- Memory stress testing (Maximum simultaneous load).
