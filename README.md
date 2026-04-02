# ⚡ AutoTrader AI — Multi-Agent Autonomous Trading System

A working multi-agent AI system where 6 specialized agents collaborate to backtest,
analyze, optimize, and decide on trading strategies.

---

## 🤖 Agent Architecture

```
User Input
    ↓
[Agent 1] INTERPRETER     — Converts plain English → structured rules
    ↓
[Agent 2] BACKTESTER #1   — Initial backtest (profit %, trades, win rate)
    ↓
[Agent 3] MARKET ANALYST  — Analyzes price data (trend, volatility, momentum)
    ↓
[Agent 4] RISK MANAGER    — Evaluates risk (score 1-10, flags issues)
    ↓
[Agent 5] OPTIMIZER       — Proposes improved strategy rules
    ↓
[Agent 2] BACKTESTER #2   — Runs the optimized strategy
    ↓
[Agent 6] DECISION AGENT  — Scores both, picks winner, explains WHY
    ↓
Frontend displays everything with charts
```

---

## 📁 Project Structure

```
autotrader_mas/
├── backend/
│   ├── main.py               # FastAPI server + orchestrator
│   └── agents/
│       ├── __init__.py
│       ├── interpreter.py    # Agent 1: NL → rules
│       ├── backtest.py       # Agent 2: runs simulation
│       ├── market.py         # Agent 3: market analysis
│       ├── risk.py           # Agent 4: risk assessment
│       ├── optimizer.py      # Agent 5: strategy improvement
│       └── decision.py       # Agent 6: final verdict
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

---

## 🚀 Setup Instructions

### Step 1 — Prerequisites
- Python 3.9 or later
- A terminal (Command Prompt, PowerShell, Terminal, etc.)

### Step 2 — Install Python dependencies

```bash
# Navigate to the project folder
cd autotrader_mas

# (Recommended) Create a virtual environment
python -m venv venv

# Activate it:
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 3 — (Optional) Set OpenAI API Key

If you have an OpenAI API key, the system will use GPT-3.5 for:
- More accurate strategy parsing
- More natural market summaries
- More detailed risk explanations
- Smarter optimization suggestions

```bash
# Mac/Linux
export OPENAI_API_KEY="sk-..."

# Windows
set OPENAI_API_KEY=sk-...
```

**Without an API key:** Every agent has a built-in fallback that works perfectly
for demos — no API key required!

### Step 4 — Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 5 — Open the frontend

Simply open `frontend/index.html` in your browser.

> No web server needed for the frontend — just double-click the file!

---

## 💡 Example Strategies to Try

| Strategy | Input Text |
|----------|-----------|
| SMA-50 Crossover | "Buy when price crosses above the 50-day moving average. Sell when it drops below." |
| RSI Reversal | "Buy when RSI drops below 30 (oversold). Sell when RSI goes above 70 (overbought)." |
| SMA-200 Trend | "Buy when price is above the 200-day moving average. Sell when it falls below." |
| SMA-20 Short-term | "Buy when price crosses above the 20-day moving average. Sell when below." |

---

## 🔌 API Reference

**POST /run-system**
```json
{
  "strategy": "Buy when price crosses above the 50-day moving average",
  "symbol": "AAPL",
  "period": "1y"
}
```

Returns a single JSON object with all agent outputs:
- `original_results` — first backtest
- `optimized_results` — second backtest with improved strategy
- `market_analysis` — trend, volatility, momentum
- `risk_analysis` — risk level, score, flags
- `final_decision` — chosen strategy, reasoning, action plan
- `agent_log` — communication log between agents

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Backend web framework |
| uvicorn | ASGI server |
| yfinance | Historical stock data |
| pandas | Data manipulation |
| openai | LLM integration (optional) |
| python-dotenv | Environment variable loading |

---

## ⚠️ Disclaimer

This is an educational demo project built for Sunhacks hackathon. It is NOT financial advice.
Never use backtested results to make real trading decisions without extensive additional research.

---

