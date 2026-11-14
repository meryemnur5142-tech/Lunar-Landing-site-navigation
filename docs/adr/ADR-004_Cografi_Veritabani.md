# ADR-004: Geographic Database Selection

**Status:** Accepted
**Date:** 2026-11-14
**Related Components:** Ground Segment — Scientific Analysis, Mission Design, DEM Processing

---

## Context

The Ground Segment must meet the following spatial data requirements:

- **DEM (Digital Elevation Model):** Lunar LOLA (Lunar Orbiter Laser Altimeter) and Kaguya/SELENE data; 5–60 m/pixel resolution for the south pole; file sizes in the GB range
- **PSR mapping:** Permanently shadowed regions stored as polygons; ray-tracing simulation results
- **Spatial queries:** Fast answering of queries such as "is there safe terrain within X km radius around a given coordinate?" and "which segments of this route have slope > Y°?"
- **Raster + vector:** DEM raster (grid), PSR and target regions as vectors (polygons); both must be queried together
- **Versioning and provenance:** Version management of different DEM sources (LOLA v1, LOLA v2, Kaguya); which data influenced which decision must be traceable

---

## Alternatives Evaluated

### Alternative 1: PostgreSQL + PostGIS

**Pros:**
- PostGIS: industry-standard open-source spatial database extension; full integration with GDAL
- OGC-standard spatial queries (ST_Within, ST_Distance, ST_Slope, raster analysis) fully supported
- Raster and vector in the same engine; mixed queries possible
- Python extension (psycopg2, SQLAlchemy+GeoAlchemy2): direct integration
- ACID compliant; data consistency guaranteed
- High schema flexibility for versioning and provenance
- Wide usage history in space/geography sector (EO data catalogues, USGS, NASA)

**Cons:**
- Requires an additional service (PostgreSQL server); increases infrastructure complexity
- Loading large DEM raster data into the database (pg_raster_loader) can be time-consuming
- Portability challenges for offline use in remote environments (solution: SQLite/SpatiaLite fallback)

---

### Alternative 2: MongoDB

**Pros:**
- Flexible schema: low cost for evolving data model
- 2dsphere indexing supported for geographic queries (GeoJSON)
- Easy horizontal scaling

**Cons:**
- **Critical gap:** Raster analysis (DEM processing) not natively supported; writing an intermediate layer with GDAL is required
- No counterpart in MongoDB for PostGIS spatial analysis functions (ST_Slope, raster statistics)
- More limited ACID guarantees; extra care needed for data consistency
- MongoDB usage history in the space science community is very limited compared to PostGIS

---

### Alternative 3: Flat-file + GDAL

**Pros:**
- No infrastructure dependency; pure file system
- GDAL: industry-standard geographic data formats (GeoTIFF, Shapefile, GeoPackage, HDF5)
- High efficiency for streaming/windowed reading of very large DEM files
- Fast prototyping in a research environment

**Cons:**
- All filtering for spatial queries requires Python code; PostGIS optimisations (R-tree indexing) absent
- Ad-hoc solutions needed for multiple data sources and version management
- Concurrent access (multiple users running queries simultaneously) unmanaged
- No data integrity guarantee; risk grows as the project scales

---

## Decision

**PostgreSQL 15+ + PostGIS 3.4+** has been selected; the GDAL flat-file layer is retained as a **supporting tool** for large DEM raster files.

**Architecture:**
- Vector data (PSR polygons, target points, route segments, waypoints): in PostGIS geometry tables
- Raster metadata and sampled DEM data (e.g. analysis result grid): in PostGIS raster tables
- Raw DEM files (large-size originals): in GeoTIFF flat-file storage; only required sections are loaded into PostGIS
- Versioning and provenance: `data_source`, `loaded_at`, `version_tag` columns; full change history in an event table

**Rationale:** MongoDB is insufficient for raster analysis. Flat-file is not suitable for operational use due to lack of indexing and concurrency. The PostGIS+GDAL combination is the strongest option in terms of both spatial analysis power and Python ecosystem integration.

---

## Consequences and Constraints

1. **Offline/remote use:** `SpatiaLite` (PostGIS-equivalent extension on SQLite) will be provided as a fallback for offline (field operation or integration testing without internet) use; an automatic sync mechanism will be designed.
2. **Large DEM performance:** DEM files larger than **TBD** GB will not be loaded directly into raster tables; analysis will be done with GDAL windowed reading. A benchmark test is needed to determine the threshold.
3. **Schema version management:** Alembic (migration tool) is mandatory; schema changes cannot be applied without a migration file.
4. **Backup:** PostGIS data backed up daily with pg_dump; DEM flat-file storage protected with checksummed archiving.
5. **Licence:** PostgreSQL and PostGIS are open source (PostgreSQL License / GPL); no cost.
