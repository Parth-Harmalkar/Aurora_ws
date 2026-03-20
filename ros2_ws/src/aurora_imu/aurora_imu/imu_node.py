import board
import busio
import adafruit_bno055
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion
import numpy as np

from adafruit_extended_bus import ExtendedI2C as I2C

class ImuNode(Node):

    def __init__(self):
        super().__init__('imu_node')
        self.publisher = self.create_publisher(Imu, 'imu', 10)

        try:
            # Using ExtendedI2C(1) to directly access I2C bus 1 (/dev/i2c-1)
            # This is more robust on Jetson boards than standard busio/board mappings
            i2c = I2C(1) 
            self.sensor = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
            self.get_logger().info("BNO055 IMU initialized at 0x28 on I2C bus 1 (Direct)")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize BNO055: {e}")
            self.sensor = None

        self.timer = self.create_timer(0.05, self.read_imu)

    def read_imu(self):
        if self.sensor is None:
            return

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        try:
            # Orientation (Quaternion)
            quat = self.sensor.quaternion
            if quat and None not in quat:
                msg.orientation.x = float(quat[0])
                msg.orientation.y = float(quat[1])
                msg.orientation.z = float(quat[2])
                msg.orientation.w = float(quat[3])

            # Angular Velocity (rad/s)
            gyro = self.sensor.gyro
            if gyro and None not in gyro:
                msg.angular_velocity.x = float(gyro[0])
                msg.angular_velocity.y = float(gyro[1])
                msg.angular_velocity.z = float(gyro[2])

            # Linear Acceleration (m/s^2)
            acc = self.sensor.acceleration
            if acc and None not in acc:
                msg.linear_acceleration.x = float(acc[0])
                msg.linear_acceleration.y = float(acc[1])
                msg.linear_acceleration.z = float(acc[2])

            self.publisher.publish(msg)
        except Exception as e:
            self.get_logger().warn(f"IMU read error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()