# vehicle/

Vehicle subsystem software: landing GNC, localisation, perception, mobility control. See v1.0 §4.6.

Compliance Note 4: Landing GNC and surface navigation are separate. Handover boundaries are defined in `vehicle/localization/navigation_architecture.md §5`.

## Subdirectories

- `landing-gnc/` — Landing guidance, navigation and control; provides handover to surface navigation.
- `localization/` — EKF-based position estimation; IMU + odometry + landmark fusion.
- `perception/` — Stereo imaging, lidar, obstacle detection; DEM update.
- `mobility-control/` — Wheel/drive command execution; slope and slip control.
