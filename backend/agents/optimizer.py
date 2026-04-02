"""
AGENT 5 — Optimization Agent
==============================
Role: Proposes an improved version of the strategy based on:
  - Original backtest results (what went wrong)
  - Market analysis (what the market was doing)
  - Risk assessment (what risks need mitigation)

Input:  original strategy + results + market + risk analysis
Output: improved strategy dict (same format as Interpreter output)
        with an added "optimization_notes" field explaining changes

Strategy improvement rules:
  - Low win rate + uptrend  → tighten entry (stricter confirmation)
  - High volatility         → use longer SMA (smoother signal)
  - Too many trades         → use longer SMA period
  - RSI strategy + loss     → flip thresholds (try other direction)
  - SMA strategy + loss     → try different SMA period
  - Good results            → minor tweak to slightly tighten exits
"""

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def optimize_strategy(
    strategy: dict,
    backtest_results: dict,
    market_analysis: dict,
    risk_analysis: dict,
) -> dict:
    """Main entry for Agent 5."""

    if OPENAI_API_KEY:
        result = _optimize_with_llm(strategy, backtest_results, market_analysis, risk_analysis)
    else:
        result = _optimize_with_rules(strategy, backtest_results, market_analysis, risk_analysis)

    # Ensure required fields are present
    result.setdefault("indicators", _extract_indicators(result["entry"], result["exit"]))
    result.setdefault("raw_input", strategy.get("raw_input", ""))
    return result


# ── LLM optimization ───────────────────────────────────────────────────────
def _optimize_with_llm(strategy, results, market, risk) -> dict:
    try:
        import json, re
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        allowed = [
            "price > sma_20","price < sma_20",
            "price > sma_50","price < sma_50",
            "price > sma_200","price < sma_200",
            "rsi < 30","rsi > 70","rsi < 40","rsi > 60",
        ]
        system = f"""You are a trading strategy optimizer.
Allowed rule tokens: {', '.join(allowed)}
Current strategy: entry={strategy['entry']}, exit={strategy['exit']}
Backtest: profit={results['profit_pct']:+.1f}%, win_rate={results['win_rate']:.0f}%, trades={results['num_trades']}
Market: trend={market['trend']}, volatility={market['volatility']}
Risk: {risk['level']} (score {risk['score']}/10)

Propose an improved strategy. Return ONLY raw JSON (no markdown):
{{"entry":"...","exit":"...","description":"one sentence","optimization_notes":"explain what changed and why"}}"""

        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"system","content":system},{"role":"user","content":"Optimize."}],
            temperature=0.4, max_tokens=180,
        )
        raw = re.sub(r"```json|```","", r.choices[0].message.content).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Optimizer] LLM failed ({e}), using rule-based optimizer")
        return _optimize_with_rules(strategy, results, market, risk)


# ── Rule-based optimizer ───────────────────────────────────────────────────
def _optimize_with_rules(strategy, results, market, risk) -> dict:
    entry   = strategy["entry"]
    exit_r  = strategy["exit"]
    profit  = results["profit_pct"]
    winrate = results["win_rate"]
    n       = results["num_trades"]
    trend   = market.get("trend", "sideways")
    vol     = market.get("volatility", "medium")

    notes = []
    new_entry, new_exit = entry, exit_r

    # ── RSI strategy adjustments ───────────────────────────────────────────
    if "rsi" in entry:
        if profit < 0 or winrate < 40:
            # Strategy is losing — loosen entry thresholds (wider net)
            if "rsi < 30" in entry:
                new_entry = "rsi < 40"
                notes.append("Widened RSI entry from <30 to <40 to catch more buy opportunities")
            elif "rsi > 70" in entry:
                new_entry = "rsi > 60"
                notes.append("Lowered RSI entry from >70 to >60 for more frequent entries")
        elif n > 30:
            # Too many trades — tighten thresholds
            if "rsi < 40" in entry:
                new_entry = "rsi < 30"
                notes.append("Tightened RSI entry to <30 to reduce over-trading")

        # Tighten exit for high-risk RSI strategies
        if risk["level"] in ("high", "very_high"):
            if "rsi > 70" in exit_r:
                new_exit = "rsi > 60"
                notes.append("Lowered RSI exit threshold to 60 to take profits earlier (risk mitigation)")

    # ── SMA strategy adjustments ───────────────────────────────────────────
    else:
        if vol == "high" and "sma_20" in entry:
            # High volatility + short SMA = too much noise → use longer SMA
            new_entry = entry.replace("sma_20", "sma_50")
            new_exit  = exit_r.replace("sma_20", "sma_50")
            notes.append("Switched from SMA-20 to SMA-50 — high volatility makes short SMA too noisy")

        elif profit < 0 and "sma_50" in entry and trend == "uptrend":
            # Losing in an uptrend with SMA-50 → try longer-term SMA-200
            new_entry = entry.replace("sma_50", "sma_200")
            new_exit  = exit_r.replace("sma_50", "sma_200")
            notes.append("Upgraded to SMA-200 filter — the uptrend suggests a long-term trend-following approach")

        elif n > 40 and "sma_20" in entry:
            new_entry = entry.replace("sma_20", "sma_50")
            new_exit  = exit_r.replace("sma_20", "sma_50")
            notes.append("Reduced trade frequency by switching SMA-20 → SMA-50")

        elif profit > 10 and winrate > 55:
            # Good strategy — just make a minor note
            notes.append("Strategy is performing well. Minor confirmation: keeping current rules.")

        elif trend == "downtrend" and "price > sma" in entry:
            # Trend following up in a downtrend — suggest flipping
            notes.append("Warning: buying into a downtrend. Consider waiting for trend reversal before using this strategy.")

    if not notes:
        notes.append("No significant changes needed — current strategy structure is appropriate.")

    return {
        "entry":               new_entry,
        "exit":                new_exit,
        "description":         f"Optimized: {strategy.get('description','SMA strategy')}",
        "optimization_notes":  " | ".join(notes),
    }


def _extract_indicators(entry: str, exit_r: str) -> list:
    inds = []
    for p in [20, 50, 200]:
        if f"sma_{p}" in entry or f"sma_{p}" in exit_r:
            inds.append(f"sma_{p}")
    if "rsi" in entry or "rsi" in exit_r:
        inds.append("rsi")
    return list(set(inds))
