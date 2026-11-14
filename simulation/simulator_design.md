# status: draft
# owner: Agent C
# depends_on: [simulation/scenarios/operational_scenarios.md, docs/adr/FMEA_KRITIK_MODULLER.md, docs/architecture/SAFETY_STATE_MACHINE.md, domain/environment/uncertainty_policy.md, config/tbd_register.md]
# open_items: [TBD-SIM-001..TBD-SIM-012 — vehicle parameters awaiting §10; HIL hardware list gated on P2]

# Digital Twin and Simulator Design — LUNA-AI v1.0

**Document ID:** LUNA-AI-SIM-001  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related Documents:** LUNA-AI-ARCH-001, LUNA-AI-FMEA-001, operational_scenarios.md (SC-001..SC-009)

---

## 1. Environment Model

### 1.1 Lunar Gravity and Surface Model

Lunar gravitational constant **g_moon = 1.62 m/s²** (reference: IAU lunar gravity model).

| Parameter | Value | Source / Note |
|-----------|-------|--------------|
| Gravitational acceleration | 1.62 m/s² | IAU constant |
| Surface acceleration local deviation | ±0.01 m/s² (equator-pole) | LRO data reference |
| Surface density (regolith) | TBD-SIM-001 (source: §10 terrain model) | For wheel-soil interaction model |
| DEM resolution | TBD-SIM-002 (source: §10 region selection) | LRO LOLA or equivalent |
| Target region reference coordinate | TBD-TIME-001 dependent | Mission authority approval |

**Surface Model Integration:**

Digital elevation model (DEM) is loaded via the terrain_analyzer module (`data-platform/processing/terrain_analyzer.py`). The simulator upgrades DEM from a planar approximation to a real coordinate grid:

```
TerrainGrid:
  resolution_m: TBD-SIM-002
  origin_lat, origin_lon: TBD-TIME-001
  elevation_data: float32[N, M]   # LRO LOLA or equivalent
  slope_map: float32[N, M]        # slope map (°)
  roughness_map: float32[N, M]    # roughness index
```

### 1.2 Solar Irradiance Model

| Parameter | Value | Note |
|-----------|-------|-----|
| Solar constant (1 AU) | 1361 W/m² | ASTM E490 |
| Lunar distance correction | ±3.3% (perigee/apogee) | NASA ephemeris |
| Panel efficiency factor | TBD-SOL-001 dependent (§10) | — |
| Panel orientation (servo angle) | Vehicle attitude data + solar angle | ICD-003 vehicle_pose |
| Shadow model | DEM-based ray-casting | PSR = 0 W/m² (permanent shadow) |

Irradiance model formula:

```
P_panel(t) = P_nominal × cos(θ_incidence(t)) × η_cell × (1 - α_dust)
  θ_incidence: angle between panel normal and solar vector
  η_cell: TBD-SOL-001 (cell efficiency, §10)
  α_dust: TBD-SIM-003 (dust coverage loss factor, §10 environment analysis)
```

### 1.3 Thermal Environment Model

Three zones of the lunar thermal environment are modelled separately in the simulator:

| Zone | Surface Temperature | Simulation Approach |
|-------|-----------------|----------------------|
| Sunlit surface | ~+120 °C | Stefan-Boltzmann radiation + solar flux; thermal equilibrium iteration |
| Dark/shadow | ~-173 °C | Radiation loss only; regolith thermal inertia |
| PSR (permanent darkness) | -200 °C to -173 °C | Permanent shadow; geothermal heat ignored (low impact) |

```
T_surface(t) = f(solar_flux, albedo, emissivity, regolith_thermal_inertia)
  albedo: TBD-SIM-004 (source: §10 region-specific measurement)
  emissivity: ~0.95 (lunar regolith default value)
  thermal_inertia: TBD-SIM-005 (source: §10 geological analysis)
```

Heat exchange between vehicle thermal model and surface model: §2.2 Thermal Model.

### 1.4 Terrain-Vehicle Interaction

| Effect | Model | Parameter |
|------|-------|-----------|
| Wheel slip | Simplified SCM (Soil Contact Mechanics) | TBD-SIM-001 (soil type + density) |
| Obstacle collision | AABB (Axis-Aligned Bounding Box) + resolution | TBD-MAS-001 (vehicle mass) |
| Sloped terrain response | Gravity force + normal force vector decomposition | g_moon = 1.62 m/s² |
| Wheel-ground torque | Simple rolling resistance model | TBD-SIM-001 |

