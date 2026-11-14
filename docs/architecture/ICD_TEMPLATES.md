# LUNA-AI Interface Control Document (ICD) Templates

**Document ID:** LUNA-AI-ARCH-002  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related ADR:** ADR-006

---

## General ICD Policy

- All modules communicate with each other only via the message formats defined in this document.
- When a producer module wishes to change an interface, it increments the version number and notifies the consumer module.
- Backward compatibility: a minor version increment does not break existing fields; it only adds new fields.
- Absence of a field (optional field) and a field value of zero/empty are semantically different.
- Error semantics: every message carries a `status` field; the consumer applies safe default behaviour when `status != OK`.

---

## ICD-001: Power Management → Mission Planner

**Interface ID:** ICD-001  
**Producer:** Power Management  
**Consumer:** Mission Planner  
**Update Frequency:** 1 Hz (nominal); 10 Hz (CAUTION or above)  
**Transport:** FreeRTOS message queue (flight); CCSDS telemetry (ground segment reflection)  
**Version:** 1.0

### Message Format: `energy_state`

| Field | Type | Unit | Range | Description |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0101 | Message type constant |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Elapsed time since system start |
| `soc_percent` | float32 | % | 0.0 – 100.0 | Current state of charge |
| `soc_uncertainty_pct` | float32 | % | 0.0 – 10.0 | SoC measurement uncertainty (1-sigma) |
| `voltage_v` | float32 | V | **TBD** – **TBD** | Main battery voltage |
| `current_ma` | float32 | mA | **TBD** – **TBD** | Instantaneous draw current (positive=consumption) |
| `panel_power_w` | float32 | W | 0.0 – **TBD** | Solar panel instantaneous power |
| `estimated_return_soc_pct` | float32 | % | 0.0 – 100.0 | Estimated SoC at end of return to safe haven |
| `return_soc_uncertainty_pct` | float32 | % | 0.0 – 20.0 | Estimate uncertainty (1-sigma) |
| `power_mode` | uint8 | — | 0=NORMAL, 1=SURVIVAL | Current power mode |
| `status` | uint8 | — | 0=OK, 1=WARN, 2=ERROR | Message status |

**Error Semantics:**
- `status == WARN`: Mission Planner evaluates CAUTION trigger
- `status == ERROR`: Mission Planner retains last valid value; error event sent to FDIR
- Message timeout (> 2 s without update): FDIR treats as Power heartbeat timeout

**Version Compatibility Policy:**
- Adding new field: minor version increment (1.0 → 1.1); consumer ignores new field
- Field type/range change: major version increment (1.0 → 2.0); consumer compatibility must be updated

---

## ICD-002: Thermal Management → Mission Planner

**Interface ID:** ICD-002  
**Producer:** Thermal Management  
**Consumer:** Mission Planner  
**Update Frequency:** 1 Hz (nominal); 10 Hz (CAUTION or above)  
**Transport:** FreeRTOS message queue  
**Version:** 1.0

### Message Format: `thermal_state`

| Field | Type | Unit | Range | Description |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0201 | Message type constant |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Elapsed time since system start |
| `num_sensors` | uint8 | — | 1–16 | Active sensor count |
| `sensor_temps_c[16]` | float32[16] | °C | **TBD** – **TBD** | Temperature of each sensor |
| `sensor_ids[16]` | uint8[16] | — | 0–255 | Sensor identification numbers |
| `critical_component_ok` | bool | — | true/false | All critical components within nominal range |
| `heater_active_mask` | uint16 | — | bit mask | Active heaters (one heater per bit) |
| `thermal_budget_w` | float32 | W | 0.0 – **TBD** | Current thermal load |
| `estimated_time_to_critical_s` | float32 | s | 0.0 – **TBD** | Time to critical threshold at current rate (-1 = cannot calculate) |
| `thermal_mode` | uint8 | — | 0=NOMINAL, 1=WARN, 2=CRITICAL | Thermal state summary |
| `status` | uint8 | — | 0=OK, 1=WARN, 2=ERROR | Message status |

**Error Semantics:**
- `thermal_mode == WARN`: Mission Planner restricts high-power activities
- `thermal_mode == CRITICAL`: Mission Planner notifies FDIR; FDIR makes CAUTION/RETURN decision
- Message timeout (> 5 s): FDIR treats as thermal heartbeat timeout

---

## ICD-003: Navigation → Local Planner

**Interface ID:** ICD-003  
**Producer:** Navigation  
**Consumer:** Local Planner  
**Update Frequency:** ≥ 10 Hz (while moving), ≥ 1 Hz (stop-wait) [QAR NAV-003]  
**Transport:** FreeRTOS message queue (high priority)  
**Version:** 1.0

