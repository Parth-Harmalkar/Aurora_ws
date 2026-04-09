import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, Imu
from vision_msgs.msg import Detection3DArray, Detection3D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
import os
import cv2
import numpy as np

class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')
        
        # Declare Parameters
        self.declare_parameter('confidence_threshold', 0.5)
        self.conf_threshold = self.get_parameter('confidence_threshold').get_parameter_value().double_value

        # 2. Publishers with Industry Standard Naming
        self.publisher = self.create_publisher(Image, 'camera/color/image_raw', 10)
        self.depth_publisher = self.create_publisher(Image, 'camera/depth/image_raw', 10)
        self.info_publisher = self.create_publisher(CameraInfo, 'camera/color/camera_info', 10)
        self.depth_info_publisher = self.create_publisher(CameraInfo, 'camera/depth/camera_info', 10)
        self.imu_publisher = self.create_publisher(Imu, 'camera/imu/data', 10)
        self.det_publisher = self.create_publisher(Detection3DArray, 'camera/detections', 10)
        self.bridge = CvBridge()

        # MobileNet-SSD Label Map (21 classes for PASCAL VOC)
        self.labels = [
            "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair",
            "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
        ]

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
        cam_rgb.setPreviewKeepAspectRatio(False)
        cam_rgb.setPreviewSize(300, 300) # Required for MobileNet-SSD
        cam_rgb.setInterleaved(False) # Optimization: NN expects planar (CHW) data

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

        # Spatial Detection Network
        spatial_nn = self.pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
        # We will attempt to load the blob from our package's share directory
        try:
            package_share = get_package_share_directory('aurora_camera')
            model_path = os.path.join(package_share, 'models', 'mobilenet-ssd_openvino_2021.4_6shave.blob')
            spatial_nn.setBlobPath(model_path)
            self.get_logger().info(f"Loaded MobileNet-SSD blob from: {model_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load MobileNet-SSD blob: {e}")
            # We don't return here so the node still streams images, but detection will fail
        
        spatial_nn.setConfidenceThreshold(self.conf_threshold)
        spatial_nn.input.setBlocking(False)
        spatial_nn.setBoundingBoxScaleFactor(0.5)
        spatial_nn.setDepthLowerThreshold(100)
        spatial_nn.setDepthUpperThreshold(5000)

        # Links
        cam_rgb.preview.link(spatial_nn.input)
        stereo.depth.link(spatial_nn.inputDepth)

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

        xout_nn = self.pipeline.create(dai.node.XLinkOut)
        xout_nn.setStreamName("det")
        spatial_nn.out.link(xout_nn.input)

        # Device connection
        try:
            self.device = dai.Device(self.pipeline)
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.imu_queue = self.device.getOutputQueue(name="imu", maxSize=10, blocking=False)
            self.det_queue = self.device.getOutputQueue(name="det", maxSize=4, blocking=False)
            
            # OAK-D Pro specific: Enable IR Dot Projector (Intensity: 0.0 to 1.0)
            # Commenting out as some DepthAI versions use different method names or aren't detecting the Pro model correctly
            # try:
            #     self.device.setIrLaserDotProjectorIntensity(0.5)
            #     self.get_logger().info("Oak-D Pro: IR Dot Projector enabled (Intensity: 0.5)")
            # except Exception as e:
            #     self.get_logger().warn(f"Failed to enable IR Projector (might be a non-Pro model): {e}")

            self.get_logger().info("Oak-D Pro Camera (IMU + Detection initialized) ready.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Oak-D Pro: {e}")
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

        self.timer = self.create_timer(0.1, self.timer_callback)  # 10Hz (Freshness Optimized)

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

        # Freshness Check: Drain all old frames
        in_rgb = None
        while True:
            tmp = self.rgb_queue.tryGet()
            if tmp is None: break
            in_rgb = tmp
        in_depth = None
        while True:
            tmp = self.depth_queue.tryGet()
            if tmp is None: break
            in_depth = tmp
        in_det = None
        while True:
            tmp = self.det_queue.tryGet()
            if tmp is None: break
            in_det = tmp

        now = self.get_clock().now().to_msg()

        if in_det is not None:
            detections = in_det.detections
            msg = Detection3DArray()
            msg.header.stamp = now
            msg.header.frame_id = "camera_optical_frame"
            
            for det in detections:
                d3d = Detection3D()
                
                # Filter out invalid depth measurements (where OAK-D returns 0.0 when out of range or ROI fails)
                if det.spatialCoordinates.z == 0.0:
                    continue
                    
                # Spatial coordinates (translated from mm to meters)
                # OAK-D uses: X-right, Y-down, Z-forward (matching optical frame)
                d3d.bbox.center.position.x = det.spatialCoordinates.x / 1000.0
                d3d.bbox.center.position.y = det.spatialCoordinates.y / 1000.0
                d3d.bbox.center.position.z = det.spatialCoordinates.z / 1000.0
                
                hyp = ObjectHypothesisWithPose()
                label_id = int(det.label)
                hyp.hypothesis.class_id = self.labels[label_id] if label_id < len(self.labels) else str(label_id)
                hyp.hypothesis.score = float(det.confidence)
                
                d3d.results.append(hyp)
                msg.detections.append(d3d)
            
            self.det_publisher.publish(msg)

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
            
            # Publish matching CameraInfo for depth
            self.camera_info_msg.header = msg.header
            self.depth_info_publisher.publish(self.camera_info_msg)

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
        # Avoid potential double-shutdown error if rclpy was already shut down
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()