---

## 2. Vehicle Model

### 2.1 Power Model

The power model consists of three sub-modules:

**Panel Generation:**
```
P_generated(t) = P_panel(t)  [from §1.2 irradiance model]
```

**Battery Model:**
```
SoC(t+dt) = SoC(t) + (P_generated - P_load) × dt / Capacity_Wh
  Capacity_Wh: TBD-BAT-001 (§10)
  SoC_min: TBD-BAT-002 dependent (cut-off voltage per chemistry)
  SoC_max: 100% (charge regulator limit)
  Coulombic_efficiency: TBD-BAT-002 (chemistry §10)
  Capacity_degradation: SoH × Capacity_nominal (SoH: digital twin §3.3)
```

**Load Consumption:**

| Subsystem | Nominal Power (W) | Source |
|------------|-----------------|--------|
| OBC + Navigation processor | TBD-SIM-006 | §10 power budget |
| Motor drivers (while moving) | TBD-SIM-007 | §10 power budget |
| Heaters (nominal) | TBD-SIM-008 | §10 thermal budget |
| Communication (HGA active) | TBD-SIM-009 | §10 power budget |
| Science sensors | TBD-SIM-010 | §10 power budget |
| Beacon mode (SURVIVAL) | TBD-SIM-009 / 10 | §10 minimum power |

### 2.2 Thermal Model

```
dT_component/dt = (Q_heater + Q_solar_input - Q_radiation - Q_conduction) / (m × Cp)
  m: TBD-MAS-001 (component mass, §10)
  Cp: TBD-THM-001 (thermal capacity, §10)
  Q_heater: heater power (from thermal control signal)
  Q_radiation: σ × ε × A × (T_component⁴ - T_env⁴)
  Q_conduction: k × A × (T1 - T2) / L   [between components]
```

**Critical Component Thermal Parameters:**

| Component | Nominal Operating Range (°C) | Critical Lower Limit | Source |
|---------|------------------------------|------------------|--------|
| Battery | TBD-THM-001 | TBD-THM-003 | §10 thermal |
| OBC processor | TBD-THM-001 | TBD-THM-003 | §10 thermal |
| IMU | TBD-THM-001 | TBD-THM-003 | §10 thermal |
| RF module | TBD-THM-001 | TBD-THM-003 | §10 thermal |

### 2.3 Kinematic Model

Vehicle differential drive model:

```
Differential Drive Kinematics:
  v_linear = (v_right + v_left) / 2
  ω_angular = (v_right - v_left) / wheel_base
  wheel_base: TBD-MAS-001 dependent (vehicle width, §10)

Position Update (Euler integration, dt = 50 ms):
  x(t+dt) = x(t) + v_linear × cos(θ) × dt
  y(t+dt) = y(t) + v_linear × sin(θ) × dt
  θ(t+dt) = θ(t) + ω_angular × dt

Wheel Dynamics:
  v_wheel_max: TBD-TRV-001 dependent (nominal speed §10)
  max_slope: TBD-TRV-002 (°, §10)
  traction_limit: TBD-SIM-001 dependent (ground model)
```

### 2.4 Sensor Model

**IMU Noise Model:**

```
a_measured = a_true + bias_a + noise_a
  bias_a ~ N(0, σ_bias)     σ_bias: TBD-SNS-002 (§10 IMU component)
  noise_a ~ N(0, σ_noise)   σ_noise: TBD-SNS-002 (§10 IMU component)

ω_measured = ω_true + bias_g + noise_g
  bias_g: TBD-SNS-002
  noise_g: TBD-SNS-002
  drift_rate: TBD-SNS-002 (°/h — will be confirmed with component selection)
```

**Camera FOV Model:**

```
Camera:
  horizontal_fov: TBD-SNS-001 (°)
  vertical_fov: TBD-SNS-001 (°)
  resolution: TBD-SNS-001 (px × px)
  noise_sigma: TBD-SNS-001 (SNR model)
  landmark_detection_range_m: TBD-SNS-001
```

**LiDAR Point Cloud Model:**

```
LiDAR:
  range_m: TBD-SNS-001
  angular_resolution: TBD-SNS-001 (°)
  point_cloud_rate_hz: TBD-SNS-001
  range_noise_sigma_m: TBD-SNS-001
  dropout_probability: TBD-SIM-003 (dust model effect)
```

