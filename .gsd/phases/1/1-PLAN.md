---
phase: 1
plan: 1
wave: 1
depends_on: []
files_modified:
  - ros2_ws/src/aurora_bringup/config/nav2_params.yaml
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Smac2D planner replaces NavFn for grid-based global planning"
    - "RPP controller lookahead and velocity params tuned for 0.22m radius differential drive"
    - "Recovery behaviors have explicit timeouts and are robust for indoor use"
  artifacts:
    - "nav2_params.yaml planner_server uses nav2_smac_planner/SmacPlanner2D"
    - "nav2_params.yaml FollowPath desired_linear_vel ≤ 0.3 (safe indoor speed)"
    - "nav2_params.yaml recoveries_server has max_retries timeout"
---

# Plan 1.1: Smac2D Planner + RPP Controller Tuning + Recovery Hardening

<objective>
Replace the weak NavFn planner with Smac2D (already installed as `ros-humble-nav2-smac-planner`), tune the RPP controller for Aurora's small 0.22m-radius differential drive chassis for safe indoor operation, and harden recovery behaviors with explicit timeouts.

Purpose: NavFn produces suboptimal paths that cause oscillation in tight indoor spaces. Smac2D produces smooth, obstacle-aware 2D paths. RPP defaults are tuned for larger robots — Aurora needs tighter lookahead and slower speeds.

Output: Updated `nav2_params.yaml` with Smac2D planner, tuned RPP, hardened recoveries.
</objective>

<context>
Load for context:
- .gsd/SPEC.md
- ros2_ws/src/aurora_bringup/config/nav2_params.yaml
</context>

<tasks>

<task type="auto">
  <name>Replace NavFn with Smac2D planner</name>
  <files>ros2_ws/src/aurora_bringup/config/nav2_params.yaml</files>
  <action>
    Replace the `planner_server` section (lines 196-205):

    FROM:
    ```yaml
    planner_server:
      ros__parameters:
        expected_planner_frequency: 20.0
        use_sim_time: False
        planner_plugins: ["GridBased"]
        GridBased:
          plugin: "nav2_navfn_planner/NavfnPlanner"
          tolerance: 0.5
          use_astar: false
          allow_unknown: true
    ```

    TO:
    ```yaml
    planner_server:
      ros__parameters:
        expected_planner_frequency: 20.0
        use_sim_time: False
        planner_plugins: ["GridBased"]
        GridBased:
          plugin: "nav2_smac_planner/SmacPlanner2D"
          tolerance: 0.125
          downsample_costmap: false
          downsampling_factor: 1
          allow_unknown: true
          max_iterations: 1000000
          max_on_approach_iterations: 1000
          max_planning_time: 2.0
          cost_travel_multiplier: 2.0
          use_final_approach_orientation: false
          smoother:
            max_iterations: 1000
            w_smooth: 0.3
            w_data: 0.2
            tolerance: 1.0e-10
    ```

    Key decisions:
    - `tolerance: 0.125` — tighter than NavFn's 0.5 because Smac2D can handle it and Aurora needs precision in tight spaces
    - `max_planning_time: 2.0` — generous for Jetson Orin Nano to avoid timeout on complex maps
    - `cost_travel_multiplier: 2.0` — prefer shorter paths over free-space-hugging
    - `use_final_approach_orientation: false` — let RPP handle final heading, not the planner
    - Smoother enabled for smooth paths (reduces oscillation)

    AVOID: Setting `downsample_costmap: true` because Aurora's 0.05m resolution costmap is already coarse enough for the Orin Nano's CPU.
    AVOID: Using SmacPlannerHybrid — it's for Ackermann vehicles, not differential drive.
  </action>
  <verify>grep -c "SmacPlanner2D" ros2_ws/src/aurora_bringup/config/nav2_params.yaml returns 1</verify>
  <done>"nav2_smac_planner/SmacPlanner2D" is the configured planner plugin, NavFn is completely removed</done>
</task>

