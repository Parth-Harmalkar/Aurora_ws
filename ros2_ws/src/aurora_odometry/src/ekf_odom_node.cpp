/*
 * Aurora EKF Odometry Publisher - PORTED FROM ARJUNA2_WS
 * Remaps /odometry/filtered to /odom for Nav2 compatibility
 */

#include <memory>
#include <cmath>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int64.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_ros/transform_broadcaster.h"
#include "geometry_msgs/msg/transform_stamped.hpp"

class AuroraEKFOdomPublisher : public rclcpp::Node
{
public:
    AuroraEKFOdomPublisher() : Node("aurora_odom_node")
    {
        // ROS2 standard remapping handled via launch, but we set default to false for TF
        this->declare_parameter("publish_tf", false); 
        publish_tf_ = this->get_parameter("publish_tf").as_bool();
        
        // Hardware Constants (Verified from arjuna2_ws)
        WHEEL_RADIUS = 0.04;
        WHEEL_BASE = 0.28;
        TICKS_PER_METER = 20475.0;
        PI = 3.141592653589793;
        
        robot_x = 0.0;
        robot_y = 0.0;
        robot_theta = 0.0;
        
        lastCountL = 0;
        lastCountR = 0;
        distanceLeft = 0.0;
        distanceRight = 0.0;
        first_left_received = true;
        first_right_received = true;
        
        linear_velocity = 0.0;
        angular_velocity = 0.0;
        
        last_time = this->now();
        
        // Publishers
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("wheel/odom", 10);
        
        // Subscribers
        right_ticks_sub_ = this->create_subscription<std_msgs::msg::Int64>(
            "right_ticks", 10, 
            std::bind(&AuroraEKFOdomPublisher::calc_right, this, std::placeholders::_1));
        left_ticks_sub_ = this->create_subscription<std_msgs::msg::Int64>(
            "left_ticks", 10, 
            std::bind(&AuroraEKFOdomPublisher::calc_left, this, std::placeholders::_1));
        
        // TF broadcaster (if enabled)
        if (publish_tf_) {
            tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
        }
        
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(33),
            std::bind(&AuroraEKFOdomPublisher::update_odom, this));
        
        RCLCPP_INFO(this->get_logger(), "Aurora Odometry Node Started (Base: %.2f, Radius: %.2f)", WHEEL_BASE, WHEEL_RADIUS);
    }

private:
    void calc_left(const std_msgs::msg::Int64::SharedPtr msg)
    {
        if (first_left_received) {
            first_left_received = false;
            lastCountL = msg->data;
            return;
        }
        int64_t leftTicks = msg->data - lastCountL;
        distanceLeft = static_cast<double>(leftTicks) / TICKS_PER_METER;
        lastCountL = msg->data;
    }
    
    void calc_right(const std_msgs::msg::Int64::SharedPtr msg)
    {
        if (first_right_received) {
            first_right_received = false;
            lastCountR = msg->data;
            return;
        }
        int64_t rightTicks = msg->data - lastCountR;
        distanceRight = static_cast<double>(rightTicks) / TICKS_PER_METER;
        lastCountR = msg->data;
    }
    
    void update_odom()
    {
        rclcpp::Time current_time = this->now();
        double dt = (current_time - last_time).seconds();
        
        double distance_center = (distanceRight + distanceLeft) / 2.0;
        double delta_theta = (distanceRight - distanceLeft) / WHEEL_BASE;
        
        double delta_x = distance_center * cos(robot_theta + delta_theta / 2.0);
        double delta_y = distance_center * sin(robot_theta + delta_theta / 2.0);
        
        robot_x += delta_x;
        robot_y += delta_y;
        robot_theta += delta_theta;
        
        // Normalize theta
        while (robot_theta > PI) robot_theta -= 2.0 * PI;
        while (robot_theta < -PI) robot_theta += 2.0 * PI;
        
        if (dt > 0.001) {
            linear_velocity = distance_center / dt;
            angular_velocity = delta_theta / dt;
        }
        
        publish_odometry(current_time);
        
        if (publish_tf_) broadcast_tf(current_time);
        
        distanceLeft = 0.0;
        distanceRight = 0.0;
        last_time = current_time;
    }
    
    void publish_odometry(const rclcpp::Time& stamp)
    {
        tf2::Quaternion q;
        q.setRPY(0.0, 0.0, robot_theta);
        
        nav_msgs::msg::Odometry odom_msg;
        odom_msg.header.stamp = stamp;
        odom_msg.header.frame_id = "odom";
        odom_msg.child_frame_id = "base_link";
        
        odom_msg.pose.pose.position.x = robot_x;
        odom_msg.pose.pose.position.y = robot_y;
        odom_msg.pose.pose.orientation.x = q.x();
        odom_msg.pose.pose.orientation.y = q.y();
        odom_msg.pose.pose.orientation.z = q.z();
        odom_msg.pose.pose.orientation.w = q.w();
        
        odom_msg.twist.twist.linear.x = linear_velocity;
        odom_msg.twist.twist.angular.z = angular_velocity;
        
        odom_pub_->publish(odom_msg);
    }
    
    void broadcast_tf(const rclcpp::Time& stamp)
    {
        geometry_msgs::msg::TransformStamped t;
        t.header.stamp = stamp;
        t.header.frame_id = "odom";
        t.child_frame_id = "base_link";
        t.transform.translation.x = robot_x;
        t.transform.translation.y = robot_y;
        
        tf2::Quaternion q;
        q.setRPY(0.0, 0.0, robot_theta);
        t.transform.rotation.x = q.x();
        t.transform.rotation.y = q.y();
        t.transform.rotation.z = q.z();
        t.transform.rotation.w = q.w();
        
        tf_broadcaster_->sendTransform(t);
    }
    
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Subscription<std_msgs::msg::Int64>::SharedPtr right_ticks_sub_;
    rclcpp::Subscription<std_msgs::msg::Int64>::SharedPtr left_ticks_sub_;
    std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::TimerBase::SharedPtr timer_;
    
    double WHEEL_RADIUS, WHEEL_BASE, TICKS_PER_METER, PI;
    double robot_x, robot_y, robot_theta;
    double linear_velocity, angular_velocity;
    int64_t lastCountL, lastCountR;
    double distanceLeft, distanceRight;
    bool first_left_received, first_right_received;
    bool publish_tf_;
    rclcpp::Time last_time;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<AuroraEKFOdomPublisher>());
    rclcpp::shutdown();
    return 0;
}
