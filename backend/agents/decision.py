"""
AGENT 6 — Decision Agent  (THE MOST IMPORTANT AGENT)
======================================================
Role: Final arbiter. Compares original vs optimized strategy results,
      weighs all context (market, risk), and selects the BEST strategy.

This agent demonstrates genuine "agentic" decision-making:
  - It has access to ALL prior agents' outputs
  - It applies a multi-factor scoring model
  - It explains its reasoning in plain English
  - Its decision can OVERRIDE the "obviously better" choice if risk is too high

Input:
  original_strategy, original_results
  optimized_strategy, optimized_results
  risk_analysis (from Risk Manager)
  market_analysis (from Market Analyst)

Output: {
    "chosen":      "original" | "optimized",
    "confidence":  "low" | "medium" | "high",
    "score_original":   float,
    "score_optimized":  float,
    "reasoning":   "detailed explanation",
    "final_rules": { entry, exit }
    "action_plan": "what the user should do next"
}
"""

import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def make_final_decision(
    original_strategy: dict,
    original_results: dict,
    optimized_strategy: dict,
    optimized_results: dict,
    risk_analysis: dict,
    market_analysis: dict,
) -> dict:
    """Main entry for Agent 6."""

    # ── Multi-factor scoring ──────────────────────────────────────────────
    score_orig = _score(original_results,  risk_analysis)
    score_opt  = _score(optimized_results, risk_analysis)

    # ── Choose winner ─────────────────────────────────────────────────────
    # If scores are very close (< 5 points), prefer original (less change = less surprise)
    if abs(score_opt - score_orig) < 5:
        chosen = "original"
        chosen_strategy  = original_strategy
        chosen_results   = original_results
    elif score_opt > score_orig:
        chosen = "optimized"
        chosen_strategy  = optimized_strategy
        chosen_results   = optimized_results
    else:
        chosen = "original"
        chosen_strategy  = original_strategy
        chosen_results   = original_results

    # ── Confidence level ──────────────────────────────────────────────────
    score_gap = abs(score_opt - score_orig)
    if score_gap >= 20:
        confidence = "high"
    elif score_gap >= 8:
        confidence = "medium"
    else:
        confidence = "low"

    # ── Generate reasoning ────────────────────────────────────────────────
    if GEMINI_API_KEY:
        reasoning = _reason_with_llm(
            chosen, score_orig, score_opt, original_results,
            optimized_results, risk_analysis, market_analysis,
            original_strategy, optimized_strategy,
        )
    else:
        reasoning = _reason_locally(
            chosen, score_orig, score_opt, original_results,
            optimized_results, risk_analysis, market_analysis,
        )

    action_plan = _build_action_plan(chosen_results, risk_analysis, market_analysis)

    return {
        "chosen":             chosen,
        "confidence":         confidence,
        "score_original":     round(score_orig, 1),
        "score_optimized":    round(score_opt, 1),
        "reasoning":          reasoning,
        "final_rules":        chosen_strategy,
        "action_plan":        action_plan,
        "chosen_results":     chosen_results,
    }


# ══════════════════════════════════════════════════════════════════════════
#  SCORING MODEL
#  Each factor contributes points. Max possible: ~100.
# ══════════════════════════════════════════════════════════════════════════

def _score(results: dict, risk: dict) -> float:
    score = 0.0
    profit = results["profit_pct"]
    wr = results["win_rate"]
    n = results["num_trades"]
    risk_lv = risk.get("level", "medium")
    risk_val = risk.get("score", 5)

    # 1. Profitability (0-40 pts)
    if profit > 40: score += 40
    elif profit > 20: score += 32
    elif profit > 5:  score += 18
    elif profit > 0:  score += 10
    else:             score += 0

    # 2. Consistency / Win Rate (0-30 pts)
    if wr >= 65 and n >= 5:   score += 30
    elif wr >= 55 and n >= 5: score += 20
    elif wr >= 45:           score += 10
    else:                    score += 0

    # 3. Robustness / Sample Size (0-15 pts)
    if 10 <= n <= 35:   score += 15
    elif 5 <= n < 10:   score += 8
    elif n > 35:        score += 5  # penalized slightly for over-trading
    else:               score += 0

    # 4. Risk Mitigation (0 to -25 pts)
    # Penalize risk more if win rate is low
    penalty = risk_val * 2.5
    if wr < 40: penalty *= 1.2
    score -= penalty

    return max(0.0, score)


