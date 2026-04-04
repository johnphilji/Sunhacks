

import os
import math

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def analyze_market(price_data: list, symbol: str) -> dict:
    """
    Main entry for Agent 3.
    Computes trend, volatility, and momentum from price_data.
    Then either asks the LLM to write the summary, or composes it locally.
    """
    if len(price_data) < 10:
        return {
            "summary":    "Not enough price data to analyze market conditions.",
            "trend":      "unknown",
            "volatility": "unknown",
            "momentum":   0.0,
            "details":    {},
        }


    prices    = [p["price"] for p in price_data]
    first     = prices[0]
    last      = prices[-1]
    momentum  = round((last - first) / first * 100, 2)

    # Trend: compare first-half average vs second-half average
    mid       = len(prices) // 2
    avg_first = sum(prices[:mid]) / mid
    avg_last  = sum(prices[mid:]) / (len(prices) - mid)
    if avg_last > avg_first * 1.03:
        trend = "uptrend"
    elif avg_last < avg_first * 0.97:
        trend = "downtrend"
    else:
        trend = "sideways"

    # Volatility: average daily % move
    daily_changes = [abs((prices[i] - prices[i-1]) / prices[i-1] * 100)
                     for i in range(1, len(prices))]
    avg_daily_change = sum(daily_changes) / len(daily_changes)
    if avg_daily_change > 2.5:
        volatility = "high"
    elif avg_daily_change > 1.2:
        volatility = "medium"
    else:
        volatility = "low"

    # 52-week high/low
    high_52 = round(max(prices), 2)
    low_52  = round(min(prices), 2)
    pct_from_high = round((last - high_52) / high_52 * 100, 1)

    details = {
        "momentum_pct":      momentum,
        "trend":             trend,
        "volatility":        volatility,
        "avg_daily_move":    round(avg_daily_change, 2),
        "period_high":       high_52,
        "period_low":        low_52,
        "pct_from_high":     pct_from_high,
        "current_price":     last,
    }


    if GEMINI_API_KEY:
        summary = _summarize_with_llm(symbol, details)
    else:
        summary = _summarize_locally(symbol, details)

    return {
        "summary":    summary,
        "trend":      trend,
        "volatility": volatility,
        "momentum":   momentum,
        "details":    details,
    }



def _summarize_with_llm(symbol: str, d: dict) -> str:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            f"Summarize this market analysis for {symbol} in 2 concise sentences for a beginner. "
            f"Data: trend={d['trend']}, volatility={d['volatility']}, "
            f"momentum={d['momentum_pct']:+.1f}%, avg_daily_move={d['avg_daily_move']}%, "
            f"pct_from_52wk_high={d['pct_from_high']}%. "
            "Be specific and educational."
        )
        r = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return r.text.strip()
    except Exception as e:
        print(f"[Market Analyst] Gemini failed ({e})")
        return _summarize_locally(symbol, d)



def _summarize_locally(symbol: str, d: dict) -> str:
    trend_desc = {
        "uptrend":   f"{symbol} is in a clear uptrend",
        "downtrend": f"{symbol} is in a downtrend",
        "sideways":  f"{symbol} is moving sideways (consolidating)",
    }.get(d["trend"], f"{symbol} shows mixed price action")

    vol_desc = {
        "high":   f"with high volatility (avg {d['avg_daily_move']}%/day) — expect big price swings",
        "medium": f"with moderate volatility (avg {d['avg_daily_move']}%/day)",
        "low":    f"with low volatility (avg {d['avg_daily_move']}%/day) — price moves are stable",
    }.get(d["volatility"], "")

    mom = d["momentum_pct"]
    mom_desc = (
        f"Overall it gained {mom:+.1f}% over the period."
        if mom > 0 else
        f"Overall it lost {abs(mom):.1f}% over the period."
    )

    high_desc = (
        f"Currently {abs(d['pct_from_high']):.1f}% below its period high of ${d['period_high']}."
        if d["pct_from_high"] < -5 else
        f"Trading near its period high of ${d['period_high']}."
    )

    return f"{trend_desc} {vol_desc}. {mom_desc} {high_desc}"
