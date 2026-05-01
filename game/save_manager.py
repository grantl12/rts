"""Save slot manager — 3 campaign slots, one JSON file each."""
from __future__ import annotations
import json, os, datetime
from typing import Optional

SAVE_DIR  = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "save"))
NUM_SLOTS = 3

FACTION_DISPLAY = {
    "regency":   "REGENCY",
    "frontline": "FRONTLINE",
    "sovereign": "SOVEREIGN",
    "oligarchy": "OLIGARCHY",
}

PHASE_DISPLAY = ["PRISTINE", "SCARRED", "SHATTERED"]


def _path(n: int) -> str:
    return os.path.join(SAVE_DIR, f"slot_{n}.json")


def load(n: int) -> Optional[dict]:
    p = _path(n)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def save(n: int, data: dict):
    os.makedirs(SAVE_DIR, exist_ok=True)
    data = dict(data)
    data["slot"]      = n
    data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(_path(n), "w") as f:
        json.dump(data, f, indent=2)


def delete(n: int):
    p = _path(n)
    if os.path.exists(p):
        os.remove(p)


def all_slots() -> list:
    """Returns list of NUM_SLOTS items, each dict or None."""
    return [load(n) for n in range(1, NUM_SLOTS + 1)]


def new_slot(faction: str) -> dict:
    return {
        "faction":              faction,
        "mission_count":        0,
        "map_phase":            0,
        "infamy_carryover":     0,
        "credits_carryover":    500,
        "passive_income_bonus": 0,
        "lp":                   0,
        "upgrades":             {},
        "hall_of_heroes":       [],
    }


def apply_postop(slot: dict, result: dict, final_infamy: int,
                 final_credits: int, lp_earned: int) -> dict:
    """Return updated slot dict after a mission completes."""
    slot = dict(slot)
    alloc    = result.get("allocated", [0, 0, 0])
    dinf     = result.get("infamy_delta", 0)
    dcred    = result.get("credits_delta", 0)

    slot["mission_count"]        = slot.get("mission_count", 0) + 1
    slot["map_phase"]            = min(2, slot.get("map_phase", 0) + 1)
    slot["infamy_carryover"]     = max(0, final_infamy + dinf)
    # Credits silo: §150 per unit; carry over base credits + press delta
    slot["credits_carryover"]    = max(0, final_credits + dcred + alloc[0] * 150)
    # Infrastructure silo: +2§/sec per unit allocated
    slot["passive_income_bonus"] = slot.get("passive_income_bonus", 0) + alloc[1] * 2
    slot["lp"]                   = slot.get("lp", 0) + lp_earned
    return slot