### Message Format: `vehicle_pose`

| Field | Type | Unit | Range | Description |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0301 | Message type constant |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Pose estimate timestamp |
| `pos_x_m` | float64 | m | **TBD** coordinate system | X position in local map |
| `pos_y_m` | float64 | m | **TBD** coordinate system | Y position in local map |
| `pos_z_m` | float64 | m | **TBD** coordinate system | Z position in local map (elevation) |
| `yaw_rad` | float32 | rad | -π – +π | Yaw angle (North-referenced) |
| `pitch_rad` | float32 | rad | -π/2 – +π/2 | Pitch angle |
| `roll_rad` | float32 | rad | -π – +π | Roll angle |
| `uncertainty_m` | float32 | m | 0.0 – 100.0 | Position uncertainty (1-sigma, RMS) |
| `uncertainty_rad` | float32 | rad | 0.0 – π | Orientation uncertainty (1-sigma) |
| `velocity_x_ms` | float32 | m/s | **TBD** – **TBD** | Velocity in X direction |
| `velocity_y_ms` | float32 | m/s | **TBD** – **TBD** | Velocity in Y direction |
| `localization_source` | uint8 | — | 0=EKF_FULL, 1=DEAD_RECKONING, 2=LANDMARK_ONLY | Active localisation source |
| `localization_valid` | bool | — | true/false | EKF convergence state |
| `status` | uint8 | — | 0=OK, 1=DEGRADED, 2=LOST | Localisation status |

**Critical Threshold — `uncertainty_m`:**
- `uncertainty_m` > 0.5 m → Local Planner halves obstacle approach speed
- `uncertainty_m` > 1.0 m → Local Planner halts, sends relocalisation request to Navigation
- `status == LOST` → Localisation loss event sent to FDIR

**Error Semantics:**
- `status == DEGRADED`: Local Planner performs only high-uncertainty-tolerant manoeuvres
- `status == LOST`: Local Planner issues halt command; FDIR decides
- Message timeout (> 500 ms, speed > 0): FDIR navigation heartbeat timeout

---

## ICD-004: FDIR → Mission Executive

**Interface ID:** ICD-004  
**Producer:** FDIR  
**Consumer:** Mission Executive (Mission Planner upper layer)  
**Update Frequency:** On state change (event-driven) + 1 Hz heartbeat  
**Transport:** FreeRTOS message queue (highest-priority queue)  
**Version:** 1.0

### Message Format: `safety_status`

| Field | Type | Unit | Range | Description |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0401 | Message type constant |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Timestamp |
| `safety_state` | uint8 | — | 0=NOMINAL, 1=CAUTION, 2=RETURN_REQUIRED, 3=SURVIVAL | Current safety state |
| `previous_state` | uint8 | — | 0–3 | Previous safety state |
| `transition_reason` | uint16 | — | bit mask | Transition triggers (each bit is one trigger) |
| `abort_signal` | bool | — | true/false | If true, Mission Planner freezes all operations |
| `allowed_actions_mask` | uint32 | — | bit mask | Actions permitted in current state |
| `time_in_state_ms` | uint32 | ms | 0 – 2^32 | Time elapsed in current state |
| `fdir_confidence` | uint8 | — | 0–100 | FDIR internal confidence score (diagnostic quality) |
| `status` | uint8 | — | 0=OK, 1=DEGRADED | FDIR own status |

### Abort Propagation Mechanism

When `abort_signal == true` is received, Mission Executive:
1. Freezes all active mission steps (finishes or aborts running action in a safe state)
2. Sends "halt" command to Motion Control
3. Sends abort_acknowledged message to FDIR
4. Awaits state change

Mission Executive **cannot** ignore an abort. This constraint is enforced in software architecture (blocking message queue, no queue overflow).

---

## ICD-005: Ground → Flight (Uplink)

**Interface ID:** ICD-005  
**Producer:** Ground Segment (Ground Station)  
**Consumer:** Vehicle Communication + Mission Planner  
**Transport:** CCSDS Telecommand (TC) protocol  
**Version:** 1.0

### Command Types

| Command Type | Code | Priority | Timeout | Description |
|------------|-----|---------|---------|----------|
| `TC_IMMEDIATE_ABORT` | 0x01 | P1 | None (process immediately) | Stop all operations |
| `TC_IMMEDIATE_RETURN` | 0x02 | P1 | None | Initiate return |
| `TC_IMMEDIATE_POWER_OFF` | 0x03 | P1 | None | Shut down specified subsystem |
| `TC_CONDITIONAL` | 0x10 | P2 | 1 hour | Conditional action package |
| `TC_PLAN_UPLOAD` | 0x20 | P3 | 24 hours | Daily mission plan (via CFDP) |
| `TC_PARAM_UPDATE` | 0x30 | P3 | 1 hour | Parameter update |
| `TC_QUERY` | 0x40 | P4 | 30 min | Telemetry/status request |

