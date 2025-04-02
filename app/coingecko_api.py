#!/usr/bin/env python3
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
import json
import time

class CoinGeckoAPI:
    """
    A client for interacting with the CoinGecko Pro API.
    Uses rate limiting to avoid hitting API limits.
    """
    
    BASE_URL = "https://pro-api.coingecko.com/api/v3"
    
    def __init__(self, api_key: str):
        """
        Initialize the CoinGecko API client.
        
        Args:
            api_key: Required CoinGecko Pro API key
        """
        if not api_key:
            raise ValueError("API key is required for CoinGecko Pro API")
            
        self.session = None
        self.last_request_time = 0
        self.api_key = api_key
        self.rate_limit_delay = 0.05  # 20 requests per second for Pro API
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a rate-limited request to the CoinGecko API."""
        # Apply rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last_request)
        
        self.last_request_time = time.time()
        
        # Prepare request parameters
        params = params or {}
        headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": self.api_key
        }
        
        # Make the request
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise Exception("Rate limit exceeded. Try again later.")
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error ({response.status}): {error_text}")
        except Exception as e:
            raise Exception(f"Error making request to {url}: {str(e)}")
    
    async def get_coin_list(self) -> List[Dict[str, Any]]:
        """Get a list of all available coins."""
        return await self._make_request("coins/list")
    
    async def get_coin_id(self, name: str) -> Optional[str]:
        """Find a coin's ID by its name."""
        coins = await self.get_coin_list()
        for coin in coins:
            if coin["name"].lower() == name.lower() or coin["symbol"].lower() == name.lower():
                return coin["id"]
        return None
    
    async def get_price(self, coin_id: str, vs_currencies: List[str] = ["usd"]) -> Dict[str, Any]:
        """Get the current price of a coin in specified currencies."""
        return await self._make_request(
            "simple/price",
            {
                "ids": coin_id,
                "vs_currencies": ",".join(vs_currencies),
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
        )
    
    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """Get detailed data for a specific coin."""
        return await self._make_request(f"coins/{coin_id}", {"localization": "false"})
    
    async def get_coin_market_chart(self, coin_id: str, days: int = 30) -> Dict[str, Any]:
        """Get historical market data for a coin."""
        return await self._make_request(
            f"coins/{coin_id}/market_chart",
            {"vs_currency": "usd", "days": str(days)}
        )

async def get_coin_info(coin_name: str, api_key: str) -> Dict[str, Any]:
    """
    Helper function to get comprehensive information about a coin.
    Returns a formatted dictionary with key information.
    
    Args:
        coin_name: Name or symbol of the coin to query
        api_key: CoinGecko Pro API key (required)
    """
    if not api_key:
        return {"error": "CoinGecko Pro API key is required"}
        
    async with CoinGeckoAPI(api_key=api_key) as api:
        try:
            # Get the coin ID
            coin_id = await api.get_coin_id(coin_name)
            if not coin_id:
                return {"error": f"Coin '{coin_name}' not found"}
            
            # Get current price data
            price_data = await api.get_price(coin_id, ["usd", "btc", "eth"])
            
            # Get detailed coin information
            coin_details = await api.get_coin_data(coin_id)
            
            # Get market chart data (last 30 days)
            market_data = await api.get_coin_market_chart(coin_id, 30)
            
            # Format the response
            result = {
                "name": coin_details.get("name", coin_name),
                "symbol": coin_details.get("symbol", "").upper(),
                "current_price": price_data.get(coin_id, {}).get("usd", "Unknown"),
                "market_cap": price_data.get(coin_id, {}).get("usd_market_cap", "Unknown"),
                "price_change_24h": price_data.get(coin_id, {}).get("usd_24h_change", "Unknown"),
                "current_btc_price": price_data.get(coin_id, {}).get("btc", "Unknown"),
                "current_eth_price": price_data.get(coin_id, {}).get("eth", "Unknown"),
                "market_rank": coin_details.get("market_cap_rank", "Unknown"),
                "description": coin_details.get("description", {}).get("en", "No description available").replace("<a href=", "<a "),
                "blockchain": coin_details.get("asset_platform_id", "Native"),
                "genesis_date": coin_details.get("genesis_date", "Unknown"),
                "homepage": coin_details.get("links", {}).get("homepage", [""])[0] if coin_details.get("links", {}).get("homepage") else "",
                "github": coin_details.get("links", {}).get("repos_url", {}).get("github", []) if coin_details.get("links", {}).get("repos_url") else [],
                "sentiment": coin_details.get("sentiment_votes_up_percentage", 0),
                "last_updated": price_data.get(coin_id, {}).get("last_updated_at", 0),
                "price_history": {
                    "prices": market_data.get("prices", [])[-7:],  # Last 7 days of prices
                    "last_updated": "Last 7 days (USD)"
                }
            }
            
            return result
        except Exception as e:
            return {"error": f"Error fetching data: {str(e)}"}

# Example usage
if __name__ == "__main__":
    import sys
    import os
    
    async def main():
        # Get API key from environment variable
        api_key = os.environ.get("COINGECKO_API_KEY")
        
        if not api_key:
            print("Error: COINGECKO_API_KEY environment variable must be set")
            sys.exit(1)
            
        if len(sys.argv) > 1:
            coin_name = sys.argv[1]
            print(f"Fetching data for {coin_name}...")
            result = await get_coin_info(coin_name, api_key)
            print(json.dumps(result, indent=2))
        else:
            print("Please provide a coin name as an argument")
    
    asyncio.run(main()) 