**Odometry Model:**

```
odometry_error:
  sigma_odo_distance: TBD-SNS-003 (§10 — %/m)
  sigma_odo_heading: TBD-SNS-003 (°/m)
  slip_model: TBD-SIM-001 dependent (ground model)
```

---

## 3. Digital Twin

### 3.1 Real Telemetry vs Simulation Comparison

The digital twin compares real vehicle telemetry against simulator output running in parallel:

```
Comparison Metrics:
  position_residual_m: |pos_real - pos_sim| (max accepted: TBD-THM-002 dependent)
  soc_residual_pct: |SoC_real - SoC_sim| (max accepted: TBD-ENE-001)
  temperature_residual_c: |T_real - T_sim| / component (max accepted: TBD-THM-002)
  nav_uncertainty_ratio: σ_pos_real / σ_pos_sim

Anomaly Detection:
  residual > threshold → digital twin alert
  → Parameter update triggered (§3.3)
  → Ground segment notification (ICD-006 downlink)
```

### 3.2 Time-Accelerated Simulation

For accelerated mission preview, the simulator supports a configurable speed factor rather than real-time:

```yaml
# Simulation time parameters
time_acceleration_factor: [1x, 10x, 100x, 1000x]
dt_physics_s: 0.05          # physics engine step size (fixed)
dt_telemetry_log_s: 1.0     # telemetry logging step
dt_snapshot_s: 60.0         # checkpoint save interval

# Time management
mission_start_utc: TBD-TIME-001
max_simulation_duration_h: TBD (depending on mission scenario)
```

**Use cases:**
- **Pre-mission preview:** Simulate 72-hour surface exploration in ~43 minutes at 100x speed.
- **PSR operation planning:** PSR entry/exit energy validation at 10x speed.
- **Thermal validation:** Simulate one lunar night/day cycle in ~90 seconds at 1000x speed.

### 3.3 Parameter Update: Vehicle SoH Degradation

State-of-Health (SoH) is updated with real telemetry data:

```python
# SoH update loop (concept — pseudocode)
class SoHUpdater:
    """
    Synchronises simulator parameters with real telemetry.
    """
    def update_battery_soh(self, real_capacity_wh: float, nominal_capacity_wh: float):
        """
        SoH = C_measured / C_nominal
        Updated on each charge-discharge cycle.
        """
        self.soh_battery = real_capacity_wh / nominal_capacity_wh  # 0.0–1.0

    def update_motor_efficiency(self, real_torque_nm: float, cmd_torque_nm: float):
        """Motor mechanical efficiency degradation."""
        self.eta_motor = real_torque_nm / cmd_torque_nm

    def update_panel_efficiency(self, real_power_w: float, expected_power_w: float):
        """Panel efficiency: effect of dust, radiation damage."""
        self.eta_panel = real_power_w / expected_power_w

    def apply_to_simulator(self, sim: 'VehicleSimulator'):
        """Apply current SoH values to simulator models."""
        sim.battery.capacity_wh *= self.soh_battery
        sim.motor.efficiency = self.eta_motor
        sim.solar_panel.efficiency = self.eta_panel
```

---

## 4. Scenario Runner

### 4.1 Scenario Format (YAML)

Each scenario YAML file consists of three main sections: initial conditions, events, termination criteria.

```yaml
# Scenario YAML Schema — LUNA-AI v1.0
scenario_id: "SC-XXX"
name: "Scenario Name"
description: "Brief description"
version: "1.0"
created: "YYYY-MM-DD"
references:
  - operational_scenarios: "SC-XXX"
  - safety_state_machine: "LUNA-AI-ARCH-001"

# --- Initial Conditions ---
initial_conditions:
  position:
    x_m: 0.0
    y_m: 0.0
    z_m: 0.0            # calculated from DEM
    uncertainty_m: 0.3  # initial position uncertainty
  heading_deg: 0.0
  velocity_ms: 0.0
  soc_percent: 85.0
  safety_state: "NOMINAL"
  mission_phase: "SURFACE_EXPLORATION"
  thermal_state:
    battery_temp_c: TBD    # §10 thermal model
    obc_temp_c: TBD
    nominal_all: true
  time_utc: TBD-TIME-001   # mission start date

# --- Events (time or condition triggered) ---
events:
  - id: "EVT-001"
    trigger:
      type: "time"           # "time" | "condition" | "command"
      time_offset_s: 0.0
    action:
      type: "waypoint_set"
      waypoints: []          # coordinate list

# --- Termination Criteria ---
termination_criteria:
  success:
    - condition: "all_waypoints_reached"
    - condition: "soc_above_threshold"
      threshold_pct: 20.0
  failure:
    - condition: "soc_below_critical"
      threshold_pct: 10.0
    - condition: "safety_state_equals"
      state: "SURVIVAL"
    - condition: "max_time_exceeded"
      max_duration_s: TBD

# --- Acceptance Criteria ---
acceptance_criteria:
  - id: "AC-001"
    description: "All waypoints reached within ±1m"
  - id: "AC-002"
    description: "SoC never fell below 10%"
  - id: "AC-003"
    description: "Nav uncertainty did not exceed 1.0m RMS"
```

