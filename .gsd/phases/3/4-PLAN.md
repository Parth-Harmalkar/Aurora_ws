---
phase: 3
plan: 4
wave: 2
---

# Plan 3.4: Voice Input (Whisper)

## Objective
Add natural language voice input capabilities using `faster-whisper`.

## Context
- .gsd/SPEC.md
- .gsd/phases/3/RESEARCH.md

## Tasks

<task type="auto">
  <name>Implement Whisper Node</name>
  <files>[ros2_ws/src/aurora_ai_bridge/aurora_ai_bridge/whisper_node.py]</files>
  <action>
    Create a dedicated node for audio capture and transcription.
    Use `faster-whisper` with `int8` quantization on CUDA.
    Implement VAD (Voice Activity Detection) or a simple energy-based trigger.
    Publish results to `/voice_command`.
  </action>
  <verify>ros2 topic echo /voice_command</verify>
  <done>Speech spoken to microphone results in accurate transcription on `/voice_command`.</done>
</task>

<task type="auto">
  <name>Unified AI Launch</name>
  <files>[ros2_ws/src/aurora_bringup/launch/intelligence.launch.py]</files>
  <action>
    Create a new launch file to bring up:
    1. ai_bridge_node
    2. whisper_node
    3. (Optional) Ollama monitor
  </action>
  <verify>ros2 launch aurora_bringup intelligence.launch.py</verify>
  <done>All AI-related nodes start and communicate correctly.</done>
</task>

## Success Criteria
- [ ] Voice transcription working with <1s latency for short phrases.
- [ ] End-to-end flow: Voice -> Transcription -> Reasoning -> Motor Action confirmed.
