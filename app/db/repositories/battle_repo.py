"""Repository for persisted battlelog entries."""

import hashlib
import json
from datetime import datetime
from typing import Dict, List

from sqlmodel import Session, select

from app.db.database import engine
from app.db.entities import Battle as BattleEntity


def _battle_id(player_tag: str, battle_time: str, opponent_tag: str) -> str:
    """Deterministic id: Supercell battle payloads have no stable id of their own."""
    raw = f"{player_tag}|{battle_time}|{opponent_tag}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_battle_time(raw: dict) -> datetime:
    battle_time = raw.get("battleTime")
    if battle_time:
        try:
            # Supercell format: "20240115T120000.000Z"
            return datetime.strptime(battle_time, "%Y%m%dT%H%M%S.%fZ")
        except ValueError:
            pass
    return datetime.utcnow()


def _extract_result(raw: dict, player_tag: str) -> str:
    team = raw.get("team", [])
    opponent = raw.get("opponent", [])
    team_crowns = team[0].get("crowns", 0) if team else 0
    opponent_crowns = opponent[0].get("crowns", 0) if opponent else 0
    if team_crowns > opponent_crowns:
        return "win"
    if team_crowns < opponent_crowns:
        return "loss"
    return "draw"


def upsert_battles(player_tag: str, battles: List[Dict]) -> None:
    """Insert battlelog entries not already persisted for this player."""
    with Session(engine) as session:
        for raw in battles:
            opponent = raw.get("opponent", [{}])
            opponent_tag = opponent[0].get("tag") if opponent else None
            battle_time_raw = raw.get("battleTime", "")

            battle_id = _battle_id(player_tag, battle_time_raw, opponent_tag or "")
            if session.get(BattleEntity, battle_id):
                continue

            opponent_deck_ids = None
            if opponent and opponent[0].get("cards"):
                opponent_deck_ids = json.dumps(
                    [c.get("id") for c in opponent[0]["cards"] if "id" in c]
                )

            session.add(
                BattleEntity(
                    id=battle_id,
                    player_tag=player_tag,
                    battle_time=_parse_battle_time(raw),
                    result=_extract_result(raw, player_tag),
                    opponent_tag=opponent_tag,
                    opponent_deck_card_ids=opponent_deck_ids,
                    raw_json=json.dumps(raw),
                )
            )
        session.commit()


def get_recent_battles(player_tag: str, limit: int = 20) -> List[BattleEntity]:
    with Session(engine) as session:
        return list(
            session.exec(
                select(BattleEntity)
                .where(BattleEntity.player_tag == player_tag)
                .order_by(BattleEntity.battle_time.desc())
                .limit(limit)
            ).all()
        )