### 4.2 Consistency with Existing Scenarios

Correspondence table with `simulation/scenarios/operational_scenarios.md` (SC-001..SC-009):

| Operational Scenario | YAML File | Test Type |
|---------------------|--------------|-----------|
| SC-001 (Nominal Exploration) | `nominal_surface_exploration.yaml` | SIL |
| SC-002 (Link Loss) | `comm_loss_surface.yaml`, `comm_loss_psr.yaml` | SIL |
| SC-003 (PSR Energy Drop) | `psr_energy_emergency.yaml` | SIL |
| SC-004 (Localisation Loss) | `localization_loss_recovery.yaml` | SIL |
| SC-005 (Safe Haven Unreachable) | `safe_haven_blocked.yaml` | SIL |
| SC-006 (Thermal Limit Violation) | `thermal_critical.yaml` | SIL |
| SC-007 (Long Communication Outage) | `long_comm_outage.yaml` | SIL |
| SC-009 (Observer Height) | `observer_height_sensitivity.yaml` | Analysis + SIL |

### 4.3 Nominal Mission Scenario

See: `simulation/scenarios/example_scenario.yaml` (Appendix A of this document).

---

## 5. Fault Injection

### 5.1 Injectable Fault Types

| Fault ID | Type | Parameters | FMEA Reference |
|---------|------|--------------|----------------|
| FI-001 | Sensor noise increase (IMU) | scale_factor × σ_noise (e.g. 5×) | FMEA-RPN-NAV-001 |
| FI-002 | IMU bias shift | bias_offset_dps (°/s) | FMEA-RPN-NAV-001 |
| FI-003 | LiDAR dust filter (dropout increase) | dropout_pct (%) | FMEA-RPN-NAV-002 |
| FI-004 | Motor stall (one wheel) | wheel_id, stall_torque_nm | FMEA-RPN-MOT-001 |
| FI-005 | Sudden battery capacity drop | delta_soc_pct (e.g. -20%) | FMEA-RPN-PWR-001 (RPN:30) |
| FI-006 | Link loss | duration_s | SC-002, SC-007 |
| FI-007 | Heater open circuit | heater_id | FMEA-RPN-THM-001 (RPN:20) |
| FI-008 | FDIR task freeze (watchdog test) | freeze_duration_ms | FMEA-RPN-FDIR-001 |
| FI-009 | EKF wrong initialisation | initial_cov_scale (e.g. 10×) | FMEA-RPN-NAV-003 |
| FI-010 | PDU single channel loss | channel_id | redundancy_matrix SPF-001 |

### 5.2 Method for Testing FDIR Response

```
Step 1: Run nominal scenario → establish baseline (all metrics)
Step 2: Inject fault (with FI-XXX parameters)
Step 3: Measure FDIR response time:
         detection_latency_ms ≤ acceptance criterion (SC-004: < 5s)
Step 4: State transition validation:
         safety_state_transition = expected_transition (e.g. NOMINAL → CAUTION)
Step 5: Recovery test:
         recovery_time ≤ acceptance criterion
Step 6: Record result: fault_injection / FDIR_response / recovery / metrics
```

**FDIR Test Metrics:**

| Metric | Acceptance Criterion | Source |
|--------|---------------|--------|
| Localisation loss detection time | < 5 s | SC-004 |
| HC-006 violation → RETURN_REQUIRED transition time | < 5 s | SC-003 |
| Thermal critical → RETURN_REQUIRED transition time | < 5 s | SC-006 |
| Motor stall detection time | < 500 ms | FMEA-RPN-MOT-001 |
| Battery anomaly detection time | < 2 s | FMEA-RPN-PWR-001 |
| FDIR HW watchdog kick miss → reset | < 30 s | SAFETY_STATE_MACHINE §3.1 |

