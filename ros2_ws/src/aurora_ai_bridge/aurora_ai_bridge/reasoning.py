from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
import json

class AgentState(TypedDict):
    input: str
    sensor_context: str
    plan: dict
    status: str

def create_reasoning_graph():
    llm = OllamaLLM(
    model="llama3.2:1b",
    format="json",
    temperature=0,
    num_gpu=0  # Force to CPU to avoid cudaMalloc OOM on 8GB Jetson
)

    def planner_node(state: AgentState):
        prompt = f"""
        You are a robot mission planner. Decompose the user's command into a motor control plan.
        
        [LIVE SENSOR TELEMETRY]
        {state.get('sensor_context', 'No sensor data available.')}
        
        CRITICAL RULE: If the user says "move forward" but the LIVE SENSOR TELEMETRY says an obstacle is less than 0.3m ahead, you MUST refuse to move and output 0.0 for all speeds.

        Example 1: "move forward" (Sensor: Clear) -> {{"linear_x": 0.5, "angular_z": 0.0, "duration": 2.0, "explanation": "Moving forward"}}
        Example 2: "turn left" -> {{"linear_x": 0.0, "angular_z": 1.0, "duration": 1.5, "explanation": "Turning left"}}
        Example 3: "stop" -> {{"linear_x": 0.0, "angular_z": 0.0, "duration": 0.0, "explanation": "Stopping"}}
        Example 4: "move forward" (Sensor: Obstacle FL at 0.15m) -> {{"linear_x": 0.0, "angular_z": 0.0, "duration": 0.0, "explanation": "Cannot move forward, obstacle detected directly ahead!"}}
        
        User Command: {state['input']}
        
        Reply ONLY with JSON: 
        {{
          "linear_x": float, 
          "angular_z": float, 
          "duration": float,
          "explanation": string
        }}
        """
        response = llm.invoke(prompt)
        print(f"DEBUG: Raw AI Response: {response}")
        try:
            plan = json.loads(response)
            return {"plan": plan, "status": "planned"}
        except:
            return {"plan": {"linear_x": 0.0, "angular_z": 0.0, "duration": 0.0}, "status": "error"}

    # Define the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", planner_node)
    
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", END)
    
    return workflow.compile()

if __name__ == "__main__":
    # Test
    graph = create_reasoning_graph()
    result = graph.invoke({"input": "move forward slowly for 2 seconds"})
    print(json.dumps(result, indent=2))
