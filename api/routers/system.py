from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def system_health():
    return {"status": "ok"}


@router.post("/kill")
def kill_switch(confirm: str = ""):
    if confirm != "CONFIRM_KILL":
        return {"error": "Must pass confirm=CONFIRM_KILL to activate kill switch"}
    # TODO: wire to execution agent kill_switch.py
    return {"status": "kill_switch_activated"}
