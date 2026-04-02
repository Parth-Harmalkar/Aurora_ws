import os
import sqlite3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from vision_msgs.msg import Detection3DArray
from aurora_msgs.srv import GetObjectPose, QueryObject, ListObjects
from geometry_msgs.msg import PoseStamped, Point
import tf2_ros
import tf2_geometry_msgs
from visualization_msgs.msg import Marker, MarkerArray
import math

class SemanticMemoryNode(Node):
    def __init__(self):
        super().__init__('semantic_memory_node')
        
        # Parameters
        self.declare_parameter('db_path', os.path.expanduser('~/.aurora/spatial_objects.db'))
        self.declare_parameter('clustering_threshold', 0.5)  # meters
        
        self.db_path = self.get_parameter('db_path').get_parameter_value().string_value
        self.clustering_threshold = self.get_parameter('clustering_threshold').get_parameter_value().double_value
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize Database
        self.conn = sqlite3.connect(self.db_path)
        self.init_db()
        
        # TF Buffer and Listener
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Subscriber
        self.subscription = self.create_subscription(
            Detection3DArray,
            '/camera/detections',
            self.detection_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )
        
        # Services
        self.srv_get = self.create_service(GetObjectPose, 'get_object_pose', self.get_object_pose_callback)
        self.srv_query = self.create_service(QueryObject, 'query_object', self.query_object_callback)
        self.srv_list = self.create_service(ListObjects, 'list_objects', self.list_objects_callback)
        
        # Marker Publisher
        self.marker_pub = self.create_publisher(MarkerArray, '/semantic_map', 10)
        
        # Timer for visualization (1Hz)
        self.create_timer(1.0, self.publish_markers)
        
        self.get_logger().info(f"Semantic Memory Node started. DB: {self.db_path}")

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL,
                confidence REAL NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        self.conn.commit()

    def detection_callback(self, msg):
        for detection in msg.detections:
            label = detection.results[0].hypothesis.class_id
            confidence = detection.results[0].hypothesis.score
            
            # Position in camera frame
            point_in_camera = detection.bbox.center.position
            
            # Transform to map frame
            try:
                # 1. Attempt exact timestamp lookup
                transform = self.tf_buffer.lookup_transform(
                    'map', 
                    msg.header.frame_id, 
                    msg.header.stamp,
                    rclpy.duration.Duration(seconds=0.1) # Shorter initial wait
                )
            except (tf2_ros.LookupException, tf2_ros.ExtrapolationException, tf2_ros.ConnectivityException):
                try:
                    # 2. Fallback to latest available transform if SLAM is lagging
                    self.get_logger().warning(
                        f"SLAM lag detected for {label}. Falling back to latest available transform.",
                        throttle_duration_sec=10.0
                    )
                    transform = self.tf_buffer.lookup_transform(
                        'map', 
                        msg.header.frame_id, 
                        rclpy.time.Time(), # Latest available
                        rclpy.duration.Duration(seconds=0.5)
                    )
                except Exception as e:
                    self.get_logger().error(f"Failed to transform {label} even with fallback: {e}", throttle_duration_sec=5.0)
                    continue

            try:
                point_stamped = tf2_geometry_msgs.PointStamped()
                point_stamped.header = msg.header
                point_stamped.point = point_in_camera
                
                point_in_map = tf2_geometry_msgs.do_transform_point(point_stamped, transform).point
                
                # Associated with existing objects
                self.associate_and_store(label, point_in_map, confidence)
                
            except Exception as e:
                self.get_logger().error(f"Error processing detection: {e}")

    def associate_and_store(self, label, point, confidence):
        cursor = self.conn.cursor()
        
        # Query for potential matches
        cursor.execute("SELECT id, x, y, z FROM objects WHERE label = ?", (label,))
        rows = cursor.fetchall()
        
        match_id = None
        for row in rows:
            obj_id, ox, oy, oz = row
            dist = math.sqrt((point.x - ox)**2 + (point.y - oy)**2 + (point.z - oz)**2)
            if dist < self.clustering_threshold:
                match_id = obj_id
                break
        
        if match_id:
            # Update existing (Simple Exponential Moving Average for position)
            alpha = 0.2
            cursor.execute('''
                UPDATE objects 
                SET x = (1-?) * x + ? * ?,
                    y = (1-?) * y + ? * ?,
                    z = (1-?) * z + ? * ?,
                    confidence = ?,
                    timestamp = ?
                WHERE id = ?
            ''', (alpha, alpha, point.x, alpha, alpha, point.y, alpha, alpha, point.z, 
                  confidence, self.get_clock().now().nanoseconds / 1e9, match_id))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO objects (label, x, y, z, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (label, point.x, point.y, point.z, confidence, self.get_clock().now().nanoseconds / 1e9))
            
        self.conn.commit()

    def get_object_pose_callback(self, request, response):
        cursor = self.conn.cursor()
        cursor.execute("SELECT x, y, z FROM objects WHERE label = ? ORDER BY confidence DESC LIMIT 1", (request.label,))
        row = cursor.fetchone()
        
        if row:
            response.success = True
            response.pose.header.frame_id = 'map'
            response.pose.header.stamp = self.get_clock().now().to_msg()
            response.pose.pose.position.x = row[0]
            response.pose.pose.position.y = row[1]
            response.pose.pose.position.z = row[2]
            response.pose.pose.orientation.w = 1.0  # Identity orientation
            response.message = f"Found {request.label} in memory."
        else:
            response.success = False
            response.message = f"Object '{request.label}' not found."
        
        return response
        
    def query_object_callback(self, request, response):
        # QueryObject has the same structure as GetObjectPose
        return self.get_object_pose_callback(request, response)

    def list_objects_callback(self, request, response):
        cursor = self.conn.cursor()
        # Get the highest confidence entry for each unique label
        cursor.execute('''
            SELECT label, x, y, z 
            FROM objects 
            GROUP BY label 
            ORDER BY confidence DESC
        ''')
        rows = cursor.fetchall()
        
        response.labels = []
        response.poses = []
        
        for row in rows:
            label, x, y, z = row
            response.labels.append(label)
            
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.position.z = z
            pose.pose.orientation.w = 1.0
            response.poses.append(pose)
            
        response.success = True
        return response

    def publish_markers(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, label, x, y, z FROM objects")
        rows = cursor.fetchall()
        
        marker_array = MarkerArray()
        for row in rows:
            obj_id, label, x, y, z = row
            
            # Text Marker (Label)
            text_marker = Marker()
            text_marker.header.frame_id = "map"
            text_marker.header.stamp = self.get_clock().now().to_msg()
            text_marker.ns = "semantic_labels"
            text_marker.id = obj_id
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = x
            text_marker.pose.position.y = y
            text_marker.pose.position.z = z + 0.3
            text_marker.scale.z = 0.1
            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 1.0
            text_marker.text = f"{label} #{obj_id}"
            marker_array.markers.append(text_marker)
            
            # Sphere Marker (Point)
            sphere_marker = Marker()
            sphere_marker.header.frame_id = "map"
            sphere_marker.header.stamp = self.get_clock().now().to_msg()
            sphere_marker.ns = "semantic_objects"
            sphere_marker.id = obj_id
            sphere_marker.type = Marker.SPHERE
            sphere_marker.action = Marker.ADD
            sphere_marker.pose.position.x = x
            sphere_marker.pose.position.y = y
            sphere_marker.pose.position.z = z
            sphere_marker.scale.x = 0.2
            sphere_marker.scale.y = 0.2
            sphere_marker.scale.z = 0.2
            sphere_marker.color.r = 0.0
            sphere_marker.color.g = 1.0
            sphere_marker.color.b = 0.0
            sphere_marker.color.a = 0.6
            marker_array.markers.append(sphere_marker)
            
        self.marker_pub.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    node = SemanticMemoryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.conn.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
