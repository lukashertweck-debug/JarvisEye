"""
JARVIS Agent — Strategy & Signals
Combines news + chart analysis into concrete trade signals.
Uses your trading rules (customizable).
"""

import json
from datetime import datetime
from core.nim_client import NIMClient


class StrategyAgent:
    """Combines all agent outputs into trade signals based on your strategy rules."""

    def __init__(self, nim: NIMClient = None):
        self.nim = nim or NIMClient()

        # ── YOUR STRATEGY RULES (customize these!) ──
        self.rules = {
            "min_confluence_score": 6,       # out of 10
            "require_htf_bias_match": True,  # Higher timeframe must agree
            "max_risk_pct": 0.02,            # 2% per trade
            "min_rr_ratio": 2.0,             # Minimum risk:reward
            "require_news_neutral": True,    # Don't trade against major news
            "rsi_oversold": 30,
            "rsi_overbought": 70,
        }

    def generate_signal(self, chart_analysis: dict, news_analysis: dict, symbol: str = "BTC/USDT") -> dict:
        """Generate a trade signal by combining all analyses."""

        system = f"""You are JARVIS, an autonomous trading strategist.
You receive technical analysis and news sentiment data.
Your job: determine if there's a valid trade signal.

STRATEGY RULES:
- Minimum confluence score: {self.rules['min_confluence_score']}/10
- Higher timeframe bias must align: {self.rules['require_htf_bias_match']}
- Minimum Risk:Reward ratio: {self.rules['min_rr_ratio']}
- Don't trade against high-impact bearish news when looking for longs (and vice versa)
- RSI overbought zone: >{self.rules['rsi_overbought']}, oversold: <{self.rules['rsi_oversold']}

Respond in JSON:
{{
    "signal": "LONG" | "SHORT" | "NO_TRADE",
    "confidence": 1-10,
    "entry": price or null,
    "stop_loss": price or null,
    "take_profit_1": price or null,
    "take_profit_2": price or null,
    "take_profit_3": price or null,
    "risk_reward": number or null,
    "reasoning": "Why this signal (2-3 sentences)",
    "confluence_factors": ["factor1", "factor2"],
    "warnings": ["warning1"] or [],
    "invalidation": "What would invalidate this setup"
}}"""

        # Build context from all analyses
        prompt = f"""SYMBOL: {symbol}
TIMESTAMP: {datetime.now().isoformat()}

═══ TECHNICAL ANALYSIS ═══
{json.dumps(chart_analysis, indent=2, default=str)}

═══ NEWS SENTIMENT ═══
{json.dumps(news_analysis, indent=2, default=str)}

Based on the strategy rules, generate a trade signal or recommend NO_TRADE."""

        result = self.nim.structured_ask(prompt, system=system)
        result["symbol"] = symbol
        result["timestamp"] = datetime.now().isoformat()
        return result

    def quick_bias(self, chart_analysis: dict) -> dict:
        """Quick bias check without full signal generation (for scanning)."""
        bias_data = chart_analysis.get("bias", {})
        snapshot = chart_analysis.get("snapshot", {})

        return {
            "symbol": chart_analysis.get("symbol", "?"),
            "bias": bias_data.get("bias", "UNKNOWN"),
            "confidence": bias_data.get("confidence", 0),
            "price": snapshot.get("close"),
            "rsi": bias_data.get("rsi"),
            "ema_stack": bias_data.get("ema_stack"),
            "actionable": bias_data.get("confidence", 0) >= 0.6,
        }
