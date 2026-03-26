import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np

class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')
        self.publisher = self.create_publisher(Image, 'camera/image_raw', 10)
        self.depth_publisher = self.create_publisher(Image, 'camera/depth', 10)
        self.info_publisher = self.create_publisher(CameraInfo, 'camera/camera_info', 10)
        self.bridge = CvBridge()

        # Create pipeline
        self.pipeline = dai.Pipeline()

        # RGB Camera
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)

        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setIspScale(1, 6) # 1920x1080 -> 320x180 (Ultra-light for Jetson 4GB)
        cam_rgb.setFps(20) # Lower FPS for bandwidth

        # Stereo Depth
        mono_left = self.pipeline.create(dai.node.MonoCamera)
        mono_right = self.pipeline.create(dai.node.MonoCamera)
        stereo = self.pipeline.create(dai.node.StereoDepth)

        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setLeftRightCheck(True)
        stereo.setSubpixel(True)
        # Use RGB for alignment
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A) 

        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)

        # Outputs
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.isp.link(xout_rgb.input)

        xout_depth = self.pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

        # Device connection
        try:
            self.device = dai.Device(self.pipeline)
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.get_logger().info("Oak-D Lite Camera with Stereo Depth initialized")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Oak-D Lite: {e}")
            self.device = None
            return

        # Get Calibration
        calibData = self.device.readCalibration()
        self.intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.RGB, 320, 180) # Match ISP scale
        self.camera_info_msg = self.get_camera_info(320, 180, self.intrinsics)

        self.timer = self.create_timer(0.033, self.timer_callback)

    def get_camera_info(self, width, height, intrinsics):
        info = CameraInfo()
        info.width = width
        info.height = height
        info.distortion_model = "plumb_bob"
        # K matrix
        info.k = [
            intrinsics[0][0], intrinsics[0][1], intrinsics[0][2],
            intrinsics[1][0], intrinsics[1][1], intrinsics[1][2],
            intrinsics[2][0], intrinsics[2][1], intrinsics[2][2]
        ]
        # P matrix (same as K for this simple case)
        info.p = [
            intrinsics[0][0], intrinsics[0][1], intrinsics[0][2], 0.0,
            intrinsics[1][0], intrinsics[1][1], intrinsics[1][2], 0.0,
            intrinsics[2][0], intrinsics[2][1], intrinsics[2][2], 0.0
        ]
        return info

    def timer_callback(self):
        if self.device is None:
            return

        in_rgb = self.rgb_queue.tryGet()
        in_depth = self.depth_queue.tryGet()

        now = self.get_clock().now().to_msg()

        if in_rgb is not None:
            frame = in_rgb.getCvFrame()
            msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            msg.header.stamp = now
            msg.header.frame_id = "camera_link"
            self.publisher.publish(msg)
            
            # Publish Info
            self.camera_info_msg.header = msg.header
            self.info_publisher.publish(self.camera_info_msg)

        if in_depth is not None:
            depth_frame = in_depth.getFrame() # in mm
            msg = self.bridge.cv2_to_imgmsg(depth_frame, encoding="passthrough")
            msg.header.stamp = now
            msg.header.frame_id = "camera_link"
            self.depth_publisher.publish(msg)

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