# ⚡ AutoTrader AI — Multi-Agent Autonomous Trading System

A comprehensive, multi-agent AI system where 6 specialized agents collaborate to analyze, backtest, optimize, and decide on financial trading strategies. This project fuses an intelligent, multi-agent Python FastAPI backend powered by Google Gemini API with a sleek, interactive, and futuristic Cyberpunk-style frontend dashboard.

---

## 🌟 Full Project Overview

AutoTrader AI bridges the gap between natural language and quantitative finance. Instead of writing complex trading algorithms manually, the user inputs a strategy in plain English (e.g., "Buy when the price crosses the 50-day moving average"). 

The system takes this input, passes it through a pipeline of **6 specialized autonomous agents**, backtests it on real historical market data via Yahoo Finance, attempts to artificially improve the strategy, and visually compares the two approaches in an immersive web interface.

---

## 🖥 Frontend Dashboard Functionalities

The frontend is a vanilla HTML/CSS/JS single-page application heavily styled with a tactical, neon-HUD aesthetic. It is completely responsive, using CSS variables and interactive JS logic.

### 1. Strategy Input Panel (SYS-01)
*   **Natural Language Input:** A text area allowing users to enter strategies purely in English.
*   **Quick Load Strategies:** Buttons allowing users to auto-fill proven starter strategies:
    *   **SMA-50:** 50-day Simple Moving Average crossover.
    *   **RSI:** Relative Strength Index oversold/overbought strategy.
    *   **SMA-200:** Long-term 200-day trend following.
    *   **SMA-20:** Short-term trend following.
*   **Configuration Selectors:** Input target Stock Symbol (e.g., AAPL, TSLA) and select the time Horizon (6 Months, 1 Year, 2 Years, 5 Years).
*   **Deployment Controller:** A "Deploy Agents" button orchestrating the backend API call with robust error handling and UI loading states.

### 2. Agent Pipeline Visualizer (SYS-02)
*   A real-time progression tracker showing exactly which agent is currently processing the data.
*   Lights up sequentially (`IDLE`, `ACTIVE`, `DONE`) as the backend websocket/REST responses complete, keeping the user visually engaged during the AI processing phase.

### 3. Top Metrics Row (Results Dashboard)
*   **Original vs Optimized Return:** Side-by-side metric cards displaying the respective profit percentages, total trades executed, and win percentage for both versions of the strategy.
*   **Risk Level:** Displays qualitative risk metrics (e.g., MODERATE, HIGH) alongside a numerical Risk Score.
*   **AI Decision:** The final verdict displaying whether the system recommends deploying the original or optimized strategy, scored by confidence %.

### 4. Strategy Rules Comparison (AGT-01 & 05)
*   Displays the parsed rules mapping translated from the user's natural language to structured JSON (Original Rules).
*   Displays the newly generated, AI-optimized structured rules (Optimized Rules).

### 5. Interactive Price Charts (AGT-02 / 02b)
*   **Powered by Chart.js:** Plots the asset's closing price over the time period specified.
*   **Buy/Sell Markers:** Dynamically injects green (buy) and red (sell) markers exactly on the chart where the agents decided to execute algorithmic trades.
*   Features dual charts—one charting the Original strategy execution, and one charting the Optimized strategy execution.

### 6. AI Agent Analytics Panels (AGT-03, 04, 05, 06)
*   **AGT-03 Market Analyst:** Delivers a narrative summary of market conditions (trend stability, ATR, volatility index).
*   **AGT-04 Risk Manager:** Detailed reasoning on risk factors, containing a specific list of "Red Flags" discovered during backtesting (e.g., drawdown thresholds exceeded).
*   **AGT-05 Optimizer Notes:** The AI's exact chain of thought explaining *why* it modified the rules (e.g., "Added a 10% Stop Loss to curb intense drawdown").
*   **AGT-06 Final Verdict:** A highly visual comparison score-bar between Original and Optimized, backed by final AI reasoning and an actionable step-by-step deployment plan.

### 7. Interactive Trade Log
*   A fully populated, scrollable data table displaying every single trade made by the winning strategy.
*   Includes columns for Buy Date/Price, Sell Date/Price, Net Return on that individual trade, and an indicator whether it was a Win or Loss.

---

## 🧠 Backend Architecture & Functionalities

The robust backend is built with Python and **FastAPI**, organizing workflows synchronously through a complex multi-agent system powered by the **Google Gemini API** (`google-genai`).

### The 6-Agent Pipeline Pipeline

