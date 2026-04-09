cmake_minimum_required(VERSION 3.8)
project(camera_teaching)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Generate custom services
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/GetObjectPose.srv"
  "srv/ListObjects.srv"
  DEPENDENCIES geometry_msgs
)

# Install scripts
install(PROGRAMS
  ${PROJECT_NAME}/teaching_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Install model files
install(DIRECTORY
  models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
