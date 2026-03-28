"""
JARVIS Utils — Technical Analysis
Calculates common indicators on OHLCV DataFrames.
"""

import pandas as pd
import numpy as np
import ta


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add a comprehensive set of technical indicators to OHLCV DataFrame."""
    d = df.copy()

    # ── Trend ──
    d["ema_9"] = ta.trend.ema_indicator(d["close"], window=9)
    d["ema_21"] = ta.trend.ema_indicator(d["close"], window=21)
    d["ema_50"] = ta.trend.ema_indicator(d["close"], window=50)
    d["ema_200"] = ta.trend.ema_indicator(d["close"], window=200)
    d["sma_20"] = ta.trend.sma_indicator(d["close"], window=20)

    # ── Momentum ──
    d["rsi"] = ta.momentum.rsi(d["close"], window=14)
    d["stoch_k"] = ta.momentum.stoch(d["high"], d["low"], d["close"], window=14, smooth_window=3)
    d["stoch_d"] = ta.momentum.stoch_signal(d["high"], d["low"], d["close"], window=14, smooth_window=3)
    macd = ta.trend.MACD(d["close"])
    d["macd"] = macd.macd()
    d["macd_signal"] = macd.macd_signal()
    d["macd_hist"] = macd.macd_diff()

    # ── Volatility ──
    bb = ta.volatility.BollingerBands(d["close"], window=20, window_dev=2)
    d["bb_upper"] = bb.bollinger_hband()
    d["bb_lower"] = bb.bollinger_lband()
    d["bb_mid"] = bb.bollinger_mavg()
    d["atr"] = ta.volatility.average_true_range(d["high"], d["low"], d["close"], window=14)

    # ── Volume ──
    d["vwap"] = (d["volume"] * (d["high"] + d["low"] + d["close"]) / 3).cumsum() / d["volume"].cumsum()
    d["obv"] = ta.volume.on_balance_volume(d["close"], d["volume"])

    return d


def detect_bias(df: pd.DataFrame) -> dict:
    """Determine market bias based on EMA stack and structure."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = latest["close"]
    ema_9 = latest.get("ema_9")
    ema_21 = latest.get("ema_21")
    ema_50 = latest.get("ema_50")
    ema_200 = latest.get("ema_200")
    rsi = latest.get("rsi")

    # EMA stack alignment
    bullish_stack = ema_9 and ema_21 and ema_50 and (ema_9 > ema_21 > ema_50)
    bearish_stack = ema_9 and ema_21 and ema_50 and (ema_9 < ema_21 < ema_50)

    # Price vs 200 EMA
    above_200 = price > ema_200 if ema_200 else None

    # RSI context
    rsi_zone = "neutral"
    if rsi:
        if rsi > 70:
            rsi_zone = "overbought"
        elif rsi < 30:
            rsi_zone = "oversold"
        elif rsi > 55:
            rsi_zone = "bullish"
        elif rsi < 45:
            rsi_zone = "bearish"

    # Determine overall bias
    if bullish_stack and above_200:
        bias = "BULLISH"
        confidence = 0.8
    elif bearish_stack and not above_200:
        bias = "BEARISH"
        confidence = 0.8
    elif bullish_stack or above_200:
        bias = "LEAN BULLISH"
        confidence = 0.5
    elif bearish_stack or not above_200:
        bias = "LEAN BEARISH"
        confidence = 0.5
    else:
        bias = "NEUTRAL"
        confidence = 0.3

    return {
        "bias": bias,
        "confidence": confidence,
        "price": round(price, 2),
        "ema_9": round(ema_9, 2) if ema_9 else None,
        "ema_21": round(ema_21, 2) if ema_21 else None,
        "ema_50": round(ema_50, 2) if ema_50 else None,
        "ema_200": round(ema_200, 2) if ema_200 else None,
        "rsi": round(rsi, 1) if rsi else None,
        "rsi_zone": rsi_zone,
        "ema_stack": "bullish" if bullish_stack else ("bearish" if bearish_stack else "mixed"),
    }


def find_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """Find key support and resistance levels from recent price action."""
    recent = df.tail(window)
    highs = recent["high"]
    lows = recent["low"]

    # Simple pivot-based S/R
    pivot = (recent.iloc[-1]["high"] + recent.iloc[-1]["low"] + recent.iloc[-1]["close"]) / 3
    r1 = 2 * pivot - recent.iloc[-1]["low"]
    s1 = 2 * pivot - recent.iloc[-1]["high"]
    r2 = pivot + (recent.iloc[-1]["high"] - recent.iloc[-1]["low"])
    s2 = pivot - (recent.iloc[-1]["high"] - recent.iloc[-1]["low"])

    return {
        "pivot": round(pivot, 2),
        "resistance_1": round(r1, 2),
        "resistance_2": round(r2, 2),
        "support_1": round(s1, 2),
        "support_2": round(s2, 2),
        "recent_high": round(highs.max(), 2),
        "recent_low": round(lows.min(), 2),
    }


def get_snapshot(df: pd.DataFrame) -> dict:
    """Create a compact snapshot of the latest candle + indicators for LLM context."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    snapshot = {
        "close": round(latest["close"], 2),
        "open": round(latest["open"], 2),
        "high": round(latest["high"], 2),
        "low": round(latest["low"], 2),
        "volume": round(latest["volume"], 2),
        "candle": "green" if latest["close"] > latest["open"] else "red",
        "change_pct": round((latest["close"] - prev["close"]) / prev["close"] * 100, 3),
    }

    # Add indicators if they exist
    for col in ["ema_9", "ema_21", "ema_50", "ema_200", "rsi", "macd", "macd_signal",
                "bb_upper", "bb_lower", "atr", "vwap", "stoch_k", "stoch_d"]:
        if col in latest and pd.notna(latest[col]):
            snapshot[col] = round(latest[col], 2)

    return snapshot
