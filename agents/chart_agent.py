"""
JARVIS Agent — Chart / Technical Analysis
Fetches market data, runs indicators, and uses NIM LLM for pattern interpretation.
"""

import json
from core.nim_client import NIMClient
from core.market_data import MarketData
from utils.indicators import add_all_indicators, detect_bias, find_support_resistance, get_snapshot


class ChartAgent:
    """Technical analysis agent that combines indicators with AI reasoning."""

    def __init__(self, nim: NIMClient = None, market: MarketData = None):
        self.nim = nim or NIMClient()
        self.market = market or MarketData()

    def analyze(self, symbol: str = "BTC/USDT", timeframe: str = "1h") -> dict:
        """Full technical analysis for a symbol/timeframe."""
        # 1. Get raw data
        df = self.market.get_ohlcv(symbol, timeframe, limit=200)

        # 2. Add indicators
        df = add_all_indicators(df)

        # 3. Extract key metrics
        bias = detect_bias(df)
        sr = find_support_resistance(df)
        snapshot = get_snapshot(df)

        # 4. LLM interpretation
        interpretation = self._interpret(symbol, timeframe, snapshot, bias, sr)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "snapshot": snapshot,
            "bias": bias,
            "support_resistance": sr,
            "interpretation": interpretation,
        }

    def multi_timeframe_analysis(self, symbol: str = "BTC/USDT") -> dict:
        """Analyze across multiple timeframes for confluence."""
        timeframes = ["15m", "1h", "4h", "1d"]
        analyses = {}

        for tf in timeframes:
            try:
                df = self.market.get_ohlcv(symbol, tf, limit=200)
                df = add_all_indicators(df)
                analyses[tf] = {
                    "bias": detect_bias(df),
                    "sr": find_support_resistance(df),
                    "snapshot": get_snapshot(df),
                }
            except Exception as e:
                analyses[tf] = {"error": str(e)}

        # LLM confluence analysis
        confluence = self._confluence_check(symbol, analyses)

        return {
            "symbol": symbol,
            "timeframes": analyses,
            "confluence": confluence,
        }

    def _interpret(self, symbol: str, timeframe: str, snapshot: dict, bias: dict, sr: dict) -> str:
        """Use NIM LLM to interpret the technical data."""
        system = """You are JARVIS, an expert technical analyst and scalper. 
You analyze market data and provide clear, actionable insights.
Be direct, precise, and confident. Use trader language.
Keep response under 150 words."""

        prompt = f"""Analyze {symbol} on the {timeframe} chart:

Price: {snapshot['close']} ({snapshot['candle']} candle, {snapshot['change_pct']}%)
Bias: {bias['bias']} (confidence: {bias['confidence']})
EMA Stack: {bias['ema_stack']}
RSI: {bias.get('rsi')} ({bias.get('rsi_zone')})
MACD: {snapshot.get('macd')} / Signal: {snapshot.get('macd_signal')}
ATR: {snapshot.get('atr')}

Key Levels:
- Resistance: {sr['resistance_1']}, {sr['resistance_2']}
- Support: {sr['support_1']}, {sr['support_2']}
- Recent Range: {sr['recent_low']} — {sr['recent_high']}

What's the play? Give me bias, key levels to watch, and what would confirm a trade."""

        return self.nim.ask(prompt, system=system)

    def _confluence_check(self, symbol: str, analyses: dict) -> str:
        """Use LLM to check multi-timeframe confluence."""
        system = """You are JARVIS, expert at multi-timeframe confluence analysis.
Analyze alignment across timeframes. Be concise and actionable.
Format: State the confluence (or lack of), the highest-probability direction, 
and what would be the ideal entry setup. Under 200 words."""

        # Build summary of each timeframe
        tf_summary = []
        for tf, data in analyses.items():
            if "error" in data:
                continue
            b = data["bias"]
            tf_summary.append(f"{tf}: Bias={b['bias']}, RSI={b.get('rsi')}, EMA Stack={b['ema_stack']}")

        prompt = f"""Multi-timeframe analysis for {symbol}:

{chr(10).join(tf_summary)}

Is there confluence? What's the highest probability trade?"""

        return self.nim.ask(prompt, system=system)
