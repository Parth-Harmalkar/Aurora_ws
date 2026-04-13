cmake_minimum_required(VERSION 3.8)
project(aurora_imu)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(bno055_bare src/bno055_bare.cpp)
ament_target_dependencies(bno055_bare rclcpp sensor_msgs)

install(TARGETS
  bno055_bare
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python scripts as well for backward compatibility
install(
  PROGRAMS
  aurora_imu/bno055_bare.py
  aurora_imu/imu_node.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
