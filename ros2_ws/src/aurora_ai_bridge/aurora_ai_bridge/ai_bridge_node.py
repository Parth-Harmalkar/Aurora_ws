import asyncio
import time
import os
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String, Int32
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import Range, LaserScan, Image
from nav_msgs.msg import Odometry
from nav2_msgs.action import NavigateToPose
from .reasoning import create_reasoning_graph
import json
import cv2
import base64
from cv_bridge import CvBridge

class AIBridgeNode(Node):

    # --- CONFIGURATION (Safe & Pro) ---
    ALLOWED_COMMANDS = {
        "status": "ros2 topic echo /ai_status --once",
        "reboot_ai": "sudo systemctl restart aurora_ai",  # Example hypothetical
        "clear_map": "ros2 service call /rtabmap/reset_odom std_srvs/srv/Empty {}"
    }

    WAYPOINTS = {
        "home": (0.0, 0.0, 1.0),
        "kitchen": (2.5, 1.2, 0.707),
        "charger": (-0.5, 0.0, -1.0),
        "table": (1.8, -0.5, 0.0)
    }

    def __init__(self):
        super().__init__('ai_bridge_node')
        
        # Subscriptions
        self.cmd_sub = self.create_subscription(String, '/voice_command', self.command_callback, 10)
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        # Publishers
        self.status_pub = self.create_publisher(String, '/ai_status', 10)
        self.speech_pub = self.create_publisher(String, '/ai_speech', 10)
        self.led_pub = self.create_publisher(Int32, '/robot_led_mode', 10) # 1: Listening, 2: Processing, 3: Success, 4: Error
        self.vel_pub = self.create_publisher(Twist, '/stop_vel', 10) # For emergency stop
        
        # Nav2 Action Client
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Frame Caching (Reduced latency for "What do you see?")
        self.bridge = CvBridge()
        self.latest_frame = None
        self.cached_frame_b64 = None
        self.frame_cache_timer = self.create_timer(1.5, self.cache_frame_callback)
        
        # State
        self.sensor_state = {"odom": "Unknown"}
        self.reasoning_graph = create_reasoning_graph()
        self.loop = asyncio.get_event_loop()
        self.current_task = None

        self.get_logger().info("AI Bridge Commander V2 (Safe & Refined) Initialized")

    def odom_callback(self, msg):
        self.sensor_state["odom"] = f"X:{msg.pose.pose.position.x:.1f}, Y:{msg.pose.pose.position.y:.1f}"

    def image_callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except: pass

    def cache_frame_callback(self):
        """Prepare a base64 frame every 1.5s to avoid capture latency."""
        if self.latest_frame is not None:
            try:
                small = cv2.resize(self.latest_frame, (320, 180))
                _, buf = cv2.imencode(".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                self.cached_frame_b64 = base64.b64encode(buf).decode("utf-8")
            except: pass

    def command_callback(self, msg):
        self.get_logger().info(f"Triggered: {msg.data}")
        self.set_led(1) # Listening/Triggered
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
        self.current_task = asyncio.run_coroutine_threadsafe(self.handle_ai_logic(msg.data), self.loop)

    async def handle_ai_logic(self, text):
        self.set_led(2) # Processing
        self.publish_status("Aurora is thinking...")
        
        try:
            result = await self.loop.run_in_executor(
                None, 
                lambda: self.reasoning_graph.invoke({
                    "input": text, 
                    "sensor_context": f"Odom: {self.sensor_state['odom']}",
                    "image": self.cached_frame_b64
                })
            )
            
            plan = result.get("plan", {})
            action = plan.get("action", "chat")
            explanation = plan.get("explanation", "...")
            
            self.publish_speech(explanation)

            if action == "navigate":
                await self.execute_navigation(plan.get("target"))
            elif action == "shell":
                await self.execute_shell(plan.get("command"))
            elif action == "stop":
                self.vel_pub.publish(Twist())
                self.publish_status("Emergency stop executed.")
            
            self.set_led(3) # Success/Ready
            self.publish_status("Ready.")

        except Exception as e:
            self.get_logger().error(f"AI Logic Error: {e}")
            self.set_led(4) # Error

    async def execute_navigation(self, target):
        """Handle semantic waypoints or direct coordinates."""
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        x, y, w = 0.0, 0.0, 1.0

        if isinstance(target, str) and target.lower() in self.WAYPOINTS:
            x, y, w = self.WAYPOINTS[target.lower()]
            self.publish_status(f"Heading to the {target}...")
        elif isinstance(target, dict):
            x = target.get('x', 0.0)
            y = target.get('y', 0.0)
            w = target.get('w', 1.0)
            self.publish_status("Moving to coordinates.")
        else:
            self.publish_speech("I don't know where that is.")
            return

        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.orientation.w = float(w)

        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.publish_status("Nav2 not responding!")
            return

        self._nav_client.send_goal_async(goal_msg)

    async def execute_shell(self, cmd):
        """Command Whitelist Implementation (Safe)."""
        if not cmd: return
        
        # Check for direct whitelist matches or prefixes
        matched = False
        for key, full_cmd in self.ALLOWED_COMMANDS.items():
            if cmd.lower() in key:
                os.system(full_cmd)
                self.publish_status(f"Executed whitelisted command: {key}")
                matched = True
                break
        
        if not matched:
            self.get_logger().warn(f"Blocked unauthorized shell command: {cmd}")
            self.publish_speech("Sorry, that command isn't in my whitelist.")

    def set_led(self, mode):
        self.led_pub.publish(Int32(data=mode))

    def publish_status(self, text):
        self.status_pub.publish(String(data=text))

    def publish_speech(self, text):
        self.speech_pub.publish(String(data=text))

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
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
