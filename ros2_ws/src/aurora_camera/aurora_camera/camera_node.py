import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')
        self.publisher = self.create_publisher(Image, 'camera/image_raw', 10)
        self.bridge = CvBridge()

        self.get_logger().info(f"DepthAI version: {dai.__version__}")
        self.get_logger().info(f"DepthAI location: {dai.__file__}")

        # Create pipeline
        self.pipeline = dai.Pipeline()

        # Define source and output using newer API if possible
        try:
            cam_rgb = self.pipeline.create(dai.node.Camera)
            cam_rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
            self.get_logger().info("Using dai.node.Camera")
        except AttributeError:
            cam_rgb = self.pipeline.create(dai.node.ColorCamera)
            cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
            self.get_logger().info("Using dai.node.ColorCamera")

        xout_video = self.pipeline.create(dai.node.XLinkOut)
        xout_video.setStreamName("video")

        # Properties
        cam_rgb.setSize(640, 480)
        
        # Linking
        cam_rgb.video.link(xout_video.input)

        # Device connection
        try:
            self.device = dai.Device(self.pipeline)
            self.video_queue = self.device.getOutputQueue(name="video", maxSize=4, blocking=False)
            self.get_logger().info("Oak-D Lite Camera initialized")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Oak-D Lite: {e}")
            self.device = None

        self.timer = self.create_timer(0.033, self.timer_callback) # ~30 FPS

    def timer_callback(self):
        if self.device is None:
            return

        in_video = self.video_queue.tryGet()
        if in_video is not None:
            frame = in_video.getCvFrame()
            msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "camera_frame"
            self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.device:
            node.device.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()