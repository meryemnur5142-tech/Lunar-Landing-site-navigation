# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/*.schema.yaml]
# open_items: []

# Schema Versioning Policy — LUNA-AI v1.1

## 1. General Rules

Every schema file must carry a `schema_version` field.
Format: **MAJOR.MINOR.PATCH** (Semantic Versioning 2.0.0).

```yaml
schema_version: "1.0.0"
```

All messages transferred between ground and vehicle include the schema version.
The vehicle compares the schema version of a received message with the version it supports; it rejects the message on a mismatch.

---

## 2. Version Increment Rules

### PATCH (1.0.0 → 1.0.1)
Corrections that are both backward- and forward-compatible and do not change behaviour:
- Description text correction
- Example update
- Comment addition/modification

### MINOR (1.0.0 → 1.1.0)
Backward-compatible addition (old receiver can still understand the new message):
- Adding a new **optional** field
- **Adding a new value** to an existing `enum` (old receiver ignores the unknown value)
- Adding a new optional constraint (widening minimum/maximum)

### MAJOR (1.0.0 → 2.0.0)
**Breaking** change (old receiver cannot understand the new message):
- Adding or removing an existing **required field**
- **Removing** or **renaming** an existing `enum` value
- Changing the type or meaning of an existing field
- Moving an existing optional field into the `required` list

---

## 3. Backward-Compatible Change Examples (→ MINOR)

| Change | Version | Rationale |
|---|---|---|
| Optional `battery_temp_c` added to `resource_state.schema.yaml` | 1.0.0 → 1.1.0 | Old vehicle software ignores the field |
| `instrument_toggle_batch` enum value added to `vehicle_command.schema.yaml` | 1.2.0 → 1.3.0 | Old receiver rejects unknown enum value → payload does not pass, safe |
| Optional `sensor_id` added to `environment_product.schema.yaml` | 1.0.0 → 1.1.0 | Old receiver ignores the field |

---

## 4. Breaking Change Examples (→ MAJOR)

| Change | Version | Why Breaking |
|---|---|---|
| Required `heater_duty_cycle` added to `resource_state.schema.yaml` | 1.x.x → 2.0.0 | Old sender does not produce the field → receiver gives a validation error |
| `abort` enum value removed from `vehicle_command.schema.yaml` | 1.x.x → 2.0.0 | Old sender may send `abort` → receiver rejects it, critical command lost |
| `authority_level` field renamed to `command_authority` in `mission_package.schema.yaml` | 1.x.x → 2.0.0 | Old receiver cannot find the field → validation error |

---

## 5. Ground–Vehicle Version Mismatch Protocol

```
The vehicle compares the MAJOR value of the received message's schema_version
with the MAJOR it supports.

If MAJOR differs:
  → Reject the message
  → Send error telemetry: SCHEMA_VERSION_MISMATCH
  → Stay in the last valid state (does not apply the command)

If MAJOR is the same but MINOR differs (receiver is older):
  → Ignore unknown fields (additionalProperties: false rule may be relaxed vehicle-side)
  → Accept the message if required fields are satisfied

If MINOR differs (receiver is newer):
  → Accept the message; apply default values for missing optional fields
```

**Critical rule:** A MAJOR version difference between the ground segment and vehicle software cannot be tolerated.
MAJOR compatibility is verified before the mission, and an ICD check is performed.

---

## 6. Schema Files and Current Versions

| File | Current Version | Last Change |
|---|---|---|
| `environment_product.schema.yaml` | 1.0.0 | v1.1 initial release |
| `resource_state.schema.yaml` | 1.0.0 | v1.1 initial release |
| `mission_package.schema.yaml` | 1.0.0 | v1.1 initial release |
| `vehicle_command.schema.yaml` | 1.0.0 | v1.1 initial release |

---

## 7. Change Process

1. The change proposal is documented as an ADR (Architectural Decision Record).
2. MAJOR changes pass through engineering review.
3. `schema_version` is updated; the §6 table in `VERSIONING.md` is updated.
4. Ground segment and vehicle software integration testing is performed.