1.  **[Agent 1: INTERPRETER]** (`interpreter.py`)
    *   Accepts the raw english sentence. Uses an LLM to accurately extract constraints, technical indicators (SMA, EMA, RSI, MACD), values, and thresholds.
    *   Outputs a tightly structured JSON dict representing programmatic trading rules.
2.  **[Agent 2: BACKTESTER #1]** (`backtest.py`)
    *   Not an LLM, but a pure quantitative workhorse. Uses `yfinance` to fetch real daily open/high/low/close/volume (OHLCV) market data and `pandas` to calculate all required indicators.
    *   Iterates through historical prices simulating a paper-trading account exactly according to the rules produced by Agent 1. Returns profit, drawdowns, win rate, and total trades.
3.  **[Agent 3: MARKET ANALYST]** (`market.py`)
    *   Reviews the fetched financial dataset to contextualize the asset's specific conditions independent of the strategy. Analyzes rolling volatilities, momentum structures, and standard deviations to flag whether it's a bull/bear/ranging regime.
4.  **[Agent 4: RISK MANAGER]** (`risk.py`)
    *   Reviews results from Backtester #1 and the contextual data from Market Analyst.
    *   Constructs a Risk Score (1-10) and identifies logical flaws (e.g., "Strategy overtrades in volatile markets," "Lacking a trailing stop").
5.  **[Agent 5: OPTIMIZER]** (`optimizer.py`)
    *   LLM-based quantitative strategist. Taking the Original Rules, Backtest #1 flaws, and the Risk Manager's warnings, it rewrites the rules array (adding new indicators, adjusting period lengths, or adding stop-losses) aiming for a higher Sharpe ratio or better returns.
6.  **[Agent 2: BACKTESTER #2]** (`backtest.py`)
    *   Re-triggered to simulate the newly generated rules produced by Agent 5 over the same historical period to gather "Optimized Results."
7.  **[Agent 6: DECISION AGENT]** (`decision.py`)
    *   The Supreme Arbiter. Evaluates Backtest #1 constraints vs Backtest #2. Weights the improvements against overfitting. Generates absolute scores, picks a winner, provides plain-English reasoning, and delivers a final recommended plan of action.

---

## 🛠 Tech Stack

**Frontend Capabilities**
*   **HTML5/CSS3:** Fully bespoke responsive layouts with CSS Custom Properties, modern Flexbox/Grid routing.
*   **Vanilla JavaScript:** Lightweight but powerful DOM manipulation, precise asynchronous `fetch` calls, dynamic JSON parsing.
*   **Chart.js**: Client-side data visualization and dynamic plotting.

**Backend Capabilities**
*   **Python 3.9+:** Core programming runtime.
*   **FastAPI:** Asynchronous, high-performance web framework for the single `POST /run-system` REST endpoint orchestrator.
*   **Uvicorn:** Production-grade ASGI server running the FastAPI environment.
*   **Google GenAI SDK (`google-genai`):** Deep API integration connecting to Google Gemini LLMs for reasoning, interpreting, and intelligent logic creation.
*   **Pandas & NumPy:** Highly vectorized internal dataframe calculations.
*   **yfinance:** Reliable external integration for fetching live and historical ticker OHLCV data.

---

## 🚀 Setup & Execution Instructions

### Step 1: Clone and Prepare
Make sure you have Python 3.9 or later installed.
```bash
# Navigate to project
cd autotrader_mas

# Create & activate a virtual isolated environment
python -m venv venv
source venv/bin/activate  # on Windows, use `venv\Scripts\activate`
```

### Step 2: Install Depedencies
```bash
pip install -r requirements.txt
```

### Step 3: API Key Configuration
Create a `.env` file in the root directory (or use terminal exports). The AI logic requires a Gemini API Key.
```bash
GEMINI_API_KEY=your_gemini_key_here
```
*(If no API Key is provided, the backend falls back securely to hard-coded mock data so the app can still be tested locally!)*

### Step 4: Run the Backend Application Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```
*The server will start successfully at `http://127.0.0.1:8000`.*

### Step 5: Boot Up the Interactive UI
Since the frontend operates statelessly through Vanilla JS/HTML:
1. Navigate to the `/frontend` directory in your file explorer.
2. Double click `index.html` to open it in any modern browser.
3. Use the interface to type in natural language, and hit **"Play/Deploy Agents"!**

---

## ⚠️ Disclosure
*AutoTrader AI was originally built for a hackathon. The trades, evaluations, and optimizations generated by this model are simulations and **do not constitute real financial advice**. Do not connect these scripts to a live brokerage without human verification and further backtesting logic!*
