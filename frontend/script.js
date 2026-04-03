/**
 * AutoTrader AI — Multi-Agent System — Frontend Script
 * =====================================================
 * Responsibilities:
 *   1. Animate the agent pipeline in real time (simulated streaming)
 *   2. Call POST /run-system and receive full results
 *   3. Render metrics, strategy rules, charts, risk, market, decision
 *   4. Build Chart.js price charts with buy/sell markers
 */

// Automatically use localhost during local development (Live Server or double-clicked file).
// When hosted fully on Vercel, use an empty string so requests are relative to the domain!
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.protocol === "file:";
const API_BASE = isLocal ? "http://localhost:8000" : "";

// ── DOM refs ─────────────────────────────────────────────────────────────
const runBtn        = document.getElementById("run-btn");
const runBtnText    = document.getElementById("run-btn-text");
const errorDisplay  = document.getElementById("error-display");
const resultsArea   = document.getElementById("results-area");
const preRun        = document.getElementById("pre-run");
const sysStatus     = document.getElementById("sys-status");

// Agent node IDs → mapped to pipeline step order
const AGENT_NODES = [
  { id: "ag-interpreter",  label: "INTERPRETER",   delay: 300  },
  { id: "ag-backtester-1", label: "BACKTESTER #1", delay: 1200 },
  { id: "ag-market",       label: "MARKET ANALYST",delay: 2400 },
  { id: "ag-risk",         label: "RISK MANAGER",  delay: 3200 },
  { id: "ag-optimizer",    label: "OPTIMIZER",     delay: 4000 },
  { id: "ag-backtester-2", label: "BACKTESTER #2", delay: 4800 },
  { id: "ag-decision",     label: "DECISION AGENT",delay: 5600 },
];

// Track Chart.js instances so we can destroy/recreate them
let chartOriginal  = null;
let chartOptimized = null;

// ── Clock ─────────────────────────────────────────────────────────────────
function updateClock() {
  document.getElementById("sys-time").textContent =
    new Date().toLocaleTimeString("en-US", { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ── Quick-load example strategies ─────────────────────────────────────────
document.querySelectorAll(".qs-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.getElementById("strategy-input").value = btn.dataset.s;
  });
});

// ── Pipeline animation helpers ────────────────────────────────────────────

function resetPipeline() {
  AGENT_NODES.forEach(({ id }) => {
    const node = document.getElementById(id);
    node.className = "pipeline-node" + (id === "ag-decision" ? " decision-node" : "");
    node.querySelector(".node-status").textContent = "IDLE";
    node.querySelector(".node-status").className   = "node-status idle";
  });
}

function setNodeState(id, state) {
  // state: "running" | "done"
  const node = document.getElementById(id);
  if (!node) return;
  const isDecision = id === "ag-decision";
  node.className = `pipeline-node${isDecision ? " decision-node" : ""} ${state}`;
  const statusEl = node.querySelector(".node-status");
  statusEl.textContent = state === "running" ? "ACTIVE" : "DONE ✓";
  statusEl.className   = `node-status ${state}`;
}

/**
 * Animates agent nodes sequentially during the API call.
 * Since the backend returns everything at once, we fake the streaming
 * using setTimeout offsets that roughly match expected processing time.
 */
function animatePipeline(onComplete) {
  AGENT_NODES.forEach(({ id, delay }, i) => {
    setTimeout(() => setNodeState(id, "running"), delay);
    // Mark done ~700ms after starting (except last)
    if (i < AGENT_NODES.length - 1) {
      setTimeout(() => setNodeState(id, "done"), delay + 700);
    }
  });
  // Complete callback fires after last expected animation
  if (onComplete) setTimeout(onComplete, 6400);
}

// ── MAIN RUN ──────────────────────────────────────────────────────────────

runBtn.addEventListener("click", runSystem);

