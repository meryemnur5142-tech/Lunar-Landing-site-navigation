"""
ICD-001: Power Management → Mission Planner data contract.

Defines the :class:`EnergyState` TypedDict that the Power Management
subsystem publishes at each telemetry heartbeat.  The Mission Planner
consumes this to adjust traverse and science activity plans under
energy constraints.

ICD version: 1.0.0
Status: Placeholder — vehicle battery/solar parameters TBD.

.. note::
    ``return_reserve_wh`` and ``uncertainty_available_wh`` implement the
    *uncertainty visible* design principle.  The Mission Planner must
    refuse any plan that would draw ``available_energy_wh`` below
    ``return_reserve_wh`` + margin.
"""

from __future__ import annotations

from typing import Literal, TypedDict

__all__ = ["EnergyState", "ICD_VERSION"]

ICD_VERSION: str = "1.0.0"


class EnergyState(TypedDict):
    """Real-time energy state published by the Power Management subsystem.

    All energy quantities are in watt-hours (Wh) and power in watts (W).

    Fields:
        timestamp_sclk: Spacecraft clock ticks at measurement epoch.
        state_of_charge_pct: Battery state of charge [0.0, 100.0] %.
        available_energy_wh: Usable energy currently stored in the battery (Wh).
        return_reserve_wh: Energy reserved for safe return traverse — must not
                           be consumed by science operations.
        solar_generation_w: Instantaneous solar array output power (W).
        total_load_w: Instantaneous total bus load (W).
        power_mode: Current operating mode affecting available power budget.
                    - ``full``: all subsystems active.
                    - ``science_restricted``: science instruments at reduced duty.
                    - ``traverse_only``: no science; navigation only.
                    - ``survival``: heaters and comms only; mission suspended.
        battery_health_pct: Battery state-of-health [0.0, 100.0] %.
        uncertainty_available_wh: 1-sigma uncertainty on ``available_energy_wh`` (Wh).
                                   Uncertainty visible — planner must account for this.
    """

    timestamp_sclk: int
    state_of_charge_pct: float          # [0.0, 100.0] %
    available_energy_wh: float          # Wh
    return_reserve_wh: float            # Wh — reserved for return traverse
    solar_generation_w: float           # W
    total_load_w: float                 # W
    power_mode: Literal[
        "full", "science_restricted", "traverse_only", "survival"
    ]
    battery_health_pct: float           # [0.0, 100.0] % — SoH
    uncertainty_available_wh: float     # ±Wh 1-sigma — uncertainty visible
