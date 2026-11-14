# LUNA-AI Concept of Operations (CONOPS)

**Document ID:** LUNA-AI-CONOPS-001  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Status:** Draft — Hardware parameters TBD

---

## 1. Mission Definition and Objectives

LUNA-AI is an autonomous lunar surface mission system that evaluates craters containing PSRs (Permanently Shadowed Regions) near the lunar south pole using scientific and operational data.

### 1.1 Primary Objectives

- Provide safe access to target craters near the lunar south pole
- Map ice/resource regions inside PSRs with in-situ sensors
- Complete each operation day by returning to safe haven with sufficient energy reserve

### 1.2 Out of Scope

- Trans-lunar (transit / cruise) phase is not covered by this CONOPS
- Landing and surface transfer phases will be addressed in a separate CONOPS

---

## 2. System Segments

| Segment | Sub-Components | Primary Responsibility |
|---------|----------------|---------------------|
| **Ground Segment** | Scientific Analysis, Mission Design, Operator Interface | Long-term mission planning, scientific prioritisation, telemetry analysis |
| **Flight Segment** | Navigation, FDIR, Motion Control, Power Management, Thermal, Communication | Real-time operation, safety, autonomous decision-making |
| **Simulation & Validation** | Digital Twin, Scenario Test Environment | Pre-mission verification, risk analysis, training |

---

## 3. Nominal Mission Day

One solar period at the lunar south pole is approximately **14 Earth days**. The vehicle follows the steps below in each operation cycle.

> **Assumption:** Vehicle has been waiting at safe haven overnight, batteries fully charged, thermal system within nominal range.

### Step 1 — Morning System Check (Owner: FDIR + Power Management)

| Sub-step | Description | Output |
|----------|----------|-------|
| 1.1 | FDIR boot-on-wakeup test: heartbeat verification from all subsystems | Go / No-Go |
| 1.2 | Power Management: battery SoC measurement, opening energy calculation | energy_state message |
| 1.3 | Thermal Management: check critical component temperatures | thermal_state message |
| 1.4 | Navigation: IMU initialisation, star-tracker / Sun-sensor calibration | vehicle_pose initial fix |
| 1.5 | Communication: uplink/downlink link test with ground | link_status |

**Exit condition:** All subsystems nominal → Give Go to Mission Planner.

### Step 2 — Solar Panel Deployment and Charging (Owner: Power Management)

| Sub-step | Description | Responsible Module |
|----------|----------|---------------|
| 2.1 | Panel orientation algorithm calculates solar angle | Power Management |
| 2.2 | Send panel servo command | Motion Control |
| 2.3 | Charging current verification: **TBD:** minimum panel efficiency threshold | Power Management |
| 2.4 | Charge update rate: publish energy_state every **TBD:** seconds | Power Management → Mission Planner |

### Step 3 — Daily Plan Reception (Owner: Communication + Mission Planner)

| Sub-step | Description |
|----------|----------|
| 3.1 | Wait for uplink window to open (link window: **TBD:** start/end) |
| 3.2 | Receive daily mission package from ground segment (ICD-005 format) |
| 3.3 | Mission Planner validates package: parameters, energy budget consistency |
| 3.4 | If validation successful, activate plan; if error, retain previous safe plan |

### Step 4 — Exploration Operation (Owner: Navigation + Local Planner + Motion Control)

| Sub-step | Description |
|----------|----------|
| 4.1 | Mission Planner publishes global route (state updates via ICD-001/002/003) |
| 4.2 | Local Planner updates obstacle map, generates instantaneous path |
| 4.3 | Motion Control executes movement toward waypoints |
| 4.4 | FDIR subsystem health check every **TBD:** seconds |
| 4.5 | Scientific sensors: start spectroscopy/camera when approaching crater edge |
| 4.6 | Telemetry: downlink to ground segment every **TBD:** seconds (ICD-006) |

**Continuous check:** Power Management monitors return energy reserve → publishes CAUTION to Mission Planner if SoC risks dropping below 15%.

### Step 5 — Afternoon Energy Assessment (Owner: Mission Planner)

| Sub-step | Description |
|----------|----------|
| 5.1 | Calculate return energy with current SoC and projected consumption |
| 5.2 | Calculated return margin < 25% SoC → shorten operation time, prepare for return |
| 5.3 | If solar angle declining, re-orient panel |
| 5.4 | Send midday status report to ground segment |

### Step 6 — Safe Haven Return Manoeuvre (Owner: Navigation + Mission Planner)

