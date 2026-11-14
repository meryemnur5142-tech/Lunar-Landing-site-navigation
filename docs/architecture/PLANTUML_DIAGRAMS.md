# status: draft
# owner: Agent C
# depends_on: [docs/architecture/ICD_TEMPLATES.md, docs/architecture/SAFETY_STATE_MACHINE.md, docs/adr/FMEA_KRITIK_MODULLER.md, autonomy/autonomy_matrix.md]
# open_items: [ICD references consistent with ICD_TEMPLATES.md v1.0; TBD parameters marked as notes in diagrams]

# LUNA-AI PlantUML Diagrams — v1.0

**Document ID:** LUNA-AI-ARCH-004  
**Version:** 0.1-draft  
**Date:** 2026-11-14  
**Related Documents:** LUNA-AI-ARCH-001 (Safety State Machine), LUNA-AI-ARCH-002 (ICD Templates), LUNA-AI-FMEA-001

---

## Diagram 1 — Component Diagram

All modules, interfaces and segment groups. Ground segment / flight segment / simulation packages separated. ICD reference on each interface.

```plantuml
@startuml LUNA-AI Component Diagram

' =====================================================
' LUNA-AI Component Diagram v1.0
' Document: LUNA-AI-ARCH-004
' Related: ICD-001..ICD-006 (LUNA-AI-ARCH-002)
' =====================================================

skinparam componentStyle rectangle
skinparam packageStyle frame
skinparam backgroundColor #FAFAFA
skinparam component {
  BackgroundColor #E8F4FD
  BorderColor #2980B9
}

' =====================================================
' GROUND SEGMENT
' =====================================================
package "Ground Segment" #EAF7EA {

  package "Scientific Analysis & Mission Design" #D5F0D5 {
    [Mission Intelligence\n(Target Scoring &\nConstraint Check)] as MI
    [Ground Control UI\n(apps/ground-control)] as GC
    [Data Platform\n(Telemetry Processing &\nArchive)] as DP
  }

  package "Mission Planning Infrastructure" #D5F0D5 {
    [Mission Planner\n(Route & Resource Planning)] as GMP
    [Orbital Geometry\n(Sun/Earth Window)] as OG
  }
}

' =====================================================
' FLIGHT SEGMENT (Vehicle)
' =====================================================
package "Flight Segment (Vehicle)" #FFF3E0 {

  package "Autonomy & Execution" #FFE0B2 {
    [Mission Executive] as ME
    [Global Planner\n(Route Planning)] as GP
    [Local Planner\n(Obstacle Avoidance)] as LP
    [Replanner\n(Replanning)] as RP
  }

  package "Perception & Navigation" #FFE0B2 {
    [Localization\n(EKF + IMU + Landmark)] as LOC
    [Terrain Analyzer\n(LiDAR + Camera)] as TA
  }

  package "Resource Management" #FFE0B2 {
    [Power Management\n(SoC, Budget)] as PM
    [Thermal Management\n(Heater Control)] as TM
  }

  package "Safety" #FFE0B2 {
    [FDIR\n(Fault Detection & Recovery)] as FDIR
    [Safety State Machine\n(NOMINAL/CAUTION/\nRETURN_REQUIRED/SURVIVAL)] as SSM
  }

  package "Hardware Interfaces" #FFE0B2 {
    [Motion Control\n(Motor Drivers)] as MC
    [Communication\n(RF Transceiver)] as COM
    [OBC\n(Main Computer)] as OBC
  }
}

' =====================================================
' SIMULATION & VALIDATION SEGMENT
' =====================================================
package "Simulation & Validation Segment" #F3E5F5 {
  [Digital Twin\n(Vehicle Simulation)] as DT
  [Environment Model\n(Lunar Surface Environment)] as EM
  [Scenario Runner\n(YAML Scenario Engine)] as SR
  [Fault Injector\n(Fault Injection)] as FI
  [SIL/HIL Bridge] as HIL
}

' =====================================================
' INTERFACES (with ICD references)
' =====================================================

' ICD-001: Power Mgmt → Mission Planner (flight) / Ground Planner (downlink reflection)
PM -right-> ME : ICD-001\nenergy_state\n(1 Hz / 10 Hz CAUTION)
PM -right-> GMP : ICD-001\nenergy_state\n(telemetry reflection)

' ICD-002: Thermal Mgmt → Mission Executive
TM -right-> ME : ICD-002\nthermal_state\n(1 Hz / 10 Hz CAUTION)

' ICD-003: Navigation → Local Planner
LOC -right-> LP : ICD-003\nvehicle_pose\n(>=10 Hz moving)
LOC -right-> GP : ICD-003\nvehicle_pose\n(1 Hz nominal)

' ICD-004: FDIR → Mission Executive
FDIR -right-> ME : ICD-004\nsafety_status\n(event-driven + 1 Hz)
SSM --> FDIR : state transition\ndecision

' ICD-005: Ground → Flight (Uplink — CCSDS TC)
GMP -down-> COM : ICD-005\nTC Uplink\n(CCSDS)
GC -down-> COM : ICD-005\nTC_IMMEDIATE\n(P1 Command)

' ICD-006: Flight → Ground (Downlink — CCSDS TM)
COM -up-> DP : ICD-006\nTM Downlink\n(CCSDS)
COM -up-> GC : ICD-006\nTelemetry\n(1 Hz / 10 Hz)

' Vehicle internal connections
ME --> GP : apply mission\nstep
GP --> LP : waypoint\nlist
LP --> MC : motion\ncommand
TA --> LOC : point cloud\n+ image
MC --> LOC : encoder\nfeedback
FDIR --> PM : power shed\ncommand (SURVIVAL)
FDIR --> TM : heater priority\ncommand (CAUTION+)
FDIR --> MC : halt command\n(RETURN_REQUIRED)
FDIR --> COM : emergency beacon\n(SURVIVAL)
RP --> GP : new route\nplan

' Simulation connections
DT --> LOC : simulated\ntelemetry
EM --> DT : environment\nconditions
SR --> FI : scenario\nevents
FI --> DT : fault injection\n(sensor/motor/power)
HIL --> OBC : HIL\ninterface

' Ground internal connections
MI --> GMP : target ranking\n+ constraint list
OG --> GMP : window\nconstraints
DP --> MI : processed\ntelemetry

@enduml
```

