# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, domain/environment/uncertainty_policy.md]
# open_items: [Blocking inputs are awaiting §10 source approval; default ranges will be tested in P1]

# Open Input Classification — LUNA-AI v1.1 (v1.0 §10)

## Purpose

Separates §10 vehicle hardware inputs into two categories: those where a default range can be used to proceed in P0/P1, and blocking inputs that cannot be advanced without being finalised.

---

## Table 1 — Range-Freezable (can proceed with assumption in P0/P1)

| Input | Default Range | Rationale | Affected Modules |
|-------|--------------|-----------|-----------------|
| Vehicle mass | 100–300 kg | Small-to-medium lunar rover class | vehicle/mobility-control, power (energy/kg consumption) |
| Battery capacity | 500–1500 Wh | Typical small-to-medium rover range | power, HC-006 (return reserve threshold) |
| Solar panel power | 300–800 W | Panel area ~1–2 m² assumption | power, HC-009 (illumination duration adequacy) |
| Max climb angle | 20–30° | Typical wheeled rover limit | HC-001 (slope limit), HC-005, autonomy/global-planner |
| Nominal traverse speed | 0.05–0.15 m/s | Lunar rover standard operating speed | autonomy/global-planner (route time estimation) |
| Heater power consumption | 50–200 W | Typical rover thermal system | thermal, power budget |
| Observer height (antenna/sensor) | 0.5–2.0 m | Typical rover mast height | communication (Earth visibility), simulation/environment-model |

**Usage rule:** Range extremes are used in worst-case scenarios. If P1 simulation results reveal out-of-range behaviour, re-evaluation is required.

---

## Table 2 — Blocking (cannot proceed without finalisation)

| Input | Why Blocking | Affected Modules | Expected Source |
|-------|-------------|-----------------|-----------------|
| Sensor suite (type, count, configuration) | Determines localisation algorithm choice; EKF noise parameters are sensor-dependent | vehicle/localization, vehicle/perception, FDIR thresholds (QAR-NAV-002) | §10 vehicle design |
| Battery chemistry (Li-ion, Li-Po, etc.) | Safe charge/discharge limits and thermal model (C-rate limit, low-temperature cutoff) depend on battery chemistry | power, thermal, HC-006, HC-007 | §10 |
| Thermal mass + insulation configuration | Darkness tolerance calculation (longest night survivability) and VIPER warning: if VIPER parameters are used before §10 arrives, there is a divergence risk | thermal, HC-007 (darkness tolerance), SC-006 (thermal violation) | §10 |
| Communication hardware (antenna type, bandwidth, power) | Link budget calculation, communication outage tolerance (SC-002, SC-007), window quality | communication, HC-014, autonomy/autonomy_matrix.md | §10 |
| Landing GNC requirements and design | Landing GNC is a separate design component; localisation handover test (P3-AC-03) cannot start without this input | vehicle/landing-gnc, vehicle/localization | §10 |
| Mission date / start window | Ephemeris validity range (2024–2035); environment model is invalid for dates outside this range | simulation/environment-model, apps/ground-control, SC-008 | Mission authority + §10 |

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-11-14 | Initial draft — C3 task |
