#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <cmath>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"

using namespace std::chrono_literals;

class BNO055BareNode : public rclcpp::Node {
public:
    BNO055BareNode() : Node("bno055_bare_node") {
        // Parameters
        this->declare_parameter("i2c_bus", 1);
        this->declare_parameter("i2c_addr", 0x28);
        this->declare_parameter("frame_id", "bno_link");
        
        // Axis Remapping (0=X, 1=Y, 2=Z)
        this->declare_parameter("axis_x", 0); 
        this->declare_parameter("axis_y", 1);
        this->declare_parameter("axis_z", 2);
        
        // Axis Signs (1=Positive, -1=Negative)
        this->declare_parameter("sign_x", 1);
        this->declare_parameter("sign_y", 1);
        this->declare_parameter("sign_z", 1);

        i2c_bus_ = this->get_parameter("i2c_bus").as_int();
        i2c_addr_ = this->get_parameter("i2c_addr").as_int();
        frame_id_ = this->get_parameter("frame_id").as_string();
        
        axis_map_ = {
            static_cast<int>(this->get_parameter("axis_x").as_int()),
            static_cast<int>(this->get_parameter("axis_y").as_int()),
            static_cast<int>(this->get_parameter("axis_z").as_int())
        };
        axis_signs_ = {
            static_cast<int>(this->get_parameter("sign_x").as_int()),
            static_cast<int>(this->get_parameter("sign_y").as_int()),
            static_cast<int>(this->get_parameter("sign_z").as_int())
        };

        publisher_ = this->create_publisher<sensor_msgs::msg::Imu>("/imu/data", 10);

        if (!init_i2c()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to initialize I2C on bus %d", i2c_bus_);
            return;
        }

        if (!init_bno055()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to initialize BNO055 at 0x%02X", i2c_addr_);
            return;
        }

        timer_ = this->create_wall_timer(50ms, std::bind(&BNO055BareNode::read_and_publish, this));
        RCLCPP_INFO(this->get_logger(), "BNO055 C++ Bare-Metal Driver Started on Bus %d", i2c_bus_);
    }

    ~BNO055BareNode() {
        if (i2c_fd_ >= 0) {
            close(i2c_fd_);
        }
    }

private:
    // BNO055 Registers
    static constexpr uint8_t BNO055_CHIP_ID_ADDR = 0x00;
    static constexpr uint8_t BNO055_OPR_MODE_ADDR = 0x3D;
    static constexpr uint8_t BNO055_SYS_TRIGGER_ADDR = 0x3F;
    static constexpr uint8_t BNO055_UNIT_SEL_ADDR = 0x3B;
    static constexpr uint8_t BNO055_CALIB_STAT_ADDR = 0x35;
    static constexpr uint8_t BNO055_QUATERNION_DATA_W_LSB_ADDR = 0x20;
    static constexpr uint8_t BNO055_GYRO_DATA_X_LSB_ADDR = 0x14;
    static constexpr uint8_t BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR = 0x28;

    // Modes
    static constexpr uint8_t OPERATION_MODE_CONFIG = 0x00;
    static constexpr uint8_t OPERATION_MODE_IMUPLUS = 0x08;

    int i2c_fd_ = -1;
    int i2c_bus_;
    int i2c_addr_;
    std::string frame_id_;
    std::vector<int> axis_map_;
    std::vector<int> axis_signs_;
    rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    int calib_counter_ = 0;

    bool init_i2c() {
        char bus_path[20];
        snprintf(bus_path, sizeof(bus_path), "/dev/i2c-%d", i2c_bus_);
        i2c_fd_ = open(bus_path, O_RDWR);
        if (i2c_fd_ < 0) return false;
        if (ioctl(i2c_fd_, I2C_SLAVE, i2c_addr_) < 0) return false;
        return true;
    }

    bool write_reg(uint8_t reg, uint8_t val) {
        uint8_t buf[2] = {reg, val};
        return write(i2c_fd_, buf, 2) == 2;
    }

    uint8_t read_reg(uint8_t reg) {
        if (write(i2c_fd_, &reg, 1) != 1) return 0xFF;
        uint8_t val;
        if (read(i2c_fd_, &val, 1) != 1) return 0xFF;
        return val;
    }

    bool read_block(uint8_t reg, uint8_t* data, size_t len) {
        if (write(i2c_fd_, &reg, 1) != 1) return false;
        return static_cast<size_t>(read(i2c_fd_, data, len)) == len;
    }

