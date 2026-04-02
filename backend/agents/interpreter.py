"""
AGENT 1 — Strategy Interpreter Agent
======================================
Role: Converts plain-English trading strategies into structured JSON rules.

Input:  "Buy when price is above the 50-day moving average"
Output: { "entry": "price > sma_50", "exit": "price < sma_50",
          "description": "...", "indicators": ["sma_50"] }

This agent is the "translator" — it bridges the gap between human language
and machine-executable trading rules.

If GEMINI_API_KEY is set → uses Gemini to parse.
Otherwise             → uses a keyword-matching fallback (works for demos).
"""

import os, re, json

# Supported rule tokens (deliberately small set for MVP clarity)
RULE_TOKENS = [
    "price > sma_20", "price < sma_20",
    "price > sma_50", "price < sma_50",
    "price > sma_200","price < sma_200",
    "rsi < 30",       "rsi > 70",
    "rsi < 40",       "rsi > 60",
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def interpret_strategy(text: str) -> dict:
    """
    Main entry point for Agent 1.
    Returns a dict with keys: entry, exit, description, indicators
    """
    if not text.strip():
        raise ValueError("Strategy text is empty.")

    if GEMINI_API_KEY:
        result = _interpret_with_llm(text)
    else:
        result = _interpret_with_keywords(text)

    # Always tag which indicators are used (downstream agents need this)
    result["indicators"] = _extract_indicators(result["entry"], result["exit"])
    result["raw_input"]  = text
    return result


# ── LLM path ──────────────────────────────────────────────────────────────
def _interpret_with_llm(text: str) -> dict:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        system = f"You are a trading strategy parser. Allowed rule tokens: {', '.join(RULE_TOKENS)}. Return ONLY raw JSON (no markdown): {{\"entry\":\"...\",\"exit\":\"...\",\"description\":\"one sentence\"}}. Default to sma_50 crossover if unclear."
        r = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"{system}\n\nStrategy to parse: {text}",
        )
        raw = re.sub(r"```json|```","", r.text).strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Interpreter] Gemini failed ({e}), falling back to keywords")
        return _interpret_with_keywords(text)


# ── Keyword fallback ───────────────────────────────────────────────────────
def _interpret_with_keywords(text: str) -> dict:
    t = text.lower()

    # RSI detection
    if "rsi" in t:
        if any(w in t for w in ["oversold","below 30","30","buy dip"]):
            return {"entry":"rsi < 30","exit":"rsi > 70",
                    "description":"Buy when RSI is oversold (<30); sell when overbought (>70)"}
        return {"entry":"rsi > 70","exit":"rsi < 30",
                "description":"Buy when RSI is overbought (>70); sell when oversold (<30)"}

    # SMA period detection
    if "200" in t:
        entry_rule = "price > sma_200" if _is_bullish(t) else "price < sma_200"
        exit_rule  = "price < sma_200" if _is_bullish(t) else "price > sma_200"
        return {"entry":entry_rule,"exit":exit_rule,
                "description":"200-day SMA trend-following strategy"}

    if "20" in t or "twenty" in t:
        entry_rule = "price > sma_20" if _is_bullish(t) else "price < sma_20"
        exit_rule  = "price < sma_20" if _is_bullish(t) else "price > sma_20"
        return {"entry":entry_rule,"exit":exit_rule,
                "description":"20-day SMA short-term strategy"}

    # Default: SMA-50
    entry_rule = "price > sma_50" if _is_bullish(t) else "price < sma_50"
    exit_rule  = "price < sma_50" if _is_bullish(t) else "price > sma_50"
    return {"entry":entry_rule,"exit":exit_rule,
            "description":"50-day SMA crossover strategy (default)"}


def _is_bullish(text: str) -> bool:
    bullish = ["above","cross","buy","long","uptrend","rise","higher","golden","breakout"]
    return any(w in text for w in bullish)


def _extract_indicators(entry: str, exit: str) -> list:
    indicators = []
    for period in [20, 50, 200]:
        if f"sma_{period}" in entry or f"sma_{period}" in exit:
            indicators.append(f"sma_{period}")
    if "rsi" in entry or "rsi" in exit:
        indicators.append("rsi")
    return list(set(indicators))
