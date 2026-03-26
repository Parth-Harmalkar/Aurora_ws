---
phase: 8
plan: 2
wave: 1
---

# Plan 8.2: Natural Language Understanding — From Commands to Conversation

## Objective
Transform the AI from requiring rigid robotic commands ("move forward 3 seconds") to understanding natural human speech ("come closer to me", "go check what's in the corner", "back up a little"). The robot should interpret *intent* and *context*, not parse keywords.

## Context
- .gsd/ROADMAP.md
- src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py
- src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py

## Tasks

<task type="auto">
  <name>Rewrite System Prompt for Conversational Intent Extraction</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</files>
  <action>
    Completely rewrite the `system_prompt` in `planner_node()`:
    1. Give the AI a clear identity: "You are Aurora, an intelligent robot companion"
    2. Define intent categories with examples:
       - APPROACH: "come here", "come closer", "follow me" → positive linear_x, small duration
       - RETREAT: "back up", "go away", "give me space" → negative linear_x
       - EXPLORE: "go check that out", "what's over there" → positive linear_x toward detected object
       - TURN: "look left", "turn around", "face the other way" → angular_z only
       - STOP: "stop", "wait", "hold on" → all zeros
       - SEARCH: "find [object]", "where is [thing]" → slow rotation to scan
    3. Make the AI reason about sensor context naturally:
       - "The user says 'come closer' — my front ultrasonic reads 1.2m, plenty of room. I'll approach slowly."
       - "The user says 'go forward' — front Lidar reads 0.4m, too close. I'll warn them."
    4. Keep response format as JSON but add richer explanations
    - WHY: The 1B model needs explicit category mapping since it can't infer intent from ambiguous language alone
    - AVOID: Do NOT remove the JSON output format — the executor depends on it
  </action>
  <verify>grep -n "Aurora\|APPROACH\|come closer\|intent" src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</verify>
  <done>System prompt contains at least 6 intent categories with natural language examples</done>
</task>

<task type="auto">
  <name>Enrich Sensor Context for Natural Reasoning</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</files>
  <action>
    Improve the `context_str` injected into the LLM in `handle_ai_logic()`:
    1. Convert raw numbers into human-readable spatial descriptions:
       - Instead of "Front: 0.6m" → "Front: 0.6m (close, proceed carefully)"
       - Instead of "Front: 3.2m" → "Front: 3.2m (open space ahead)"
       - Thresholds: <0.3m="blocked", <0.6m="close", <1.5m="nearby", >1.5m="open"
    2. Add person detection context from vision:
       - If OAK-D detects a "person", add: "A human is detected {distance}m ahead"
       - This enables "come closer to me" to work contextually
    3. Add a brief movement history: "Last movement: forward 0.15 m/s for 3s"
    - WHY: The LLM reasons better with natural language context than raw sensor dumps
  </action>
  <verify>grep -n "open space\|blocked\|person.*detected\|human" src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</verify>
  <done>Sensor context includes spatial descriptions and person-awareness</done>
</task>

## Success Criteria
- [ ] AI correctly interprets "come closer" as approach with positive linear_x
- [ ] AI correctly interprets "back up" as retreat with negative linear_x
- [ ] AI warns when asked to move toward an obstacle < 0.3m
- [ ] Sensor context uses human-readable descriptions, not just raw numbers
