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
        
        # Command Heartbeat Tracking
        self.last_cmd_time = self.get_clock().now()
        self.cmd_warning_logged = False

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

        # Initialize Sync Communication objects
        # SyncRead for positions (Register 56, length 2 bytes for position)
        # We read 4 bytes starting at 56 to get both Position and Speed in one go
        from STservo_sdk import GroupSyncRead
        self.groupSyncRead = GroupSyncRead(self.packetHandler, 56, 4)
        self.groupSyncRead.addParam(1)
        self.groupSyncRead.addParam(2)
        
        # Initialize motors in Wheel Mode and Enable Torque
        for motor_id in [1, 2, 3, 4]:
            self.packetHandler.WheelMode(motor_id)
            # Register 40 is Torque Enable (1), using the correct SDK method
            self.packetHandler.write1ByteTxRx(motor_id, 40, 1)
        self.get_logger().info("Motors (1,2,3,4) initialized and Torque Enabled (Sync Mode)")

        # Timer for tick publishing and main loop (10Hz)
        self.timer = self.create_timer(0.1, self.main_loop)

    def listener_callback(self, msg):
        linear_vel = msg.linear.x
        angular_vel = msg.angular.z

        # Update Heartbeat
        self.last_cmd_time = self.get_clock().now()
        if self.cmd_warning_logged:
            self.get_logger().info("Control commands resumed.")
            self.cmd_warning_logged = False

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
        """Optimized tick counting using SyncRead"""
        # Execute SyncRead for IDs 1 and 2
        comm_result = self.groupSyncRead.txRxPacket()
        if comm_result != COMM_SUCCESS:
            # self.get_logger().warn(f"SyncRead failed: {self.packetHandler.getTxRxResult(comm_result)}")
            return

        # Right Wheel (Motor ID 2)
        pos_r = self.groupSyncRead.getData(2, 56, 2)
        if pos_r is not None:
            raw_ticks_r = int(pos_r / 2.5)
            if self.prev_right_ticks != 0:
                diff = raw_ticks_r - self.prev_right_ticks
                if diff > 16000: diff -= 32768
                elif diff < -16000: diff += 32768
                self.total_right_ticks += diff
            self.prev_right_ticks = raw_ticks_r

        # Left Wheel (Motor ID 1)
        pos_l = self.groupSyncRead.getData(1, 56, 2)
        if pos_l is not None:
            raw_ticks_l = int(pos_l / 2.5)
            if self.prev_left_ticks != 0:
                diff = raw_ticks_l - self.prev_left_ticks
                if diff > 16000: diff -= 32768
                elif diff < -16000: diff += 32768
                # Negate: left motor is commanded with -speed (mirror mount)
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
            
        # Check command heartbeat: if > 2.0s without cmd_vel, log warning
        now = self.get_clock().now()
        time_diff = (now - self.last_cmd_time).nanoseconds / 1e9
        if time_diff > 2.0 and not self.cmd_warning_logged:
            # Only log if we were actually receiving commands before (to avoid noise at startup)
            if self.last_cmd_time.nanoseconds > 0:
                self.get_logger().warn(f"Control heartbeat idle for {time_diff:.1f}s. Waiting for commands...")
            self.cmd_warning_logged = True
            # Set target speeds to zero for safety
            self.left_speed = 0
            self.right_speed = 0

        # Write speeds to motors using SyncWrite
        try:
            # SyncWrite uses Register 41 (STS_ACC) and writes 7 bytes
            # We must use help methods from sts class to format speed
            # Packet format: [acc, 0, 0, 0, 0, low_speed, high_speed]
            
            # Left (IDs 1,4) - Negated due to mirroring
            l_val = self.packetHandler.sts_toscs(-self.left_speed, 15)
            l_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(l_val), self.packetHandler.sts_hibyte(l_val)]
            
            # Right (IDs 2,3) - Positive
            r_val = self.packetHandler.sts_toscs(self.right_speed, 15)
            r_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(r_val), self.packetHandler.sts_hibyte(r_val)]
            
            # Add to SyncWrite
            self.packetHandler.groupSyncWrite.clearParam()
            self.packetHandler.groupSyncWrite.addParam(1, l_packet)
            self.packetHandler.groupSyncWrite.addParam(4, l_packet)
            self.packetHandler.groupSyncWrite.addParam(2, r_packet)
            self.packetHandler.groupSyncWrite.addParam(3, r_packet)
            
            # Transmit (one packet for all)
            self.packetHandler.groupSyncWrite.txPacket()
            
        except Exception as e:
            self.get_logger().error(f"Motor SyncWrite Error: {e}")

    def stop_motors(self):
        """Force motors to zero speed using Broadcast ID for instant stop"""
        self.get_logger().info("Safety Shutdown: Broadcasting STOP to all motors.")
        try:
            # ID 254 is Broadcast ID for STServo
            self.packetHandler.WriteSpec(254, 0, self.motor_acc)
            time.sleep(0.05)
        except Exception as e:
            self.get_logger().error(f"Failed to broadcast stop: {e}")

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
