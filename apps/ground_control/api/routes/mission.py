"""GET /api/v1/mission/status — current mission phase and safety state."""

from fastapi import APIRouter
from ..schemas import MissionStatusResponse

router = APIRouter(prefix="/api/v1/mission", tags=["Mission"])


@router.get("/status", response_model=MissionStatusResponse)
def mission_status():
    """
    Return current mission phase and safety state.

    Phase and safety state are static placeholders until the flight segment
    telemetry interface (ICD-001/002) is wired up. The UI can poll this
    endpoint and render the phase state machine display.
    """
    return MissionStatusResponse(
        mission_id="LUNA-AI-DEMO",
        phase="PRE_LAUNCH",
        phase_description=(
            "Architecture and software development phase. "
            "No vehicle data available yet."
        ),
        safety_state="NOMINAL",
        tbd_open_count=24,
        note=(
            "Phase will update automatically once vehicle telemetry is "
            "connected via the ICD-001 EnergyState and ICD-002 ThermalState "
            "interfaces. TBD count decreases as hardware parameters are confirmed."
        ),
    )
