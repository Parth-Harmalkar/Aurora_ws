#include <iostream>
#include <cstdint>
#include <cstddef>

namespace imu_bno055 {
typedef struct {
  int16_t raw_linear_acceleration_x;
  int16_t raw_linear_acceleration_y;
  int16_t raw_linear_acceleration_z;
  int16_t raw_magnetic_field_x;
  int16_t raw_magnetic_field_y;
  int16_t raw_magnetic_field_z;
  int16_t raw_angular_velocity_x;
  int16_t raw_angular_velocity_y;
  int16_t raw_angular_velocity_z;
  int16_t fused_heading;
  int16_t fused_roll;
  int16_t fused_pitch;
  int16_t fused_orientation_w;
  int16_t fused_orientation_x;
  int16_t fused_orientation_y;
  int16_t fused_orientation_z;
  int16_t fused_linear_acceleration_x;
  int16_t fused_linear_acceleration_y;
  int16_t fused_linear_acceleration_z;
  int16_t gravity_vector_x;
  int16_t gravity_vector_y;
  int16_t gravity_vector_z;
  int8_t temperature;
  uint8_t calibration_status;
  uint8_t self_test_result;
  uint8_t interrupt_status;
  uint8_t system_clock_status;
  uint8_t system_status;
  uint8_t system_error_code;
} IMURecord;
}

int main() {
    std::cout << "Size: " << sizeof(imu_bno055::IMURecord) << std::endl;
    std::cout << "Offset of fused_linear_acceleration_x: " << offsetof(imu_bno055::IMURecord, fused_linear_acceleration_x) << std::endl;
    std::cout << "Offset of temperature: " << offsetof(imu_bno055::IMURecord, temperature) << std::endl;
    return 0;
}