---

## Diagram 2 — PSR Operation Sequence Diagram

From PSR (Permanently Shadowed Region) entry decision to end of scientific mission and safe haven return. Including critical message exchanges, fault branches, abort triggers.

```plantuml
@startuml LUNA-AI PSR Operation Sequence

' =====================================================
' PSR Operation Sequence Diagram v1.0
' Scenario: PSR entry decision → scientific mission → return
' Related: SC-003 (operational_scenarios.md), ICD-001..004
' =====================================================

skinparam sequenceArrowThickness 2
skinparam sequenceGroupBackgroundColor #FFF8E1
skinparam sequenceLifeLineBorderColor #666666

actor "Ground\nControl" as GC
participant "Mission\nPlanner" as MP
participant "Power\nMgmt" as PWR
participant "Thermal\nMgmt" as THM
participant "Navigation" as NAV
participant "FDIR" as FDIR
participant "Mission\nExecutive" as ME

== Phase: PSR Entry Decision ==

GC -> MP : TC_PLAN_UPLOAD\nPSR waypoint + energy budget\n[ICD-005]
MP -> PWR : energy reserve query\nfor PSR entry\n[ICD-001]
PWR --> MP : energy_state\nsoc_percent=TBD%\nestimated_return_soc=TBD%\n[ICD-001]
MP -> THM : thermal state\nquery\n[ICD-002]
THM --> MP : thermal_state\ncritical_component_ok=true\n[ICD-002]
MP -> NAV : position uncertainty\nquery\n[ICD-003]
NAV --> MP : vehicle_pose\nuncertainty_m < 0.5m\n[ICD-003]

alt PSR Entry Conditions Met\n(SoC sufficient, thermal ok, nav reliable)
  MP -> ME : PSR_ENTRY_AUTHORIZED\nwaypoint_list, return_reserve_wh
  ME -> FDIR : PSR entry notification\n(monitoring increased)
  FDIR --> ME : safety_state=NOMINAL\nabort_signal=false\n[ICD-004]
  ME -> GC : TC ACK — PSR entry authorised\n[ICD-006]
else PSR Entry Conditions Not Met
  MP -> GC : PSR entry rejected\n(reason: SoC < threshold or thermal warning)\n[ICD-006]
  note right of GC: Wait for new window\nor plan revision
end

== Phase: In-PSR Scientific Operation ==

ME -> NAV : begin movement\nto science waypoint
NAV -> FDIR : heartbeat\n(every 100 ms)\n[SAFETY_STATE_MACHINE]
PWR -> FDIR : heartbeat + energy_state\n(every 500 ms)\n[ICD-001]
THM -> FDIR : heartbeat + thermal_state\n(every 1 s)\n[ICD-002]

loop Science Data Collection Loop
  ME -> NAV : next waypoint
  NAV --> ME : waypoint reached
  ME -> ME : activate\nscience sensor
  ME -> PWR : power state check\n(return_reserve_wh >= threshold?)
  PWR --> ME : energy_state updated\n[ICD-001]
end

== Abort Scenarios (Fault Branches) ==

group ABORT-1: HC-006 Return Reserve Violation [ABT-001]
  PWR -> FDIR : ANOMALY\nreturn_reserve_wh < HC-006_threshold\n[ICD-001 status=WARN]
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
  ME -> NAV : ALL OPERATIONS FROZEN\nrequest return route
  note right of FDIR: abort_trigger=ABT-001\nHC-006 violation
  ME -> GC : HC-006 violation notification\nposition + expected return time\n[ICD-006]
end

group ABORT-2: Thermal Critical Violation [SC-006]
  THM -> FDIR : ANOMALY\nthermal_mode=CRITICAL\n[ICD-002 status=ERROR]
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
  FDIR -> THM : all heaters MAX priority
  ME -> NAV : initiate emergency return route
  ME -> GC : thermal critical notification\n[ICD-006]
end

group ABORT-3: Link Loss (inside PSR) [SC-002, ABT-004]
  note over ME, FDIR: Link > TBD(source: §10) minutes cut
  FDIR -> ME : safety_status\nsafety_state=RETURN_REQUIRED\n(pre-planned ACL triggered)\n[ICD-004]
  ME -> NAV : return to pre-planned safe haven\n(no ground approval awaited — ACL)
end

== Phase: Safe Haven Return ==

NAV -> ME : safe haven route\nready
ME -> PWR : energy conservation\nmode during return
PWR -> THM : relay minimum heater\nrequest
ME -> GC : return started\nETA: TBD minutes\n[ICD-006]

loop Return Monitoring
  PWR -> FDIR : return_reserve_wh updated
  NAV -> FDIR : position + uncertainty
  FDIR -> ME : safety_status (1 Hz)\n[ICD-004]
end

ME -> GC : safe haven reached\n[ICD-006]
GC -> MP : RETURN_REQUIRED → NOMINAL approval\n[ICD-005 TC_CONDITIONAL]
MP -> FDIR : ground approval received
FDIR -> ME : safety_state=NOMINAL\n[ICD-004]

@enduml
```

