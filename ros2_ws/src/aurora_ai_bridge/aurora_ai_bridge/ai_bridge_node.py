import asyncio
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range
from vision_msgs.msg import Detection3DArray
from .reasoning import create_reasoning_graph
import json

class AIBridgeNode(Node):

    def __init__(self):
        super().__init__('ai_bridge_node')
        
        # Subscriptions
        self.cmd_sub = self.create_subscription(String, '/voice_command', self.command_callback, 10)
        self.us_fl_sub = self.create_subscription(Range, '/ultrasonic/front_left', self.us_fl_callback, 10)
        self.us_fr_sub = self.create_subscription(Range, '/ultrasonic/front_right', self.us_fr_callback, 10)
        self.vision_sub = self.create_subscription(Detection3DArray, '/oak/nn/spatial_detections', self.vision_callback, 10)
        
        # VOC Class Mapping for default OAK-D MobileNet
        self.voc_labels = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
        
        # Sensor State Memory
        self.sensor_state = {
            "front_left": "Clear", 
            "front_right": "Clear", 
            "vision": "OAK-D Spatial Network Offline"
        }
        
        # Publishers
        self.vel_pub = self.create_publisher(Twist, '/ai_vel', 10)
        self.status_pub = self.create_publisher(String, '/ai_status', 10)
        
        # Reasoner
        self.reasoning_graph = create_reasoning_graph()
        
        # Task queue for handling incoming commands asynchronously
        self.loop = asyncio.get_event_loop()
        self.current_task = None
        self.get_logger().info("AI Bridge Semantic Perception Node Initialized")

    def us_fl_callback(self, msg):
        dist = msg.range
        self.sensor_state["front_left"] = f"{dist:.2f}m" if dist < 2.0 else "Clear"

    def us_fr_callback(self, msg):
        dist = msg.range
        self.sensor_state["front_right"] = f"{dist:.2f}m" if dist < 2.0 else "Clear"

    def vision_callback(self, msg):
        if not msg.detections:
            self.sensor_state["vision"] = "Vision clear (No objects detected)."
            return
            
        objs = []
        for d in msg.detections:
            if not d.results: continue
            class_id = int(d.results[0].hypothesis.class_id)
            score = d.results[0].hypothesis.score
            z_dist = d.bbox.center.position.z # depth distance in meters
            
            label = self.voc_labels[class_id] if 0 <= class_id < len(self.voc_labels) else f"Unknown({class_id})"
            
            if score > 0.5:
                objs.append(f"{label} at {z_dist:.1f}m")
                
        if objs:
            self.sensor_state["vision"] = ", ".join(objs)
        else:
            self.sensor_state["vision"] = "Vision clear (No objects detected)."

    def command_callback(self, msg):
        self.get_logger().info("Received command: '%s'" % msg.data)
        # Cancel current task if new command arrives
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            self.publish_status("Task cancelled by new command")
            self.stop_robot()
            
        self.current_task = asyncio.run_coroutine_threadsafe(self.handle_ai_logic(msg.data), self.loop)

    async def handle_ai_logic(self, text):
        self.publish_status("Thinking: %s" % text)
        
        try:
            # Inject Sensors into AI Context
            context_str = f"Ultrasonics -> Front Left: {self.sensor_state['front_left']}, Front Right: {self.sensor_state['front_right']} | Vision -> OAK-D: {self.sensor_state['vision']}"
            self.get_logger().info(f"Context applied: {context_str}")
            
            # Invoke LangGraph
            result = await self.loop.run_in_executor(None, lambda: self.reasoning_graph.invoke({"input": text, "sensor_context": context_str}))
            
            if result.get("status") == "planned":
                plan = result.get("plan", {})
                await self.execute_plan(plan)
            else:
                self.publish_status("Failed to create plan")
        except Exception as e:
            self.get_logger().error("Reasoning error: %s" % str(e))
            self.publish_status("Error in reasoning layer")

    async def execute_plan(self, plan):
        lx = float(plan.get("linear_x", 0.0))
        az = float(plan.get("angular_z", 0.0))
        duration = float(plan.get("duration", 0.0))
        explanation = plan.get("explanation", "Executing AI plan")
        
        self.publish_status(explanation)
        self.get_logger().info("Executing: lx=%.2f, az=%.2f for %.1fs" % (lx, az, duration))
        
        start_time = self.loop.time()
        twist = Twist()
        twist.linear.x = lx
        twist.angular.z = az
        
        try:
            while self.loop.time() - start_time < duration:
                self.vel_pub.publish(twist)
                await asyncio.sleep(0.1) # 10Hz control loop
            
            self.stop_robot()
            self.publish_status("Task complete")
        except asyncio.CancelledError:
            self.stop_robot()
            raise

    def stop_robot(self):
        self.vel_pub.publish(Twist())

    def publish_status(self, status):
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

async def ros_loop(node):
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.01)
        await asyncio.sleep(0.01)

def main(args=None):
    rclpy.init(args=args)
    node = AIBridgeNode()
    
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(ros_loop(node))
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
