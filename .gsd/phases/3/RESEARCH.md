# Research: Phase 3 — Intelligence Layer

## LLM: Ollama on Jetson Orin Nano
- **Capability**: Officially supported with GPU acceleration.
- **Model Choice**: 3B models (e.g., `llama3:3b`, `phi3`) are optimal. An 8B model is possible but consumes ~5-6GB of the 8GB total, leaving little for Nav2/SLAM.
- **Optimization**: Use `int4` or `int8` quantization. `llama.cpp` backend is used by default.

## STT: Faster-Whisper
- **Why**: 4x faster than OpenAI Whisper, optimized for C++ (CTranslate2).
- **Quantization**: `int8` on CUDA is critical for memory.
- **Latency**: Audio chunks of 1-3s are needed for "near real-time" feel.

## Integration: LangGraph + ROS2
- **Pattern**: `ai_bridge_node` using `asyncio`.
- **Logic**:
    - `asyncio` event loop running `rclpy.spin_once()` periodically.
    - LangGraph `.ainvoke()` for stateful reasoning.
    - ROS2 Sub: `/voice_command` (from Whisper node or audio node).
    - ROS2 Pub: `/ai_vel` (priority 5 in `twist_mux`), `/ai_speech`.

## Memory Management (8GB RAM)
- **ZRAM**: Mandatory (4GB-8GB ZRAM).
- **NVMe Swap**: Mandatory (8GB+).
- **Concurrent Load**:
    - Nav2/SLAM: ~1.2GB
    - Ollama (3B): ~2.5GB
    - Whisper (Base): ~0.8GB
    - Total: ~4.5GB (well within 8GB, but headroom needed for spikes).
