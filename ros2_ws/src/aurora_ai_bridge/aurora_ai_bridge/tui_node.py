import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range, LaserScan
from rcl_interfaces.msg import Log
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.logging import RichHandler
from collections import deque
import threading
import time

class AuroraTUI(Node):
    def __init__(self):
        super().__init__('aurora_tui')
        
        # State Data
        self.ai_status = "Waiting for Aurora..."
        self.ai_thought = "N/A"
        self.last_voice = "..."
        self.velocity = (0.0, 0.0)
        self.sensors = {
            "Lidar (F)": 0.0,
            "Lidar (B)": 0.0,
            "US (L)": 0.0,
            "US (R)": 0.0
        }
        self.vision = []
        self.bug_logs = deque(maxlen=10) # Last 10 WARN/ERRORs
        
        # Subscriptions
        self.status_sub = self.create_subscription(String, '/ai_status', self.status_callback, 10)
        self.vel_sub = self.create_subscription(Twist, '/ai_vel', self.vel_callback, 10)
        self.voice_sub = self.create_subscription(String, '/voice_command', self.voice_callback, 10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.us_fl_sub = self.create_subscription(Range, '/ultrasonic/front_left', self.us_fl_callback, 10)
        self.us_fr_sub = self.create_subscription(Range, '/ultrasonic/front_right', self.us_fr_callback, 10)
        self.rosout_sub = self.create_subscription(Log, '/rosout', self.rosout_callback, 10)

        # UI Threading
        self.console = Console()
        self.layout = self.make_layout()
        self.get_logger().info("TUI Dashboard Node Started")

    def make_layout(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["main"].split_row(
            Layout(name="side", ratio=1),
            Layout(name="body", ratio=2)
        )
        return layout

    def status_callback(self, msg):
        self.ai_status = msg.data
        if "Thinking:" in msg.data:
            self.ai_thought = msg.data.split("Thinking:")[1].strip()

    def vel_callback(self, msg):
        self.velocity = (msg.linear.x, msg.angular.z)

    def voice_callback(self, msg):
        self.last_voice = msg.data

    def scan_callback(self, msg):
        # Sample front and back from lidar scan
        if msg.ranges:
            center = len(msg.ranges) // 2
            self.sensors["Lidar (F)"] = msg.ranges[0]
            self.sensors["Lidar (B)"] = msg.ranges[center]

    def us_fl_callback(self, msg):
        self.sensors["US (L)"] = msg.range

    def us_fr_callback(self, msg):
        self.sensors["US (R)"] = msg.range

    def rosout_callback(self, msg):
        if msg.level >= Log.WARN:
            node_name = msg.name
            level_str = "WARN" if msg.level == Log.WARN else "ERROR"
            color = "yellow" if msg.level == Log.WARN else "red"
            timestamp = time.strftime('%H:%M:%S', time.localtime(msg.stamp.sec))
            log_entry = f"[{color}][{timestamp}] [{node_name}] {msg.msg}[/]"
            self.bug_logs.append(log_entry)

    def generate_dashboard(self):
        # Header
        self.layout["header"].update(Panel(Text("✨ AURORA COMPANION DASHBOARD ✨", justify="center", style="bold magenta")))
        
        # Side: Sensors
        sensor_table = Table(show_header=False, box=None)
        for s, v in self.sensors.items():
            val_str = f"{v:.2f}m" if v < 10 else "Clear"
            color = "red" if v < 0.3 else "white"
            sensor_table.add_row(s, Text(val_str, style=color))
        
        self.layout["side"].update(Panel(sensor_table, title="[cyan]Perception[/]"))
        
        # Body: AI Thoughts
        body_text = Text()
        body_text.append("\nLast Heard: ", style="bold")
        body_text.append(f"\"{self.last_voice}\"\n", style="italic yellow")
        body_text.append("\nAI Thought:\n", style="bold")
        body_text.append(f"{self.ai_status}\n", style="green")
        body_text.append(f"\nMotion: lx={self.velocity[0]:.2f}, az={self.velocity[1]:.2f}", style="bold blue")
        
        self.layout["body"].update(Panel(body_text, title="[magenta]AI Core[/]"))
        
        # Footer: Logs
        log_text = Text.from_markup("\n".join(self.bug_logs))
        self.layout["footer"].update(Panel(log_text, title="[red]System Logs & Bugs[/]"))
        
        return self.layout

def main(args=None):
    rclpy.init(args=args)
    node = AuroraTUI()
    
    # Run UI in Live context
    with Live(node.layout, refresh_per_second=4, screen=True) as live:
        try:
            while rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.1)
                live.update(node.generate_dashboard())
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
