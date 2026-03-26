---
phase: 8
plan: 3
wave: 2
---

# Plan 8.3: Personality & Emotional Awareness

## Objective
Give Aurora a consistent personality that makes it feel alive — curious, friendly, and cautious. The robot should exhibit idle behaviors when bored, react emotionally to sudden stimuli, and respond with character in its reasoning explanations.

## Context
- .gsd/ROADMAP.md
- src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py
- src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py

## Tasks

<task type="auto">
  <name>Inject Personality into LLM System Prompt</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</files>
  <action>
    Add a personality definition block to the system prompt:
    1. Core traits: "You are Aurora — a curious, friendly, and slightly cautious robot companion. You love exploring new spaces but are careful around obstacles."
    2. Response style rules:
       - Use first person: "I'll move forward carefully" not "The robot will move"
       - Express curiosity: "Ooh, I see something interesting ahead!" 
       - Show caution: "Hmm, that's a bit close for comfort, let me back up"
       - Be playful: "Sure! Let me zoom over there... safely, of course"
    3. Personality-influenced motion:
       - When curious (exploring): slightly faster, wider turns
       - When cautious (obstacles nearby): slower, shorter durations
       - When confused (ambiguous command): small rotation to scan, ask for clarification
    - WHY: Personality makes the robot feel like a pet/companion rather than a machine
  </action>
  <verify>grep -n "Aurora\|curious\|friendly\|cautious\|personality" src/aurora_ai_bridge/aurora_ai_bridge/reasoning.py</verify>
  <done>System prompt defines Aurora's personality with at least 3 core traits and example responses</done>
</task>

<task type="auto">
  <name>Add Idle Behavior Loop</name>
  <files>src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</files>
  <action>
    Add a periodic timer (every 30s) that triggers "idle awareness":
    1. Create a `self.idle_timer` using `self.create_timer(30.0, self.idle_behavior_callback)`
    2. In the callback, if no command has been received in the last 30s:
       - Publish a small random rotation (±0.1 rad/s for 1s) — "looking around curiously"
       - Log personality-flavored messages: "Just checking out my surroundings..."
    3. If a command IS active, skip the idle behavior
    4. Track `self.last_command_time` to determine idle state
    - WHY: A robot that just sits frozen feels dead. Small idle movements make it feel alive.
    - AVOID: Do NOT make idle behaviors aggressive — keep velocities very small
  </action>
  <verify>grep -n "idle\|curious\|last_command_time" src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py</verify>
  <done>Robot exhibits subtle curiosity movements when no commands are received for 30+ seconds</done>
</task>

<task type="checkpoint:human-verify">
  <name>Personality Integration Test</name>
  <files>N/A</files>
  <action>
    User launches the full stack and tests:
    1. Say "come closer" — robot should approach with a friendly explanation
    2. Say "what do you see?" — robot should describe vision detections with personality
    3. Wait 30+ seconds — robot should exhibit idle curiosity movements
    4. Say "stop" — robot should immediately halt
  </action>
  <verify>User observes robot behavior and confirms personality is consistent</verify>
  <done>User confirms the robot feels like a living companion, not a command executor</done>
</task>

## Success Criteria
- [ ] LLM responses use first-person language with personality
- [ ] Robot exhibits idle curiosity behaviors when not commanded
- [ ] Motion style varies based on context (cautious near obstacles, confident in open space)
- [ ] User feels the robot has a consistent character
