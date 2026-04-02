#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus2
import time
import struct
import math

class BNO055BareNode(Node):
    # Core BNO055 Registers
    BNO055_ADDRESS = 0x28
    BNO055_CHIP_ID_ADDR = 0x00
    BNO055_OPR_MODE_ADDR = 0x3D
    BNO055_SYS_TRIGGER_ADDR = 0x3F
    BNO055_UNIT_SEL_ADDR = 0x3B
    BNO055_CALIB_STAT_ADDR = 0x35

    # Operational Modes
    OPERATION_MODE_CONFIG = 0x00
    OPERATION_MODE_IMUPLUS = 0x08  # 6-DOF (Gyro + Accel). No Mag. Fixes magnetic drift/jumping.

    # Data Registers
    BNO055_GYRO_DATA_X_LSB_ADDR = 0x14
    BNO055_QUATERNION_DATA_W_LSB_ADDR = 0x20
    BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR = 0x28

    def __init__(self):
        super().__init__('bno055_bare_node')
        
        self.publisher = self.create_publisher(Imu, '/bno055_raw', 10)

        # Load parameters
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_addr', self.BNO055_ADDRESS)
        
        i2c_bus = self.get_parameter('i2c_bus').value
        self.i2c_addr = self.get_parameter('i2c_addr').value
        
        self.calib_timer_counter = 0

        # Initialize I2C Bus via smbus2
        try:
            self.bus = smbus2.SMBus(i2c_bus)
            self.get_logger().info(f"Connected to I2C bus {i2c_bus}")
            self.init_bno055()
        except Exception as e:
            self.get_logger().error(f"Failed to open I2C bus {i2c_bus}: {e}")
            self.bus = None
            return

        # Start timer for publishing data at ~20Hz
        self.timer = self.create_timer(0.05, self.read_and_publish)

    def init_bno055(self):
        chip_id = self.bus.read_byte_data(self.i2c_addr, self.BNO055_CHIP_ID_ADDR)
        if chip_id != 0xA0:
            self.get_logger().error(f"Incorrect Chip ID: 0x{chip_id:02X} (Expected 0xA0)")
            return
            
        self.get_logger().info("BNO055 Found. Initializing bare-metal driver...")

        self.bus.write_byte_data(self.i2c_addr, self.BNO055_OPR_MODE_ADDR, self.OPERATION_MODE_CONFIG)
        time.sleep(0.02)
        
        try:
            self.bus.write_byte_data(self.i2c_addr, self.BNO055_SYS_TRIGGER_ADDR, 0x20)
            time.sleep(0.65)
        except IOError:
            pass 
            
        while True:
            try:
                if self.bus.read_byte_data(self.i2c_addr, self.BNO055_CHIP_ID_ADDR) == 0xA0:
                    break
            except IOError:
                pass
            time.sleep(0.01)

        self.bus.write_byte_data(self.i2c_addr, 0x3E, 0x00) # PWR_MODE normal
        time.sleep(0.01)

        self.bus.write_byte_data(self.i2c_addr, self.BNO055_UNIT_SEL_ADDR, 0x00)
        time.sleep(0.01)
        
        # Switch to IMUPlus (6-DOF) Mode instead of NDOF. 
        # NDOF relies on Magnetometer which causes wild drifting if uncalibrated or near motors.
        # IMUPlus uses only Gyro + Accel to maintain absolutely rock-solid pitch/roll and relative yaw.
        self.bus.write_byte_data(self.i2c_addr, self.BNO055_OPR_MODE_ADDR, self.OPERATION_MODE_IMUPLUS)
        time.sleep(0.01) 
        
        self.get_logger().info("BNO055 Initialization Complete. Mode: IMUPlus (Rock-stable, No Mag Drift).")

    def read_and_publish(self):
        if self.bus is None:
            return

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'bno_link'

        try:
            # --- Check Calibration Status every 1 second (20 ticks of 0.05s) ---
            self.calib_timer_counter += 1
            if self.calib_timer_counter >= 20:
                self.calib_timer_counter = 0
                calib = self.bus.read_byte_data(self.i2c_addr, self.BNO055_CALIB_STAT_ADDR)
                sys = (calib >> 6) & 0x03
                gyro = (calib >> 4) & 0x03
                accel = (calib >> 2) & 0x03
                mag = calib & 0x03
                # Log calibration (3 is fully calibrated, 0 is uncalibrated)
                self.get_logger().info(f"Calibration Status [0-3] -> Sys: {sys}, Gyro: {gyro}, Accel: {accel}")

            # --- Read Quaternions (8 bytes starting at 0x20) ---
            quat_data = self.bus.read_i2c_block_data(self.i2c_addr, self.BNO055_QUATERNION_DATA_W_LSB_ADDR, 8)
            q_w, q_x, q_y, q_z = struct.unpack('<hhhh', bytes(quat_data))
            
            # Invert Pitch (Y) and Roll (X) direction of rotation manually 
            msg.orientation.w = q_w / 16384.0
            msg.orientation.x = -q_x / 16384.0
            msg.orientation.y = -q_y / 16384.0
            msg.orientation.z = q_z / 16384.0
            
            # Safety fallback if hardware returns all 0s (prevents RTAB-Map rejection)
            if msg.orientation.w == 0.0 and msg.orientation.x == 0.0 and msg.orientation.y == 0.0 and msg.orientation.z == 0.0:
                msg.orientation.w = 1.0

            # --- Read Gyro (6 bytes starting at 0x14) ---
            gyro_data = self.bus.read_i2c_block_data(self.i2c_addr, self.BNO055_GYRO_DATA_X_LSB_ADDR, 6)
            g_x, g_y, g_z = struct.unpack('<hhh', bytes(gyro_data))
            
            deg2rad = math.pi / 180.0
            # Also mathematically invert the angular velocity for Pitch and Roll
            msg.angular_velocity.x = -(g_x / 16.0) * deg2rad
            msg.angular_velocity.y = -(g_y / 16.0) * deg2rad
            msg.angular_velocity.z = (g_z / 16.0) * deg2rad

            # --- Read Linear Acceleration (Gravity-compensated) (6 bytes at 0x28) ---
            acc_data = self.bus.read_i2c_block_data(self.i2c_addr, self.BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR, 6)
            a_x, a_y, a_z = struct.unpack('<hhh', bytes(acc_data))
            
            msg.linear_acceleration.x = a_x / 100.0
            msg.linear_acceleration.y = a_y / 100.0
            msg.linear_acceleration.z = a_z / 100.0

            # Provide small fallback covariances since the BNO055 does internal fusion
            # Initializing diagonals to non-zero prevents EKF and RTAB-Map from failing
            for i in range(9):
                msg.orientation_covariance[i] = 0.0
                msg.angular_velocity_covariance[i] = 0.0
                msg.linear_acceleration_covariance[i] = 0.0
            
            msg.orientation_covariance[0] = 0.01
            msg.orientation_covariance[4] = 0.01
            msg.orientation_covariance[8] = 0.01
            
            msg.angular_velocity_covariance[0] = 0.001
            msg.angular_velocity_covariance[4] = 0.001
            msg.angular_velocity_covariance[8] = 0.001
            
            msg.linear_acceleration_covariance[0] = 0.05
            msg.linear_acceleration_covariance[4] = 0.05
            msg.linear_acceleration_covariance[8] = 0.05
            
            self.publisher.publish(msg)
            
        except Exception as e:
            self.get_logger().warn(f"Error reading BNO055 data over I2C: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = BNO055BareNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.bus is not None:
            node.bus.close()
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
