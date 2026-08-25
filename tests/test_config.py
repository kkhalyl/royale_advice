"""Unit tests for app/config.py Settings."""

from app.config import Settings


def test_cors_allow_origins_wildcard_in_debug():
    settings = Settings(debug=True, cors_origins="http://example.com")
    assert settings.cors_allow_origins == ["*"]


def test_cors_allow_origins_explicit_list_when_not_debug():
    settings = Settings(debug=False, cors_origins="http://a.com, http://b.com")
    assert settings.cors_allow_origins == ["http://a.com", "http://b.com"]


def test_cors_allow_origins_empty_string_yields_empty_list():
    settings = Settings(debug=False, cors_origins="")
    assert settings.cors_allow_origins == []
