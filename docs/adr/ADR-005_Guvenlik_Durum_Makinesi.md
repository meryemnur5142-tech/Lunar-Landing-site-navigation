# ADR-005: Safety State Machine Architecture

**Status:** Accepted
**Date:** 2026-11-14
**Related QAR:** FDIR-001, FDIR-002, FDIR-004, FDIR-005
**Related Document:** docs/architecture/SAFETY_STATE_MACHINE.md

---

## Context

LUNA-AI must manage multiple risk layers simultaneously:

- **Four safety states:** NOMINAL, CAUTION, RETURN_REQUIRED, SURVIVAL
- **Multiple triggers:** Energy, thermal, navigation, communication, internal software failure
- **Priority hierarchy:** When multiple triggers are active simultaneously, which state takes precedence?
- **External independence:** The FDIR state machine must operate independently of Mission Planner; safety decisions must continue to work even if the planner freezes
- **Deterministic behaviour:** The same set of inputs must produce the same state transition (FDIR-005 analogue: requires formal verification)
- **Traceability:** Every transition must be loggable, testable, and independently auditable

---

## Alternatives Evaluated

### Alternative 1: Hierarchical State Machine (HSM)

**Pros:**
- Hierarchy between states (parent state shares common behaviour); common cleanup logic shared on CAUTION → NOMINAL return
- 4 states is few; HSM complexity is manageable at this scale
- Fully expressible with UML state diagrams; formal analysis and testing simplified
- Mature implementation possible with C++ template-based HSM libraries (Boost.Statechart, QP/C++)
- Deterministic: every event → single transition; naturally meets FDIR-005 requirement
- Direct watchdog integration: heartbeat reset can be added to entry/exit actions of each state

**Cons:**
- Adding new states in the future requires a schema change; flexibility limited
- Modelling parallel regions (energy + thermal operating independently at the same time) can become complex

---

### Alternative 2: Behaviour Tree

**Pros:**
- Modular: new condition/action nodes can be added without breaking the hierarchy
- Proven in game/robotics AI; observable with visual tools (Groot)
- Parallel branches natural: energy monitoring and thermal monitoring can run simultaneously

**Cons:**
- **Safety-critical compliance difficulty:** The behaviour tree's structure that traverses the entire tree on every tick cycle makes WCET analysis harder; additional constraints needed to guarantee < 50 ms
- Querying "current state" is more indirect compared to a state machine's explicit transition table; logging/audit is harder
- No reference certification history in the space FDIR context

---

### Alternative 3: Rule-Based System

**Pros:**
- IF-THEN rules are the easiest to understand; operators can read the rule table
- Adding new rules is relatively simple

**Cons:**
- **Conflict problem:** Multiple rules triggering at the same time (energy critical + localisation loss) can produce inconsistent behaviour; priority ambiguity is a safety vulnerability
- No state persistence; additional structure needed to remember the current state → effectively becomes a state machine
- Formal verification is difficult; rule combinations grow exponentially

---

## Decision

**Hierarchical State Machine (HSM)** has been selected; **QP/C++ (Quantum Platform) or an equivalent MISRA-compliant HSM library** will be used for implementation.

**Rationale:**
- 4 states is few; HSM remains at manageable complexity.
- Deterministic transition guarantee meets FDIR-005 requirement.
- Formal verification (TLA+ or state machine model checker) can be directly applied to HSM.
- UML state diagram (PlantUML) is the standard documentation format; facilitates operator and engineer agreement.
- QP/C++ is MISRA-C++ compliant, compatible with flight code constraints; DO-178C reference implementation is available.

**Parallel region requirement:**
Energy and thermal monitoring, navigation and communication monitoring operate independently in separate modules; they send events to the HSM. The HSM merges these events in a single transition table. This approach captures the parallel advantage of Behaviour Trees while preserving the deterministic transition guarantee.

---

## Consequences and Constraints

1. **Mission Planner independence:** The HSM runs in a different FreeRTOS task from the Mission Planner process; the message queue between them is one-directional (Planner sends events to HSM; HSM notifies Planner of its decision). HSM has no dependency on the Planner.
2. **Formal verification:** The HSM state transition table will be model-checked with TLA+; the vehicle cannot be fielded until verification is complete.
3. **Extension constraint:** Adding a new state can only be done with approval of an Architecture Review Board equivalent; instant hotfixes are forbidden.
4. **Test coverage:** A minimum of 3 test scenarios per state transition (normal path, boundary value, fault injection) is mandatory.
5. **Detailed design:** PlantUML diagram, watchdog design, and state definitions are in SAFETY_STATE_MACHINE.md.
