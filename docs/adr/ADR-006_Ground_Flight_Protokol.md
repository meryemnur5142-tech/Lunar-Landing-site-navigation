# ADR-006: Ground-Vehicle Communication Protocol

**Status:** Accepted
**Date:** 2026-11-14
**Related QAR:** COM-001, COM-002, COM-003, COM-005
**Related ICD:** ICD-005 (Uplink), ICD-006 (Downlink)

---

## Context

Ground-vehicle communication takes place at lunar distance (approximately 384,000 km):

- **Link budget constraint:** Weak signal, limited antenna gain and bandwidth; keeping packet size small is critical
- **Latency:** Speed-of-light delay ~1.3 seconds (one way); the protocol must be designed to work with this delay
- **Reliability first:** Packet loss and bit corruption are expected; error detection and correction are mandatory
- **Command priority:** TC-IMMEDIATE commands must be processed before TC-PLAN commands; the protocol must support priority ordering
- **Bandwidth conservation:** All uplink/downlink data should be compressible or delta-encodable
- **Autonomous operation:** The vehicle must work independently of the protocol when there is no link; the protocol must not affect the state machine
- **Standards compliance:** Interoperability with other agency vehicles or ground stations may be required in the future

---

## Alternatives Evaluated

### Alternative 1: CCSDS (Consultative Committee for Space Data Systems)

**Pros:**
- Space sector industry standard (used by NASA, ESA, JAXA in all missions)
- **Space Packet Protocol (CCSDS 133.0-B):** Optimised for telemetry packets; small header, high payload efficiency
- **Telecommand (CCSDS 232.0-B):** Command sequence management, acknowledgement mechanism, priority ordering built in
- **CCSDS File Delivery Protocol (CFDP):** Reliable file transfer for time-delayed links
- Reed-Solomon and LDPC error correction codes defined within the standard
- Interoperability: can directly work with other agency infrastructure
- Open standard; reference implementations available (cFS/NASA, yamCS)

**Cons:**
- Learning the standard and full implementation is time-consuming; engineering overhead at the start
- CCSDS tools (packet decoder, telemetry monitor) require expertise
- May seem overkill for a small-scale test environment

---

### Alternative 2: MQTT (Message Queuing Telemetry Transport)

**Pros:**
- Very common, easy to learn; extensive tool ecosystem
- Publish-subscribe model suits flexible topologies
- QoS levels (0/1/2) provide reliability control
- Fast prototype development

**Cons:**
- **Link budget issue:** Requires TCP/IP infrastructure; TCP three-way handshake at lunar distance is practically impossible (1.3 s RTT × handshake cycles)
- Command priority management (TC-IMMEDIATE vs TC-PLAN) not built into MQTT; additional layer needed to implement
- No forward error correction (FEC); bit errors in the space radiation environment cannot be compensated
- No certified reference implementation for space mission communication

---

### Alternative 3: gRPC (Google Remote Procedure Call)

**Pros:**
- Protocol Buffers: efficient binary serialisation; bandwidth saving
- Strong type system and API definition; ground-vehicle interface definition (ICD) is easier
- Bidirectional streaming support

**Cons:**
- **Critical blocker:** Built on HTTP/2; managing HTTP/2 connection state on the lunar link is practically impossible (constantly dropping link, delayed ACK)
- Not designed for space communication; no link budget optimisation
- No FEC and no priority management; additional layer required
- No usage history in the space sector

---

## Decision

**CCSDS (Space Packet Protocol + Telecommand + CFDP)** has been selected; a **NASA cFS (core Flight System)**-compatible structure will be adopted as the implementation reference.

**Protocol stack:**
| Layer | Standard Used | Purpose |
|-------|--------------|---------|
| Data link | CCSDS TM/TC Sync & Channel Coding | Bit error correction (Reed-Solomon or LDPC) |
| Packet | CCSDS Space Packet (133.0-B) | Telemetry and science data downlink |
| Command | CCSDS Telecommand (232.0-B) | Uplink; priority and ACK built in |
| File transfer | CCSDS CFDP (727.0-B) | Mission plan upload, software update |

**Priority management:** The `Priority` field in the CCSDS TC layer directly handles the TC-IMMEDIATE (P1) → TC-PLAN (P3) ordering.

**Rationale:** MQTT and gRPC physically cannot operate under lunar link conditions (TCP handshake). CCSDS's connectionless design and link intermittency support make it the only realistic option.

---

## Consequences and Constraints

1. **yamCS integration:** The ground segment operator interface can be built on yamCS (Python-based open-source Mission Control System); CCSDS is natively supported.
2. **Bandwidth budget:** The size of each packet **TBD:** will be adjusted once link budget analysis is complete; telemetry update periods will be determined accordingly.
3. **Encryption:** CCSDS Security Layer (355.0-B) to be evaluated in later phases; CRC integrity check only at the start.
4. **Test environment:** A CCSDS link simulator (e.g. socat + packet loss injection on Linux) will be set up in the integration test environment; COM-005 integrity test runs in this environment.
5. **Team load:** CCSDS tools carry an engineering overhead; a mandatory training plan for the first 2 months is required.
