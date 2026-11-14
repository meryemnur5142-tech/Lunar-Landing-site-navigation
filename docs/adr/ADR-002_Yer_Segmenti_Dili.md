# ADR-002: Ground Segment Programming Language

**Status:** Accepted
**Date:** 2026-11-14
**Related Components:** Ground Segment — Scientific Analysis, Mission Design, Operator Interface

---

## Context

The Ground Segment performs the following tasks:

- **GDAL-based DEM (Digital Elevation Model) processing:** Loading, converting, and analysing lunar surface elevation data (e.g. LOLA, MiniRF)
- **SPICE/SpiceyPy integration:** NASA NAIF SPICE toolkit — orbital mechanics, illumination analysis, sun angle calculation
- **Scientific data analysis:** Spectroscopy, thermal mapping, PSR resource estimation models
- **Operator interface:** Web-based or desktop tool (mission plan visualisation, telemetry monitoring)
- **No real-time requirement:** Ground segment is soft-realtime; delays in the order of seconds are tolerable

---

## Alternatives Evaluated

### Alternative 1: Python

**Pros:**
- SpiceyPy is the official Python binding; full SPICE support
- GDAL/Rasterio most mature in the Python ecosystem; extensive documentation and community
- NumPy, SciPy, Pandas: industry standard for scientific computing
- Matplotlib, Plotly: visualisation
- The majority of NASA/ESA mission analysis tools are in Python; interoperability is high
- Prototyping speed: fast iteration, critical advantage for a small team
- Existing astro-data-science team is Python-proficient (assumption)

**Cons:**
- GIL (Global Interpreter Lock): performance issue in CPU-intensive parallel processing; can be worked around with multiprocessing but adds complexity
- Dynamic type system: prone to runtime errors in a large codebase; partly mitigated with type hints (mypy)
- Uncontrolled memory management; careful memory handling needed with large DEM files

---

### Alternative 2: Go

**Pros:**
- Strong concurrency model (goroutines): suitable for telemetry streaming and parallel data processing
- Static type system: compile-time error detection
- Small binary size; ease of deployment
- Fast compilation

**Cons:**
- **Critical blocker:** No Go binding for SpiceyPy / NAIF SPICE; writing a CGO wrapper over the CSPICE C library is required — hard to maintain, security risk
- Go GDAL binding (go-gdal) is immature; not tested with large DEM processing
- Scientific computing ecosystem is extremely limited compared to Python

---

### Alternative 3: Rust

**Pros:**
- Memory safety guarantee (ownership/borrow checker): strong advantage in critical systems
- High performance; no GIL
- Static type system, extensive compile-time checks

**Cons:**
- **Critical blocker:** No Rust binding equivalent to SpiceyPy; writing a CSPICE FFI layer is required — significant engineering cost
- Rust GDAL binding (gdal crate) is developing but far below the maturity level of Python/GDAL
- Learning curve: difficult to acquire Rust proficiency in a short time for a lunar surface mission team
- Scientific/data analysis ecosystem (plotting, stats) is insufficient compared to Python

---

## Decision

**Python 3.11+ (with type hints, using mypy)** has been selected.

**Rationale:**
- SpiceyPy and GDAL/Rasterio integration is directly available and mature in the Python ecosystem; the critical dependency blocker for Go and Rust is considered insurmountable.
- The ground segment has no real-time constraint; Python performance shortfalls are within acceptable limits.
- Python integrations are available for NASA open-source space mission tools (GMAT, OpenSPIFe, Basilisk); ecosystem compatibility is preserved.
- In a small team, scientific productivity is critical; Python prototyping speed is unmatched.

**Code quality guarantees:**
- `mypy --strict` mandatory (gated in CI)
- `ruff` / `black` style checking
- Unit tests for core modules (80% coverage target)
- Large DEM processing: memory windowing via `rasterio`'s `windowed reading` API

---

## Consequences and Constraints

1. **Performance limit:** `multiprocessing` or a `Cython` extension may be used for CPU-intensive route analysis (A* preview on large DEM); pure Python is preferred until this need arises.
2. **API version pinning:** SpiceyPy, GDAL, and scientific library versions are fixed with `requirements.txt` + `poetry.lock`; automatic upgrades are forbidden.
3. **Language boundary with flight segment:** Python code can never be ported to the flight segment; the ground-vehicle boundary is strictly enforced.
4. **Data format independence:** The ground segment operates on file formats that are not Python-dependent (GeoTIFF, FITS, JSON/CBOR); data is migratable in the event of a language change.
