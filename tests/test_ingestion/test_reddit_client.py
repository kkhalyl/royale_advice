"""Unit tests for ingestion/reddit_client.py - no live Reddit calls."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ingestion.reddit_client import RedditClientError, build_reddit_client, search_subreddit


def test_build_reddit_client_raises_without_credentials(monkeypatch):
    monkeypatch.setattr("ingestion.reddit_client.settings.reddit_client_id", None)
    monkeypatch.setattr("ingestion.reddit_client.settings.reddit_client_secret", None)
    with pytest.raises(RedditClientError):
        build_reddit_client()


def test_build_reddit_client_constructs_when_configured(monkeypatch):
    monkeypatch.setattr("ingestion.reddit_client.settings.reddit_client_id", "id")
    monkeypatch.setattr("ingestion.reddit_client.settings.reddit_client_secret", "secret")
    monkeypatch.setattr("ingestion.reddit_client.settings.reddit_user_agent", "test-agent")

    with patch("praw.Reddit") as mock_ctor:
        build_reddit_client()

    mock_ctor.assert_called_once_with(
        client_id="id", client_secret="secret", user_agent="test-agent", read_only=True
    )


def _fake_submission(id_="abc123", subreddit="ClashRoyale", title="Great tips", body="use them", score=10):
    return SimpleNamespace(
        id=id_,
        subreddit=subreddit,
        title=title,
        selftext=body,
        score=score,
        created_utc=1700000000.0,
        permalink=f"/r/{subreddit}/comments/{id_}/",
    )


def test_search_subreddit_returns_plain_dicts():
    fake_reddit = MagicMock()
    fake_reddit.subreddit.return_value.search.return_value = [_fake_submission()]

    results = search_subreddit(fake_reddit, "ClashRoyale", "hog rider tips")

    assert len(results) == 1
    hit = results[0]
    assert hit["id"] == "t3_abc123"
    assert hit["subreddit"] == "ClashRoyale"
    assert hit["title"] == "Great tips"
    assert hit["body"] == "use them"
    assert hit["score"] == 10
    assert hit["url"].startswith("https://reddit.com/r/ClashRoyale")


def test_search_subreddit_handles_empty_selftext():
    submission = _fake_submission(body="")
    fake_reddit = MagicMock()
    fake_reddit.subreddit.return_value.search.return_value = [submission]

    results = search_subreddit(fake_reddit, "ClashRoyale", "query")
    assert results[0]["body"] == ""


def test_search_subreddit_returns_empty_list_on_error():
    fake_reddit = MagicMock()
    fake_reddit.subreddit.side_effect = Exception("network down")

    results = search_subreddit(fake_reddit, "ClashRoyale", "query")
    assert results == []
