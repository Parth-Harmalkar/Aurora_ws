---
phase: 1
plan: 2
wave: 1
depends_on: []
files_modified:
  - ros2_ws/src/aurora_bringup/launch/navigation.launch.py
  - ros2_ws/src/aurora_bringup/launch/mapping.launch.py
autonomous: true
user_setup: []

must_haves:
  truths:
    - "AMCL is NOT launched when RTAB-Map is running (prevents dual map→odom TF)"
    - "map_server is NOT launched when RTAB-Map publishes /map via /grid_map"
    - "Nav2 lifecycle manager only manages nodes that are actually launched"
    - "mapping.launch.py passes slam_mode=true to navigation.launch.py"
  artifacts:
    - "navigation.launch.py accepts slam_mode argument"
    - "navigation.launch.py conditionally excludes amcl and map_server when slam_mode=true"
    - "mapping.launch.py passes slam_mode=true to navigation.launch.py"
---

# Plan 1.2: Fix SLAM/Nav2 TF Conflict — Conditional AMCL & Map Server

<objective>
Fix the critical TF conflict where both RTAB-Map and AMCL fight over the map→odom transform, and both RTAB-Map and map_server fight over the /map topic. When running in SLAM mode (via `mapping.launch.py`), AMCL and map_server must NOT be launched.

Purpose: Currently, `mapping.launch.py` includes `navigation.launch.py` which unconditionally starts AMCL + map_server. This causes:
1. TF conflict: RTAB-Map publishes map→odom, AMCL also publishes map→odom → EKF confusion
2. Topic conflict: RTAB-Map publishes /map (via /grid_map remap), map_server also publishes /map
3. Lifecycle crash: lifecycle_manager tries to manage map_server which has no map file

Output: Modified launch files that conditionally exclude AMCL/map_server in SLAM mode.
</objective>

<context>
Load for context:
- .gsd/SPEC.md
- ros2_ws/src/aurora_bringup/launch/navigation.launch.py
- ros2_ws/src/aurora_bringup/launch/mapping.launch.py
- ros2_ws/src/aurora_bringup/config/nav2_params.yaml
</context>

<tasks>

