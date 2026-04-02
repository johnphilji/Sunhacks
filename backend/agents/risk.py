"""
AGENT 4 — Risk Manager Agent
==============================
Role: Takes backtest results and produces a structured risk assessment.

Input:  backtest result dict (from Backtesting Agent)
Output: {
    "level":       "low" | "medium" | "high" | "very_high",
    "score":       int 1-10  (10 = maximum risk),
    "flags":       [list of specific risks detected],
    "explanation": "plain English paragraph",
    "metrics":     { raw numbers used in assessment }
}

Risk factors evaluated:
  • Profit percentage (negative = high risk)
  • Win rate (below 40% = concerning)
  • Trade frequency (too few or too many)
  • Max drawdown proxy (worst single trade loss)
  • Consistency (standard deviation of trade returns)
"""

import os
import math

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def assess_risk(backtest_results: dict) -> dict:
    """Main entry for Agent 4."""
    results = backtest_results
    trades  = results.get("trades", [])
    n       = results["num_trades"]
    profit  = results["profit_pct"]
    winrate = results["win_rate"]

    flags = []   # specific issues found
    score = 0    # risk score accumulator (0-10)

    # ── Risk factor 1: Profitability ──────────────────────────────────────
    if profit < -20:
        score += 3; flags.append("Severe drawdown: strategy lost more than 20%")
    elif profit < 0:
        score += 2; flags.append("Strategy was unprofitable in the test period")
    elif profit < 5:
        score += 1; flags.append("Very low returns — may not beat a savings account")

    # ── Risk factor 2: Win rate ───────────────────────────────────────────
    if n > 0:
        if winrate < 30:
            score += 3; flags.append(f"Very low win rate ({winrate:.0f}%) — most trades are losers")
        elif winrate < 45:
            score += 2; flags.append(f"Below-average win rate ({winrate:.0f}%)")
        elif winrate < 55:
            score += 1; flags.append(f"Marginally acceptable win rate ({winrate:.0f}%)")

    # ── Risk factor 3: Trade frequency ───────────────────────────────────
    if n == 0:
        score += 3; flags.append("No trades executed — strategy never triggered")
    elif n > 60:
        score += 2; flags.append(f"Over-trading detected ({n} trades) — transaction costs will erode returns")
    elif n < 3:
        score += 1; flags.append(f"Too few trades ({n}) — results may not be statistically meaningful")

    # ── Risk factor 4: Worst single-trade loss ────────────────────────────
    trade_pcts = [t["pct"] for t in trades]
    if trade_pcts:
        worst = min(trade_pcts)
        if worst < -15:
            score += 2; flags.append(f"Large single-trade loss detected: {worst:.1f}%")
        elif worst < -8:
            score += 1; flags.append(f"Notable single-trade loss: {worst:.1f}%")

        # ── Risk factor 5: Consistency ────────────────────────────────────
        if len(trade_pcts) >= 3:
            mean = sum(trade_pcts) / len(trade_pcts)
            variance = sum((x - mean)**2 for x in trade_pcts) / len(trade_pcts)
            std_dev = math.sqrt(variance)
            if std_dev > 15:
                score += 1; flags.append(f"Highly inconsistent returns (std dev: {std_dev:.1f}%)")
        else:
            std_dev = 0.0
    else:
        worst   = 0.0
        std_dev = 0.0

    # ── Map score to level ────────────────────────────────────────────────
    score = min(score, 10)
    if score <= 2:
        level = "low"
    elif score <= 4:
        level = "medium"
    elif score <= 6:
        level = "high"
    else:
        level = "very_high"

    metrics = {
        "profit_pct":  profit,
        "win_rate":    winrate,
        "num_trades":  n,
        "worst_trade": round(worst, 2) if trade_pcts else 0,
        "std_dev":     round(std_dev, 2),
        "risk_score":  score,
    }

    # ── Generate explanation ──────────────────────────────────────────────
    if GEMINI_API_KEY:
        explanation = _explain_with_llm(level, score, flags, metrics)
    else:
        explanation = _explain_locally(level, score, flags)

    return {
        "level":       level,
        "score":       score,
        "flags":       flags,
        "explanation": explanation,
        "metrics":     metrics,
    }


# ── LLM explanation ────────────────────────────────────────────────────────
def _explain_with_llm(level, score, flags, metrics) -> str:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Write a 2-sentence beginner-friendly risk assessment. "
            f"Risk level: {level} (score {score}/10). "
            f"Issues found: {'; '.join(flags) if flags else 'none'}. "
            f"Metrics: profit={metrics['profit_pct']:+.1f}%, "
            f"win_rate={metrics['win_rate']:.0f}%, trades={metrics['num_trades']}. "
            "Give one practical improvement tip at the end."
        )
        r = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return r.text.strip()
    except Exception as e:
        print(f"[Risk Manager] Gemini failed ({e})")
        return _explain_locally(level, score, flags)


# ── Local explanation ──────────────────────────────────────────────────────
def _explain_locally(level: str, score: int, flags: list) -> str:
    intros = {
        "low":       "✅ This strategy shows a healthy risk profile.",
        "medium":    "⚠️ This strategy carries moderate risk.",
        "high":      "🔴 This strategy carries high risk.",
        "very_high": "🚨 This strategy is very high risk.",
    }
    tips = {
        "low":       "Consider increasing position size slightly for better returns.",
        "medium":    "Consider adding a stop-loss at 5% to limit downside.",
        "high":      "Strongly consider a stop-loss and reducing position size to 50%.",
        "very_high": "Do not use this strategy with real money without major revisions.",
    }
    flag_summary = (" Issues found: " + "; ".join(flags[:2]) + ".") if flags else ""
    return f"{intros[level]}{flag_summary} Tip: {tips[level]}"