async function runSystem() {
  const strategy = document.getElementById("strategy-input").value.trim();
  const symbol   = document.getElementById("symbol-input").value.trim();
  const period   = document.getElementById("period-select").value;

  if (!strategy) {
    showError("Please enter a trading strategy.");
    return;
  }

  // ── UI: loading state ──────────────────────────────────────────────────
  runBtn.disabled   = true;
  runBtnText.textContent = "▶ AGENTS RUNNING…";
  hideError();
  preRun.classList.add("hidden");
  resultsArea.classList.add("hidden");
  resetPipeline();

  sysStatus.textContent  = "● RUNNING";
  sysStatus.className    = "sys-indicator running";

  // Start pipeline animation (independent of API timing)
  animatePipeline(() => {
    // If API returns before animation ends, the response handler takes over.
    // If animation ends first, we just wait for the API.
  });

  try {
    const res = await fetch(`${API_BASE}/run-system`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ strategy, symbol, period }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Unknown server error");
    }

    // Mark all nodes done immediately if API returns early
    AGENT_NODES.forEach(({ id }) => setNodeState(id, "done"));

    // Small delay to let animation settle before rendering results
    await sleep(400);

    renderResults(data);

  } catch (err) {
    showError("Error: " + err.message);
    resetPipeline();
    preRun.classList.remove("hidden");
  } finally {
    runBtn.disabled  = false;
    runBtnText.textContent = "▶ DEPLOY AGENTS";
    sysStatus.textContent  = "● STANDBY";
    sysStatus.className    = "sys-indicator";
  }
}


// ══════════════════════════════════════════════════════════════════════════
//  RENDER RESULTS
// ══════════════════════════════════════════════════════════════════════════

function renderResults(data) {
  const { original_results, optimized_results, market_analysis,
          risk_analysis, final_decision, original_strategy, optimized_strategy } = data;

  // ── Metrics row ────────────────────────────────────────────────────────
  renderMetric("orig-profit",   original_results.profit_pct);
  renderMetric("opt-profit",    optimized_results.profit_pct);
  document.getElementById("orig-trades-wr").textContent =
    `${original_results.num_trades} trades · ${original_results.win_rate}% win rate`;
  document.getElementById("opt-trades-wr").textContent =
    `${optimized_results.num_trades} trades · ${optimized_results.win_rate}% win rate`;

  // Risk
  const riskEl = document.getElementById("risk-level");
  riskEl.textContent = risk_analysis.level.toUpperCase().replace("_", " ");
  riskEl.className   = `mc-value risk-${risk_analysis.level}`;
  document.getElementById("risk-score").textContent = `Risk score: ${risk_analysis.score}/10`;

  // Decision winner
  const winner = final_decision.chosen;
  document.getElementById("winner-label").textContent = winner.toUpperCase();
  document.getElementById("winner-label").className   = `mc-value ${winner === "optimized" ? "positive" : ""}`;
  document.getElementById("winner-confidence").textContent =
    `Confidence: ${final_decision.confidence.toUpperCase()}`;

  // ── Strategy rules ─────────────────────────────────────────────────────
  renderRules("orig-rules-box", original_strategy, null);
  renderRules("opt-rules-box",  optimized_strategy, optimized_strategy.optimization_notes);

  // ── Charts ─────────────────────────────────────────────────────────────
  buildChart("chart-original",  original_results,  "chart-original");
  buildChart("chart-optimized", optimized_results, "chart-optimized");

  // ── Market Analyst ─────────────────────────────────────────────────────
  const mBadge = document.getElementById("market-badge");
  mBadge.textContent  = market_analysis.trend.toUpperCase();
  mBadge.className    = `agent-badge ${market_analysis.trend}`;
  document.getElementById("market-summary").textContent = market_analysis.summary;

  const det = market_analysis.details || {};
  document.getElementById("market-stats").innerHTML = `
    <div class="stat-mini"><div class="stat-mini-label">MOMENTUM</div>
      <div class="stat-mini-val">${(det.momentum_pct||0) > 0 ? "+" : ""}${(det.momentum_pct||0).toFixed(1)}%</div></div>
    <div class="stat-mini"><div class="stat-mini-label">VOLATILITY</div>
      <div class="stat-mini-val">${(market_analysis.volatility||"?").toUpperCase()}</div></div>
    <div class="stat-mini"><div class="stat-mini-label">PERIOD HIGH</div>
      <div class="stat-mini-val">$${det.period_high||"?"}</div></div>
    <div class="stat-mini"><div class="stat-mini-label">AVG DAILY MOVE</div>
      <div class="stat-mini-val">${det.avg_daily_move||"?"}%</div></div>
  `;

  // ── Risk Manager ───────────────────────────────────────────────────────
  const rBadge = document.getElementById("risk-badge");
  rBadge.textContent = risk_analysis.level.toUpperCase().replace("_"," ");
  rBadge.className   = `agent-badge ${risk_analysis.level}`;
  document.getElementById("risk-explanation").textContent = risk_analysis.explanation;

  const flagsEl = document.getElementById("risk-flags");
  flagsEl.innerHTML = (risk_analysis.flags || [])
    .map(f => `<div class="flag-item">⚠ ${f}</div>`)
    .join("");

  // ── Optimizer notes ────────────────────────────────────────────────────
  document.getElementById("optimizer-notes").textContent =
    optimized_strategy.optimization_notes || "No significant changes proposed.";

  // ── Decision Agent ─────────────────────────────────────────────────────
  const sOrig = final_decision.score_original;
  const sOpt  = final_decision.score_optimized;
  const maxS  = Math.max(sOrig, sOpt, 1);

  document.getElementById("score-orig").textContent = `${sOrig}/100`;
  document.getElementById("score-opt").textContent  = `${sOpt}/100`;

  // Animate score bars
  setTimeout(() => {
    const bOrig = document.getElementById("sbar-orig");
    const bOpt  = document.getElementById("sbar-opt");
    bOrig.style.width = `${(sOrig / maxS) * 100}%`;
    bOpt.style.width  = `${(sOpt  / maxS) * 100}%`;
    if (winner === "original")  { bOrig.classList.add("winner"); }
    else                        { bOpt.classList.add("winner");  }
  }, 300);

  document.getElementById("decision-reasoning").textContent = final_decision.reasoning;
  document.getElementById("action-plan").textContent        = final_decision.action_plan;

  // ── Trade log — show chosen strategy's trades ──────────────────────────
  const chosenResults = winner === "optimized" ? optimized_results : original_results;
  document.getElementById("trade-log-label").textContent =
    `${winner.toUpperCase()} STRATEGY — ${data.symbol}`;
  buildTradeLog(chosenResults.trades || []);

  // ── Show results ───────────────────────────────────────────────────────
  sysStatus.textContent = "● COMPLETE";
  sysStatus.className   = "sys-indicator done";
  resultsArea.classList.remove("hidden");
  resultsArea.scrollIntoView({ behavior: "smooth", block: "start" });
}