# ══════════════════════════════════════════════════════════════════════════
#  REASONING GENERATORS
# ══════════════════════════════════════════════════════════════════════════

def _reason_with_llm(
    chosen, s_orig, s_opt, orig_r, opt_r, risk, market,
    orig_strat, opt_strat,
) -> str:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        opt_notes = opt_strat.get("optimization_notes", "")
        prompt = (
            f"You are a trading system's final decision agent. Explain in 3 sentences why "
            f"the {'optimized' if chosen == 'optimized' else 'original'} strategy was chosen. "
            f"Original: profit={orig_r['profit_pct']:+.1f}%, winrate={orig_r['win_rate']:.0f}%, "
            f"score={s_orig:.0f}/100. "
            f"Optimized: profit={opt_r['profit_pct']:+.1f}%, winrate={opt_r['win_rate']:.0f}%, "
            f"score={s_opt:.0f}/100. "
            f"Market: {market.get('trend','?')} trend, {market.get('volatility','?')} volatility. "
            f"Risk: {risk.get('level','?')} (score {risk.get('score','?')}/10). "
            f"Optimization changes: {opt_notes}. "
            "Be specific and beginner-friendly."
        )
        r = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        return r.text.strip()
    except Exception as e:
        print(f"[Decision Agent] Gemini failed ({e})")
        return _reason_locally(chosen, s_orig, s_opt, orig_r, opt_r, risk, market)


def _reason_locally(chosen, s_orig, s_opt, orig_r, opt_r, risk, market) -> str:
    if chosen == "optimized":
        gap = s_opt - s_orig
        return (
            f"The optimized strategy scored {s_opt:.0f}/100 vs {s_orig:.0f}/100 for the original "
            f"(+{gap:.0f} point improvement). "
            f"It achieved {opt_r['profit_pct']:+.1f}% profit and a {opt_r['win_rate']:.0f}% win rate, "
            f"compared to {orig_r['profit_pct']:+.1f}% and {orig_r['win_rate']:.0f}% originally. "
            f"Given the {market.get('trend','current')} market trend and "
            f"{risk.get('level','moderate')} risk profile, the optimizer's adjustments produced "
            f"a meaningfully better outcome."
        )
    else:
        if s_orig >= s_opt:
            reason = f"the original scored {s_orig:.0f} vs {s_opt:.0f} for the optimized version"
        else:
            reason = f"the score difference ({abs(s_opt-s_orig):.0f} pts) was too small to justify the change"
        return (
            f"The original strategy was retained because {reason}. "
            f"Original: {orig_r['profit_pct']:+.1f}% profit, {orig_r['win_rate']:.0f}% win rate. "
            f"Optimized: {opt_r['profit_pct']:+.1f}% profit, {opt_r['win_rate']:.0f}% win rate. "
            f"In a {market.get('trend','current')} market with {risk.get('level','moderate')} risk, "
            f"stability and familiarity with the original rules is preferred."
        )


def _build_action_plan(results: dict, risk: dict, market: dict) -> str:
    profit  = results["profit_pct"]
    wr      = results["win_rate"]
    risk_lv = risk.get("level", "medium")
    trend   = market.get("trend", "sideways")

    parts = []

    if profit > 10 and wr > 50:
        parts.append("📋 Paper-trade this strategy for 30 days before using real money.")
    elif profit > 0:
        parts.append("📋 Consider paper-trading this strategy to verify the results live.")
    else:
        parts.append("📋 Do NOT use real money with this strategy yet — refine it further first.")

    if risk_lv in ("high", "very_high"):
        parts.append("🛡 Add a hard stop-loss at 5-7% per trade to cap your downside.")
    elif risk_lv == "medium":
        parts.append("🛡 Consider setting a stop-loss at 8-10% as a safety net.")

    if trend == "downtrend":
        parts.append("📉 Be cautious — you're backtesting in a downtrend. Verify on a different period.")
    elif trend == "uptrend":
        parts.append("📈 The uptrend helped performance — retest in a sideways or down market too.")

    parts.append("📚 Always backtest across multiple time periods and symbols before going live.")
    return " ".join(parts)
