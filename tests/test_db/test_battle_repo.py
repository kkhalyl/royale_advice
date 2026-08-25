"""Unit tests for app/db/repositories/battle_repo.py."""

from app.db.repositories import battle_repo


def _raw_battle(opponent_tag="#OPP1", team_crowns=3, opponent_crowns=1, battle_time="20240115T120000.000Z"):
    return {
        "battleTime": battle_time,
        "team": [{"crowns": team_crowns}],
        "opponent": [{"tag": opponent_tag, "crowns": opponent_crowns, "cards": [{"id": 1}, {"id": 2}]}],
    }


def test_upsert_battles_inserts_rows(test_engine):
    battle_repo.upsert_battles("#ABC123", [_raw_battle()])
    battles = battle_repo.get_recent_battles("#ABC123")
    assert len(battles) == 1
    assert battles[0].result == "win"
    assert battles[0].opponent_tag == "#OPP1"


def test_upsert_battles_is_idempotent(test_engine):
    raw = _raw_battle()
    battle_repo.upsert_battles("#ABC123", [raw])
    battle_repo.upsert_battles("#ABC123", [raw])  # same battle again
    battles = battle_repo.get_recent_battles("#ABC123")
    assert len(battles) == 1


def test_upsert_battles_extracts_loss_result(test_engine):
    battle_repo.upsert_battles("#ABC123", [_raw_battle(team_crowns=0, opponent_crowns=2)])
    battles = battle_repo.get_recent_battles("#ABC123")
    assert battles[0].result == "loss"


def test_upsert_battles_extracts_draw_result(test_engine):
    battle_repo.upsert_battles("#ABC123", [_raw_battle(team_crowns=1, opponent_crowns=1)])
    battles = battle_repo.get_recent_battles("#ABC123")
    assert battles[0].result == "draw"


def test_get_recent_battles_respects_limit(test_engine):
    raws = [
        _raw_battle(opponent_tag=f"#OPP{i}", battle_time=f"2024011{i}T120000.000Z")
        for i in range(1, 6)
    ]
    battle_repo.upsert_battles("#ABC123", raws)
    battles = battle_repo.get_recent_battles("#ABC123", limit=2)
    assert len(battles) == 2


def test_get_recent_battles_scoped_to_player(test_engine):
    battle_repo.upsert_battles("#PLAYER1", [_raw_battle()])
    battle_repo.upsert_battles("#PLAYER2", [_raw_battle()])
    assert len(battle_repo.get_recent_battles("#PLAYER1")) == 1
    assert len(battle_repo.get_recent_battles("#PLAYER2")) == 1
