"""
ICD-003: Navigation → Local Planner data contract.

Defines the :class:`VehiclePose` TypedDict that the Navigation subsystem
publishes at each navigation cycle.  The Local Planner consumes this to
compute safe motion commands and update the global traverse plan.

ICD version: 1.0.0
Status: Placeholder — absolute localisation uncertainty budget TBD;
        depends on LOLA DEM co-registration and IMU noise model.

.. note::
    ``position_uncertainty_m`` and ``heading_uncertainty_deg`` implement
    the *uncertainty visible* design principle.  The Local Planner must
    plan motion with these uncertainties accounted for — a rover near a
    PSR rim cannot assume the nominal position is the true position.
    ``localization_mode`` drives the *safety first* response:
    ``"lost"`` mode must trigger an immediate safe stop.
"""

from __future__ import annotations

from typing import Literal, TypedDict

__all__ = ["VehiclePose", "ICD_VERSION"]

ICD_VERSION: str = "1.0.0"


class VehiclePose(TypedDict):
    """Real-time vehicle pose published by the Navigation subsystem.

    Coordinates are areocentric (IAU_MOON_2015).

    Fields:
        timestamp_sclk: Spacecraft clock ticks at measurement epoch.
        lat_deg: Areocentric latitude of vehicle centre of mass (degrees).
        lon_deg: Areocentric east longitude of vehicle centre of mass (degrees).
        alt_m: Height above the LOLA reference surface (metres).
        heading_deg: Vehicle heading measured clockwise from north (degrees, [0, 360)).
        velocity_ms: Instantaneous ground speed (m/s).
        position_uncertainty_m: 1-sigma horizontal position uncertainty (metres).
                                  Uncertainty visible — Local Planner uses this for
                                  PSR rim keep-out buffer sizing.
        heading_uncertainty_deg: 1-sigma heading uncertainty (degrees).
                                  Uncertainty visible — impacts steering correction.
        localization_mode: Quality of the current localisation estimate.
                            - ``nominal``: full LOLA co-registration active.
                            - ``degraded``: reduced accuracy; increase safety margins.
                            - ``lost``: localisation failed; immediate safe stop required.
    """

    timestamp_sclk: int
    lat_deg: float                      # degrees, areocentric
    lon_deg: float                      # degrees, areocentric east
    alt_m: float                        # metres above LOLA reference surface
    heading_deg: float                  # degrees, clockwise from north [0, 360)
    velocity_ms: float                  # m/s
    position_uncertainty_m: float       # 1-sigma m — uncertainty visible
    heading_uncertainty_deg: float      # 1-sigma degrees — uncertainty visible
    localization_mode: Literal["nominal", "degraded", "lost"]
