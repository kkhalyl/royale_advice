"""Unit tests for app/db/repositories/tip_repo.py."""

from datetime import datetime, timedelta

from app.db.repositories import tip_repo


def _future(days=30):
    return datetime.utcnow() + timedelta(days=days)


def _past(days=1):
    return datetime.utcnow() - timedelta(days=days)


def test_upsert_tip_creates_row(test_engine):
    tip = tip_repo.upsert_tip(
        subject_type="card",
        subject_key="Hog Rider",
        text="Use hog rider com feitiço leve para ciclar.",
        stale_after=_future(),
    )
    assert tip.id is not None
    assert tip.subject_key == "hog rider"  # normalized lowercase


def test_get_tips_for_matches_card_name(test_engine):
    tip_repo.upsert_tip(
        subject_type="card", subject_key="hog rider", text="Dica A", stale_after=_future()
    )
    tips = tip_repo.get_tips_for(card_names=["Hog Rider"])
    assert len(tips) == 1
    assert tips[0].text == "Dica A"


def test_get_tips_for_matches_archetype(test_engine):
    tip_repo.upsert_tip(
        subject_type="archetype", subject_key="cycle", text="Dica de ciclo", stale_after=_future()
    )
    tips = tip_repo.get_tips_for(archetype="cycle")
    assert len(tips) == 1


def test_get_tips_for_excludes_stale_tips(test_engine):
    tip_repo.upsert_tip(
        subject_type="card", subject_key="hog rider", text="Velha", stale_after=_past()
    )
    tips = tip_repo.get_tips_for(card_names=["Hog Rider"])
    assert tips == []


def test_get_tips_for_filters_by_king_level_range(test_engine):
    tip_repo.upsert_tip(
        subject_type="card",
        subject_key="hog rider",
        text="Só para nível alto",
        stale_after=_future(),
        king_level_min=12,
        king_level_max=15,
    )
    assert tip_repo.get_tips_for(card_names=["Hog Rider"], king_level=13) != []
    assert tip_repo.get_tips_for(card_names=["Hog Rider"], king_level=5) == []


def test_get_tips_for_ranks_by_confidence(test_engine):
    tip_repo.upsert_tip(
        subject_type="card", subject_key="hog rider", text="Baixa confiança",
        stale_after=_future(), confidence=0.2,
    )
    tip_repo.upsert_tip(
        subject_type="card", subject_key="hog rider", text="Alta confiança",
        stale_after=_future(), confidence=0.9,
    )
    tips = tip_repo.get_tips_for(card_names=["Hog Rider"])
    assert tips[0].text == "Alta confiança"


def test_get_tips_for_returns_empty_without_subject(test_engine):
    assert tip_repo.get_tips_for() == []


def test_get_tips_for_respects_limit(test_engine):
    for i in range(10):
        tip_repo.upsert_tip(
            subject_type="card", subject_key="hog rider", text=f"Dica {i}", stale_after=_future()
        )
    tips = tip_repo.get_tips_for(card_names=["Hog Rider"], limit=3)
    assert len(tips) == 3
