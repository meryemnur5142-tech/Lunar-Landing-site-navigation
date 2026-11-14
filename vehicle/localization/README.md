# Vehicle Localization

**v1.0 Reference:** §4.6 Navigation & Mobility

EKF-based position estimation: fusion of IMU, LiDAR odometry, sun angle, and (when available) ground reference measurements.

## Compliance Note 4

The landing GNC system and the surface navigation system are separate design domains.
This module covers the surface mission only.

The traverse history path (traverse_path) is forwarded to the planner via ICD-003;
raw sensor data is kept on the flight computer and is not transmitted to the ground segment.
See `interfaces/nav_to_local_planner.schema.yaml` (ICD-003)
