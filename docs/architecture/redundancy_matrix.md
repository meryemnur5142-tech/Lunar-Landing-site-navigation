# status: draft
# owner: Agent C
# depends_on: [docs/adr/FMEA_KRITIK_MODULLER.md, docs/architecture/SAFETY_STATE_MACHINE.md, docs/architecture/ICD_TEMPLATES.md]
# open_items: [TBD-RED-001..TBD-RED-008 — redundancy options not implementable until vehicle mass/volume constraints are confirmed; RPNs will be updated after hardware selection]

# Redundancy Matrix — LUNA-AI v1.0

**Document ID:** LUNA-AI-ARCH-003  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related Documents:** LUNA-AI-FMEA-001, LUNA-AI-ARCH-001, ADR-005

---

## Redundancy Type Definitions

| Code | Type | Description |
|-----|-----|----------|
| **Simplex** | Single | No backup; single component. Failure has immediate impact. |
| **Dual** | Dual | Two identical components; one takes over when the other fails. |
| **Triple (2-of-3)** | Triple Voting | Three independent channels; the value agreed by 2 is used (majority voting). |
| **Functional** | Functional | Backup that provides the same function via a different technology/method (heterogeneous). |

## Failover Type Definitions

| Code | Type | Description |
|-----|-----|----------|
| **Cold Standby** | Cold Standby | Backup waits unpowered; failover time on the order of minutes. |
| **Warm Standby** | Warm Standby | Backup is powered but not active; failover on the order of seconds. |
| **Hot Standby** | Hot Standby | Backup is continuously active and synchronised; instant (< 1 s) failover. |

---

## Redundancy Matrix

| Module | Component | Redundancy Type | Failover Strategy | Detection Time | Recovery Time | FMEA RPN Ref |
|-------|---------|-----------------|---------------------|---------------|-----------------|--------------|
| **Power Management** | Power Distribution Unit (PDU) | Dual | Hot Standby — secondary PDU monitors continuously; instant transfer if primary is lost | < 500 ms (hardware latch) | < 1 s (automatic) | FMEA-RPN-PWR-003 (RPN: 10) |
| **Power Management** | Battery System | Dual (two independent modules) | Warm Standby — secondary module waits charged; connects when primary fails | < 2 s (SoC monitor) | < 5 s (power transfer) | FMEA-RPN-PWR-001 (RPN: 30) |
| **Flight Computer** | Main Computer (OBC) | Dual | Warm Standby — backup OBC gets synchronous memory updates; watchdog triggers when primary hangs | < 500 ms (FDIR watchdog) | < 10 s (boot + state restoration) | FMEA-RPN-FDIR-001 (RPN: 5) |
| **Navigation** | IMU / Navigation Sensor | Functional (IMU primary + visual odometry/EKF backup) | Warm Standby — full fusion when IMU healthy; switches to camera+odometry-only mode on failure | < 500 ms (EKF covariance monitoring) | < 5 s (mode transition) | FMEA-RPN-NAV-001 (RPN: 24) |
| **Safety** | FDIR Watchdog | Dual (software FDIR + hardware watchdog) | Hot Standby — hardware watchdog operates independently of FDIR; hardware reset fires when FDIR hangs | < 25 ms (hardware kick period) | < 30 s (boot + start from CAUTION) | FMEA-RPN-FDIR-001 (RPN: 5) |
| **Communication** | Transceiver | Dual (high-gain directional + omni UHF) | Cold Standby — omni UHF activates on primary pointing loss (low bandwidth but maintains link) | < 30 s (link timeout monitoring) | < 60 s (omni UHF link establishment) | FMEA-RPN-COM-001 (N/A — SPF list) |
| **Thermal Management** | Heater Controller | Dual (primary controller + hardware fallback circuit) | Warm Standby — FDIR directly triggers hardware fallback circuit when primary controller hangs | < 5 s (thermal heartbeat timeout) | < 2 s (fallback circuit activation) | FMEA-RPN-THM-001 (RPN: 20) |
| **Motion Control** | Motor Drivers | Functional (4+ wheel differential drive; tolerates single wheel loss) | Degraded Mode — faulty wheel isolated; asymmetric drive with remaining wheels | < 500 ms (current sensor anomaly detection) | < 2 s (driver isolation command) | FMEA-RPN-MOT-001 (RPN: 18) |

