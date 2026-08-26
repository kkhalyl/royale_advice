"""Clash Royale API client."""

import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import quote

from app.config import settings
from app.db.repositories import card_repo


class RoyaleAPIError(Exception):
    """Custom exception for RoyaleAPI errors."""
    pass


class RoyaleClient:
    """Async HTTP client for Clash Royale API via RoyaleAPI proxy."""
    
    def __init__(self):
        self.base_url = settings.royale_api_base
        self.api_key = settings.royale_api_key
        self._cards_cache: Optional[Dict] = None
        self._cards_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=24)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization."""
        if not self.api_key:
            raise RoyaleAPIError(
                "ROYALE_API_KEY is not configured. Set it in your .env file."
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    @staticmethod
    def normalize_tag(tag: str) -> str:
        """
        Normalize player tag.
        - Strip leading '#'
        - Uppercase
        - Return ready for URL encoding
        
        Example: "#2PP" -> "2PP"
        """
        tag = tag.lstrip("#").upper()
        return tag
    
    @staticmethod
    def _url_safe_tag(tag: str) -> str:
        """URL-encode tag for path segment (encode # as %23)."""
        normalized = RoyaleClient.normalize_tag(tag)
        # Add # back and URL encode the whole thing
        return quote(f"#{normalized}")
    
    async def _request(self, method: str, endpoint: str) -> Dict:
        """
        Make HTTP request to RoyaleAPI proxy.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/players/2PP")
        
        Returns:
            JSON response as dict
        
        Raises:
            RoyaleAPIError: If API request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        async with httpx.AsyncClient(verify=settings.verify_ssl) as client:
            try:
                response = await client.request(method, url, headers=headers, timeout=30.0)
                
                if response.status_code == 403:
                    raise RoyaleAPIError(
                        "API key invalid or proxy IP not whitelisted. "
                        "Check your ROYALE_API_KEY and ensure 45.79.218.79 is added to ALLOWED IP ADDRESSES."
                    )
                elif response.status_code == 404:
                    raise RoyaleAPIError(f"Player or resource not found: {endpoint}")
                elif response.status_code == 429:
                    raise RoyaleAPIError("Rate limit exceeded. Please retry later.")
                elif response.status_code >= 400:
                    raise RoyaleAPIError(
                        f"API error {response.status_code}: {response.text}"
                    )
                
                return response.json()
            
            except httpx.RequestError as e:
                raise RoyaleAPIError(f"Network error: {str(e)}")
            except httpx.TimeoutException:
                raise RoyaleAPIError("Request timeout. Please retry.")
    
    async def get_player(self, tag: str) -> Dict:
        """
        Fetch player profile.
        
        Args:
            tag: Player tag (with or without #)
        
        Returns:
            Player profile dict with name, trophies, current deck, etc.
        """
        normalized_tag = self.normalize_tag(tag)
        url_safe = self._url_safe_tag(normalized_tag)
        endpoint = f"/players/{url_safe}"
        
        return await self._request("GET", endpoint)
    
    async def get_player_battlelog(self, tag: str, limit: int = 20) -> List[Dict]:
        """
        Fetch player's recent battle log.

        Args:
            tag: Player tag (with or without #)
            limit: Number of recent battles to fetch (default 20)

        Returns:
            List of battle objects (opponent, deck used, result, etc.)
        """
        normalized_tag = self.normalize_tag(tag)
        url_safe = self._url_safe_tag(normalized_tag)
        endpoint = f"/players/{url_safe}/battlelog"

        battlelog = await self._request("GET", endpoint)
        return battlelog[:limit] if isinstance(battlelog, list) else []

    async def get_clan(self, tag: str) -> Dict:
        """
        Fetch clan profile.

        Args:
            tag: Clan tag (with or without #)

        Returns:
            Clan profile dict with name, member list, etc.
        """
        normalized_tag = self.normalize_tag(tag)
        url_safe = self._url_safe_tag(normalized_tag)
        endpoint = f"/clans/{url_safe}"

        return await self._request("GET", endpoint)

    async def get_cards(self, force: bool = False) -> Dict[str, Dict]:
        """
        Fetch all cards. Two-tier cache: in-memory (this process, 24h TTL)
        backed by the persisted card catalog (app/db/repositories/card_repo.py),
        which survives process restarts. Only hits the live API when both
        caches are stale, unless force=True (used by scripts/seed_cards.py
        to force a real refresh regardless of either cache tier's TTL).

        Args:
            force: Skip both cache tiers and always fetch fresh from the API.

        Returns:
            Dict mapping card ID to card details (name, elixir, rarity, type, etc.)
        """
        now = datetime.now()

        if not force:
            # Tier 1: in-memory cache for this process.
            if self._cards_cache is not None and self._cards_cache_time is not None:
                if now - self._cards_cache_time < self._cache_ttl:
                    return self._cards_cache

        # Tier 2: persisted catalog, if not stale.
        if not force and not card_repo.is_catalog_stale(self._cache_ttl):
            persisted = card_repo.get_all_cards()
            if persisted:
                cards_dict = {}
                for card in persisted:
                    cards_dict[str(card.id)] = {
                        "id": card.id,
                        "name": card.name,
                        "elixirCost": card.elixir,
                        "rarity": card.rarity,
                        "type": card.type,
                        "iconUrls": {"medium": card.icon_url} if card.icon_url else {},
                    }
                    cards_dict[card.name.lower()] = cards_dict[str(card.id)]
                self._cards_cache = cards_dict
                self._cards_cache_time = now
                return cards_dict

        # Tier 3: fetch fresh data from the live API.
        endpoint = "/cards"
        cards_list = await self._request("GET", endpoint)

        # Convert list to dict keyed by card ID or name for easier lookup
        if isinstance(cards_list, dict) and "items" in cards_list:
            cards_list = cards_list["items"]

        cards_dict = {}
        raw_cards = cards_list if isinstance(cards_list, list) else []
        for card in raw_cards:
            # Key by both ID and name for flexibility
            if "id" in card:
                cards_dict[str(card["id"])] = card
            if "name" in card:
                cards_dict[card["name"].lower()] = card

        if raw_cards:
            card_repo.upsert_cards(raw_cards)

        # Update in-memory cache
        self._cards_cache = cards_dict
        self._cards_cache_time = now

        return cards_dict


# Global client instance
_client_instance: Optional[RoyaleClient] = None


def get_client() -> RoyaleClient:
    """Get or create global RoyaleClient instance (singleton)."""
    global _client_instance
    if _client_instance is None:
        _client_instance = RoyaleClient()
    return _client_instance
