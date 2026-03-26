import os
import json
import requests
import re
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    input: str
    sensor_context: str
    image: Optional[str]
    plan: dict
    status: str

def reasoner_node(state: AgentState):
    """
    Aurora's high-level brain.
    Decides between:
    1. navigate: Move to a waypoint or coordinate.
    2. shell: Standard OS commands (Whitelisted in bridge).
    3. vision: Explicit request to look at something.
    4. stop: Emergency stop.
    5. chat: No physical action.
    """
    ollama_url = os.environ.get("AURORA_OLLAMA_URL", "http://localhost:11434")
    
    prompt = f"""
You are Aurora, a smart autonomous robot. 
Current Senses: {state['sensor_context']}

Analyze the user command and current senses.
Output ONLY a valid JSON object.

Action Types:
- "navigate": Move to a target. Requires "target" (e.g. "kitchen", "home", or coordinate {{x,y,theta}}).
- "shell": Execute a system command. Requires "command".
- "vision": Explicitly describe the current camera view.
- "stop": Immediate rest/stop.
- "chat": Just a conversational response.

Output Format (STRICT):
{{
  "action": "navigate" | "shell" | "vision" | "stop" | "chat",
  "target": "string_or_obj",
  "command": "string",
  "confidence": 0.0-1.0,
  "explanation": "Friendly response to the user"
}}

User: "{state['input']}"
"""

    try:
        # Use moondream if image is present, else llama3.2:1b
        model = "moondream" if state.get("image") else "llama3.2:1b"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        if state.get("image"):
            payload["images"] = [state["image"]]

        response = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        raw_text = data.get("response", "{}").strip()
        
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
            return {**state, "plan": plan, "status": "success"}
        
        return {**state, "plan": {"action": "chat", "explanation": raw_text}, "status": "partial"}
        
    except Exception as e:
        return {**state, "plan": {"action": "chat", "explanation": f"Logic error: {str(e)}"}, "status": "error"}

def create_reasoning_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("reasoner", reasoner_node)
    workflow.set_entry_point("reasoner")
    workflow.add_edge("reasoner", END)
    return workflow.compile()