---

## 1. Single-Point Failure List

Simplex design or high-RPN components; failure in current architecture immediately causes mission interruption:

| # | Component | Why SPF | FMEA RPN | Current Risk |
|---|---------|-----------|----------|-------------|
| SPF-001 | Solar Panel Mechanical Deployment | No charging if servo stalls; no software backup (mechanical system) | RPN: 16 | Mission loss (energy generation drops to zero) |
| SPF-002 | Battery Main Pack (in current single-module design) | Total power loss; vehicle completely disabled | RPN: 30 | **Vehicle loss** |
| SPF-003 | FDIR State Machine Logic | Wrong state transition or FDIR freeze → safety decisions cannot be made | RPN: 12–30 | Vehicle loss risk |
| SPF-004 | IMU (Primary navigation; if visual odometry not yet integrated) | Navigation completely blind; vehicle cannot move | RPN: 24 | Mission loss / vehicle stranded |
| SPF-005 | Load Management Circuit (Load Switch) | High-power cut command cannot be transmitted in SURVIVAL mode; SoC drops rapidly | RPN: 10 | Vehicle loss (energy depletion) |

---

## 2. Recommended Actions

| # | Target SPF / Component | Recommendation | Priority |
|---|---------------------|-------|---------|
| ACT-001 | Battery System (SPF-002) | Add two independent battery modules (parallel or separate circuit); approve Dual design in current matrix and size by mass | P-CRIT |
| ACT-002 | Communication Transceiver | Validate UHF omni backup link on primary high-gain antenna failure through HIL tests | P-HIGH |
| ACT-003 | IMU (SPF-004) | Integrate visual odometry / camera-based odometry as functional backup in P2; connect as second source to EKF | P-HIGH |
| ACT-004 | Load Management Circuit (SPF-005) | Formally verify latching relay hardware switch + hardware path independent from software path; update FMEA RPN | P-HIGH |
| ACT-005 | Solar Panel Deployment (SPF-001) | Spring-assisted fail-open mechanism present; additional action: add deployment success to post-launch check protocol and verify with sensor | P-MED |
| ACT-006 | OBC Dual Computer | Design memory synchronisation protocol for warm standby OBC; validate failover time < 10 s acceptance criterion in SIL | P-MED |

---

## 3. Redundancies Not Implementable Without Vehicle Mass/Volume Constraints (TBD)

The following redundancy decisions cannot be implemented until §10 vehicle data (mass budget, volume envelope, power budget) arrives. Added to `config/tbd_register.md`.

| TBD ID | Redundancy | Why TBD |
|--------|------------|-----------|
| TBD-RED-001 | Adding second IMU module | IMU mass + volume constrained by vehicle budget; dual IMU or extra camera selection to be determined after §10 |
| TBD-RED-002 | Triple OBC (Triple Voting) | Each additional OBC ~TBD kg; triple feasibility cannot be evaluated without vehicle mass budget |
| TBD-RED-003 | Second battery module sizing (Wh) | Dual battery volume planning not possible until battery capacity (TBD-BAT-001) and chemistry (TBD-BAT-002) are confirmed |
| TBD-RED-004 | UHF omni antenna size and frequency band | Antenna selection unclear until antenna mounting volume in vehicle structure (§10 structure subsystem) and approved frequency plan (TBD-COM-001) are known |
| TBD-RED-005 | Motor driver redundancy level (Triple instead of Dual) | Adding extra driver cannot be evaluated until motor count and vehicle drive architecture (§10 mobility subsystem) are approved |
| TBD-RED-006 | Thermal fallback heater power capacity (W) | Fallback heater sizing not possible until thermal mass (TBD-THM-001) and insulation configuration are known |
| TBD-RED-007 | Backup solar panel or alternative energy source | Additional panel feasibility cannot be evaluated until vehicle mass and panel output (TBD-SOL-001) are confirmed |
| TBD-RED-008 | PDU redundancy detail (power line routing) | Vehicle power distribution topology (cable harness) determined with §10 vehicle engineering |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — Agent C, C1 task |
