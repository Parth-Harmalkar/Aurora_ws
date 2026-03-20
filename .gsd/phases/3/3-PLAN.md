---
phase: 3
plan: 3
wave: 2
---

# Plan 3.3: Reasoning Layer (LangGraph)

## Objective
Implement the stateful reasoning layer using LangGraph to allow the robot to handle multi-step instructions and contextual awareness.

## Context
- .gsd/SPEC.md
- .gsd/phases/3/RESEARCH.md
- aurora_ai_bridge/ai_bridge_node.py

## Tasks

<task type="auto">
  <name>Integrate LangGraph State Machine</name>
  <files>[ros2_ws/src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py]</files>
  <action>
    Define a LangGraph state machine with Nodes for:
    1. Input Parsing (Ollama)
    2. Tool Selection (Move, Stop, Status)
    3. Action Execution (Pub to ROS2)
    4. Response Generation (Ollama)
  </action>
  <verify>python3 -m aurora_ai_bridge.reasoning --test "move forward"</verify>
  <done>Graph resolves to successful action states for basic commands.</done>
</task>

<task type="auto">
  <name>Connect Bridge to Reasoning</name>
  <files>[ros2_ws/src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py]</files>
  <action>
    Update `ai_bridge_node.py` to invoke the LangGraph `.ainvoke()` when message arrives on `/voice_command`.
    Connect Graph Outputs directly to ROS2 Publishers (`/ai_vel`).
  </action>
  <verify>ros2 topic pub /voice_command std_msgs/msg/String "data: 'move forward'" -1</verify>
  <done>Command triggers the reasoning graph and results in a Twist message on `/ai_vel`.</done>
</task>

## Success Criteria
- [ ] LangGraph state machine implemented.
- [ ] Bidirectional flow (ROS2 -> LLM -> Graph -> ROS2 Action) verified.
- [ ] Latency for prompt-to-action is within acceptable 2-5s range.
