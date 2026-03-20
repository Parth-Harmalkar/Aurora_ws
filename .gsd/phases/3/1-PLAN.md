---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: System Hardening & LLM Foundation

## Objective
Prepare the Jetson Orin Nano for LLM workloads by maximizing available memory (ZRAM) and deploying the Ollama inference server with GPU acceleration.

## Context
- .gsd/SPEC.md
- .gsd/phases/3/RESEARCH.md

## Tasks

<task type="auto">
  <name>Configure ZRAM and Swap</name>
  <files>[/etc/default/zram-config, /etc/fstab]</files>
  <action>
    Install zram-config and configure it for 8GB of ZRAM. 
    Ensure the existing NVMe swap (8GB+) is prioritized as backup.
  </action>
  <verify>zramctl</verify>
  <done>ZRAM device shows 8GB capacity; swap prioritization is correct.</done>
</task>

<task type="auto">
  <name>Deploy Ollama and Model</name>
  <files>[]</files>
  <action>
    Install Ollama using the official Jetson-optimized script.
    Pull the `llama3:3b` (or `llama3.2:3b`) model.
    Verify GPU acceleration is active by checking memory usage during a test prompt.
  </action>
  <verify>ollama list && curl -X POST http://localhost:11434/api/generate -d '{"model": "llama3:3b", "prompt": "hi"}'</verify>
  <done>Ollama server responds to HTTP requests; model is loaded; GPU memory is consumed.</done>
</task>

## Success Criteria
- [ ] ZRAM 8GB active.
- [ ] Ollama running with GPU acceleration.
- [ ] `llama3:3b` model pulle and responsive.
