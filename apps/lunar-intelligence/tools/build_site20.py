"""
Build dist/site20.js from the NASA LOLA Site20 5 m/px rasters (branch veri/site20-arazi).

Inputs (GeoTIFF, south polar stereographic, sphere R=1737.4 km, 3200x3200 px, 5 m/px,
x 65000..81000 m, y 110000..126000 m):
  *_surf.tif  elevation (m, relative to 1737.4 km)
  *_slp.tif   slope (deg)

Per 100 m x 100 m window (20x20 px) it derives:
  slopeDeg     mean slope in the window                                (LOLA, real)
  slopeP95     95th percentile slope                                   (LOLA, real)
  roughness    std of elevation residual after a best-fit plane (m)    (LOLA, real)
  hazardFree   fraction of pixels with slope <= 10 deg                 (LOLA, real)
  edgeKm       distance to nearest pixel with slope > 20 deg (km)      (LOLA, real)
  rockCover / stability: no data in repo -> constant placeholders (do not affect ranking)

Usage:
  python tools/build_site20.py <dir-with-tifs>
Requires numpy, scipy, tifffile.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy.ndimage import distance_transform_edt

R = 1737400.0
PX = 5.0
X0, Y0 = 65000.0, 126000.0  # top-left corner (from GeoTIFF tiepoint)
WIN = 20                    # 20 px = 100 m
STEEP_DEG = 20.0
SAFE_DEG = 10.0
REF_CLEARANCE_KM = 0.5
ROCK_PLACEHOLDER = 0.10
STABILITY_PLACEHOLDER = 85
WEIGHTS = dict(smoothness=.25, slope=.20, rocks=.15, hazards=.20, edge=.10, stability=.10)


def find(d, key):
    hits = sorted(Path(d).glob(f"*{key}*.tif"))
    if not hits:
        sys.exit(f"missing *{key}*.tif in {d}")
    return tifffile.imread(hits[0]).astype("float64")


def xy_to_latlon(x, y):
    r = math.hypot(x, y)
    lat = -(90.0 - 2.0 * math.degrees(math.atan(r / (2.0 * R))))
    lon = math.degrees(math.atan2(x, y))
    return lat, lon


def pixel_xy(row, col):
    return X0 + PX * (col + .5), Y0 - PX * (row + .5)


def score(z):
    clamp = lambda v: max(0.0, min(100.0, v))
    s = dict(smoothness=clamp(100 - z["roughness"] * 50), slope=clamp(100 - z["slopeDeg"] * 5),
             rocks=clamp((1 - ROCK_PLACEHOLDER) * 100), hazards=clamp(z["hazardFree"] * 100),
             edge=clamp(z["edgeKm"] / REF_CLEARANCE_KM * 100), stability=STABILITY_PLACEHOLDER)
    return sum(s[k] * w for k, w in WEIGHTS.items())


def main(d):
    elev, slope = find(d, "surf"), find(d, "slp")
    n = elev.shape[0] // WIN

    # distance (m) from every pixel to the nearest steep pixel (Euclidean distance transform)
    dist = distance_transform_edt(slope <= STEEP_DEG) * PX

    yy, xx = np.mgrid[0:WIN, 0:WIN] * PX
    A = np.c_[xx.ravel(), yy.ravel(), np.ones(WIN * WIN)]
    cands = []
    for wr in range(n):
        for wc in range(n):
            r0, c0 = wr * WIN, wc * WIN
            e = elev[r0:r0 + WIN, c0:c0 + WIN]
            s = slope[r0:r0 + WIN, c0:c0 + WIN]
            if not (np.isfinite(e).all() and np.isfinite(s).all()):
                continue
            coef, *_ = np.linalg.lstsq(A, e.ravel(), rcond=None)
            resid = e.ravel() - A @ coef
            z = dict(r=r0 + WIN // 2, c=c0 + WIN // 2,
                     slopeDeg=float(s.mean()), slopeP95=float(np.percentile(s, 95)),
                     roughness=float(resid.std()), hazardFree=float((s <= SAFE_DEG).mean()),
                     edgeKm=float(dist[r0:r0 + WIN, c0:c0 + WIN].min() / 1000.0),
                     elevation=float(e.mean()))
            z["total"] = score(z)
            cands.append(z)
    cands.sort(key=lambda z: -z["total"])

    def pick(pool, k, chosen, min_sep_px=200):  # 1 km separation
        out = []
        for z in pool:
            if all(math.hypot(z["r"] - o["r"], z["c"] - o["c"]) >= min_sep_px for o in chosen + out):
                out.append(z)
                if len(out) == k:
                    break
        return out

    chosen = []
    chosen += pick(cands, 2, chosen)                                  # most efficient
    mid = len(cands) // 2
    chosen += pick(cands[mid - 2000:mid + 2000], 3, chosen)            # middle of the distribution
    chosen += pick(list(reversed(cands)), 2, chosen)                   # most risky

    cx, cy = (X0 + X0 + elev.shape[1] * PX) / 2, (Y0 + Y0 - elev.shape[0] * PX) / 2
    clat, clon = xy_to_latlon(cx, cy)
    zones = []
    for i, z in enumerate(chosen):
        x, y = pixel_xy(z["r"], z["c"])
        lat, lon = xy_to_latlon(x, y)
        # real E-W elevation profile through the window centre: 81 samples, 2.5 m apart (200 m)
        cols = z["c"] - 20 + np.arange(81) * 0.5
        c_lo = np.clip(np.floor(cols).astype(int), 0, elev.shape[1] - 1)
        c_hi = np.clip(c_lo + 1, 0, elev.shape[1] - 1)
        t = cols - np.floor(cols)
        prof = elev[z["r"], c_lo] * (1 - t) + elev[z["r"], c_hi] * t
        prof = prof - prof[0]
        zones.append(dict(
            id="ABCDEFG"[i], lat=round(lat, 5), lon=round(lon, 5),
            x=round((x - cx) / 1000, 3), y=round((y - cy) / 1000, 3),
            roughness=round(z["roughness"], 3), slopeDeg=round(z["slopeDeg"], 2),
            slopeP95=round(z["slopeP95"], 2), hazardFree=round(z["hazardFree"], 3),
            edgeKm=round(z["edgeKm"], 3), elevationM=round(z["elevation"], 1),
            rockCover=ROCK_PLACEHOLDER, stability=STABILITY_PLACEHOLDER,
            referenceClearance=REF_CLEARANCE_KM, profileSeed=i,
            profile=[round(float(v), 2) for v in prof]))

    site = dict(
        id="mons-mouton-site20", name="Mons Mouton — Site20 (LOLA 5 m)", kind="lola",
        lat=round(clat, 4), lon=round(clon, 4), diameter=16, depth=round(float(elev.mean()) / 1000, 2),
        region="SOUTH POLAR HIGHLAND · MONS MOUTON / VIPER AREA",
        description="NASA LOLA Site20 5 m/px tile (16×16 km) — slope, roughness, hazard & profiles derived from real data",
        shift=4, zones=zones,
        stats=dict(windows=len(cands), windowM=WIN * PX, safeSlopeDeg=SAFE_DEG, steepSlopeDeg=STEEP_DEG,
                   elevMinM=round(float(elev.min()), 1), elevMaxM=round(float(elev.max()), 1),
                   slopeMedianDeg=round(float(np.median(slope)), 2)),
    )
    out = Path(__file__).resolve().parent.parent / "dist" / "site20.js"
    out.write_text("// GENERATED by tools/build_site20.py from NASA LOLA Site20 rasters — do not edit.\n"
                   "export const site20=" + json.dumps(site, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"wrote {out}  ({len(cands)} windows)")
    for z in zones:
        print(z["id"], z["lat"], z["lon"], "slope", z["slopeDeg"], "p95", z["slopeP95"], "rough", z["roughness"],
              "safe", z["hazardFree"], "edgeKm", z["edgeKm"], "elev", z["elevationM"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
