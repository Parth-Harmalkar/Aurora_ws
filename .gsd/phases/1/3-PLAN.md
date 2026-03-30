---
phase: 1
plan: 3
wave: 2
depends_on: ["1.1", "1.2"]
files_modified: []
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Workspace builds successfully with colcon"
    - "nav2_params.yaml is valid YAML"
    - "Launch files are valid Python"
    - "All Nav2 plugin names resolve correctly"
  artifacts:
    - "colcon build succeeds for aurora_bringup"
---

# Plan 1.3: Build Validation & Integration Check

<objective>
Verify that all Phase 1 changes (Smac2D planner, RPP tuning, recovery hardening, SLAM/Nav2 TF fix) build correctly and launch files are syntactically valid.

Purpose: Catch configuration errors before testing on hardware. A broken YAML or Python syntax error would waste a full hardware test cycle.

Output: Confirmed build success and config validation.
</objective>

<context>
Load for context:
- ros2_ws/src/aurora_bringup/config/nav2_params.yaml
- ros2_ws/src/aurora_bringup/launch/navigation.launch.py
- ros2_ws/src/aurora_bringup/launch/mapping.launch.py
</context>

<tasks>

<task type="auto">
  <name>Validate YAML and Python syntax</name>
  <files>
    ros2_ws/src/aurora_bringup/config/nav2_params.yaml
    ros2_ws/src/aurora_bringup/launch/navigation.launch.py
    ros2_ws/src/aurora_bringup/launch/mapping.launch.py
  </files>
  <action>
    Run syntax validation:

    1. Validate nav2_params.yaml:
    ```bash
    python3 -c "import yaml; yaml.safe_load(open('ros2_ws/src/aurora_bringup/config/nav2_params.yaml'))"
    ```

    2. Validate navigation.launch.py:
    ```bash
    python3 -c "import ast; ast.parse(open('ros2_ws/src/aurora_bringup/launch/navigation.launch.py').read())"
    ```

    3. Validate mapping.launch.py:
    ```bash
    python3 -c "import ast; ast.parse(open('ros2_ws/src/aurora_bringup/launch/mapping.launch.py').read())"
    ```

    4. Verify key configuration values:
    ```bash
    grep "SmacPlanner2D" ros2_ws/src/aurora_bringup/config/nav2_params.yaml
    grep "desired_linear_vel: 0.26" ros2_ws/src/aurora_bringup/config/nav2_params.yaml
    grep "slam_mode" ros2_ws/src/aurora_bringup/launch/navigation.launch.py
    grep "slam_mode" ros2_ws/src/aurora_bringup/launch/mapping.launch.py
    ```

    All commands must succeed with exit code 0.

    AVOID: Running `colcon build` if syntax checks fail — fix issues first.
  </action>
  <verify>All four validation commands return exit code 0</verify>
  <done>YAML and Python files are syntactically valid. Key configuration values are present.</done>
</task>

<task type="auto">
  <name>Build aurora_bringup package</name>
  <files>ros2_ws/src/aurora_bringup/</files>
  <action>
    Build just the aurora_bringup package to verify everything installs correctly:

    ```bash
    cd ros2_ws
    source /opt/ros/humble/setup.bash
    colcon build --packages-select aurora_bringup --symlink-install
    ```

    The build must complete with "0 packages had errors".

    After build, verify installed files:
    ```bash
    source install/setup.bash
    ros2 pkg prefix aurora_bringup
    ls $(ros2 pkg prefix aurora_bringup)/share/aurora_bringup/config/nav2_params.yaml
    ls $(ros2 pkg prefix aurora_bringup)/share/aurora_bringup/launch/navigation.launch.py
    ```

    AVOID: Building the entire workspace — only aurora_bringup changed.
  </action>
  <verify>colcon build --packages-select aurora_bringup completes with 0 errors</verify>
  <done>aurora_bringup package builds successfully. Config and launch files are installed to the correct locations.</done>
</task>

<task type="checkpoint:human-verify">
  <name>Hardware launch verification</name>
  <files></files>
  <action>
    Ask the user to test on hardware:

    ```bash
    ros2 launch aurora_bringup mapping.launch.py
    ```

    Verify:
    1. No TF errors in terminal output about map→odom conflict
    2. Nav2 lifecycle manager reports all nodes active
    3. `ros2 topic list` shows /map from RTAB-Map only
    4. `ros2 node list` does NOT show map_server or amcl
    5. In RViz, set a Nav2 goal — robot should plan and move

    This is a human-verify checkpoint because it requires physical hardware.
  </action>
  <verify>User confirms: no TF conflicts, Nav2 nodes active, robot can plan paths</verify>
  <done>Full stack launches without conflicts. Nav2 plans paths using Smac2D. Robot moves with tuned RPP controller.</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] YAML is valid
- [ ] Python launch files parse correctly
- [ ] colcon build succeeds
- [ ] Key config values present (SmacPlanner2D, regulated velocity scaling, slam_mode)
</verification>

<success_criteria>
- [ ] aurora_bringup builds with 0 errors
- [ ] All config files are syntactically valid
- [ ] All launch files are syntactically valid
- [ ] Hardware test confirms no TF conflicts (user checkpoint)
</success_criteria>
