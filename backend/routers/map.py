import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

BAYS_PATH = Path(__file__).parent.parent / "data" / "bays.json"


@router.get("/bays")
async def get_bays():
    data = json.loads(BAYS_PATH.read_text())
    return data
