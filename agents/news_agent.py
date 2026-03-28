"""
JARVIS Agent — News & Sentiment v2
Fetches crypto/forex/geopolitical news from multiple sources + AI sentiment.
Now with: working RSS feeds, free crypto news API, and macro/geopolitical coverage.
"""

import feedparser
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from core.nim_client import NIMClient


# ── Working RSS feeds (tested March 2026) ──
RSS_FEEDS = {
    # Crypto
    "theblock": "https://www.theblock.co/rss.xml",
    "decrypt": "https://decrypt.co/feed",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
    # Macro / Geopolitical / Markets
    "reuters_markets": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "cnbc": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "bbc_business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "bbc_world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    # Forex / Trading
    "fxstreet": "https://www.fxstreet.com/rss",
    "dailyfx": "https://www.dailyfx.com/feeds/market-news",
    "investinglive": "https://investinglive.com/feed",
}

# Free crypto news API (no key needed)
CRYPTO_NEWS_API = "https://cryptocurrency.cv/api/news?limit=10"


class NewsAgent:
    """Fetches financial + geopolitical news and performs AI sentiment analysis."""

    def __init__(self, nim: NIMClient = None):
        self.nim = nim or NIMClient()

    def fetch_headlines(self, max_per_feed: int = 5, max_age_hours: int = 48) -> list:
        """Fetch recent headlines from all RSS feeds + crypto API."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        headlines = []

        # ── RSS Feeds ──
        for source, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                count = 0
                for entry in feed.entries:
                    if count >= max_per_feed:
                        break

                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        try:
                            published = datetime(*entry.published_parsed[:6])
                            if published < cutoff:
                                continue
                        except Exception:
                            pass

                    title = entry.get("title", "").strip()
                    if not title:
                        continue

                    headlines.append({
                        "source": source,
                        "title": title,
                        "summary": (entry.get("summary") or "")[:200],
                        "link": entry.get("link", ""),
                        "published": published.isoformat() if published else None,
                    })
                    count += 1
            except Exception as e:
                pass  # Skip broken feeds silently

        # ── Free Crypto News API ──
        try:
            req = urllib.request.Request(CRYPTO_NEWS_API, headers={"User-Agent": "JARVIS/0.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                articles = data if isinstance(data, list) else data.get("articles", data.get("data", []))
                for article in articles[:5]:
                    title = article.get("title", "").strip()
                    if title:
                        headlines.append({
                            "source": "crypto_api",
                            "title": title,
                            "summary": (article.get("description") or article.get("snippet") or "")[:200],
                            "link": article.get("url", ""),
                            "published": article.get("published_at") or article.get("pubDate"),
                        })
        except Exception:
            pass  # API might be down, that's fine

        return headlines

    def analyze_sentiment(self, headlines: list, asset: str = "BTC") -> dict:
        """Use NIM LLM to analyze sentiment of news headlines for a specific asset."""
        valid_headlines = [h for h in headlines if "error" not in h and h.get("title")]

        if not valid_headlines:
            return {"sentiment": "neutral", "score": 0, "summary": "No news available.", "impact": "low"}

        # Format headlines for LLM — include source for context
        news_text = "\n".join([
            f"[{h['source']}] {h['title']}"
            for h in valid_headlines
        ][:20])  # Max 20 headlines

        system = f"""You are JARVIS, an expert financial and geopolitical news analyst.
Analyze these news headlines for their impact on {asset} and crypto/forex markets.
Consider: geopolitical tensions (wars, sanctions, tariffs), central bank policy, 
regulatory changes, whale movements, and macro events.

Respond in JSON format ONLY:
{{
    "sentiment": "bullish" | "bearish" | "neutral",
    "score": -10 to +10 (negative=bearish, positive=bullish),
    "impact": "high" | "medium" | "low",
    "key_events": ["event1", "event2", "event3"],
    "geopolitical": "Summary of any geopolitical factors affecting markets",
    "summary": "One sentence overall market mood",
    "trade_implication": "What this means for {asset} traders right now"
}}"""

        result = self.nim.structured_ask(
            f"Analyze these headlines for {asset} impact:\n\n{news_text}",
            system=system,
        )
        return result

    def get_briefing(self, asset: str = "BTC") -> dict:
        """Full news briefing: fetch + analyze."""
        headlines = self.fetch_headlines()
        valid = [h for h in headlines if h.get("title")]
        sentiment = self.analyze_sentiment(headlines, asset)

        return {
            "asset": asset,
            "headlines_count": len(valid),
            "sources_reached": len(set(h["source"] for h in valid)),
            "sentiment_analysis": sentiment,
            "top_headlines": [
                {"source": h["source"], "title": h["title"]}
                for h in valid
            ][:10],
            "timestamp": datetime.now().isoformat(),
        }
