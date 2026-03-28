"""
JARVIS Core — Market Data via CCXT
Fetches OHLCV, ticker, and orderbook data from 100+ exchanges.
Phase 1: Read-only (no trading).
"""

import os
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class MarketData:
    """Fetches market data from exchanges via CCXT."""

    def __init__(self, exchange_id: str = None):
        exchange_id = exchange_id or os.getenv("EXCHANGE", "bybit")
        exchange_class = getattr(ccxt, exchange_id, None)
        if not exchange_class:
            raise ValueError(f"Exchange '{exchange_id}' not found in CCXT")

        self.exchange = exchange_class({
            "enableRateLimit": True,
            # API keys only needed for trading (Phase 4)
            # "apiKey": os.getenv("EXCHANGE_API_KEY"),
            # "secret": os.getenv("EXCHANGE_SECRET"),
        })
        self.exchange.load_markets()

    def get_ohlcv(self, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV candle data as a DataFrame."""
        raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df

    def get_ticker(self, symbol: str = "BTC/USDT") -> dict:
        """Get current price and 24h stats."""
        t = self.exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "price": t.get("last"),
            "bid": t.get("bid"),
            "ask": t.get("ask"),
            "high_24h": t.get("high"),
            "low_24h": t.get("low"),
            "volume_24h": t.get("baseVolume"),
            "change_pct": t.get("percentage"),
            "timestamp": datetime.now().isoformat(),
        }

    def get_multi_ticker(self, symbols: list = None) -> list:
        """Get tickers for multiple symbols."""
        if symbols is None:
            watchlist = os.getenv("WATCHLIST", "BTC/USDT,ETH/USDT")
            symbols = [s.strip() for s in watchlist.split(",")]
        return [self.get_ticker(s) for s in symbols]

    def get_orderbook(self, symbol: str = "BTC/USDT", limit: int = 10) -> dict:
        """Get orderbook (bids/asks) for liquidity analysis."""
        ob = self.exchange.fetch_order_book(symbol, limit=limit)
        return {
            "symbol": symbol,
            "bids": ob["bids"][:limit],  # [[price, amount], ...]
            "asks": ob["asks"][:limit],
            "spread": ob["asks"][0][0] - ob["bids"][0][0] if ob["asks"] and ob["bids"] else None,
            "bid_wall": max(ob["bids"], key=lambda x: x[1]) if ob["bids"] else None,
            "ask_wall": max(ob["asks"], key=lambda x: x[1]) if ob["asks"] else None,
        }

    def get_multi_timeframe(self, symbol: str = "BTC/USDT", timeframes: list = None, limit: int = 50) -> dict:
        """Get OHLCV data across multiple timeframes for confluence analysis."""
        if timeframes is None:
            timeframes = ["15m", "1h", "4h", "1d"]
        result = {}
        for tf in timeframes:
            try:
                result[tf] = self.get_ohlcv(symbol, tf, limit)
            except Exception as e:
                result[tf] = f"Error: {e}"
        return result