    bool init_bno055() {
        // 1. Verify Chip ID
        uint8_t id = read_reg(BNO055_CHIP_ID_ADDR);
        if (id != 0xA0) {
            RCLCPP_ERROR(this->get_logger(), "Got unexpected Chip ID: 0x%02X", id);
            return false;
        }

        // 2. Enter CONFIG mode
        write_reg(BNO055_OPR_MODE_ADDR, OPERATION_MODE_CONFIG);
        std::this_thread::sleep_for(25ms);

        // 3. Reset
        write_reg(BNO055_SYS_TRIGGER_ADDR, 0x20);
        std::this_thread::sleep_for(700ms);
        while (read_reg(BNO055_CHIP_ID_ADDR) != 0xA0) { std::this_thread::sleep_for(10ms); }

        // 4. Power mode normal
        write_reg(0x3E, 0x00);
        std::this_thread::sleep_for(10ms);

        // 5. Hardware Axis Remapping
        // Config: bits 0-1 (X), 2-3 (Y), 4-5 (Z)
        // Sign: bit 0 (X), 1 (Y), 2 (Z)
        uint8_t remap_config = (axis_map_[2] << 4) | (axis_map_[1] << 2) | axis_map_[0];
        uint8_t remap_sign = (axis_signs_[2] < 0 ? 4 : 0) | (axis_signs_[1] < 0 ? 2 : 0) | (axis_signs_[0] < 0 ? 1 : 0);
        
        write_reg(0x41, remap_config);
        std::this_thread::sleep_for(10ms);
        write_reg(0x42, remap_sign);
        std::this_thread::sleep_for(10ms);

        // 6. Units: m/s^2, Dps, Degrees, Celsius
        write_reg(BNO055_UNIT_SEL_ADDR, 0x00);
        std::this_thread::sleep_for(10ms);

        // 7. Switch to IMUPlus Mode
        write_reg(BNO055_OPR_MODE_ADDR, OPERATION_MODE_IMUPLUS);
        std::this_thread::sleep_for(25ms);

        return true;
    }

    void read_and_publish() {
        sensor_msgs::msg::Imu msg;
        msg.header.stamp = this->get_clock()->now();
        msg.header.frame_id = frame_id_;

        // Calibration status
        if (++calib_counter_ >= 20) {
            calib_counter_ = 0;
            uint8_t calib = read_reg(BNO055_CALIB_STAT_ADDR);
            int gyro = (calib >> 4) & 0x03;
            if (gyro < 3) {
                RCLCPP_WARN(this->get_logger(), "IMU Gyro Calibration low: %d (0-3)", gyro);
            }
        }

        // 1. Quaternions (8 bytes)
        uint8_t quat_buf[8];
        if (read_block(BNO055_QUATERNION_DATA_W_LSB_ADDR, quat_buf, 8)) {
            int16_t w = static_cast<int16_t>((quat_buf[1] << 8) | quat_buf[0]);
            int16_t x = static_cast<int16_t>((quat_buf[3] << 8) | quat_buf[2]);
            int16_t y = static_cast<int16_t>((quat_buf[5] << 8) | quat_buf[4]);
            int16_t z = static_cast<int16_t>((quat_buf[7] << 8) | quat_buf[6]);

            msg.orientation.w = w / 16384.0;
            msg.orientation.x = (x / 16384.0) * -1.0; // Inverted Roll movement
            msg.orientation.y = (y / 16384.0) * -1.0; // Inverted Pitch movement
            msg.orientation.z = z / 16384.0;

            if (msg.orientation.w == 0.0 && msg.orientation.x == 0.0 && msg.orientation.y == 0.0 && msg.orientation.z == 0.0) {
                msg.orientation.w = 1.0;
            }
        }

        double deg2rad = M_PI / 180.0;
        
        // 2. Gyro (6 bytes)
        uint8_t gyro_buf[6];
        if (read_block(BNO055_GYRO_DATA_X_LSB_ADDR, gyro_buf, 6)) {
            int16_t x = static_cast<int16_t>(gyro_buf[1] << 8 | gyro_buf[0]);
            int16_t y = static_cast<int16_t>(gyro_buf[3] << 8 | gyro_buf[2]);
            int16_t z = static_cast<int16_t>(gyro_buf[5] << 8 | gyro_buf[4]);

            msg.angular_velocity.x = (x / 16.0) * deg2rad * -1.0; // Inverted Roll rate
            msg.angular_velocity.y = (y / 16.0) * deg2rad * -1.0; // Inverted Pitch rate
            msg.angular_velocity.z = (z / 16.0) * deg2rad;
        }

        // 3. Linear Accel (6 bytes)
        uint8_t acc_buf[6];
        if (read_block(BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR, acc_buf, 6)) {
            int16_t x = static_cast<int16_t>(acc_buf[1] << 8 | acc_buf[0]);
            int16_t y = static_cast<int16_t>(acc_buf[3] << 8 | acc_buf[2]);
            int16_t z = static_cast<int16_t>(acc_buf[5] << 8 | acc_buf[4]);

            msg.linear_acceleration.x = (x / 100.0) * -1.0; // Inverted for consistency
            msg.linear_acceleration.y = (y / 100.0) * -1.0; // Inverted for consistency
            msg.linear_acceleration.z = (z / 100.0);
        }

        // Covariances
        for (int i = 0; i < 9; ++i) {
            msg.orientation_covariance[i] = 0.0;
            msg.angular_velocity_covariance[i] = 0.0;
            msg.linear_acceleration_covariance[i] = 0.0;
        }
        msg.orientation_covariance[0] = 0.01; msg.orientation_covariance[4] = 0.01; msg.orientation_covariance[8] = 0.01;
        msg.angular_velocity_covariance[0] = 0.001; msg.angular_velocity_covariance[4] = 0.001; msg.angular_velocity_covariance[8] = 0.001;
        msg.linear_acceleration_covariance[0] = 0.05; msg.linear_acceleration_covariance[4] = 0.05; msg.linear_acceleration_covariance[8] = 0.05;

        publisher_->publish(msg);
    }
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<BNO055BareNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
