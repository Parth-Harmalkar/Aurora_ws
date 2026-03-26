---
phase: 8
plan: 1
wave: 1
---

# Plan 8.1: Safety Clamping & Motion Reasoning Fix

## Objective
Make the robot physically safe by hard-clamping all LLM velocity outputs and fixing the broken reasoning pipeline. This is the critical prerequisite before any NLU or personality work — a hallucinating LLM must never drive real motors at unsafe speeds.

## Context
- .gsd/ROADMAP.md
- src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py
- src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py

## Tasks

<task type="auto">
  <name>Hard-Clamp Velocity Outputs in execute_plan()</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</files>
  <action>
    In `execute_plan()`, after extracting `lx`, `az`, `duration` from the LLM plan dict:
    1. Clamp `lx` to `[-0.2, 0.2]` using `max(-0.2, min(0.2, lx))`
    2. Clamp `az` to `[-0.5, 0.5]` using `max(-0.5, min(0.5, az))`
    3. Clamp `duration` to `[0.0, 15.0]` (no infinite drives)
    4. Log a warning if any value was clamped (so we can see LLM hallucinations)
    - WHY: The LLM outputted `lx=1.20, az=3.40` which is 6x and 7x the safe limits
  </action>
  <verify>grep -n "clamp\|max.*min" src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</verify>
  <done>All velocity values are mathematically bounded before reaching the motors, regardless of LLM output</done>
</task>

<task type="auto">
  <name>Add Real-Time Safety Override During Execution</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</files>
  <action>
    In the `execute_plan()` while-loop that publishes Twist messages:
    1. Before each publish, check `self.sensor_state` for immediate obstacles
    2. If moving forward (`lx > 0`) and front Lidar < 0.3m OR any ultrasonic < 0.2m → emergency stop
    3. If moving backward (`lx < 0`) and back Lidar < 0.3m → emergency stop
    4. Log the override reason clearly
    - WHY: The LLM takes 12-18s to respond, during which the world changes. We need real-time reflexes independent of the LLM.
  </action>
  <verify>grep -n "emergency\|override\|safety" src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</verify>
  <done>Robot stops instantly when obstacles appear during execution, regardless of LLM plan duration</done>
</task>

<task type="auto">
  <name>Fix LLM Prompt Velocity Constraints</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</files>
  <action>
    Update the system_prompt to be much more explicit about velocity limits:
    1. Change max values: "linear_x: float between -0.2 and 0.2" and "angular_z: float between -0.5 and 0.5"
    2. Add explicit examples: {"linear_x": 0.15, "angular_z": 0.0, "duration": 3.0} for "move forward"
    3. Add duration reasoning: "duration should be proportional to the distance requested"
    - WHY: The 1B model needs very explicit boundaries with examples to stay within bounds
  </action>
  <verify>grep -n "0.2\|0.5\|linear_x" src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</verify>
  <done>LLM prompt contains explicit numeric bounds and at least 2 worked examples</done>
</task>

## Success Criteria
- [ ] Robot velocity never exceeds 0.2 m/s linear or 0.5 rad/s angular under any LLM output
- [ ] Robot emergency-stops if an obstacle appears < 0.3m during active movement
- [ ] LLM prompt contains explicit velocity bounds and examples
