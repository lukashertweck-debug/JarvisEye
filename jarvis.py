#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║          J.A.R.V.I.S. v0.1              ║
║   Just A Rather Very Intelligent System  ║
║        Trading Agent Platform            ║
╚══════════════════════════════════════════╝

Phase 1: Foundation — All agents running, read-only market data.
Start: python jarvis.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import box

from core.nim_client import NIMClient
from core.market_data import MarketData
from agents.news_agent import NewsAgent
from agents.chart_agent import ChartAgent
from agents.strategy_agent import StrategyAgent

console = Console()


def print_banner():
    console.print(Panel(
        "[bold cyan]J.A.R.V.I.S.[/bold cyan] v0.1\n"
        "[dim]Just A Rather Very Intelligent System[/dim]\n"
        "[dim]Trading Agent Platform — Phase 1[/dim]\n\n"
        "[bold green]✓[/bold green] NVIDIA NIM (free LLM)  "
        "[bold green]✓[/bold green] CCXT (market data)  "
        "[bold green]✓[/bold green] TA (indicators)",
        title="[bold white]🤖 JARVIS ONLINE[/bold white]",
        border_style="cyan",
        box=box.DOUBLE,
    ))


def print_help():
    table = Table(title="Available Commands", box=box.ROUNDED, border_style="cyan")
    table.add_column("Command", style="bold cyan")
    table.add_column("Description")

    commands = [
        ("briefing", "Full morning briefing (news + chart + signal)"),
        ("price <SYM>", "Current price & 24h stats (e.g. 'price BTC/USDT')"),
        ("chart <SYM>", "Technical analysis for a symbol"),
        ("mtf <SYM>", "Multi-timeframe confluence analysis"),
        ("news", "Latest news + sentiment analysis"),
        ("signal <SYM>", "Full trade signal (chart + news + strategy)"),
        ("scan", "Quick bias scan of your entire watchlist"),
        ("ask <question>", "Ask JARVIS anything about markets"),
        ("help", "Show this help"),
        ("exit", "Shutdown JARVIS"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)


def cmd_price(market: MarketData, symbol: str):
    """Show current price and 24h stats."""
    ticker = market.get_ticker(symbol)
    color = "green" if (ticker.get("change_pct") or 0) >= 0 else "red"

    table = Table(title=f"📊 {symbol}", box=box.ROUNDED, border_style=color)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right", style=f"bold {color}")

    table.add_row("Price", f"${ticker['price']:,.2f}")
    table.add_row("24h Change", f"{ticker.get('change_pct', 0):+.2f}%")
    table.add_row("24h High", f"${ticker.get('high_24h', 0):,.2f}")
    table.add_row("24h Low", f"${ticker.get('low_24h', 0):,.2f}")
    table.add_row("Bid / Ask", f"${ticker.get('bid', 0):,.2f} / ${ticker.get('ask', 0):,.2f}")
    table.add_row("Volume (24h)", f"{ticker.get('volume_24h', 0):,.0f}")

    console.print(table)


def cmd_chart(chart_agent: ChartAgent, symbol: str, timeframe: str = "1h"):
    """Run technical analysis."""
    with console.status(f"[cyan]JARVIS analyzing {symbol} {timeframe} chart...[/cyan]"):
        analysis = chart_agent.analyze(symbol, timeframe)

    # Bias panel
    bias = analysis["bias"]
    bias_color = {"BULLISH": "green", "LEAN BULLISH": "green", "BEARISH": "red", "LEAN BEARISH": "red"}.get(bias["bias"], "yellow")
    console.print(Panel(
        f"[bold {bias_color}]{bias['bias']}[/bold {bias_color}] "
        f"(confidence: {bias['confidence']:.0%})\n"
        f"EMA Stack: {bias['ema_stack']} | RSI: {bias.get('rsi')} ({bias.get('rsi_zone')})",
        title=f"📈 {symbol} {timeframe} Bias",
        border_style=bias_color,
    ))

    # S/R levels
    sr = analysis["support_resistance"]
    table = Table(title="Key Levels", box=box.SIMPLE)
    table.add_column("Level", style="dim")
    table.add_column("Price", justify="right")
    table.add_row("[red]Resistance 2[/red]", f"${sr['resistance_2']:,.2f}")
    table.add_row("[red]Resistance 1[/red]", f"${sr['resistance_1']:,.2f}")
    table.add_row("[bold]Pivot[/bold]", f"${sr['pivot']:,.2f}")
    table.add_row("[green]Support 1[/green]", f"${sr['support_1']:,.2f}")
    table.add_row("[green]Support 2[/green]", f"${sr['support_2']:,.2f}")
    console.print(table)

    # LLM Interpretation
    console.print(Panel(
        analysis["interpretation"],
        title="🤖 JARVIS Analysis",
        border_style="cyan",
    ))


def cmd_mtf(chart_agent: ChartAgent, symbol: str):
    """Multi-timeframe confluence analysis."""
    with console.status(f"[cyan]JARVIS running multi-timeframe analysis on {symbol}...[/cyan]"):
        result = chart_agent.multi_timeframe_analysis(symbol)

    table = Table(title=f"🔍 MTF Confluence — {symbol}", box=box.ROUNDED, border_style="cyan")
    table.add_column("TF", style="bold")
    table.add_column("Bias")
    table.add_column("RSI", justify="right")
    table.add_column("EMA Stack")
    table.add_column("Conf.", justify="right")

    for tf, data in result["timeframes"].items():
        if "error" in data:
            table.add_row(tf, f"[red]Error[/red]", "-", "-", "-")
            continue
        b = data["bias"]
        color = {"BULLISH": "green", "LEAN BULLISH": "green", "BEARISH": "red", "LEAN BEARISH": "red"}.get(b["bias"], "yellow")
        table.add_row(
            tf,
            f"[{color}]{b['bias']}[/{color}]",
            str(b.get("rsi", "-")),
            b.get("ema_stack", "-"),
            f"{b['confidence']:.0%}",
        )

    console.print(table)
    console.print(Panel(result["confluence"], title="🤖 Confluence Analysis", border_style="cyan"))


def cmd_news(news_agent: NewsAgent, asset: str = "BTC"):
    """News briefing with sentiment."""
    with console.status(f"[cyan]JARVIS scanning news for {asset}...[/cyan]"):
        briefing = news_agent.get_briefing(asset)

    sentiment = briefing.get("sentiment_analysis", {})

    # Handle both parsed and unparsed sentiment
    if isinstance(sentiment, dict) and "error" not in sentiment:
        score = sentiment.get("score", 0)
        sent_label = sentiment.get("sentiment", "neutral")
        color = "green" if score > 0 else ("red" if score < 0 else "yellow")

        console.print(Panel(
            f"Sentiment: [{color}][bold]{sent_label.upper()}[/bold] ({score:+d}/10)[/{color}]\n"
            f"Impact: {sentiment.get('impact', '?')}\n"
            f"Summary: {sentiment.get('summary', 'N/A')}\n"
            f"Trade Implication: {sentiment.get('trade_implication', 'N/A')}",
            title=f"📰 News Briefing — {asset}",
            border_style=color,
        ))

        events = sentiment.get("key_events", [])
        if events:
            console.print("[bold]Key Events:[/bold]")
            for e in events:
                console.print(f"  • {e}")
    else:
        console.print(Panel(str(sentiment), title=f"📰 News — {asset}", border_style="yellow"))

    # Headlines
    console.print(f"\n[dim]Latest {briefing['headlines_count']} headlines analyzed[/dim]")
    for h in briefing.get("top_headlines", [])[:5]:
        console.print(f"  [dim]{h['source']}[/dim] {h['title']}")


def cmd_signal(chart_agent: ChartAgent, news_agent: NewsAgent, strategy_agent: StrategyAgent, symbol: str):
    """Full signal generation."""
    with console.status(f"[cyan]JARVIS generating signal for {symbol}...[/cyan]"):
        chart = chart_agent.analyze(symbol, "1h")
        asset = symbol.split("/")[0]
        news = news_agent.get_briefing(asset)
        signal = strategy_agent.generate_signal(chart, news.get("sentiment_analysis", {}), symbol)

    if isinstance(signal, dict) and "error" not in signal:
        sig = signal.get("signal", "NO_TRADE")
        conf = signal.get("confidence", 0)
        color = {"LONG": "green", "SHORT": "red"}.get(sig, "yellow")

        # Main signal panel
        lines = [f"[bold {color}]{sig}[/bold {color}] — Confidence: {conf}/10"]
        if signal.get("entry"):
            lines.append(f"Entry: ${signal['entry']:,.2f}")
        if signal.get("stop_loss"):
            lines.append(f"Stop Loss: ${signal['stop_loss']:,.2f}")
        for i in range(1, 4):
            tp = signal.get(f"take_profit_{i}")
            if tp:
                lines.append(f"TP{i}: ${tp:,.2f}")
        if signal.get("risk_reward"):
            lines.append(f"Risk:Reward = 1:{signal['risk_reward']:.1f}")

        console.print(Panel(
            "\n".join(lines),
            title=f"⚡ TRADE SIGNAL — {symbol}",
            border_style=color,
            box=box.DOUBLE,
        ))

        if signal.get("reasoning"):
            console.print(f"\n[bold]Reasoning:[/bold] {signal['reasoning']}")
        if signal.get("confluence_factors"):
            console.print("[bold]Confluence:[/bold]")
            for f in signal["confluence_factors"]:
                console.print(f"  ✓ {f}")
        if signal.get("warnings"):
            for w in signal["warnings"]:
                console.print(f"  [yellow]⚠ {w}[/yellow]")
        if signal.get("invalidation"):
            console.print(f"[dim]Invalidation: {signal['invalidation']}[/dim]")
    else:
        console.print(Panel(str(signal), title="Signal Result", border_style="yellow"))


def cmd_scan(chart_agent: ChartAgent, strategy_agent: StrategyAgent):
    """Quick scan of the entire watchlist."""
    watchlist = os.getenv("WATCHLIST", "BTC/USDT,ETH/USDT").split(",")

    table = Table(title="🔎 Watchlist Scan", box=box.ROUNDED, border_style="cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("Bias")
    table.add_column("RSI", justify="right")
    table.add_column("EMA Stack")
    table.add_column("Action?")

    for sym in watchlist:
        sym = sym.strip()
        try:
            with console.status(f"[dim]Scanning {sym}...[/dim]"):
                analysis = chart_agent.analyze(sym, "1h")
                quick = strategy_agent.quick_bias(analysis)

            color = {"BULLISH": "green", "LEAN BULLISH": "green", "BEARISH": "red", "LEAN BEARISH": "red"}.get(quick["bias"], "yellow")
            action = "[bold green]✓ Watch[/bold green]" if quick["actionable"] else "[dim]—[/dim]"

            table.add_row(
                sym,
                f"${quick['price']:,.2f}" if quick["price"] else "-",
                f"[{color}]{quick['bias']}[/{color}]",
                str(quick.get("rsi", "-")),
                quick.get("ema_stack", "-"),
                action,
            )
        except Exception as e:
            table.add_row(sym, "[red]Error[/red]", str(e)[:30], "-", "-", "-")

    console.print(table)


def cmd_ask(nim: NIMClient, question: str):
    """Free-form question to JARVIS."""
    system = """You are JARVIS, a highly intelligent trading assistant created by Lukas.
You have deep knowledge of crypto markets, forex, indices (NAS100, GER40), 
technical analysis, and market microstructure. You speak directly and concisely.
You reference specific price levels, indicators, and patterns when relevant.
Keep answers under 200 words unless the question requires more depth."""

    with console.status("[cyan]JARVIS thinking...[/cyan]"):
        answer = nim.ask(question, system=system)

    console.print(Panel(answer, title="🤖 JARVIS", border_style="cyan"))


def main():
    print_banner()

    # ── Initialize components ──
    try:
        nim = NIMClient()
        console.print("[bold green]✓[/bold green] NIM Client connected")
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)

    try:
        market = MarketData()
        console.print(f"[bold green]✓[/bold green] Exchange connected: {os.getenv('EXCHANGE', 'bybit')}")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Exchange error: {e}")
        sys.exit(1)

    chart_agent = ChartAgent(nim, market)
    news_agent = NewsAgent(nim)
    strategy_agent = StrategyAgent(nim)

    console.print(f"[bold green]✓[/bold green] All agents online")
    console.print(f"[dim]Watchlist: {os.getenv('WATCHLIST', 'BTC/USDT,ETH/USDT')}[/dim]")
    console.print(f"[dim]Model: {nim.model}[/dim]\n")
    console.print("[dim]Type 'help' for commands or just talk to JARVIS.[/dim]\n")

    # ── Main loop ──
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]JARVIS[/bold cyan]").strip()
            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else None

            if cmd in ("exit", "quit", "q"):
                console.print("[dim]JARVIS shutting down. Good luck out there. 🫡[/dim]")
                break

            elif cmd == "help":
                print_help()

            elif cmd == "briefing":
                sym = arg or "BTC/USDT"
                asset = sym.split("/")[0] if "/" in sym else sym
                console.rule(f"[bold]Morning Briefing — {asset}[/bold]")
                cmd_news(news_agent, asset)
                console.print()
                cmd_chart(chart_agent, f"{asset}/USDT", "4h")
                console.print()
                cmd_signal(chart_agent, news_agent, strategy_agent, f"{asset}/USDT")

            elif cmd == "price":
                cmd_price(market, arg or "BTC/USDT")

            elif cmd == "chart":
                sym = arg or "BTC/USDT"
                cmd_chart(chart_agent, sym)

            elif cmd == "mtf":
                cmd_mtf(chart_agent, arg or "BTC/USDT")

            elif cmd == "news":
                cmd_news(news_agent, arg or "BTC")

            elif cmd == "signal":
                cmd_signal(chart_agent, news_agent, strategy_agent, arg or "BTC/USDT")

            elif cmd == "scan":
                cmd_scan(chart_agent, strategy_agent)

            elif cmd == "ask":
                if arg:
                    cmd_ask(nim, arg)
                else:
                    console.print("[dim]Usage: ask <your question>[/dim]")

            else:
                # Treat as free-form question
                cmd_ask(nim, user_input)

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
