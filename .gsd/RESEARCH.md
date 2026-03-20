# RESEARCH.md — Project Research & Recommendations (Embodied AI Agent)

## 1. Memory Optimization (Jetson Orin Nano 8GB)
-   **Swap Strategy**: Disable ZRAM and allocate a **16GB NVMe-based swap file**. This provides a larger/faster safety net for LLM spikes.
-   **Lifecycle Management**: Use **Process Isolation** for memory-heavy AI components. Specifically, we can relaunch the `Whisper` or `XTTS` nodes as needed to ensure complete memory reclamation.
-   **KV Cache**: Tune Ollama's `num_ctx` to 2048 or 4096 max to keep the KV cache footprint small.

## 2. Intelligence Bridge (`ai_bridge_node`)
-   **Role**: A standard ROS2 Node that manages the LangGraph agent's inputs/outputs.
-   **Data Flow**:
    -   *Inputs*: Subscribes to `/scan`, `/odom`, `/imu/data`, `/oak/detections`, and `whisper/transcript`.
    -   *Outputs*: Dispatches goals to Nav2 (Action Client) and publishes status strings to the UI/Voice system.
-   **State Sync**: The bridge maintains a local JSON-based "World Model" that is updated by ROS2 topics and queried by the LangGraph agent during tool calls.

## 3. Tool Calling & Digital Agency
-   **Sandboxing**: Use Python `shlex` and `subprocess` for safe shell execution.
-   **Playwright**: Use in headless mode with `--no-sandbox` and `--disable-gpu` (if necessary) to save VRAM.
-   **Framework**: **LangGraph** provides the state management for multi-step tasks (e.g., "Find recipe -> Go to kitchen -> Read out loud").

## 4. Hardware Reference (arjuna2_ws)
-   **Base**: 0.28m | Radius: 0.04m | Ticks: 20475.0 | Motors: `/dev/ttyUSB2`.
-   **Safety**: `twist_mux` prioritized: `100: Emergency` > `50: Teleop` > `10: Nav2` > `5: AI`.