---

## Diagram 3 — Fault Management Sequence Diagram

Scenario: Localisation uncertainty exceeded → FDIR decision → replanning → return or recovery. Related: SC-004 (operational_scenarios.md).

```plantuml
@startuml LUNA-AI Fault Management Sequence

' =====================================================
' Fault Management Sequence Diagram v1.0
' Scenario: Localisation uncertainty exceeded → FDIR → replanning → return
' Related: SC-004, QAR-NAV-002, FMEA-RPN-NAV-001 (RPN:24)
' =====================================================

skinparam sequenceArrowThickness 2
skinparam sequenceGroupBorderColor #CC0000
skinparam sequenceGroupBackgroundColor #FFF0F0

participant "Local\nPlanner" as LP
participant "Navigation\n(EKF + IMU)" as NAV
participant "FDIR" as FDIR
participant "Mission\nExecutive" as ME
participant "Global\nPlanner" as GP
participant "Replanner" as RP
participant "Ground\nControl" as GC

== Detection: Localisation Uncertainty Detected ==

NAV -> NAV : EKF covariance monitoring\ncontinuous (10 Hz)
NAV -> LP : vehicle_pose\nuncertainty_m = 0.6m\n[ICD-003 status=DEGRADED]
LP -> LP : uncertainty_m > 0.5m ->\nhalve obstacle\napproach speed

NAV -> FDIR : ANOMALY EVENT\nuncertainty_m > QAR-NAV-002_threshold\n(> 1.0m)
FDIR -> ME : safety_status\nsafety_state=CAUTION\nabort_signal=false\n[ICD-004]
ME -> LP : HALT command\n(movement stopped)
ME -> GC : CAUTION notification\nlocalisation uncertainty exceeded\n[ICD-006]

== Isolation: Faulty Sensor Detection ==

FDIR -> NAV : begin sensor\nisolation test
NAV -> NAV : IMU inconsistency test
NAV -> NAV : odometry / IMU\ncomparison
NAV -> NAV : last landmark\nmatch quality

alt IMU Fault Detected
  NAV -> FDIR : IMU_FAULT\n(faulty sensor isolated)
  FDIR -> NAV : IMU disabled\nswitch to odometry-only mode
  note right of NAV : Degraded mode:\nodometry + visual landmark
else Sensor Combination Inconsistent
  NAV -> FDIR : FUSION_ANOMALY\n(source cannot be determined)
  note right of FDIR : Most likely: IMU drift\n(FMEA-RPN-NAV-001)
end

== Recovery: Landmark Relocalisation ==

FDIR -> NAV : begin landmark search\nattempt (N tries)
loop Landmark Search Loop (max N attempts — TBD)
  NAV -> NAV : rotate in place\nmatch against orbital map
  alt Landmark Match Successful
    NAV -> FDIR : RECOVERY_SUCCESS\nuncertainty_m < 0.5m
    FDIR -> ME : safety_status\nsafety_state=NOMINAL\n[ICD-004]
    ME -> LP : resume movement\n(normal speed)
    ME -> GC : recovery successful\n[ICD-006]
  else Match Failed — Continue
    NAV -> FDIR : LANDMARK_NO_MATCH\n(attempt i/N)
  end
end

== Recovery Failed → Replanning ==

FDIR -> ME : RECOVERY_FAILED\nsafety_state=RETURN_REQUIRED\nabort_signal=true\n[ICD-004]
ME -> RP : replanning request\ncurrent position (degraded sigma_pos)\ntarget: safe haven
RP -> GP : generate IMU-only route\nin degraded nav mode

alt Inside PSR
  GP -> ME : PSR exit route\n(energy critical check)
  ME -> FDIR : route approval
  FDIR -> ME : approved
  note right of FDIR : PSR exit with degraded nav:\nerror accumulation bounded by acceptance distance
else SURFACE_EXPLORATION
  GP -> ME : IMU-only route to\npre-planned safe haven coordinates
end

ME -> LP : apply new route\n(degraded mode — low speed)
ME -> GC : RETURN_REQUIRED\nsensor fault + degraded nav\nexpected return time\n[ICD-006]

== Return and Recovery ==

LP -> ME : approaching safe haven
ME -> FDIR : safe haven arrival
FDIR -> GC : safe haven reached\nawaiting ground approval\n[ICD-006]
GC -> ME : ground approval\n(TC_CONDITIONAL)\n[ICD-005]
FDIR -> ME : safety_state=NOMINAL\n(ground-approved transition)\n[ICD-004]

note right of FDIR
  Sensor calibration:\n
  - IMU recalibration procedure
  - Parameter update from ground segment
  - No operations until new mission plan received
end note

@enduml
```

