import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int64
import time
import sys
import os
import serial

# Add the current directory to sys.path so we can import the SDK
sys.path.append(os.path.dirname(__file__))
from STservo_sdk import PortHandler, sts, COMM_SUCCESS

class MotorDriverNode(Node):

    def __init__(self):
        super().__init__('motor_driver')
        
        # Publishers for ticks (as per arjuna2_ws)
        self.left_ticks_pub = self.create_publisher(Int64, 'left_ticks', 10)
        self.right_ticks_pub = self.create_publisher(Int64, 'right_ticks', 10)
        
        # Subscriber for cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        
        # Parameters aligned with arjuna2_ws
        self.declare_parameter('port', '/dev/ttyUSB2')
        self.declare_parameter('baudrate', 1000000)
        self.declare_parameter('wheel_sep', 0.30)
        self.declare_parameter('motor_acc', 0)
        
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.wheel_sep = self.get_parameter('wheel_sep').get_parameter_value().double_value
        self.motor_acc = self.get_parameter('motor_acc').get_parameter_value().integer_value

        # Encoder Tracking Variables (from Arjuna_Ticks_Pub.py)
        self.total_left_ticks = 0
        self.total_right_ticks = 0
        self.prev_left_ticks = 0
        self.prev_right_ticks = 0
        self.left_velocity_cmd = 0
        self.right_velocity_cmd = 0
        self.left_speed = 0
        self.right_speed = 0

        self.portHandler = PortHandler(self.port)
        self.packetHandler = sts(self.portHandler)

        if self.portHandler.openPort():
            self.get_logger().info(f"Succeeded to open the port {self.port}")
        else:
            self.get_logger().error(f"Failed to open the port {self.port}")
            raise RuntimeError(f"Failed to open port {self.port}")

        if self.portHandler.setBaudRate(self.baudrate):
            self.get_logger().info(f"Succeeded to change the baudrate to {self.baudrate}")
        else:
            self.get_logger().error(f"Failed to change the baudrate to {self.baudrate}")
            raise RuntimeError(f"Failed to set baudrate {self.baudrate}")

        # Initialize motors in Wheel Mode and Enable Torque
        for motor_id in [1, 2, 3, 4]:
            self.packetHandler.WheelMode(motor_id)
            # Register 40 is Torque Enable (1), using the correct SDK method
            self.packetHandler.write1ByteTxRx(motor_id, 40, 1)
        self.get_logger().info("Motors (1,2,3,4) initialized and Torque Enabled")

        # Timer for tick publishing and main loop (10Hz)
        self.timer = self.create_timer(0.1, self.main_loop)

    def listener_callback(self, msg):
        linear_vel = msg.linear.x
        angular_vel = msg.angular.z
        
        # Only log non-zero commands at INFO
        # if abs(linear_vel) > 0.001 or abs(angular_vel) > 0.001:
        #    self.get_logger().info(f"Command received: lx={linear_vel:.2f}, az={angular_vel:.2f}")
 
        # Differential drive kinematics
        self.right_velocity_cmd = ((linear_vel * 2) + (angular_vel * self.wheel_sep)) / 2.0
        self.left_velocity_cmd = ((linear_vel * 2) - (angular_vel * self.wheel_sep)) / 2.0
 
        # Scaling to motor units (Recalibrated to 3000 for STS3215 full range)
        self.speed_scaling = 3000 
        self.right_speed = int(self.right_velocity_cmd * self.speed_scaling)
        self.left_speed = int(self.left_velocity_cmd * self.speed_scaling)
        
        if abs(self.left_speed) > 0 or abs(self.right_speed) > 0:
            # self.get_logger().info(f"Target Units: L={self.left_speed}, R={self.right_speed}")
            pass # Muted 'Target Units' log as per instruction

    def present_pos(self, motor_id):
        """Read current motor position"""
        position, speed, result, error = self.packetHandler.ReadPosSpeed(motor_id)
        if result != COMM_SUCCESS:
            return None
        return position

    def update_ticks(self):
        """Fixed tick counting logic from Arjuna_Ticks_Pub.py"""
        # Right Wheel (Motor ID 2)
        pos_r = self.present_pos(2)
        if pos_r is not None:
            raw_ticks_r = int(pos_r / 2.5)
            if self.prev_right_ticks != 0:
                diff = raw_ticks_r - self.prev_right_ticks
                if diff > 16000: diff -= 32768
                elif diff < -16000: diff += 32768
                
                # Directional logic based on command (Auto-detect from diff if possible)
                self.total_right_ticks += diff
            self.prev_right_ticks = raw_ticks_r

        # Left Wheel (Motor ID 1)
        pos_l = self.present_pos(1)
        if pos_l is not None:
            raw_ticks_l = int(pos_l / 2.5)
            if self.prev_left_ticks != 0:
                diff = raw_ticks_l - self.prev_left_ticks
                if diff > 16000: diff -= 32768
                elif diff < -16000: diff += 32768
                
                # Negate: left motor is commanded with -speed (mirror mount),
                # so encoder counts backwards. Negate to get forward-positive ticks.
                self.total_left_ticks -= diff
            self.prev_left_ticks = raw_ticks_l

        # Publish
        msg_l = Int64()
        msg_l.data = self.total_left_ticks
        self.left_ticks_pub.publish(msg_l)

        msg_r = Int64()
        msg_r.data = self.total_right_ticks
        self.right_ticks_pub.publish(msg_r)

    def main_loop(self):
        try:
            self.update_ticks()
        except serial.SerialException as e:
            self.get_logger().warn(f"Serial read glitch (will retry): {e}")
            return  # Skip this cycle, don't crash
        except Exception as e:
            self.get_logger().warn(f"Tick update error: {e}")
            return
        # Write speeds to motors
        try:
            # Left (IDs 1,4)
            self.packetHandler.WriteSpec(1, -self.left_speed, self.motor_acc)
            self.packetHandler.WriteSpec(4, -self.left_speed, self.motor_acc)
            # Right (IDs 2,3)
            self.packetHandler.WriteSpec(2, self.right_speed, self.motor_acc)
            self.packetHandler.WriteSpec(3, self.right_speed, self.motor_acc)
        except AttributeError:
            # Handle case where speeds aren't set yet
            pass
        except Exception as e:
            self.get_logger().error(f"Motor Write Error: {e}")

    def stop_motors(self):
        """Force motors to zero speed before shutting down"""
        self.get_logger().info("Safety Shutdown: Stopping all motors.")
        try:
            self.packetHandler.WriteSpec(1, 0, self.motor_acc)
            self.packetHandler.WriteSpec(4, 0, self.motor_acc)
            self.packetHandler.WriteSpec(2, 0, self.motor_acc)
            self.packetHandler.WriteSpec(3, 0, self.motor_acc)
            # Give it a tiny bit of time to send over serial before the port closes
            time.sleep(0.1)
        except Exception as e:
            self.get_logger().error(f"Failed to stop motors on shutdown: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_motors()
        if hasattr(node, 'portHandler') and node.portHandler:
            node.portHandler.closePort()
        node.destroy_node()
        # Shutdown is already handled by the launch framework sometimes, 
        # so we try/except it to avoid the noisy RCLError
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