<task type="auto">
  <name>Add slam_mode conditional to navigation.launch.py</name>
  <files>ros2_ws/src/aurora_bringup/launch/navigation.launch.py</files>
  <action>
    Rewrite `navigation.launch.py` to accept a `slam_mode` launch argument (default: 'false').

    When `slam_mode=true`:
    - Do NOT launch `map_server` (RTAB-Map provides /map)
    - Do NOT launch AMCL (RTAB-Map provides map→odom TF)
    - Remove `map_server` from `lifecycle_nodes` list
    - Note: AMCL is not currently in the launch file but IS in nav2_params.yaml config — just make sure it's never added

    When `slam_mode=false` (standalone navigation with pre-built map):
    - Launch `map_server` normally
    - Lifecycle manager manages all nodes including map_server

    Implementation approach:
    - Use `LaunchConfiguration('slam_mode')` with `OpaqueFunction` to dynamically build the node list
    - Use `OpaqueFunction` because ROS2 launch conditionals (IfCondition) don't support dynamic lifecycle_nodes lists easily
    - The lifecycle_nodes list must match exactly the nodes that are launched

    ```python
    import os
    from ament_index_python.packages import get_package_share_directory
    from launch import LaunchDescription
    from launch.actions import DeclareLaunchArgument, OpaqueFunction
    from launch.substitutions import LaunchConfiguration, PythonExpression
    from launch_ros.actions import Node

    def launch_setup(context, *args, **kwargs):
        pkg_bringup = get_package_share_directory('aurora_bringup')
        nav2_params_path = os.path.join(pkg_bringup, 'config', 'nav2_params.yaml')
        use_tui = LaunchConfiguration('use_tui')
        slam_mode = LaunchConfiguration('slam_mode')
        output_cfg = PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])

        slam_mode_val = context.perform_substitution(slam_mode)
        is_slam = slam_mode_val.lower() == 'true'

        nodes = []
        lifecycle_nodes = [
            'controller_server',
            'planner_server',
            'behavior_server',
            'bt_navigator',
        ]

        if not is_slam:
            lifecycle_nodes.append('map_server')
            nodes.append(Node(
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output=output_cfg,
                parameters=[nav2_params_path]
            ))

        nodes.extend([
            Node(
                package='nav2_controller',
                executable='controller_server',
                name='controller_server',
                output=output_cfg,
                arguments=['--ros-args', '--log-level', 'warn'],
                parameters=[nav2_params_path]
            ),
            Node(
                package='nav2_planner',
                executable='planner_server',
                name='planner_server',
                output=output_cfg,
                arguments=['--ros-args', '--log-level', 'warn'],
                parameters=[nav2_params_path]
            ),
            Node(
                package='nav2_behaviors',
                executable='behavior_server',
                name='behavior_server',
                output=output_cfg,
                parameters=[nav2_params_path]
            ),
            Node(
                package='nav2_bt_navigator',
                executable='bt_navigator',
                name='bt_navigator',
                output=output_cfg,
                parameters=[nav2_params_path]
            ),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                output=output_cfg,
                parameters=[
                    {'use_sim_time': False},
                    {'autostart': True},
                    {'node_names': lifecycle_nodes}
                ]
            )
        ])

        return nodes

    def generate_launch_description():
        return LaunchDescription([
            DeclareLaunchArgument('use_tui', default_value='false'),
            DeclareLaunchArgument('slam_mode', default_value='false',
                                 description='Set true when RTAB-Map SLAM provides map and TF'),
            OpaqueFunction(function=launch_setup)
        ])
    ```

    CRITICAL: The behavior_server node name MUST be `behavior_server` (not `recoveries_server`) to match the updated nav2_params.yaml from Plan 1.1. The lifecycle_nodes list must use `behavior_server` as well.

    AVOID: Using IfCondition for map_server — it doesn't prevent the node name from appearing in lifecycle_nodes, which causes lifecycle_manager to hang waiting for a node that doesn't exist.
    AVOID: Launching AMCL under any condition — RTAB-Map handles localization in SLAM mode, and for pre-built map mode we'll add AMCL in a future phase if needed.
  </action>
  <verify>python3 -c "import ast; ast.parse(open('ros2_ws/src/aurora_bringup/launch/navigation.launch.py').read())" succeeds</verify>
  <done>navigation.launch.py accepts slam_mode argument. When slam_mode=true, map_server is excluded from both node list and lifecycle_nodes.</done>
</task>

<task type="auto">
  <name>Pass slam_mode=true from mapping.launch.py</name>
  <files>ros2_ws/src/aurora_bringup/launch/mapping.launch.py</files>
  <action>
    Update the navigation.launch.py IncludeLaunchDescription in `mapping.launch.py` (line 78-83) to pass `slam_mode=true`:

    Change:
    ```python
    IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={'use_tui': use_tui}.items()
    )
    ```

    To:
    ```python
    IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'slam_mode': 'true'
        }.items()
    )
    ```

    This ensures that when mapping.launch.py is used (SLAM mode), Nav2 does NOT start map_server or AMCL. RTAB-Map owns the map→odom TF and /map topic.

    AVOID: Changing any RTAB-Map parameters — those are correct and verified.
  </action>
  <verify>grep "slam_mode" ros2_ws/src/aurora_bringup/launch/mapping.launch.py returns the slam_mode line</verify>
  <done>mapping.launch.py passes slam_mode=true to navigation.launch.py, preventing TF conflicts between RTAB-Map and Nav2 localization nodes.</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] navigation.launch.py accepts slam_mode argument
- [ ] navigation.launch.py with slam_mode=true does NOT include map_server
- [ ] navigation.launch.py with slam_mode=false DOES include map_server
- [ ] mapping.launch.py passes slam_mode='true' to navigation.launch.py
- [ ] behavior_server name matches in both launch file and nav2_params.yaml
- [ ] Both Python files parse without syntax errors
</verification>

<success_criteria>
- [ ] No TF conflict: RTAB-Map is sole owner of map→odom when SLAM is active
- [ ] No topic conflict: Only RTAB-Map publishes /map in SLAM mode
- [ ] Lifecycle manager only manages nodes that actually exist
- [ ] Both launch files are valid Python
</success_criteria>