---

## Diagram 4 — Deployment Diagram

Hardware on vehicle and software components running on them. Ground segment servers and connection type.

```plantuml
@startuml LUNA-AI Deployment Diagram

' =====================================================
' Deployment Diagram v1.0
' Vehicle hardware + ground segment servers + connections
' =====================================================

skinparam nodeStyle rectangle
skinparam componentStyle rectangle
skinparam backgroundColor #FAFAFA

' =====================================================
' VEHICLE (Flight Hardware)
' =====================================================
node "Rover (Vehicle)" as ROVER #FFE0B2 {

  node "Main Computer (OBC)\n[FreeRTOS, COTS Rad-Hard CPU\nTBD-SNS-001]" as OBC #FFCC80 {
    component [FDIR Task\n(Priority: Highest)] as FDIR_SW
    component [Mission Executive] as ME_SW
    component [Global Planner] as GP_SW
    component [Local Planner] as LP_SW
    component [Replanner] as RP_SW
    component [Power Mgmt Task] as PM_SW
    component [Thermal Mgmt Task] as TM_SW
    component [Communication Task] as COM_SW
  }

  node "Navigation Processor\n[TBD — separate SoC or separate\ncore on OBC]" as NAV_CPU #FFCC80 {
    component [EKF Localization] as EKF_SW
    component [Terrain Analyzer] as TA_SW
    component [Sensor Fusion] as SF_SW
  }

  node "IMU Module\n[TBD-SNS-001/002]" as IMU_HW #FFD54F {
    component [Accelerometer + Gyroscope] as IMU_SENS
  }

  node "LiDAR\n[TBD-SNS-001]" as LIDAR_HW #FFD54F {
    component [Point Cloud\nGenerator] as LIDAR_SW
  }

  node "Camera System\n[TBD-SNS-001]" as CAM_HW #FFD54F {
    component [Stereo Image\nProcessing] as CAM_SW
  }

  node "RF Module\n[TBD-COM-001]" as RF_HW #FFD54F {
    component [High Gain Antenna\n(HGA)] as HGA
    component [UHF Omni Antenna\n(Backup)] as UHF
  }

  node "Power System\n[TBD-BAT-001/002, TBD-SOL-001]" as PWR_HW #FFD54F {
    component [Solar Panel\n+ Charge Regulator] as SOLAR
    component [Battery Module\n(Dual — TBD-RED-003)] as BAT
    component [PDU\n(Dual Channel)] as PDU
  }

  node "Thermal System\n[TBD-THM-001]" as THM_HW #FFD54F {
    component [Heaters\n(Primary + Fallback)] as HEATER
    component [Temperature Sensors\n(>=2 independent/point)] as TEMP_SENS
  }

  node "Motion System" as MOT_HW #FFD54F {
    component [Motor Drivers\n(4+ wheel)] as MOTOR_DRV
    component [Wheel Encoders] as ENC
  }

  node "Hardware Watchdog\n[Independent HW Timer]" as HW_WD #EF9A9A {
    component [FDIR HW Watchdog\n(25 ms kick)] as WD_HW
  }
}

' =====================================================
' GROUND SEGMENT
' =====================================================
node "Ground Control Centre\n(Ground Segment Server)" as GROUND #E8F5E9 {

  node "Mission Control Server" as MCS #C8E6C9 {
    component [Ground Control UI\n(apps/ground-control)] as GC_UI
    component [Mission Planner\n(Route & Resource)] as GMP_SW
    component [Mission Intelligence\n(Target & Constraint)] as MI_SW
  }

  node "Data Processing Server" as DPS #C8E6C9 {
    component [Data Platform\n(Ingestion + Catalog)] as DP_SW
    component [Telemetry Archive] as TM_ARCH
    component [Scientific Data Store] as SCI_DATA
  }

  node "Simulation Server" as SIM_SRV #C8E6C9 {
    component [Digital Twin] as DT_SW
    component [Environment Model] as EM_SW
    component [Scenario Runner] as SR_SW
    component [Fault Injector] as FI_SW
  }

  node "Deep Space Network\n(DSN Antenna)" as DSN #A5D6A7 {
    component [RF Uplink/Downlink\n(CCSDS)] as DSN_RF
  }
}

' =====================================================
' CONNECTIONS
' =====================================================

' Vehicle hardware connections
OBC --> RF_HW : UART/SPI\ncommunication command
OBC --> PWR_HW : I2C/CAN\npower control
OBC --> THM_HW : GPIO / I2C\nheater control
OBC --> MOT_HW : CAN Bus\nmotor command
OBC --> HW_WD : FDIR HW kick\n(25 ms)
NAV_CPU --> IMU_HW : SPI\nsampling (200+ Hz)
NAV_CPU --> LIDAR_HW : Ethernet/PCIe\npoint cloud
NAV_CPU --> CAM_HW : USB3/Ethernet\nimage stream
OBC --> NAV_CPU : IPC / Shared Memory\nvehicle_pose [ICD-003]

' Ground-vehicle connection
DSN_RF --> RF_HW : CCSDS TC/TM\n(ICD-005 Uplink / ICD-006 Downlink)\n[TBD-COM-001: frequency, band]

' Ground internal connections
GC_UI --> MCS : HTTP/gRPC
GMP_SW --> MI_SW : target list
DP_SW --> TM_ARCH : telemetry store
DSN_RF --> DP_SW : raw TM\nreception
SIM_SRV --> DPS : simulation\ntelemetry
SIM_SRV --> MCS : SIL test\ninterface

@enduml
```