// ──────────────────────────────────────────────────────────────────────────
//  HELPERS
// ──────────────────────────────────────────────────────────────────────────

function renderMetric(id, profitPct) {
  const el = document.getElementById(id);
  el.textContent = `${profitPct >= 0 ? "+" : ""}${profitPct.toFixed(1)}%`;
  el.className   = `mc-value ${profitPct >= 0 ? "positive" : "negative"}`;
}

function renderRules(containerId, strategy, notes) {
  const el = document.getElementById(containerId);
  el.innerHTML = `
    <div class="rule-line">
      <span class="rule-tag entry">ENTRY</span>
      <span class="rule-code">${strategy.entry}</span>
    </div>
    <div class="rule-line">
      <span class="rule-tag exit">EXIT</span>
      <span class="rule-code">${strategy.exit}</span>
    </div>
    <p class="rule-desc">${strategy.description || ""}</p>
    ${notes ? `<p class="opt-notes">⚙ ${notes}</p>` : ""}
  `;
}

function buildTradeLog(trades) {
  const tbody = document.getElementById("trade-tbody");
  if (!trades.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted);text-align:center">No trades executed</td></tr>`;
    return;
  }
  tbody.innerHTML = trades.map((t, i) => `
    <tr>
      <td>${i + 1}${t.open ? " *" : ""}</td>
      <td>$${t.buy}</td>
      <td>$${t.sell}</td>
      <td class="${t.pct >= 0 ? "win" : "loss"}">${t.pct >= 0 ? "+" : ""}${t.pct.toFixed(2)}%</td>
      <td class="${t.pct >= 0 ? "win" : "loss"}">${t.pct >= 0 ? "WIN" : "LOSS"}</td>
    </tr>
  `).join("");
}

