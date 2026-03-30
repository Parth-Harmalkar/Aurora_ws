## Plan 1.1 Summary: Smac2D + RPP Tuning + Recovery Hardening

### What was done
- Replaced `nav2_navfn_planner/NavfnPlanner` with `nav2_smac_planner/SmacPlanner2D`
  - Added path smoother (w_smooth=0.3, w_data=0.2)
  - Tighter tolerance (0.125 vs 0.5)
  - max_planning_time: 2.0s for Jetson Orin Nano
- Tuned RPP controller for 0.22m differential drive:
  - desired_linear_vel: 0.26 (from 0.5)
  - lookahead: 0.2-0.6 range (from 0.3-0.9)
  - Added `use_regulated_linear_velocity_scaling: true`
  - max_angular_accel: 2.5 (from 3.2)
  - use_interpolation: true (from false)
- Renamed `recoveries_server` → `behavior_server` (Humble API)
  - `recovery_plugins` → `behavior_plugins`
  - min_rotational_vel: 0.3, rotational_accel: 2.5

### Files modified
- `ros2_ws/src/aurora_bringup/config/nav2_params.yaml`

### Verification
- YAML valid ✓
- SmacPlanner2D configured ✓
- Regulated velocity scaling enabled ✓
- Behavior server uses Humble naming ✓