| Sub-step | Description |
|----------|----------|
| 6.1 | Mission Planner transitions to RETURN_REQUIRED when return trigger is reached (energy, time or ground command) |
| 6.2 | Navigation calculates A* route to safe haven coordinates |
| 6.3 | Motion Control executes return route |
| 6.4 | Record checkpoint at each safe location reached (fallback point for emergencies) |
| 6.5 | At safe haven arrival, verify system state, send final daily report to ground segment |

### Step 7 — Night Preparation (Owner: Thermal + Power Management)

| Sub-step | Description |
|----------|----------|
| 7.1 | Shut down panel solar tracking |
| 7.2 | Thermal Management: activate heaters, keep critical components above minimum temperature |
| 7.3 | Power Management: switch to night survival power mode, shed deferrable loads |
| 7.4 | FDIR initiates night monitoring mode (low-frequency heartbeat) |

---

## 4. PSR Entry Scenario

PSR operations carry the highest mission risk. The flow below shows the conditional transition logic applying the safety-first principle.

### 4.1 Pre-Entry Condition Verification

| Condition | Responsible Module | Acceptance Threshold |
|-------|---------------|-------------|
| Battery SoC | Power Management | **TBD:** minimum % SoC (full return + safety margin must be met) |
| Navigation accuracy | Navigation | < 0.5 m RMS position error |
| Ground communication | Communication | Last successful uplink < **TBD:** minutes ago |
| Thermal budget | Thermal Management | All critical components within nominal range |
| Local conditions | Navigation | No dust storm detected |
| FDIR state | FDIR | NOMINAL or CAUTION (no entry in RETURN_REQUIRED) |

**If all conditions are not met, PSR entry is cancelled and the vehicle enters standby mode.**

### 4.2 In-PSR Operations

| Step | Description | Critical Parameter |
|------|----------|-----------------|
| 4.2.1 | Cross PSR boundary; FDIR transitions to PSR mode (increased monitoring frequency) | — |
| 4.2.2 | Start active illumination (LED or spotlight) | Add power consumption increase to energy budget |
| 4.2.3 | Local Planner transitions to limited-visibility navigation mode | Increase LiDAR/stereo weight |
| 4.2.4 | Evaluate energy consumption and battery state every **TBD:** seconds | Return trigger SoC threshold |
| 4.2.5 | Collect scientific samples/measurements | spectroscopy, thermal measurement, photography |
| 4.2.6 | Communication loss expected; autonomous decision-making engages | link_timeout = **TBD:** seconds |

### 4.3 Return Decision

When **any** of the following conditions is triggered, the vehicle begins exiting the PSR:

| Trigger | Threshold | Priority |
|------------|------|---------|
| Battery SoC return threshold | **TBD:** % SoC | P1 (highest) |
| Planned PSR mission duration elapsed | **TBD:** minutes | P2 |
| Ground "PSR exit" command received | — | P2 |
| Thermal critical warning | **TBD:** °C | P1 |
| Navigation localisation loss | Position uncertainty > **TBD:** m | P1 |

### 4.4 Emergency Return

When a P1 trigger is met, the vehicle immediately returns to the **last known safe waypoint**:

1. FDIR transitions to SURVIVAL state
2. All scientific operations frozen
3. Motion Control calculates emergency return route (current map + last known position)
4. Power Management activates survival mode (only navigation + FDIR + communication remain powered)
5. When outside PSR, an emergency status packet is sent to ground segment

---

## 5. Crisis Scenarios

### Scenario A — Communication Loss

**Trigger:** Downlink or uplink interruption > **TBD:** minutes (link_timeout)

| Step | Vehicle Decision | Ground Notification |
|------|-------------|---------------|
| A.1 | Autonomous mode active: mission plan continues from local copy | Ground immediately notified of link loss |
| A.2 | FDIR state machine CAUTION → internal silent message (if not inside PSR) | — |
| A.3 | Communication module retries reconnection (retry every **TBD:** seconds) | — |
| A.4 | link_timeout_extended (> **TBD:** minutes) → RETURN_REQUIRED | Ground segment searches for position with DF antenna |
| A.5 | On safe haven arrival → system waits for reconnection in low-power mode | Ground segment re-establishes link when ping received from vehicle |

**Rules:** Without link the vehicle takes no new risks; only completes current plan or returns.

---

### Scenario B — Energy Critical (Below 15% SoC)

**Trigger:** SoC < 15% or projected return energy insufficient

