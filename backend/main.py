"""
AutoTrader AI — Multi-Agent Autonomous Trading System
======================================================
main.py: FastAPI server + Agent Orchestrator

The orchestrator is the "conductor" that calls each agent in sequence,
passing the output of one agent as input to the next.

Agent Pipeline:
  User Input
    → [1] Interpreter Agent   (NL → structured rules)
    → [2] Backtest Agent      (initial run: profit, win rate)
    → [3] Market Analyst      (reads historical data, defines regime)
    → [4] Risk Manager        (scores risk, flags volatility/drawdown)
    → [5] Optimizer Agent     (proposes improved strategy via rule-based heuristics)
    → [6] Backtest Agent      (second run with optimized strategy)
    → [7] Decision Agent      (picks the winner, scores 0-100, gives reasoning)
    → Final Output to frontend
"""

import time
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# ── Import all six agents ──────────────────────────────────────────────────
from agents.interpreter  import interpret_strategy
from agents.backtest     import run_backtest
from agents.market       import analyze_market
from agents.risk         import assess_risk
from agents.optimizer    import optimize_strategy
from agents.decision     import make_final_decision

# ── App setup ──────────────────────────────────────────────────────────────
app = FastAPI(title="AutoTrader AI – Multi-Agent System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request model ──────────────────────────────────────────────────────────
class SystemInput(BaseModel):
    strategy: str          # e.g. "Buy when price crosses above 50-day SMA"
    symbol:   str = "AAPL"
    period:   str = "1y"


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Multi-Agent Trading System online 🤖"}


# ══════════════════════════════════════════════════════════════════════════
#  MAIN ENDPOINT — runs the full multi-agent pipeline
# ══════════════════════════════════════════════════════════════════════════
@app.post("/run-system")
def run_system(body: SystemInput):
    """
    Orchestrates all 6 agents in sequence.
    Each agent's output becomes the next agent's input.
    """
    t0 = time.time()
    symbol = body.symbol.upper().strip()
    log    = []   # agent communication log (shown in frontend)

    try:
        # ── AGENT 1: Interpret natural language → structured rules ─────────
        log.append({"agent": "Interpreter", "status": "running", "msg": f'Parsing: "{body.strategy[:60]}…"'})
        strategy = interpret_strategy(body.strategy)
        log[-1]["status"] = "done"
        log[-1]["output"] = f'entry={strategy["entry"]}  exit={strategy["exit"]}'

        # ── AGENT 2 (first run): Backtest with original strategy ──────────
        log.append({"agent": "Backtester", "status": "running", "msg": f"Running initial backtest on {symbol} ({body.period})"})
        original_results = run_backtest(strategy, symbol, body.period)
        log[-1]["status"] = "done"
        log[-1]["output"] = (
            f'profit={original_results["profit_pct"]:+.1f}%  '
            f'trades={original_results["num_trades"]}  '
            f'winrate={original_results["win_rate"]:.0f}%'
        )

        # ── AGENT 3: Market Analyst reads the price data ───────────────────
        log.append({"agent": "Market Analyst", "status": "running", "msg": f"Analyzing {symbol} market conditions"})
        market_analysis = analyze_market(original_results["price_data"], symbol)
        log[-1]["status"] = "done"
        log[-1]["output"] = market_analysis["summary"][:80]

        # ── AGENT 4: Risk Manager reads the backtest results ───────────────
        log.append({"agent": "Risk Manager", "status": "running", "msg": "Assessing strategy risk profile"})
        risk_analysis = assess_risk(original_results)
        log[-1]["status"] = "done"
        log[-1]["output"] = f'risk={risk_analysis["level"]}  score={risk_analysis["score"]}/10'

        # ── AGENT 5: Optimizer proposes an improved strategy ───────────────
        log.append({"agent": "Optimizer", "status": "running", "msg": "Searching for strategy improvements"})
        optimized_strategy = optimize_strategy(strategy, original_results, market_analysis, risk_analysis)
        log[-1]["status"] = "done"
        log[-1]["output"] = f'entry={optimized_strategy["entry"]}  exit={optimized_strategy["exit"]}'

        # ── AGENT 2 (second run): Backtest with optimized strategy ─────────
        log.append({"agent": "Backtester", "status": "running", "msg": "Running optimized strategy backtest"})
        optimized_results = run_backtest(optimized_strategy, symbol, body.period)
        log[-1]["status"] = "done"
        log[-1]["output"] = (
            f'profit={optimized_results["profit_pct"]:+.1f}%  '
            f'trades={optimized_results["num_trades"]}  '
            f'winrate={optimized_results["win_rate"]:.0f}%'
        )

        # ── AGENT 6: Decision Agent picks the winner ───────────────────────
        log.append({"agent": "Decision Agent", "status": "running", "msg": "Comparing strategies and selecting best"})
        decision = make_final_decision(
            original_strategy=strategy,
            original_results=original_results,
            optimized_strategy=optimized_strategy,
            optimized_results=optimized_results,
            risk_analysis=risk_analysis,
            market_analysis=market_analysis,
        )
        log[-1]["status"] = "done"
        log[-1]["output"] = f'Chose: {decision["chosen"]}  confidence={decision["confidence"]}'

        elapsed = round(time.time() - t0, 2)

        return {
            "success":            True,
            "elapsed_seconds":    elapsed,
            "agent_log":          log,
            "symbol":             symbol,
            "period":             body.period,

            # Strategy objects
            "original_strategy":  strategy,
            "optimized_strategy": optimized_strategy,

            # Backtest result objects (include chart data)
            "original_results":   original_results,
            "optimized_results":  optimized_results,

            # Agent outputs
            "market_analysis":    market_analysis,
            "risk_analysis":      risk_analysis,
            "final_decision":     decision,
            "metadata":           {
                "symbol": symbol,
                "period": body.period,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"System error: {e}")