// ──────────────────────────────────────────────────────────────────────────
//  CHART BUILDER
// ──────────────────────────────────────────────────────────────────────────

function buildChart(canvasId, results, chartKey) {
  const canvas = document.getElementById(canvasId);

  // Destroy existing chart instance to avoid memory leaks
  if (chartKey === "chart-original"  && chartOriginal)  { chartOriginal.destroy(); }
  if (chartKey === "chart-optimized" && chartOptimized) { chartOptimized.destroy(); }

  const labels  = results.price_data.map(d => d.date);
  const prices  = results.price_data.map(d => d.price);
  const smaVals = results.sma_data  ? results.sma_data.map(d => d.value) : [];

  // Buy / Sell point scatter data
  const buyDates  = new Set(results.buy_signals.map(b => b.date));
  const sellDates = new Set(results.sell_signals.map(s => s.date));

  const buyPoints = results.price_data
    .filter(d => buyDates.has(d.date))
    .map(d => ({ x: d.date, y: d.price }));

  const sellPoints = results.price_data
    .filter(d => sellDates.has(d.date))
    .map(d => ({ x: d.date, y: d.price }));

  const datasets = [
    {
      label: "Price",
      data: prices,
      borderColor: "rgba(0,204,255,.8)",
      backgroundColor: "rgba(0,204,255,.04)",
      borderWidth: 1.5,
      fill: true,
      tension: 0.2,
      pointRadius: 0,
    },
  ];

  // SMA overlay (if data available)
  if (smaVals.length) {
    // Pad beginning with nulls to align with price_data
    const padCount = labels.length - smaVals.length;
    const paddedSma = Array(padCount).fill(null).concat(smaVals);
    datasets.push({
      label: results.sma_label || "SMA",
      data: paddedSma,
      borderColor: "rgba(255,170,0,.6)",
      borderWidth: 1,
      borderDash: [4, 3],
      fill: false,
      tension: 0.2,
      pointRadius: 0,
    });
  }

  // Buy markers
  datasets.push({
    label: "Buy",
    data: buyPoints,
    parsing: { xAxisKey: "x", yAxisKey: "y" },
    type: "scatter",
    pointStyle: "triangle",
    pointRadius: 8,
    backgroundColor: "rgba(0,255,136,.85)",
    borderColor: "rgba(0,255,136,1)",
    borderWidth: 1,
    showLine: false,
  });

  // Sell markers
  datasets.push({
    label: "Sell",
    data: sellPoints,
    parsing: { xAxisKey: "x", yAxisKey: "y" },
    type: "scatter",
    pointStyle: "triangle",
    rotation: 180,
    pointRadius: 8,
    backgroundColor: "rgba(255,51,85,.85)",
    borderColor: "rgba(255,51,85,1)",
    borderWidth: 1,
    showLine: false,
  });

  const instance = new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: {
          labels: { color: "rgba(200,216,232,.5)", font: { family: "Share Tech Mono", size: 10 }, boxWidth: 12 },
        },
        tooltip: {
          backgroundColor: "#0c1118",
          borderColor: "#1a2535",
          borderWidth: 1,
          titleColor: "#00ccff",
          bodyColor: "#c8d8e8",
          titleFont: { family: "Share Tech Mono" },
          bodyFont:  { family: "Share Tech Mono" },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "rgba(200,216,232,.3)",
            maxTicksLimit: 8,
            font: { family: "Share Tech Mono", size: 10 },
          },
          grid: { color: "rgba(26,37,53,.8)" },
        },
        y: {
          ticks: {
            color: "rgba(200,216,232,.3)",
            font: { family: "Share Tech Mono", size: 10 },
            callback: v => "$" + v.toLocaleString(),
          },
          grid: { color: "rgba(26,37,53,.8)" },
        },
      },
    },
  });

  if (chartKey === "chart-original")  chartOriginal  = instance;
  if (chartKey === "chart-optimized") chartOptimized = instance;
}

// ── Utility ───────────────────────────────────────────────────────────────
function showError(msg) {
  errorDisplay.textContent = msg;
  errorDisplay.classList.remove("hidden");
}
function hideError() {
  errorDisplay.classList.add("hidden");
}
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
