# ADR-003: Vehicle Software Platform and RTOS Selection

**Status:** Accepted
**Date:** 2026-11-14
**Related QAR:** FDIR-001, FDIR-002, FDIR-005, THM-001, PWR-003

---

## Context

The Flight Segment software must meet the following requirements:

- **Deterministic timing:** Hard deadlines exist such as FDIR < 50 ms anomaly detection (FDIR-001) and < 10 ms load shedding (PWR-004); worst-case execution time (WCET) analysis must be possible
- **FDIR reliability:** Critical safety decisions cannot be preempted or stalled; WCET analysis must be feasible
- **Radiation tolerance:** SEU (Single Event Upset) events are expected from space radiation; software must be recoverable after such events
- **Memory constraint:** Vehicle RAM and Flash are **TBD** (dependent on hardware selection); deterministic memory management is critical
- **Long mission lifetime:** Software must run faultlessly for days/weeks; memory leaks cannot be tolerated
- **Partial hardware independence:** Sensor and motor interfaces may change; the driver layer must be decoupled

---

## Alternatives Evaluated

### Alternative 1: C++ / FreeRTOS

**Pros:**
- FreeRTOS: wide space project usage history (CubeSats, small planetary rovers)
- Open source; full source code access; customisation flexibility
- Modern software design with C++ (RAII, interface segregation); strong tools for FDIR and state machines
- Wide library ecosystem: CAN, SPI, I2C drivers easily added
- Real-time performance sufficient: tick granularity < 1 ms, preemptive scheduling
- MISRA-C++ compliance is not difficult; low-level control is simplified

**Cons:**
- FreeRTOS timestamps and features are platform-dependent; portability limited
- No official DO-178C / ECSS certification (additional effort required)
- C++ dynamic memory management (new/delete) must be carefully restricted; operator override required

---

### Alternative 2: C++ / VxWorks

**Pros:**
- Wide certification history in aerospace/space; DO-178C support
- Determinism and WCET analysis tools are mature
- Proven high reliability; Mars Rovers (Spirit, Opportunity) used VxWorks

**Cons:**
- **Licence cost:** Commercial licence; adds significant burden to project budget
- Source code access restricted; independent audit is harder
- Community support and open-source ecosystem more closed than FreeRTOS/Zephyr
- Learning curve and tool dependency for a small development team

---

### Alternative 3: Ada / RTEMS

**Pros:**
- Ada's strong type system and compile-time safety checks: overflow, range, null dereference largely caught at compile time
- RTEMS (Real-Time Executive for Multiprocessor Systems): NASA-originated, certified use history in space sector
- SPARK Ada subset enables formal verification; FDIR state machine can be formally proven

**Cons:**
- Extremely difficult to find Ada-proficient developers; high team staffing risk
- Community and library ecosystem is very small compared to C/C++; driver writing largely from scratch
- Development tools (GNAT) are commercial; open-source GNAT FSF version contains some platform restrictions
- Slow prototyping speed; negative for early-phase iteration

---

## Decision

**C++ / FreeRTOS** has been selected; ECSS-E-ST-40C compliance work is planned for later phases.

**Rationale:**
- VxWorks licence cost and dependency are disproportionate for this project; open-source architecture is preferred.
- Ada/RTEMS formal verification advantage is attractive, but team development capacity and library absence risk are unacceptably large.
- FreeRTOS, combined with C++'s strong type system, provides the required hard-realtime guarantees (preemptive scheduling, deterministic context switch).
- Being a proven combination in CubeSats and small planetary rovers provides maturity assurance.

**Mandatory C++ restrictions (flight code):**
- Dynamic memory allocation (`new`/`delete`) is forbidden in critical paths of flight code; pre-allocated memory pools are used
- Exceptions disabled; error handling via return code + FDIR
- RTTI (runtime type information) disabled
- Template usage restricted to those with no WCET impact
- MISRA-C++ 2008 profile compliance mandatory; static analysis (cppcheck, clang-tidy) gated in CI

---

## Consequences and Constraints

1. **Scheduler configuration:** FreeRTOS task priorities configured as FDIR > Navigation > Power > Thermal > Planner > Communication; priority inversion mechanism (priority inheritance mutex) activated.
2. **Watchdog design:** Every critical task sends a heartbeat to the FreeRTOS watchdog timer; heartbeat loss directly triggers FDIR (consistent with ADR-005 and SAFETY_STATE_MACHINE.md).
3. **WCET analysis:** WCET analysis is mandatory for critical paths (FDIR decision, load shedding, navigation update); tool: **TBD** (AbsInt aiT or equivalent).
4. **Memory budget:** Flash and RAM usage **TBD** (hardware BoM pending); static memory budget analysis to be completed in design phase.
5. **Version control:** Flight code builds are tagged with the git hash; bootloader performs version verification.
