import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, Imu
from cv_bridge import CvBridge
import cv2
import numpy as np

class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')
        self.publisher = self.create_publisher(Image, 'camera/image_raw', 10)
        self.depth_publisher = self.create_publisher(Image, 'camera/depth', 10)
        self.info_publisher = self.create_publisher(CameraInfo, 'camera/camera_info', 10)
        self.imu_publisher = self.create_publisher(Imu, 'camera/imu', 10)
        self.bridge = CvBridge()

        # Target resolution for both RGB and depth (must match for RTAB-Map)
        self.target_width = 640
        self.target_height = 360

        # Create pipeline
        self.pipeline = dai.Pipeline()

        # RGB Camera
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)

        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setIspScale(1, 3) # 1920x1080 -> 640x360 (Good balance for 3D mapping)
        cam_rgb.setFps(10) # Lower FPS to keep Jetson CPU manageable at higher res

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
        # Align depth to RGB camera viewpoint
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A) 

        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)

        # IMU (BMI270)
        imu = self.pipeline.create(dai.node.IMU)
        # Enable Accel + Gyro at 100Hz
        imu.enableIMUSensor([dai.IMUSensor.ACCELEROMETER_RAW, dai.IMUSensor.GYROSCOPE_RAW], 100)
        imu.setBatchReportThreshold(1)
        imu.setMaxBatchReports(10)

        # Outputs
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.isp.link(xout_rgb.input)

        xout_depth = self.pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

        xout_imu = self.pipeline.create(dai.node.XLinkOut)
        xout_imu.setStreamName("imu")
        imu.out.link(xout_imu.input)

        # Device connection
        try:
            self.device = dai.Device(self.pipeline)
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.imu_queue = self.device.getOutputQueue(name="imu", maxSize=10, blocking=False)
            self.get_logger().info("Oak-D Lite Camera (with BMI270 IMU) initialized")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Oak-D Lite: {e}")
            self.device = None
            return

        # Get Calibration for the target resolution
        calibData = self.device.readCalibration()
        self.intrinsics = calibData.getCameraIntrinsics(
            dai.CameraBoardSocket.RGB, self.target_width, self.target_height
        )
        self.camera_info_msg = self.build_camera_info(
            self.target_width, self.target_height, self.intrinsics
        )

        self.timer = self.create_timer(0.05, self.timer_callback)  # 20Hz

    def build_camera_info(self, width, height, intrinsics):
        info = CameraInfo()
        info.width = width
        info.height = height
        info.distortion_model = "plumb_bob"
        # K matrix (3x3 intrinsics)
        info.k = [
            intrinsics[0][0], intrinsics[0][1], intrinsics[0][2],
            intrinsics[1][0], intrinsics[1][1], intrinsics[1][2],
            intrinsics[2][0], intrinsics[2][1], intrinsics[2][2]
        ]
        # P matrix (3x4 projection)
        info.p = [
            intrinsics[0][0], intrinsics[0][1], intrinsics[0][2], 0.0,
            intrinsics[1][0], intrinsics[1][1], intrinsics[1][2], 0.0,
            intrinsics[2][0], intrinsics[2][1], intrinsics[2][2], 0.0
        ]
        # R matrix (identity for monocular)
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        # D vector (zero distortion — OAK-D ISP already rectifies)
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
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
            # Publish in camera_optical_frame (Z-forward, X-right, Y-down)
            # This is what RTAB-Map and all ROS vision tools expect
            msg.header.frame_id = "camera_optical_frame"
            self.publisher.publish(msg)
            
            # Publish CameraInfo with matching header
            self.camera_info_msg.header = msg.header
            self.info_publisher.publish(self.camera_info_msg)

        if in_depth is not None:
            depth_frame = in_depth.getFrame()  # uint16, millimeters
            
            # Resize depth to match RGB resolution (required for RTAB-Map pixel correspondence)
            h, w = depth_frame.shape[:2]
            if w != self.target_width or h != self.target_height:
                depth_frame = cv2.resize(
                    depth_frame,
                    (self.target_width, self.target_height),
                    interpolation=cv2.INTER_NEAREST  # Nearest-neighbor for depth (no blending)
                )
            
            # Publish with explicit encoding so RTAB-Map knows it's mm depth
            msg = self.bridge.cv2_to_imgmsg(depth_frame, encoding="16UC1")
            msg.header.stamp = now
            msg.header.frame_id = "camera_optical_frame"
            self.depth_publisher.publish(msg)

        # Process IMU
        imu_data = self.imu_queue.tryGet()
        if imu_data is not None:
            packets = imu_data.packets
            for packet in packets:
                accel = packet.acceleroMeter
                gyro = packet.gyroscope
                
                imu_msg = Imu()
                imu_msg.header.stamp = self.get_clock().now().to_msg()
                imu_msg.header.frame_id = "camera_imu_optical_frame"
                
                # OAK-D IMU is usually aligned with camera_link
                # Accelerometer (m/s^2)
                imu_msg.linear_acceleration.x = float(accel.x)
                imu_msg.linear_acceleration.y = float(accel.y)
                imu_msg.linear_acceleration.z = float(accel.z)
                
                # Gyroscope (rad/s)
                imu_msg.angular_velocity.x = float(gyro.x)
                imu_msg.angular_velocity.y = float(gyro.y)
                imu_msg.angular_velocity.z = float(gyro.z)
                
                # Orientation is usually fused in EKF, but we can set identity covariance for unused fields
                imu_msg.orientation_covariance = [0.0] * 9
                imu_msg.angular_velocity_covariance = [0.0] * 9
                imu_msg.linear_acceleration_covariance = [0.0] * 9
                
                self.imu_publisher.publish(imu_msg)

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