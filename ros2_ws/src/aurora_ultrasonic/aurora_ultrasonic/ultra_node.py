import smbus2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

class UltrasonicNode(Node):

    def __init__(self):
        super().__init__('ultrasonic_node')
        
        # Publishers for two sensors
        self.pub_left = self.create_publisher(Range, '/ultrasonic/front_left', 10)
        self.pub_right = self.create_publisher(Range, '/ultrasonic/front_right', 10)
        
        self.bus_num = 1
        self.addr = 0x08
        try:
            self.bus = smbus2.SMBus(self.bus_num)
            self.get_logger().info(f"Ultrasonic node initialized at I2C {hex(self.addr)}")
        except Exception as e:
            self.get_logger().error(f"Failed to open I2C bus {self.bus_num}: {e}")
            self.bus = None

        self.timer = self.create_timer(0.1, self.read_sensor)
        
        # Filtering state
        self.MIN_HITS = 3
        self.us_data = [2.0, 2.0] # Current published values
        self.us_counters = [0, 0] # Counters for stable readings
        self.last_raw = [2.0, 2.0] # Last raw readings seen

    def read_sensor(self):
        if self.bus is None:
            return

        try:
            # Reading from indices 0 and 1 for the 2 sensors (values in cm)
            raw_cm = [
                self.bus.read_byte_data(self.addr, 0),
                self.bus.read_byte_data(self.addr, 1)
            ]
            
            for i in range(2):
                val_m = float(raw_cm[i]) / 100.0
                
                # If reading is similar to last raw, increment stable counter
                # Using a 5cm tolerance for 'stable'
                if abs(val_m - self.last_raw[i]) < 0.05:
                    self.us_counters[i] += 1
                else:
                    self.us_counters[i] = 0
                    self.last_raw[i] = val_m
                
                # Update published data only if stable for N hits
                if self.us_counters[i] >= self.MIN_HITS:
                    self.us_data[i] = val_m
            
            # Publish Front Left
            self.pub_left.publish(self.create_range_msg('ultrasonic_front_left', self.us_data[0]))
            
            # Publish Front Right
            self.pub_right.publish(self.create_range_msg('ultrasonic_front_right', self.us_data[1]))

        except Exception as e:
            self.get_logger().warn(f"Ultrasonic read error: {e}")

    def create_range_msg(self, frame_id, distance_m):
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = 0.523 # Approx 30 degrees
        msg.min_range = 0.02
        msg.max_range = 2.0
        msg.range = distance_m
        return msg

def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            if node.bus:
                node.bus.close()
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()