| Step | Vehicle Decision | Ground Notification |
|------|-------------|---------------|
| B.1 | FDIR CAUTION → all scientific loads and optional subsystems shed | CAUTION flag in telemetry |
| B.2 | Power Management calculates survival power budget | — |
| B.3 | If SoC < 15%: RETURN_REQUIRED: begin safe haven route | Critical energy warning downlink |
| B.4 | If SoC < 10%: SURVIVAL: only navigation + FDIR + communication remain powered | Send emergency energy packet |
| B.5 | On safe haven arrival, position panel, await charge | Ground segment monitors energy state |

**Note:** 15% SoC is the nominal return margin; at step B.3 the vehicle also accounts for positional and thermal losses.

---

### Scenario C — Localisation Loss

**Trigger:** Navigation position uncertainty > **TBD:** m RMS or EKF (Extended Kalman Filter) inconsistent

| Step | Vehicle Decision | Ground Notification |
|------|-------------|---------------|
| C.1 | Motion Control halts (position hold / zero velocity command) | FDIR sends localisation loss warning |
| C.2 | Navigation references last known good position | — |
| C.3 | Relocalisation attempt: IMU dead-reckoning + visual landmark matching | — |
| C.4 | Localisation restored within **TBD:** s → exit CAUTION, resume movement | — |
| C.5 | If localisation not restored → RETURN_REQUIRED; return via last-known-good waypoint | Ground segment notified of localisation loss |
| C.6 | If localisation never restored → SURVIVAL; dead-reckoning to safe haven with radar/camera assistance | Emergency measure activation notification |

---

### Scenario D — Thermal Critical

**Trigger:** Any monitored component temperature exceeds acceptable threshold

| Step | Vehicle Decision | Ground Notification |
|------|-------------|---------------|
| D.1 | FDIR generates thermal warning; Thermal Management engages | CAUTION flag downlink |
| D.2 | Activate heating/cooling system; return temperature to nominal range within **TBD:** seconds | — |
| D.3 | If thermal critical region persists: shed loads contributing to temperature | — |
| D.4 | If temperature exceeds `max_critical` threshold → RETURN_REQUIRED; move away from Sun-facing surface | Send critical thermal warning |
| D.5 | Rapid overheating (rate > **TBD:** °C/min) → SURVIVAL; emergency power cut + check position | Send emergency thermal packet |

---

## 6. Ground-Vehicle Boundary

### 6.1 Command Types

| Command Type | Description | Priority | Effect on Vehicle |
|------------|----------|---------|---------------------|
| **TC-IMMEDIATE** | Emergency stop, emergency return, emergency power off | P1 | Direct execution bypassing FDIR |
| **TC-CONDITIONAL** | "Do if condition X is met" | P2 | Execute after FDIR validation |
| **TC-PLAN** | Load daily mission package | P3 | Mission Planner validates |
| **TC-PARAM** | Parameter update (threshold, timeout) | P3 | Subsystem approval required |
| **TC-QUERY** | Telemetry/status request | P4 | Information flow, no action |

### 6.2 Link Window

**TBD:** When orbital mechanics simulation is complete, real link window times (start, duration, frequency) will be added. High-gain antenna orientation is also tied to this analysis.

**Typical assumption (to be replaced):** Approximately 2–4 link windows per day, each window 15–45 minutes.

### 6.3 Rules During No-Link

1. Vehicle continues active mission plan — takes no new risks, does not enter PSR.
2. State machine remains in CAUTION; RETURN_REQUIRED transition occurs via its own triggers.
3. Autonomous decision authority fully active: Mission Planner and FDIR operate independently.
4. When link window opens, vehicle first flushes all buffered telemetry, then receives new commands.
5. Conflicting command + autonomous decision: **TC-IMMEDIATE** always takes precedence; other commands pass FDIR approval.

---

## 7. Core Principles (Reference)

| Principle | Description |
|---------|----------|
| **Safety First** | No mission objective can override safety state requirements |
| **Ground-Flight Separation** | Ground segment performs planning and analysis; instantaneous decisions belong to flight segment |
| **Uncertainty Visible** | All estimates and calculations are published with uncertainty bands |
| **Simulation Before Flight** | No new mission parameter may be applied without first testing in the digital twin |
| **Interface-Based Modularity** | Modules communicate only over defined ICD messages |

---

*Next step: Once hardware parameters (battery capacity, panel area, thermal limits) are received, all TBD fields will be updated and CONOPS version 1.0 will be published.*
