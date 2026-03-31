# Phase 4 Research: OAK-D Spatial Object Detection

## Overview
Phase 4 focuses on moving beyond raw camera streaming to on-device object detection with 3D spatial coordinates. This leverages the Myriad X VPU on the OAK-D to perform neural network inference and depth-based positioning without stressing the Jetson Orin Nano's CPU/GPU.

## 1. Spatial Detection Pipeline
The `depthai` API provides a dedicated node: `MobileNetSpatialDetectionNetwork` (or `YoloSpatialDetectionNetwork`).
- **Input 1**: Color camera (640x360 or similar resolution).
- **Input 2**: Stereo Depth (aligned to color).
- **Output**: `SpatialImgDetections`, which includes:
  - Bounding boxes (2D).
  - Label ID.
  - Confidence.
  - **X, Y, Z coordinates** in millimeters relative to the camera center.

## 2. Neural Network Model
- **Choice**: `mobilenet-ssd` (requested).
- **Source**: Can be loaded from a `.blob` file.
- **Integration**: The blob must be compiled for the specific OpenVINO version used by the DepthAI firmware.

## 3. ROS 2 Integration
- **Messages**:
  - `vision_msgs/msg/Detection2DArray` (standard for bboxes).
  - `vision_msgs/msg/Detection3DArray` (best for spatial info).
  - `visualization_msgs/msg/MarkerArray` (for Rviz persistent markers).
- **Node**: Extend `camera_node.py` in `aurora_camera` to avoid duplicate driver instances.

## 4. Implementation Details
- **Sync**: Spatial detection automatically handles the depth sync if the pipeline is linked correctly.
- **Coordinates**: The VPU returns coordinates in the camera's physical frame. We need to publish these accurately so `tf2` can transform them into the `map` or `base_link` frame in subsequent phases (Phase 5).
- **Performance**: Running detections at 10Hz-15Hz is feasible on VPU without impacting the 10Hz RGB/Depth streams needed for SLAM.

## 5. Risks
- **Model Loading**: Need to ensure the blob is available or can be downloaded.
- **Message Type**: Some visualization tools prefer `Detection3D` vs `Detection2D` with spatial metadata. Standardizing on `vision_msgs` is the safest bet.
