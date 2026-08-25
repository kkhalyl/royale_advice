"""Unit tests for the pt-BR string rendering layer."""

import pytest
from app.analysis.issue_codes import IssueCode, StrengthCode
from app.i18n.strings_pt_br import render_issue, render_strength, ISSUE_TEMPLATES, STRENGTH_TEMPLATES


def test_every_issue_code_has_a_template():
    for code in IssueCode:
        assert code in ISSUE_TEMPLATES


def test_every_strength_code_has_a_template():
    for code in StrengthCode:
        assert code in STRENGTH_TEMPLATES


def test_render_issue_interpolates_params():
    text = render_issue(IssueCode.ELIXIR_TOO_HIGH, avg_elixir=4.9)
    assert "4.9" in text


def test_render_issue_without_params():
    text = render_issue(IssueCode.NO_WIN_CONDITION)
    assert "condição de vitória" in text.lower() or "condicao de vitoria" in text.lower()


def test_render_strength_interpolates_params():
    text = render_strength(StrengthCode.BALANCED_CURVE, avg_elixir=3.5)
    assert "3.5" in text


def test_incomplete_deck_sync_no_longer_references_sync_fix_file():
    text = render_issue(IssueCode.INCOMPLETE_DECK_SYNC, card_count=7)
    assert "SYNC_FIX" not in text
    assert "7" in text
