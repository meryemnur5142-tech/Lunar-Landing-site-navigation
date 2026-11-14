# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/environment_product.schema.yaml, safety/safety_budget.md, mission-intelligence/constraints/hard_constraints.py, docs/qar/]
# open_items: [All numerical thresholds TBD — to be calibrated against QAR and vehicle model, quality_score threshold (0.7) to be revised based on vehicle sensor package]

# Uncertainty Management Policy — LUNA-AI v1.1

## Purpose

This document defines how uncertainties in environmental data and vehicle state estimates are defined, accumulated, managed, and reflected in the decision flow for the LUNA-AI system.

**Core principle:** Hard constraints (HC-001..015) are always evaluated first. Uncertainty management ensures the conservative application of the HC set.

---

## 1. Uncertainty Thresholds — Decision Table

> **Note:** All numerical values are TBD — to be calibrated against QAR requirements and vehicle model. The values below are design reference points.

| Uncertainty Type | Low (accept — continue) | Medium (ask operator) | High (eliminate/stop) | FDIR Trigger |
|-----------------|--------------------------|---------------------|-------------------|----------------|
| Position uncertainty σ_pos | < 0.5m | 0.5–2m | > 2m | > QAR-NAV-002_threshold → SC-004 |
| PSR boundary confidence | > 0.85 | 0.70–0.85 | < 0.70 | PSR entry rejected (HC check) |
| Energy budget error | < 10% | 10–20% | > 20% | > 20% → worst-case planning mandatory |
| DEM resolution adequacy | < 5m/px | 5–20m/px | > 20m/px | > 20m/px → PSR mapping rejected |
| Thermal model deviation | < TBD% | TBD–TBD% | > TBD% | > threshold → SC-006 warning |
| Landmark match confidence | > 0.80 | 0.60–0.80 | < 0.60 | < 0.60 → localisation reset attempt |

**Usage rule:** When uncertainty enters the "Medium" range, the vehicle sends an ask-operator notification and waits for approval (GCA — autonomy matrix). In the "High" range, elimination, halt or FDIR trigger is applied depending on the decision structure.

---

## 2. Nominal vs Worst-Case Planning

### 2.1 Nominal Planning

Calculation using nominal expected values. Use cases: science target ranking, preliminary exploration route planning, telemetry estimation.

### 2.2 Worst-Case Planning

Conservative calculation adding 2σ uncertainty margin. **Mandatory use cases:**

- PSR return reserve calculation (HC-006) — **worst-case in all conditions**
- Safe haven selection (7 criteria)
- Emergency return time estimation
- Darkness tolerance calculation

**PSR special rule:** In PSR operations, energy calculations ALWAYS use worst-case, not nominal. Nominal calculation is for reporting purposes only.

### 2.3 Uncertainty Margin Formulation

Worst-case estimate of return reserve:

```
return_reserve_wh_wc = return_reserve_wh_nominal × (1 + k_sigma × σ_energy_pct)
```

Where `k_sigma = 2` (2σ), `σ_energy_pct` is energy consumption model uncertainty (TBD — §10 vehicle profile).

---

## 3. Uncertainty Accumulation Rule

### 3.1 Position Uncertainty Accumulation

At each navigation step:

```
σ_pos²(t+1) = σ_pos²(t) + σ_IMU_drift² + σ_odometry²
```

Unit: metres², independent noise added at each step.

**Parameters:** `σ_IMU_drift` and `σ_odometry` values are TBD(source: §10 sensor package).

### 3.2 Uncertainty Reset Conditions

| Reset Trigger | Reset Effect | New σ_pos Value |
|------------------|--------------|-------------------|
| Landmark match (confidence > 0.80) | σ_pos reset | Landmark measurement uncertainty |
| Orbital map fit | σ_pos updated | Dependent on fit quality |
| IMU calibration during static pause | Drift reduced | TBD |

### 3.3 FDIR Trigger Threshold

`σ_pos > §1 table "High" threshold` → SC-004 triggered (Detection phase).

---

## 4. Data Quality Degradation Protocol

If environment product quality score `quality_score < 0.7`:

1. **Revise product uncertainty upward:** `uncertainty_1sigma` field is widened (automatic).
2. **Send low quality warning to planner:** Product transmitted with `data_quality_flag = LOW`.
3. **Apply hard constraint threshold more conservatively:** Worst-case threshold used instead of nominal.
4. **temporal_class check:** Product from low-quality source is marked `temporal_class = predicted`; cannot be used as `historical`.

