"""
AGENT 2 — Backtesting Agent
=============================
Role: Fetches historical stock data and simulates the strategy day-by-day.

Input:  strategy dict + stock symbol + period
Output: profit_pct, num_trades, win_rate, buy/sell signals, price data

This agent is "stateless" — it can be called multiple times with different
strategies (original and optimized) and returns comparable result dicts.

Supported indicators: SMA-20, SMA-50, SMA-200, RSI-14
"""

import yfinance as yf
import pandas as pd


# ══════════════════════════════════════════════════════════════════════════
#  INDICATOR HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0).rolling(window).mean()
    loss     = (-delta.clip(upper=0)).rolling(window).mean()
    rs       = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


# ══════════════════════════════════════════════════════════════════════════
#  DATA FETCHING
# ══════════════════════════════════════════════════════════════════════════

def _fetch(symbol: str, period: str) -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period=period)
    if df.empty:
        raise ValueError(f"No data for '{symbol}'. Check the ticker symbol.")
    df = df[["Open","High","Low","Close","Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


# ══════════════════════════════════════════════════════════════════════════
#  RULE EVALUATOR
# ══════════════════════════════════════════════════════════════════════════

def _eval(rule: str, row: pd.Series) -> bool:
    """Check if a rule fires for this row. Returns False if data is NaN."""
    r = rule.strip().lower().replace(" ", "")
    def safe(col):
        v = row.get(col, float("nan"))
        return v if not pd.isna(v) else None

    pairs = {
        "price>sma_20":  lambda: (safe("Close") or 0) > (safe("sma_20") or float("inf")),
        "price<sma_20":  lambda: (safe("Close") or 0) < (safe("sma_20") or 0),
        "price>sma_50":  lambda: (safe("Close") or 0) > (safe("sma_50") or float("inf")),
        "price<sma_50":  lambda: (safe("Close") or 0) < (safe("sma_50") or 0),
        "price>sma_200": lambda: (safe("Close") or 0) > (safe("sma_200") or float("inf")),
        "price<sma_200": lambda: (safe("Close") or 0) < (safe("sma_200") or 0),
        "rsi<30":  lambda: safe("rsi") is not None and safe("rsi") < 30,
        "rsi>70":  lambda: safe("rsi") is not None and safe("rsi") > 70,
        "rsi<40":  lambda: safe("rsi") is not None and safe("rsi") < 40,
        "rsi>60":  lambda: safe("rsi") is not None and safe("rsi") > 60,
    }
    fn = pairs.get(r)
    if fn is None:
        print(f"[Backtester] Unknown rule: '{rule}'")
        return False
    try:
        return bool(fn())
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
#  MAIN BACKTEST FUNCTION
# ══════════════════════════════════════════════════════════════════════════

def run_backtest(strategy: dict, symbol: str, period: str = "1y") -> dict:
    """
    Simulates trading $10,000 using the strategy rules day-by-day.

    Returns a result dict consumed by: Risk Manager, Optimizer, Decision Agent.
    """
    entry_rule = strategy["entry"]
    exit_rule  = strategy["exit"]

    # ── Fetch & enrich data ───────────────────────────────────────────────
    df = _fetch(symbol, period)
    df["sma_20"]  = _sma(df["Close"], 20)
    df["sma_50"]  = _sma(df["Close"], 50)
    df["sma_200"] = _sma(df["Close"], 200)
    df["rsi"]     = _rsi(df["Close"], 14)

    # Drop rows where key indicators are not yet calculated
    required_sma = 50
    if "sma_200" in entry_rule or "sma_200" in exit_rule:
        required_sma = 200
    elif "sma_20" in entry_rule or "sma_20" in exit_rule:
        required_sma = 20
    df = df.dropna(subset=[f"sma_{required_sma}"])

    if len(df) < 10:
        raise ValueError("Not enough data rows after computing indicators. Try a longer period.")

    # ── Simulate ──────────────────────────────────────────────────────────
    cash      = 10_000.0
    shares    = 0.0
    buy_price = 0.0
    trades    = []
    buys, sells = [], []

    for date, row in df.iterrows():
        price    = row["Close"]
        date_str = str(date.date())

        if shares == 0:
            if _eval(entry_rule, row):
                shares    = cash / price
                buy_price = price
                cash      = 0.0
                buys.append({"date": date_str, "price": round(price, 2)})
        else:
            if _eval(exit_rule, row):
                cash      = shares * price
                pct       = (price - buy_price) / buy_price * 100
                trades.append({"buy": round(buy_price,2), "sell": round(price,2), "pct": round(pct,2)})
                sells.append({"date": date_str, "price": round(price, 2)})
                shares    = 0.0
                buy_price = 0.0

    # Close any open position at last price
    if shares > 0:
        last = df["Close"].iloc[-1]
        cash = shares * last
        pct  = (last - buy_price) / buy_price * 100
        trades.append({"buy": round(buy_price,2), "sell": round(last,2), "pct": round(pct,2), "open": True})

    # ── Stats ─────────────────────────────────────────────────────────────
    profit_pct = (cash - 10_000) / 10_000 * 100
    n          = len(trades)
    wins       = [t for t in trades if t["pct"] > 0]
    win_rate   = len(wins) / n * 100 if n > 0 else 0.0

    # ── Chart data (last 252 rows for readability) ────────────────────────
    view = df.tail(252)
    price_data = [{"date": str(d.date()), "price": round(p, 2)}
                  for d, p in zip(view.index, view["Close"])]

    # Determine which SMA line to overlay
    sma_col = "sma_50"
    for s in ["sma_20","sma_200"]:
        if s in entry_rule or s in exit_rule:
            sma_col = s
    sma_data = [{"date": str(d.date()), "value": round(v, 2)}
                for d, v in zip(view.index, view[sma_col])
                if not pd.isna(v)]

    # RSI data for secondary chart (if relevant)
    rsi_data = [{"date": str(d.date()), "value": round(v, 2)}
                for d, v in zip(view.index, view["rsi"])
                if not pd.isna(v)]

    return {
        "strategy":      strategy,
        "profit_pct":    round(profit_pct, 2),
        "final_value":   round(cash, 2),
        "num_trades":    n,
        "win_rate":      round(win_rate, 1),
        "trades":        trades,
        "buy_signals":   buys,
        "sell_signals":  sells,
        "price_data":    price_data,
        "sma_data":      sma_data,
        "sma_label":     sma_col.upper().replace("_","-"),
        "rsi_data":      rsi_data,
    }
