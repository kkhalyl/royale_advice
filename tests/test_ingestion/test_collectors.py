"""Unit tests for ingestion/collectors.py - mocks search_subreddit, no network."""

from unittest.mock import patch

from ingestion import collectors


def _hit(query):
    return {"id": f"t3_{query}", "subreddit": "x", "title": query, "body": "", "score": 1}


@patch("ingestion.collectors.search_subreddit")
def test_collect_for_card_searches_every_subreddit(mock_search):
    mock_search.side_effect = lambda reddit, subreddit, query, limit=15: [_hit(query)]

    results = collectors.collect_for_card(reddit=None, card_name="Hog Rider", limit=10)

    # 3 subreddits x 2 query variants = 6 calls
    assert mock_search.call_count == len(collectors.SUBREDDITS) * 2
    assert len(results) == 6
    called_subreddits = {call.args[1] for call in mock_search.call_args_list}
    assert called_subreddits == set(collectors.SUBREDDITS)


@patch("ingestion.collectors.search_subreddit")
def test_collect_for_archetype_uses_keyword_queries(mock_search):
    mock_search.return_value = []

    collectors.collect_for_archetype(reddit=None, archetype="cycle", limit=10)

    called_queries = {call.args[2] for call in mock_search.call_args_list}
    assert "cycle deck" in called_queries


@patch("ingestion.collectors.search_subreddit")
def test_collect_for_archetype_falls_back_to_archetype_name_for_unknown(mock_search):
    mock_search.return_value = []

    collectors.collect_for_archetype(reddit=None, archetype="bridge_spam", limit=10)

    called_queries = {call.args[2] for call in mock_search.call_args_list}
    assert "bridge_spam" in called_queries


@patch("ingestion.collectors.search_subreddit")
def test_collect_for_king_levels_searches_all_level_queries(mock_search):
    mock_search.return_value = []

    collectors.collect_for_king_levels(reddit=None, limit=10)

    expected_calls = len(collectors.SUBREDDITS) * len(collectors.KING_LEVEL_QUERIES)
    assert mock_search.call_count == expected_calls