**quality_score definition:** Weighted average of source data resolution, temporal freshness and sensor confidence score. Calculation method TBD(source: data-platform provenance module).

---

## 5. Cross-References

| Reference | Document | Field |
|----------|-------|------|
| Environment product uncertainty field | `interfaces/schemas/environment_product.schema.yaml` | `uncertainty_1sigma` |
| Safety budget uncertainty margin | `safety/safety_budget.md` | Energy budget uncertainty section |
| Return energy hard constraint | `mission-intelligence/constraints/hard_constraints.py` | HC-012, HC-006 |
| Illumination duration hard constraint | `mission-intelligence/constraints/hard_constraints.py` | HC-009 |
| Localisation QAR threshold | `docs/qar/` | QAR-NAV-002 |
| PSR entry autonomy rule | `autonomy/autonomy_matrix.md` | PSR_OPS row |

---

## 6. Implementation Notes

### 6.1 Uncertainty Propagation to Planner

The planner receives each environment product together with `uncertainty_1sigma`. In route planning:
- Low uncertainty: nominal behaviour
- Medium uncertainty: safety margin increased
- High uncertainty: relevant area excluded from plan or ground control approval requested

### 6.2 PSR Boundary Confidence Score

When PSR boundary confidence < 0.85, PSR entry requires ground control approval (even when confidence > 0.85 — no additional check required). When confidence < 0.70, PSR entry is rejected.

### 6.3 Energy Budget Error

`energy_budget_error > 20%` → Hard constraint thresholds switch to worst-case mode. Power Mgmt makes this decision and communicates it to the Planner (Compliance Note 3: Power Mgmt is the owner, Planner is the consumer).

---

## 7. Earth Visibility Uncertainty (B5-EK)

### 7.1 Marginal Condition Uncertainty

When Earth is near the horizon (elevation < TBD°), geometric visibility calculation is sensitive to additional uncertainty sources:

- **Atmospheric refraction (Earth eclipse):** The pipeline does not calculate this effect. Real Earth visibility can deviate by ±unknown in marginal conditions when Earth is near the horizon. This effect must be reflected in the `uncertainty_minutes` field.
- **Horizon profile sensitivity:** 720-ray horizon calculation produced from 80m DEM. The difference between the real horizon and the model affects visibility window start/end times.
- **Application rule:** Windows where Earth elevation < TBD° are marked `confidence: LOW`; these windows are counted as worst-case in `longest_outage_hours` calculation.

### 7.2 temporal_class Policy

| Viewer time | temporal_class | Description |
|------------------|---------------|----------|
| Past (< current time) | `historical` | Occurred geometry — exact value |
| Future (≥ current time) | `predicted` | Calculated geometry — uncertainty margin applied |

**Rule:** When a time slider is used in the user interface, `temporal_class` is updated automatically. Data labelled `predicted` cannot be mixed with `historical` sources.

### 7.3 Resolution Uncertainty Sources

| DEM Resolution | Uncertainty Type | Impact |
|-----------------|-----------------|------|
| 80m (base resolution) | Small obstacle miss | Hidden obstacle risk in local path planning (aligned with RR-006) |
| 300m (site finder cell) | Site boundary uncertainty | ±150m boundary uncertainty — affects PSR boundary confidence calculation |
| 2.7km (global trend) | Large-scale trend | Deviation in long-range energy/illumination estimates |

**In practice:** PSR boundary confidence score calculated at 80m resolution may change when recalculated at 20m resolution. B4 AC-VAL-005 measures this.

### 7.4 Earth Eclipse Refraction — Known Gap

The reference pipeline (lunar-navigator) does not model the refraction effect during Earth eclipse. This effect:
- Can shift visibility window start/end time by ±TBD minutes
- In marginal conditions (Earth elevation < 2°) can produce incorrect "visible" or "invisible" decisions
- **Mitigation:** These windows are marked `confidence: LOW` and kept outside the safety band in link planning calculations

---

## Revision History

| Version | Date | Change |
|----------|-------|------------|
| 0.1 | 2026-11-14 | First draft — B5 task |
| 0.2 | 2026-11-14 | B5-EK: Earth visibility uncertainty, temporal_class policy, resolution sources, refraction gap |
