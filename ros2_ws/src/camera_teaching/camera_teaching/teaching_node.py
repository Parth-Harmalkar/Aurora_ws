#!/usr/bin/env python3
import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from vision_msgs.msg import Detection3DArray, Detection3D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
import os
import cv2
import numpy as np
import math
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import Marker, MarkerArray
from camera_teaching.srv import GetObjectPose, ListObjects

class TeachingNode(Node):
    def __init__(self):
        super().__init__('teaching_node')
        
        # 1. Configuration
        self.target_width = 640
        self.target_height = 360
        self.labels = [
            "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair",
            "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
        ]
        
        # Simple list to hold detections from the current frame
        self.current_detections = [] 

        # 2. Publishers
        self.pub_color = self.create_publisher(Image, 'camera/color/image_raw', 10)
        self.pub_depth = self.create_publisher(Image, 'camera/depth/image_raw', 10)
        self.pub_debug = self.create_publisher(Image, 'camera/color/image_debug', 10)
        self.pub_info = self.create_publisher(CameraInfo, 'camera/color/camera_info', 10)
        self.pub_depth_info = self.create_publisher(CameraInfo, 'camera/depth/camera_info', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/semantic_map', 10)
        self.bridge = CvBridge()

        # 3. Services
        self.srv_get = self.create_service(GetObjectPose, 'get_object_pose', self.get_object_pose_callback)
        self.srv_list = self.create_service(ListObjects, 'list_objects', self.list_objects_callback)

        # 4. DepthAI Pipeline Initialization
        self.pipeline = dai.Pipeline()
        self.setup_pipeline()
        
        try:
            self.device = dai.Device(self.pipeline)
            self.get_logger().info("OAK-D Teacher Mode (Real-Time Only): Initialized.")
            
            # Calibration
            calibData = self.device.readCalibration()
            intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, self.target_width, self.target_height)
            self.camera_info_msg = self.build_camera_info(self.target_width, self.target_height, intrinsics)
            
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            self.det_queue = self.device.getOutputQueue(name="det", maxSize=4, blocking=False)
        except Exception as e:
            self.get_logger().error(f"Failed to start camera: {e}")
            return

        self.timer = self.create_timer(0.1, self.timer_callback)

    def setup_pipeline(self):
        # RGB
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setIspScale(1, 3) # 640x360
        cam_rgb.setFps(10)
        cam_rgb.setInterleaved(False)

        # Depth
        mono_left = self.pipeline.create(dai.node.MonoCamera)
        mono_right = self.pipeline.create(dai.node.MonoCamera)
        stereo = self.pipeline.create(dai.node.StereoDepth)
        
        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.CAM_C)
        
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A) # Align to RGB
        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)

        # NN 
        spatial_nn = self.pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
        pkg_share = get_package_share_directory('camera_teaching')
        model_path = os.path.join(pkg_share, 'models', 'mobilenet-ssd_openvino_2021.4_6shave.blob')
        spatial_nn.setBlobPath(model_path)
        spatial_nn.setConfidenceThreshold(0.5)
        spatial_nn.input.setBlocking(False)
        spatial_nn.setBoundingBoxScaleFactor(0.5)
        
        # Links
        cam_rgb.preview.link(spatial_nn.input)
        stereo.depth.link(spatial_nn.inputDepth)

        # XOut
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.isp.link(xout_rgb.input)

        xout_depth = self.pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

        xout_nn = self.pipeline.create(dai.node.XLinkOut)
        xout_nn.setStreamName("det")
        spatial_nn.out.link(xout_nn.input)

    def build_camera_info(self, width, height, intrinsics):
        info = CameraInfo()
        info.width = width
        info.height = height
        info.distortion_model = "plumb_bob"
        info.k = [intrinsics[0][0], intrinsics[0][1], intrinsics[0][2],
                  intrinsics[1][0], intrinsics[1][1], intrinsics[1][2],
                  intrinsics[2][0], intrinsics[2][1], intrinsics[2][2]]
        info.p = [intrinsics[0][0], intrinsics[0][1], intrinsics[0][2], 0.0,
                  intrinsics[1][0], intrinsics[1][1], intrinsics[1][2], 0.0,
                  intrinsics[2][0], intrinsics[2][1], intrinsics[2][2], 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        return info

    def timer_callback(self):
        in_rgb = self.rgb_queue.tryGet()
        in_depth = self.depth_queue.tryGet()
        in_det = self.det_queue.tryGet()
        
        now = self.get_clock().now().to_msg()
        
        # Clear detections for the new frame
        self.current_detections = []

        if in_rgb is not None:
            cv_frame = in_rgb.getCvFrame()
            debug_frame = cv_frame.copy()

            # Process Detections
            if in_det is not None:
                for det in in_det.detections:
                    if det.spatialCoordinates.z == 0: continue
                    
                    label = self.labels[det.label]
                    conf = det.confidence
                    
                    # Store as a real-time detection (mm -> meters)
                    self.current_detections.append({
                        'label': label,
                        'conf': conf,
                        'x': det.spatialCoordinates.x / 1000.0,
                        'y': det.spatialCoordinates.y / 1000.0,
                        'z': det.spatialCoordinates.z / 1000.0
                    })

                    # Draw on debug frame
                    h, w = debug_frame.shape[:2]
                    x1, y1 = int(det.xmin * w), int(det.ymin * h)
                    x2, y2 = int(det.xmax * w), int(det.ymax * h)
                    
                    cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    text = f"{label} ({conf:.2f})"
                    cv2.putText(debug_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Publish Color / Debug
            raw_msg = self.bridge.cv2_to_imgmsg(cv_frame, encoding="bgr8")
            raw_msg.header.stamp = now
            raw_msg.header.frame_id = "camera_optical_frame"
            self.pub_color.publish(raw_msg)
            
            debug_msg = self.bridge.cv2_to_imgmsg(debug_frame, encoding="bgr8")
            debug_msg.header.stamp = now
            debug_msg.header.frame_id = "camera_optical_frame"
            self.pub_debug.publish(debug_msg)

            self.camera_info_msg.header = raw_msg.header
            self.pub_info.publish(self.camera_info_msg)

        if in_depth is not None:
            depth_frame = in_depth.getFrame()
            if depth_frame.shape[1] != self.target_width:
                depth_frame = cv2.resize(depth_frame, (self.target_width, self.target_height), interpolation=cv2.INTER_NEAREST)
            
            msg = self.bridge.cv2_to_imgmsg(depth_frame, encoding="16UC1")
            msg.header.stamp = now
            msg.header.frame_id = "camera_optical_frame"
            self.pub_depth.publish(msg)
            
            self.camera_info_msg.header = msg.header
            self.pub_depth_info.publish(self.camera_info_msg)

        self.publish_markers()

    def publish_markers(self):
        """Publish 3D markers for currently visible objects only."""
        marker_array = MarkerArray()
        
        # Clear previous markers to avoid "ghosts"
        clear_marker = Marker()
        clear_marker.action = Marker.DELETEALL
        marker_array.markers.append(clear_marker)
        
        for i, det in enumerate(self.current_detections):
            # Sphere
            m = Marker()
            m.header.frame_id = "camera_optical_frame"
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = "real_time_objects"
            m.id = i
            m.type = Marker.SPHERE
            m.action = Marker.ADD
            m.pose.position.x = det['x']
            m.pose.position.y = det['y']
            m.pose.position.z = det['z']
            m.scale.x = m.scale.y = m.scale.z = 0.2
            m.color.r, m.color.g, m.color.b, m.color.a = 0.0, 1.0, 0.0, 0.8
            marker_array.markers.append(m)
            
            # Label
            t = Marker()
            t.header.frame_id = "camera_optical_frame"
            t.header.stamp = m.header.stamp
            t.ns = "real_time_labels"
            t.id = i
            t.type = Marker.TEXT_VIEW_FACING
            t.pose.position.x = det['x']
            t.pose.position.y = det['y'] - 0.2
            t.pose.position.z = det['z']
            t.scale.z = 0.1
            t.color.r = t.color.g = t.color.b = t.color.a = 1.0
            t.text = f"{det['label']} ({det['conf']:.2f})"
            marker_array.markers.append(t)
            
        self.pub_markers.publish(marker_array)

    def get_object_pose_callback(self, request, response):
        """Find the highest confidence detection of the requested label in the CURRENT frame."""
        matches = [d for d in self.current_detections if d['label'] == request.label]
        if matches:
            best = max(matches, key=lambda d: d['conf'])
            response.success = True
            response.pose.header.frame_id = "camera_optical_frame"
            response.pose.header.stamp = self.get_clock().now().to_msg()
            response.pose.pose.position.x = best['x']
            response.pose.pose.position.y = best['y']
            response.pose.pose.position.z = best['z']
            response.pose.pose.orientation.w = 1.0
            return response
        
        response.success = False
        response.message = f"Object '{request.label}' not currently visible."
        return response

    def list_objects_callback(self, request, response):
        """List everything the camera has detected in the CURRENT frame."""
        response.labels = []
        response.poses = []
        for det in self.current_detections:
            response.labels.append(det['label'])
            p = PoseStamped()
            p.header.frame_id = "camera_optical_frame"
            p.header.stamp = self.get_clock().now().to_msg()
            p.pose.position.x = det['x']
            p.pose.position.y = det['y']
            p.pose.position.z = det['z']
            p.pose.orientation.w = 1.0
            response.poses.append(p)
        response.success = True
        return response

def main(args=None):
    rclpy.init(args=args)
    node = TeachingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(node, 'device'):
            node.device.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
