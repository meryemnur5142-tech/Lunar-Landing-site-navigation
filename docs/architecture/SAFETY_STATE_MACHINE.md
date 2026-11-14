# LUNA-AI Safety State Machine Design

**Document ID:** LUNA-AI-ARCH-001
**Version:** 0.1-draft
**Date:** 2026-11-14
**Related ADR:** ADR-005
**Related QAR:** FDIR-001, FDIR-002, FDIR-004, FDIR-005

---

## 1. State Definitions

### NOMINAL

The vehicle is operating at full operational capacity. All subsystems are within accepted parameter ranges.

**Monitored Parameters:**
- SoC > return threshold + safety margin (see QAR PWR-001)
- Navigation position uncertainty < 0.5 m RMS (NAV-001)
- All critical component temperatures within nominal range (THM-004/005)
- Communication link_timeout counter < threshold (COM-004)
- All FDIR heartbeats received on time

**Permitted Actions:**
- PSR entry (if all PSR entry conditions are satisfied)
- Full-speed exploration operation
- Scientific sensor operation
- Receiving and applying a new mission plan
- Route replanning

---

### CAUTION

One or more parameters are in the observation range (early warning) but not yet at the critical threshold. The vehicle continues operations but risk has increased.

**Triggers (any of the following):**
- SoC < 25% or projected return margin < 20%
- Navigation uncertainty 0.5–1.0 m RMS
- Any component temperature in warning range (80% of nominal limit)
- Communication link absence > **TBD:** minutes (warning threshold)
- Mission Planner heartbeat delayed (warning threshold; not critical)

**Permitted Actions:**
- Ongoing operation completed (up to safe stopping point)
- No new PSR entry
- Replanning prioritised (return route kept ready)
- CAUTION flag sent to ground segment

**Restricted Actions:**
- Cannot initiate new PSR entry
- Cannot start high-power scientific operation

---

### RETURN_REQUIRED

The vehicle must begin a safe return. Continuing carries unacceptable risk.

**Triggers (any of the following):**
- SoC < 15% (PWR-001) or projected return energy insufficient
- Communication link absence > **TBD:** minutes (critical threshold, COM-004)
- Navigation localisation loss recovery failed > **TBD:** seconds
- RETURN_REQUIRED command from ground segment (TC-IMMEDIATE)
- Thermal critical ongoing and local intervention failed

**Permitted Actions:**
- Safe haven return route calculation and execution
- Navigation and FDIR fully operational
- Communication active (if uplink available)
- Checkpoint saving

**Restricted Actions:**
- Scientific operation completely frozen
- Exploration route not continued
- PSR entry strictly forbidden

---

### SURVIVAL

Risk of mission loss or vehicle loss is high. All resources directed to survival.

**Triggers (any of the following):**
- SoC < 10%
- Critical hardware failure (motion control, thermal, primary navigation)
- Rapid overheating: temperature rise > **TBD:** °C/min
- FDIR lost its own internal heartbeat (self-watchdog)
- Multiple simultaneous P1 failures

**Permitted Actions:**
- Navigation (reduced to minimum mode: IMU + dead-reckoning)
- FDIR (core function)
- Communication (minimum-power beacon)
- Minimum heating (battery protection)

**Shed Loads:**
- All scientific sensors
- High-power communication (beacon only remains)
- Planner and replanning calculations
- Camera, LiDAR (not for navigation)
- Panel servo (locked at last position)

---

## 2. State Transition Conditions

```
NOMINAL ──────────────────────► CAUTION
 │  energy_warning OR nav_warning OR thermal_warning OR link_warning
 │
 ├──────────────────────────────► RETURN_REQUIRED
 │  SoC < 15% OR link_critical OR nav_loss_timeout OR ground_command
 │
 └──────────────────────────────► SURVIVAL
    SoC < 10% OR critical_failure OR rapid_heating

CAUTION ──────────────────────► NOMINAL
 │  all parameters returned to nominal range
 │
 ├──────────────────────────────► RETURN_REQUIRED
 │  any RETURN trigger active
 │
 └──────────────────────────────► SURVIVAL
    any SURVIVAL trigger active

RETURN_REQUIRED ──────────────► SURVIVAL
 │  SURVIVAL trigger active during return
 │
 └──────────────────────────────► NOMINAL  [ground approval only]
    safe_haven_reached AND energy_sufficient AND ground_segment_approved

SURVIVAL ─────────────────────► RETURN_REQUIRED [ground approval only]
    basic_system_recovered AND energy > 10% AND ground_segment_approved
```

> **Note:** There is no direct transition from SURVIVAL to NOMINAL. The vehicle always passes through RETURN_REQUIRED and requires explicit ground segment approval.

### Numerical Threshold Reference Table

| Parameter | CAUTION Threshold | RETURN_REQUIRED Threshold | SURVIVAL Threshold |
|-----------|-----------------|--------------------------|-------------------|
| SoC | < 25% | < 15% | < 10% |
| Nav. Uncertainty | 0.5–1.0 m RMS | > 1.0 m RMS loss | — |
| Link Outage | > **TBD** min (warning) | > **TBD** min (critical) | — |
| Temperature | 80% of nominal limit | Outside nominal limit | Rapid rise > **TBD** °C/min |
| SoC Projected Margin | < 20% return margin | < 15% return margin | < 10% total SoC |

---

## 3. Watchdog Design

### 3.1 Modules Sending Heartbeats

Every critical FreeRTOS task sends regular heartbeat messages to the FDIR watchdog queue:

