"""Unit tests for RoyaleAPI client."""

import pytest
from unittest.mock import AsyncMock, patch
import respx
import httpx
from app.clients.royale_client import RoyaleClient, RoyaleAPIError


@pytest.fixture
def client():
    """Create a RoyaleClient instance for testing."""
    test_client = RoyaleClient()
    test_client.api_key = "test-api-key"
    return test_client


class TestTagNormalization:
    """Test tag normalization logic."""
    
    def test_normalize_tag_with_hash(self, client):
        """Test normalizing tag with # prefix."""
        assert RoyaleClient.normalize_tag("#2PP") == "2PP"
    
    def test_normalize_tag_without_hash(self, client):
        """Test normalizing tag without # prefix."""
        assert RoyaleClient.normalize_tag("2PP") == "2PP"
    
    def test_normalize_tag_lowercase(self, client):
        """Test that tag is uppercased."""
        assert RoyaleClient.normalize_tag("abc") == "ABC"
    
    def test_normalize_tag_multiple_hashes(self, client):
        """Test tag with multiple # (edge case)."""
        assert RoyaleClient.normalize_tag("###2PP") == "2PP"


class TestUrlSafeTag:
    """Test URL-safe tag encoding."""
    
    def test_url_safe_tag_encoding(self):
        """Test that URL encoding adds encoded # prefix."""
        result = RoyaleClient._url_safe_tag("2PP")
        assert "%23" in result  # %23 is URL-encoded #


class TestGetPlayer:
    """Test get_player method."""
    
    @pytest.mark.asyncio
    async def test_get_player_success(self, client):
        """Test successful player fetch."""
        mock_response = {
            "tag": "#2PP",
            "name": "TestPlayer",
            "trophies": 5500,
            "bestTrophies": 6000,
            "wins": 1000,
            "losses": 500,
            "draws": 50,
            "currentDeck": [
                {
                    "id": 1,
                    "name": "Hog Rider",
                    "elixir": 4,
                    "rarity": "Rare",
                    "type": "troop",
                }
            ],
        }
        
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/players/%232PP").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            
            result = await client.get_player("#2PP")
            assert result["name"] == "TestPlayer"
            assert result["trophies"] == 5500


class TestGetPlayerBattlelog:
    """Test get_player_battlelog method."""
    
    @pytest.mark.asyncio
    async def test_get_battlelog_success(self, client):
        """Test successful battlelog fetch."""
        mock_battlelog = [
            {
                "result": "win",
                "opponent": {"name": "Player1"},
                "arena": {"name": "Arena1"},
            },
            {
                "result": "loss",
                "opponent": {"name": "Player2"},
                "arena": {"name": "Arena2"},
            },
        ]
        
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/players/%232PP/battlelog").mock(
                return_value=httpx.Response(200, json=mock_battlelog)
            )
            
            result = await client.get_player_battlelog("#2PP", limit=2)
            assert len(result) == 2
            assert result[0]["result"] == "win"


class TestErrorHandling:
    """Test error handling for API responses."""
    
    @pytest.mark.asyncio
    async def test_error_403_invalid_key(self, client):
        """Test 403 error (invalid API key)."""
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/players/%232PP").mock(
                return_value=httpx.Response(403, json={"error": "Forbidden"})
            )
            
            with pytest.raises(RoyaleAPIError) as exc_info:
                await client.get_player("#2PP")
            
            assert "API key invalid" in str(exc_info.value) or "not whitelisted" in str(
                exc_info.value
            )
    
    @pytest.mark.asyncio
    async def test_error_404_player_not_found(self, client):
        """Test 404 error (player not found)."""
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/players/%23INVALID").mock(
                return_value=httpx.Response(404, json={"error": "Not Found"})
            )
            
            with pytest.raises(RoyaleAPIError) as exc_info:
                await client.get_player("#INVALID")
            
            assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_error_429_rate_limit(self, client):
        """Test 429 error (rate limited)."""
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/players/%232PP").mock(
                return_value=httpx.Response(429, json={"error": "Too Many Requests"})
            )
            
            with pytest.raises(RoyaleAPIError) as exc_info:
                await client.get_player("#2PP")
            
            assert "rate limit" in str(exc_info.value).lower()


class TestCaching:
    """Test card caching mechanism."""
    
    @pytest.mark.asyncio
    async def test_cards_cached(self, client):
        """Test that cards are cached after first fetch."""
        mock_cards = [
            {"id": 1, "name": "Hog Rider", "elixir": 4, "rarity": "Rare"},
            {"id": 2, "name": "Fireball", "elixir": 4, "rarity": "Rare"},
        ]
        
        with respx.mock:
            respx.get("https://proxy.royaleapi.dev/v1/cards").mock(
                return_value=httpx.Response(200, json=mock_cards)
            )
            
            # First call
            result1 = await client.get_cards()
            
            # Second call should use cache
            result2 = await client.get_cards()
            
            assert result1 == result2