### Uplink Packet Structure (CCSDS Space Packet)

| Field | Type | Unit | Description |
|------|-----|-------|----------|
| `primary_header` | 6 bytes | — | CCSDS primary header (APID, sequence, length) |
| `secondary_header` | 10 bytes | — | Timestamp (CCSDS CUC format), command type, priority |
| `cmd_sequence_no` | uint32 | — | Command sequence number (duplicate detection) |
| `checksum_crc32` | uint32 | — | CRC-32 integrity code |
| `payload` | variable | — | Command body (structure varies by command type) |

**No-Link Rule:** When vehicle has no link, TC_PLAN_UPLOAD is held pending; processed in next window. TC_IMMEDIATE commands move to front of processing queue.

**Version Compatibility:** Vehicle responds to unrecognised command types with `NACK`; does not ignore them.

---

## ICD-006: Flight → Ground (Downlink)

**Interface ID:** ICD-006  
**Producer:** Vehicle (Flight Segment)  
**Consumer:** Ground Segment (Ground Station)  
**Transport:** CCSDS Space Packet (TM — Telemetry)  
**Version:** 1.0

### Telemetry Packet Structure

| Field | Type | Unit | Update Frequency | Description |
|------|-----|-------|---------------------|----------|
| `primary_header` | 6 bytes | — | Every packet | CCSDS primary header |
| `secondary_header` | 10 bytes | — | Every packet | Timestamp + packet type |
| `safety_state` | uint8 | — | On state change + 1 Hz | Current safety state |
| `soc_percent` | float32 | % | 1 Hz / 10 Hz (CAUTION) | State of charge |
| `pos_x_m` | float64 | m | 1 Hz / 10 Hz (CAUTION) | Vehicle X position |
| `pos_y_m` | float64 | m | 1 Hz / 10 Hz (CAUTION) | Vehicle Y position |
| `pos_uncertainty_m` | float32 | m | 1 Hz | Position uncertainty |
| `avg_temp_c` | float32 | °C | 1 Hz | Average critical component temperature |
| `max_temp_c` | float32 | °C | 1 Hz | Hottest measured component |
| `link_quality` | uint8 | % | 1 Hz | Received signal strength indicator |
| `active_faults_mask` | uint32 | — | On change | Active fault flags |
| `mission_step_id` | uint16 | — | 1 Hz | Current mission step |
| `science_data_pending_kb` | uint32 | KB | 1 Hz | Scientific data awaiting downlink |
| `checksum_crc32` | uint32 | — | Every packet | CRC-32 integrity code |

### Downlink Prioritisation

| Packet Type | Priority | Frequency | Description |
|-----------|---------|---------|----------|
| Emergency telemetry | P1 | Instantaneous | Safety state transition, critical fault |
| Core system telemetry | P2 | ≤ 10 s | SoC, position, temperature |
| Mission status | P3 | ≤ 60 s | Step ID, scientific data summary |
| Scientific raw data | P4 | As link permits | Images, spectroscopy |

**Buffering:** All telemetry is written to onboard buffer memory when link is absent. When buffer is full, lowest-priority packets are overwritten. P1 packets are never overwritten.

**Error Semantics:**
- CRC error: ground segment discards packet and re-requests (TC_QUERY)
- Packet loss: if sequence number gap detected, ground segment reports missing range

---

## Interface Version Matrix

| ICD ID | Current Version | Producer Module | Consumer Module | Last Updated |
|--------|-------------|----------------|-----------------|----------------|
| ICD-001 | 1.0 | Power Management | Mission Planner | 2026-11-14 |
| ICD-002 | 1.0 | Thermal Management | Mission Planner | 2026-11-14 |
| ICD-003 | 1.0 | Navigation | Local Planner | 2026-11-14 |
| ICD-004 | 1.0 | FDIR | Mission Executive | 2026-11-14 |
| ICD-005 | 1.0 | Ground Segment | Vehicle Communication | 2026-11-14 |
| ICD-006 | 1.0 | Vehicle | Ground Segment | 2026-11-14 |

---

*TBD values will be updated when hardware parameters and orbital analysis are complete. Each ICD change is notified to consumer module owner at least 48 hours in advance.*