| Module | Heartbeat Period | Timeout Threshold | Timeout Result |
|--------|-----------------|-------------------|----------------|
| Navigation | 100 ms | 500 ms | CAUTION → nav heartbeat loss |
| Power Management | 500 ms | 2 s | CAUTION → power heartbeat loss |
| Thermal Management | 1 s | 5 s | CAUTION → thermal heartbeat loss |
| Motion Control | 100 ms | 500 ms | CAUTION → motion heartbeat loss |
| Mission Planner | 2 s | 10 s | CAUTION (planner frozen — FDIR operates independently) |
| Communication | 5 s | 30 s | CAUTION → communication heartbeat loss |

**FDIR's own watchdog loop:**
- FDIR sends a heartbeat to a separate hardware watchdog timer
- When FDIR itself freezes, the hardware watchdog restarts the system
- After restart, FDIR starts from CAUTION and evaluates history

### 3.2 Watchdog Implementation

```
FDIR_Task (Priority: Highest)
│
├── Heartbeat monitor loop (checks every 50 ms)
│   └── Check subsystem heartbeat record table
│       → Timeout? → Trigger state transition
│
├── State machine evaluation
│   → Current state + all trigger signals
│   → Apply transition table
│   → New state activation
│
└── Hardware watchdog kick (every 25 ms)
    → If missed: hardware reset → FDIR restarts
```

---

## 4. FDIR Independence Requirements

FDIR delegates mission execution decisions to Mission Planner; however, safety decisions are within FDIR's exclusive authority.

### 4.1 Not Shared Between FDIR and Mission Planner

| Resource / Data | Why Not Shared |
|----------------|----------------|
| FDIR state machine runtime state | Planner failure must not affect FDIR |
| Watchdog timer records | Tamper risk; only FDIR reads |
| SURVIVAL mode power shed list | Must work even when planner is inactive |
| Hardware watchdog kick signal | Belongs to FDIR's own loop |
| Critical hardware interfaces not easily interrupted | No planner command needed |

### 4.2 Shared Between FDIR and Mission Planner (via ICD)

| Data | Direction | ICD | Description |
|------|-----------|-----|-------------|
| `safety_status` | FDIR → Planner | ICD-004 | Current safety state |
| `abort_signal` | FDIR → Planner | ICD-004 | Planner freezes all operations |
| Planner heartbeat | Planner → FDIR | — | Planner health report |
| `fdir_caution_event` | FDIR → Planner | ICD-004 | Planner updates restricted action list |

### 4.3 Independent Operation Scenario

When Mission Planner freezes, FDIR can independently:
- Perform state transition (NOMINAL → RETURN_REQUIRED)
- Issue basic motion stop command (directly to Motion Control)
- Issue power shed command (directly to Power Management)
- Issue minimum-mode transition command to Navigation
- Issue emergency beacon command to Communication

---

## 5. PlantUML State Diagram

```plantuml
@startuml LUNA-AI Safety State Machine

[*] --> NOMINAL : boot_complete AND subsystems_ok

state NOMINAL {
  NOMINAL : All subsystems nominal
  NOMINAL : PSR entry permitted
  NOMINAL : Full exploration operation
  NOMINAL : Monitored: SoC, nav, thermal, link, heartbeat
}

state CAUTION {
  CAUTION : Early warning state
  CAUTION : New PSR entry forbidden
  CAUTION : Ongoing operation completed
  CAUTION : Return route kept ready
}

state RETURN_REQUIRED {
  RETURN_REQUIRED : Return mandatory
  RETURN_REQUIRED : Scientific operation frozen
  RETURN_REQUIRED : Safe haven route active
}

state SURVIVAL {
  SURVIVAL : Survival mode
  SURVIVAL : Only nav + FDIR + beacon active
  SURVIVAL : All optional loads shed
}

NOMINAL --> CAUTION : energy_warning OR nav_warning OR\nthermal_warning OR link_warning
NOMINAL --> RETURN_REQUIRED : SoC < 15% OR link_critical OR\nnav_loss OR ground_command
NOMINAL --> SURVIVAL : SoC < 10% OR critical_failure OR\nrapid_heating

CAUTION --> NOMINAL : all_parameters_nominal\n[all_triggers_clear]
CAUTION --> RETURN_REQUIRED : RETURN trigger active
CAUTION --> SURVIVAL : SURVIVAL trigger active

RETURN_REQUIRED --> SURVIVAL : SURVIVAL trigger active
RETURN_REQUIRED --> NOMINAL : safe_haven_reached AND\nenergy_sufficient AND ground_approval

SURVIVAL --> RETURN_REQUIRED : basic_system_recovered AND\nenergy > 10% AND ground_approval

note right of SURVIVAL
  No direct transition from
  SURVIVAL to NOMINAL.
  Ground segment approval mandatory.
end note

note right of FDIR
  FDIR operates in every state.
  Independent of Mission Planner.
  Hardware watchdog: 25 ms kick.
end note

@enduml
```

---

## 6. Formal Verification Scope

The following properties will be verified with TLA+ or an equivalent model checker:

| Property | Description | Test Type |
|----------|-------------|-----------|
| **Safety** | No exit from SURVIVAL without ground approval | Invariant check |
| **Liveness** | When RETURN_REQUIRED is triggered, the vehicle eventually reaches the safe haven | Liveness check |
| **Deterministic** | The same set of inputs always produces the same transition | State space exhaustion |
| **No deadlock** | No deadlock occurs in any state combination | Deadlock freedom check |
| **Multiple trigger consistency** | Simultaneous P1 triggers always transition to the highest-priority state | Reachability check |

---

*Detailed watchdog timer configuration and FreeRTOS task priority table will be added to this document during the system design phase.*
