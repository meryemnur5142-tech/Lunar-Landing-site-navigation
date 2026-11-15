"""
SPICE-based orbital window calculator for LUNA-AI.

Kernels NOT loaded yet — module is importable and returns the hardcoded
fallback until kernel files are placed in the path given to `load_kernels()`.

Usage (once kernels are available)::

    from mission_intelligence.efficiency.spice_windows import SpiceWindowCalculator
    calc = SpiceWindowCalculator()
    calc.load_kernels("path/to/kernels/meta_kernel.tm")
    windows = calc.compute_windows(lat=-89.9, lon=0.0, epoch_utc="2026-11-23")
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import List, Optional

__all__ = ["OrbitalWindow", "SpiceWindowCalculator"]

try:
    import spiceypy as spice
    _SPICE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SPICE_AVAILABLE = False


@dataclass
class OrbitalWindow:
    label: str
    utc_time: str
    solar_elevation_deg: float
    earth_elevation_deg: float
    descent_angle_deg: float
    delta_v_penalty_ms: float


# Fallback windows used before kernels are loaded (same values as landing_efficiency.py)
_FALLBACK_WINDOWS: list[dict] = [
    {"label": "W-1", "utc": "2026-11-23 14:32 UTC", "solar": 3.2, "earth": 12.5, "angle": 8.0,  "dv": 0.0},
    {"label": "W-2", "utc": "2026-11-24 02:17 UTC", "solar": 2.5, "earth": 8.0,  "angle": 10.0, "dv": 12.0},
    {"label": "W-3", "utc": "2026-11-24 19:55 UTC", "solar": 1.8, "earth": 5.5,  "angle": 12.0, "dv": 28.0},
    {"label": "W-4", "utc": "2026-11-25 11:40 UTC", "solar": 1.2, "earth": 3.0,  "angle": 15.0, "dv": 45.0},
]


class SpiceWindowCalculator:
    """Compute landing windows using SPICE ephemeris data.

    Falls back to hardcoded estimates if kernels have not been loaded.

    Args:
        kernel_path: Path to a SPICE meta-kernel (.tm) that furnishes at
                     minimum: LSK (naif0012.tls), SPK for Earth + Moon
                     (de440.bsp), and PCK (pck00011.tpc).
    """

    def __init__(self, kernel_path: Optional[str] = None) -> None:
        self._kernels_loaded = False
        if kernel_path:
            self.load_kernels(kernel_path)

    def load_kernels(self, kernel_path: str) -> None:
        """Furnish SPICE kernels from a meta-kernel file.

        Args:
            kernel_path: Absolute or relative path to the .tm meta-kernel.
        """
        if not _SPICE_AVAILABLE:
            raise ImportError(
                "spiceypy is not installed. Run: pip install spiceypy"
            )
        spice.furnsh(kernel_path)
        self._kernels_loaded = True

    @property
    def ready(self) -> bool:
        """True if kernels are loaded and real computation is active."""
        return self._kernels_loaded and _SPICE_AVAILABLE

    def compute_windows(
        self,
        lat: float,
        lon: float,
        epoch_utc: str = "2026-11-23",
        n_windows: int = 4,
        step_hours: float = 12.0,
    ) -> List[OrbitalWindow]:
        """Return landing windows for a surface point.

        When kernels are loaded, computes real Sun/Earth elevation angles
        using SPICE. Otherwise returns the hardcoded fallback values with
        a warning.

        Args:
            lat: Areocentric latitude of the site (degrees, −90 to +90).
            lon: Areocentric east longitude (degrees, 0 to 360).
            epoch_utc: Start date string ("YYYY-MM-DD") to search from.
            n_windows: Number of windows to return (max 4 without kernels).
            step_hours: Time step between candidate windows (hours).

        Returns:
            List of :class:`OrbitalWindow` sorted by solar elevation descending.
        """
        if not self.ready:
            warnings.warn(
                "SPICE kernels not loaded — returning hardcoded fallback windows. "
                "Call load_kernels('path/to/meta_kernel.tm') to enable real computation.",
                stacklevel=2,
            )
            return [
                OrbitalWindow(
                    label=w["label"],
                    utc_time=w["utc"],
                    solar_elevation_deg=w["solar"],
                    earth_elevation_deg=w["earth"],
                    descent_angle_deg=w["angle"],
                    delta_v_penalty_ms=w["dv"],
                )
                for w in _FALLBACK_WINDOWS[:n_windows]
            ]

        return self._compute_spice(lat, lon, epoch_utc, n_windows, step_hours)

    # ------------------------------------------------------------------
    # SPICE implementation (runs only when kernels are loaded)
    # ------------------------------------------------------------------

    def _compute_spice(
        self,
        lat: float,
        lon: float,
        epoch_utc: str,
        n_windows: int,
        step_hours: float,
    ) -> List[OrbitalWindow]:
        """Real SPICE-based computation.  Called only when kernels are ready."""

        _MOON_RADIUS_KM = 1737.4  # IAU mean radius

        moon_id    = "MOON"
        earth_id   = "EARTH"
        sun_id     = "SUN"
        frame      = "IAU_MOON"
        abcorr     = "LT+S"

        # Site position in Moon-fixed frame (unit vector on surface)
        lat_r = math.radians(lat)
        lon_r = math.radians(lon)
        site_vec = [
            math.cos(lat_r) * math.cos(lon_r),
            math.cos(lat_r) * math.sin(lon_r),
            math.sin(lat_r),
        ]

        start_et = spice.str2et(f"{epoch_utc} 00:00:00 UTC")

        windows: List[OrbitalWindow] = []
        for i in range(n_windows * 3):  # oversample, keep best n_windows
            et = start_et + i * step_hours * 3600.0
            utc_str = spice.et2utc(et, "ISOC", 0)[:16] + " UTC"

            solar_el  = self._body_elevation(et, site_vec, sun_id,   frame, moon_id, abcorr)
            earth_el  = self._body_elevation(et, site_vec, earth_id, frame, moon_id, abcorr)

            if solar_el < 0.5:  # skip windows with sun below horizon
                continue

            descent_angle, dv = self._descent_params(solar_el)

            windows.append(OrbitalWindow(
                label=f"W-{len(windows)+1}",
                utc_time=utc_str,
                solar_elevation_deg=round(solar_el, 2),
                earth_elevation_deg=round(earth_el, 2),
                descent_angle_deg=descent_angle,
                delta_v_penalty_ms=dv,
            ))
            if len(windows) == n_windows:
                break

        windows.sort(key=lambda w: w.solar_elevation_deg, reverse=True)
        for i, w in enumerate(windows, 1):
            w.label = f"W-{i}"
        return windows

    @staticmethod
    def _body_elevation(
        et: float,
        site_vec: list,
        target: str,
        frame: str,
        obs: str,
        abcorr: str,
    ) -> float:
        """Elevation angle (degrees) of *target* above local horizon at site."""
        pos, _ = spice.spkpos(target, et, frame, abcorr, obs)
        # Vector from site to target in body-fixed frame
        rel = [pos[j] - site_vec[j] * _MOON_RADIUS_KM * 1e3 for j in range(3)]
        dot = sum(site_vec[j] * rel[j] for j in range(3))
        mag = math.sqrt(sum(x**2 for x in rel))
        if mag < 1e-6:
            return 0.0
        return math.degrees(math.asin(max(-1.0, min(1.0, dot / mag))))

    @staticmethod
    def _descent_params(solar_el: float) -> tuple[float, float]:
        """Map solar elevation to optimal descent angle and Δv penalty."""
        if solar_el >= 3.0:
            return 8.0, 0.0
        elif solar_el >= 2.0:
            return 10.0, 12.0
        elif solar_el >= 1.5:
            return 12.0, 28.0
        else:
            return 15.0, 45.0
