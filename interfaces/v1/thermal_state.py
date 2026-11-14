"""
ICD-002: Thermal Management → Mission Planner data contract.

Defines the :class:`ThermalState` TypedDict that the Thermal Management
subsystem publishes at each telemetry heartbeat.  The Mission Planner
consumes this to enforce safe dark-exposure duration limits and adjust
traverse/science plans when thermal margins are tight.

ICD version: 1.0.0
Status: Placeholder — vehicle thermal model (battery operating range,
motor thermal limits, heater power budget) TBD.

.. note::
    ``safe_dark_duration_s`` implements the *safety first* principle:
    the Mission Planner must not plan a PSR entry that exceeds this limit.
    ``thermal_margin_c`` implements *uncertainty visible*: a margin close
    to zero signals that the system is approaching a critical thermal limit.
"""

from __future__ import annotations

from typing import List, TypedDict

__all__ = ["ThermalState", "ICD_VERSION"]

ICD_VERSION: str = "1.0.0"


class ThermalState(TypedDict):
    """Real-time thermal state published by the Thermal Management subsystem.

    All temperatures are in degrees Celsius (°C).

    Fields:
        timestamp_sclk: Spacecraft clock ticks at measurement epoch.
        battery_temp_c: Battery pack temperature (°C).
        electronics_temp_c: Central electronics box temperature (°C).
        motor_temps_c: Individual motor temperatures list of 4 values (°C).
                       Order: [FL, FR, RL, RR] (front-left, front-right, etc.)
        safe_dark_duration_s: Maximum safe continuous time inside a PSR (seconds).
                               Safety first — Mission Planner must not exceed this.
                               TBD: depends on vehicle thermal model.
        heater_load_w: Total heater power consumption (W).
        thermal_margin_c: Temperature margin of the hottest critical component
                           below its operational limit (°C).  Positive = safe;
                           zero or negative = mission suspend required.
                           Uncertainty visible — planner monitors this continuously.
    """

    timestamp_sclk: int
    battery_temp_c: float               # °C
    electronics_temp_c: float           # °C
    motor_temps_c: List[float]          # °C — [FL, FR, RL, RR], 4 motors
    safe_dark_duration_s: float         # s — TBD: depends on vehicle thermal model
    heater_load_w: float                # W
    thermal_margin_c: float             # °C — uncertainty visible; monitor continuously