### 5.3 Regression Test Suite (Every PR)

Test suite running automatically in CI pipeline on every pull request:

```yaml
# regression_test_suite.yaml — CI triggered
test_suite: "LUNA-AI Regression Tests v1.0"
trigger: "every_PR"
timeout_minutes: TBD-SIM-011   # depends on §10 CI infrastructure capacity

test_cases:
  - id: "RT-001"
    scenario: "nominal_surface_exploration.yaml"
    fault_injection: none
    expected_result: "success"
    max_duration_s: TBD-SIM-012

  - id: "RT-002"
    scenario: "psr_energy_emergency.yaml"
    fault_injection: "FI-005"   # Sudden SoC drop
    expected_result: "RETURN_REQUIRED_triggered"
    acceptance: "detection_latency < 5s"

  - id: "RT-003"
    scenario: "localization_loss_recovery.yaml"
    fault_injection: "FI-001"   # IMU noise increase
    expected_result: "CAUTION_then_recovery OR RETURN_REQUIRED"
    acceptance: "FDIR_state_matches_expected"

  - id: "RT-004"
    scenario: "comm_loss_psr.yaml"
    fault_injection: "FI-006"   # Link loss
    expected_result: "RETURN_REQUIRED_triggered"
    acceptance: "pre_planned_abort_activated"

  - id: "RT-005"
    scenario: "thermal_critical.yaml"
    fault_injection: "FI-007"   # Heater open circuit
    expected_result: "CAUTION_then_RETURN_REQUIRED"
    acceptance: "heater_fallback_activated"

  - id: "RT-006"
    scenario: "nominal_surface_exploration.yaml"
    fault_injection: "FI-008"   # FDIR task freeze
    expected_result: "HW_watchdog_reset"
    acceptance: "system_reboots_to_CAUTION_in_30s"

metrics_collected:
  - safety_state_transitions
  - fdir_detection_latency_ms
  - recovery_time_ms
  - soc_min_pct
  - nav_uncertainty_max_m
  - thermal_min_temp_c
```

---

## 6. SIL/HIL Strategy

### 6.1 SIL (Software-in-the-Loop) — P1 Phase

In SIL, all vehicle software runs on the host computer; no hardware is present. Environment and vehicle models are defined in this document.

**Modules to be executed first in SIL:**

| Module | SIL Priority | Why SIL First |
|-------|--------------|----------------|
| FDIR state machine | P1 — critical | HIL is not meaningful before formal verification begins |
| Navigation EKF | P1 — critical | Sensor fusion algorithm is hardware-independent |
| Global planner (route) | P1 | Computation-heavy; hardware-independent |
| Power management logic | P1 | Energy budget calculations are hardware-independent |
| Thermal management logic | P1 | Control loop is algorithmic |
| Mission executive | P1 | State logic; ICD compliance |
| Scenario regression tests | P1 | Runs with SIL on every PR |

### 6.2 HIL (Hardware-in-the-Loop) — P2/P3 Phase

In HIL, the real vehicle computer (OBC + Navigation processor) connects to the simulator via real-time interfaces.

**Modules requiring HIL:**

| Module | HIL Justification | P2/P3 |
|-------|---------------|-------|
| FDIR hardware watchdog | HW timer independence can only be tested on real HW | P2 |
| FreeRTOS task prioritisation | Real RTOS scheduling tests | P2 |
| IMU sensor interface (SPI) | Real sensor noise + timing | P2 |
| Motor driver control loop | Real CAN bus latency | P2 |
| RF communication chain | Real CCSDS packet transmission | P3 |
| Power distribution interface (I2C/CAN) | Real PDU command delay | P3 |
| Thermal heater hardware | Failback circuit activation test | P3 |

**HIL Interface Bridge:**

```
SIL/HIL Bridge (simulation/digital-twin/sil_hil_bridge):
  - Simulator sensor outputs → converted to vehicle HW sensor interface format
  - Vehicle HW actuator commands → converted to simulator model inputs
  - Timing: 50 ms step synchronisation (adjustable)
  - Protocol: TBD (after §10 OBC interface is confirmed)
```

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — Agent C, C3 task |
