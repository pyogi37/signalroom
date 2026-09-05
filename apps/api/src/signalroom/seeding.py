"""Seed the room list with bundled synthetic fixtures from recorded model runs.

Seeding always uses replay mode so a fresh start never spends money. A
fixture without recordings is skipped and reported, never run live.
"""

import logging

from .fixtures import load_fixtures
from .persistence import get_room, log_event, save_room
from .workflow import start_room, to_room

log = logging.getLogger("signalroom.seeding")


def seed_rooms() -> dict[str, list[str]]:
    seeded: list[str] = []
    skipped: list[str] = []
    for fixture in load_fixtures():
        if not fixture.seed or get_room(fixture.id):
            continue
        state = start_room(fixture.id, fixture.organization, fixture.industry, fixture.transcript, model_mode="replay")
        if state.get("error"):
            skipped.append(fixture.id)
            log.info("Skipped seeding %s: %s", fixture.id, state.get("error"))
            continue
        room = to_room(state, fixture=fixture.id)
        save_room(room)
        log_event(room.id, "room_seeded", {"fixture": fixture.id, "metrics": room.metrics})
        seeded.append(fixture.id)
    return {"seeded": seeded, "skipped": skipped}