---

## Diagram 5 — Safety State Machine

Nominal / Caution / Return_Required / Survival. Transition conditions and guard expressions. Consistent with LUNA-AI-ARCH-001.

```plantuml
@startuml LUNA-AI Safety State Machine

' =====================================================
' Safety State Machine v1.0
' Document: LUNA-AI-ARCH-004 (Diagram 5)
' Source: LUNA-AI-ARCH-001 (SAFETY_STATE_MACHINE.md)
' Related: ADR-005, QAR FDIR-001/002/004/005
' =====================================================

skinparam state {
  BackgroundColor #E8F4FD
  BorderColor #2980B9
  ArrowColor #333333
}
skinparam state<<NOMINAL>> {
  BackgroundColor #E8F5E9
  BorderColor #27AE60
}
skinparam state<<CAUTION>> {
  BackgroundColor #FFF9C4
  BorderColor #F39C12
}
skinparam state<<RETURN_REQUIRED>> {
  BackgroundColor #FFE0B2
  BorderColor #E67E22
}
skinparam state<<SURVIVAL>> {
  BackgroundColor #FFCDD2
  BorderColor #C0392B
}

' Initial
[*] --> NOMINAL : boot_complete\nAND subsystems_ok\nAND fdir_heartbeat_ok

' =====================================================
' NOMINAL
' =====================================================
state NOMINAL<<NOMINAL>> {
  NOMINAL : entry / all subsystems placed under monitoring
  NOMINAL : do / full exploration operation; PSR entry permitted
  NOMINAL : monitored: SoC > threshold+margin, nav sigma < 0.5m RMS
  NOMINAL : monitored: all component temperatures nominal
  NOMINAL : monitored: link_timeout < warning threshold
  NOMINAL : monitored: all FDIR heartbeats on time
}

' =====================================================
' CAUTION
' =====================================================
state CAUTION<<CAUTION>> {
  CAUTION : entry / send CAUTION flag to ground segment
  CAUTION : do / complete current operation to safe endpoint
  CAUTION : do / keep return route ready; new PSR entry prohibited
  CAUTION : monitored: SoC < 25% or return margin < 20%
  CAUTION : monitored: nav uncertainty 0.5-1.0 m RMS
  CAUTION : monitored: component temperature at 80% of nominal limit
}

' =====================================================
' RETURN_REQUIRED
' =====================================================
state RETURN_REQUIRED<<RETURN_REQUIRED>> {
  RETURN_REQUIRED : entry / abort_signal=true -> Mission Exec frozen
  RETURN_REQUIRED : entry / scientific operation fully stopped
  RETURN_REQUIRED : do / safe haven return route active
  RETURN_REQUIRED : do / navigation + FDIR fully operational
  RETURN_REQUIRED : do / periodic communication attempts continue
  RETURN_REQUIRED : exit / safe_haven_reached AND ground_approval
}

' =====================================================
' SURVIVAL
' =====================================================
state SURVIVAL<<SURVIVAL>> {
  SURVIVAL : entry / all science sensors shed
  SURVIVAL : entry / high-power communication shed (beacon remains)
  SURVIVAL : entry / planner and replanning stopped
  SURVIVAL : do / navigation (IMU + dead-reckoning minimum)
  SURVIVAL : do / FDIR core function active
  SURVIVAL : do / minimum heater power (battery preservation)
  SURVIVAL : do / periodic beacon broadcast
}

' =====================================================
' TRANSITIONS — exit from NOMINAL
' =====================================================
NOMINAL --> CAUTION : [SoC < 25%\nOR return_margin < 20%\nOR nav_uncertainty 0.5-1.0m RMS\nOR component_temp nominal_80%\nOR link_timeout > warning_threshold (TBD)\nOR planner_heartbeat_delayed]

NOMINAL --> RETURN_REQUIRED : [SoC < 15%\nOR link_timeout > critical_threshold (TBD)\nOR nav_localisation_loss_timeout > TBD_s\nOR ground_command=TC_IMMEDIATE_RETURN\nOR thermal_critical AND local_intervention_failed]

NOMINAL --> SURVIVAL : [SoC < 10%\nOR critical_hardware_fault\nOR rapid_heating > TBD_degrees/min\nOR FDIR_self_watchdog_loss\nOR multiple_simultaneous_P1_faults]

' =====================================================
' TRANSITIONS — exit from CAUTION
' =====================================================
CAUTION --> NOMINAL : [all_triggers_clear\nAND all_parameters_within_nominal_range]

CAUTION --> RETURN_REQUIRED : [SoC < 15%\nOR link_timeout > critical_threshold\nOR nav_recovery_failed\nOR thermal_critical\nOR ground_command=TC_IMMEDIATE_RETURN]

CAUTION --> SURVIVAL : [SoC < 10%\nOR critical_hardware_fault\nOR FDIR_self_watchdog_loss\nOR rapid_heating > TBD]

' =====================================================
' TRANSITIONS — exit from RETURN_REQUIRED
' =====================================================
RETURN_REQUIRED --> SURVIVAL : [survival_trigger_active_during_return]

RETURN_REQUIRED --> NOMINAL : [safe_haven_reached\nAND energy_sufficient\nAND ground_segment_approved]\n{guard: ground approval only}

' =====================================================
' TRANSITIONS — exit from SURVIVAL
' =====================================================
SURVIVAL --> RETURN_REQUIRED : [core_system_recovered\nAND energy > 10%\nAND ground_segment_approved]\n{guard: ground approval only}

note right of SURVIVAL
  There is NO direct transition
  from SURVIVAL to NOMINAL.
  Mandatory: SURVIVAL -> RETURN_REQUIRED -> NOMINAL
  Both require ground approval.
  FDIR continues operating in all states.
  Hardware watchdog: 25 ms kick period.
end note

note right of RETURN_REQUIRED
  Mission Executive freezes all operations
  when abort_signal=true is received.
  "Halt" command sent to Motion Control.
  This constraint is enforced in software architecture.
  (ICD-004 — blocking message queue)
end note

note bottom of CAUTION
  CAUTION -> NOMINAL transition:
  ALL triggers must be clear simultaneously.
  Hysteresis: noise filter applied
  (10 consecutive measurements within nominal range).
end note

@enduml
```

---

## Diagram Reference Table

| # | Diagram | PlantUML Type | Source Documents | Purpose |
|---|----------|--------------|-----------------|------|
| 1 | Component Diagram | Component | ICD-001..006, ADR-005 | All modules and interfaces; segment groups |
| 2 | PSR Operation Sequence | Sequence | SC-003, ICD-001..005, HC-006 | PSR entry decision → mission → return; abort branches |
| 3 | Fault Management Sequence | Sequence | SC-004, FMEA-RPN-NAV-001, QAR-NAV-002 | Localisation loss → FDIR → replanning → return |
| 4 | Deployment Diagram | Deployment | ADR-003, ICD-005/006, TBD-SNS/BAT/COM | Hardware nodes, software deployment, connection types |
| 5 | Safety State Machine | State | LUNA-AI-ARCH-001, ADR-005, QAR FDIR-001..005 | 4 safety states, transition guards, FDIR independence |

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — Agent C, C2 task; 5 diagrams |
