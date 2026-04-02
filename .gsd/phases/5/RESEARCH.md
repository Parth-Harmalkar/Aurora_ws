# Research - Phase 5: Semantic Spatial Database

## Goal
Implement a persistent spatial memory system for the Aurora robot to store and query object locations.

## Findings

### 1. Database Implementation
- **Tool**: SQLite 3 (Python `sqlite3` module).
- **Location**: `~/.aurora/semantic_memory.db`.
- **Schema**:
    ```sql
    CREATE TABLE IF NOT EXISTS objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        z REAL NOT NULL,
        confidence REAL NOT NULL,
        timestamp REAL NOT NULL
    );
    ```

### 2. Spatiotemporal Association
- **Algorithm**: Euclidean distance-based clustering.
- **Threshold**: $0.5m$ (tuned for indoor objects).
- **Logic**: 
    1. Receive `Detection3DArray`.
    2. Transform each detection to `map` frame using `tf2_ros`.
    3. Query database for objects with the same `label` within the distance threshold.
    4. If found: Update existing record (EMA for position).
    5. If not found: Insert new record.

### 3. Coordinate Transformation
- **Subscriber**: `/camera/detections` (`vision_msgs/Detection3DArray`).
- **TF Listener**: Listen to `tf` for `map` -> `camera_optical_frame`.
- **Calculation**: Use `tf2_geometry_msgs` to transform `Point` messages.

### 4. ROS 2 Interface
- **Service**: `GetObjectPose.srv` (Request: `label`, Response: `pose`, `success`, `message`).
- **Markers**: Publish `visualization_msgs/MarkerArray` on `/semantic_map` for RViz.

## Recommendations
- Create a new package `aurora_semantic_memory`.
- Add the `GetObjectPose.srv` to the existing `aurora_msgs` package to keep custom interfaces centralized.
- Implement the node in Python for rapid development of the database logic.