<task type="auto">
  <name>Tune RPP controller for Aurora chassis + harden recoveries</name>
  <files>ros2_ws/src/aurora_bringup/config/nav2_params.yaml</files>
  <action>
    Update the `FollowPath` section under `controller_server` (lines 81-101):

    ```yaml
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 0.26
      lookahead_dist: 0.4
      min_lookahead_dist: 0.2
      max_lookahead_dist: 0.6
      lookahead_time: 1.0
      rotate_to_heading_angular_vel: 1.5
      transform_tolerance: 0.1
      use_velocity_scaled_lookahead_dist: true
      min_approach_linear_velocity: 0.05
      approach_velocity_scaling_dist: 0.4
      use_collision_detection: true
      max_allowed_time_to_collision_up_to_carrot: 1.0
      use_regulated_linear_velocity_scaling: true
      regulated_linear_scaling_min_radius: 0.4
      regulated_linear_scaling_min_speed: 0.1
      use_rotate_to_heading: true
      allow_reversing: false
      rotate_to_heading_min_angle: 0.785
      max_angular_accel: 2.5
      max_robot_pose_search_dist: 10.0
      use_interpolation: true
    ```

    Key tuning rationale for 0.22m robot:
    - `desired_linear_vel: 0.26` — down from 0.5, safe indoor speed for a small robot
    - `lookahead_dist: 0.4` — down from 0.6, tighter cornering for indoor hallways
    - `min_lookahead_dist: 0.2` — down from 0.3, allows precision near goals
    - `max_lookahead_dist: 0.6` — down from 0.9, prevents cutting corners
    - `lookahead_time: 1.0` — down from 1.5, more responsive
    - `rotate_to_heading_angular_vel: 1.5` — down from 1.8, smoother rotations
    - `use_regulated_linear_velocity_scaling: true` — NEW: slows down near obstacles and tight turns
    - `regulated_linear_scaling_min_radius: 0.4` — curvature threshold to start slowing
    - `regulated_linear_scaling_min_speed: 0.1` — minimum speed in tight turns
    - `max_angular_accel: 2.5` — down from 3.2, reduces wheel slip on small robot
    - `use_interpolation: true` — was false, smoother path following
    - `approach_velocity_scaling_dist: 0.4` — down from 0.6, stops overshooting goals

    Also update `recoveries_server` section (lines 207-226):

    ```yaml
    behavior_server:
      ros__parameters:
        costmap_topic: local_costmap/costmap_raw
        footprint_topic: local_costmap/published_footprint
        cycle_frequency: 10.0
        behavior_plugins: ["spin", "backup", "wait"]
        spin:
          plugin: "nav2_behaviors/Spin"
        backup:
          plugin: "nav2_behaviors/BackUp"
        wait:
          plugin: "nav2_behaviors/Wait"
        global_frame: odom
        robot_base_frame: base_link
        transform_timeout: 0.1
        use_sim_time: False
        simulate_ahead_time: 2.0
        max_rotational_vel: 1.0
        min_rotational_vel: 0.3
        rotational_accel: 2.5
    ```

    Changes to recovery/behavior server:
    - Rename from `recoveries_server` to `behavior_server` for Humble compatibility naming
    - Rename `recovery_plugins` to `behavior_plugins` for Humble API
    - `min_rotational_vel: 0.3` — down from 0.4 for finer rotation control
    - `rotational_accel: 2.5` — down from 3.2 to prevent wheel slip

    AVOID: Adding `drive_on_heading` behavior — it's not useful for differential drive in tight spaces.
    AVOID: Setting `simulate_ahead_time` too high — 2.0s is enough for safety checks at Aurora's speed.
  </action>
  <verify>grep -c "regulated_linear_velocity_scaling" ros2_ws/src/aurora_bringup/config/nav2_params.yaml returns 1 AND grep -c "behavior_plugins" nav2_params.yaml returns 1</verify>
  <done>RPP controller uses velocity-scaled lookahead with regulated linear scaling. Recovery/behavior server uses Humble naming convention. All velocities and accelerations tuned for 0.22m differential drive.</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] `nav2_params.yaml` contains `SmacPlanner2D` (not NavFn)
- [ ] `nav2_params.yaml` contains `regulated_linear_velocity_scaling`
- [ ] `nav2_params.yaml` contains `behavior_plugins` (Humble naming)
- [ ] `desired_linear_vel` is 0.26 (not 0.5)
- [ ] No syntax errors in YAML (python3 -c "import yaml; yaml.safe_load(open('nav2_params.yaml'))")
</verification>

<success_criteria>
- [ ] Smac2D planner configured with smoother enabled
- [ ] RPP controller tuned for 0.22m indoor robot with regulated velocity scaling
- [ ] Recovery behaviors hardened with Humble naming convention
- [ ] YAML is valid
</success_criteria>
