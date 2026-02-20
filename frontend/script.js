const state = { dataset: null, signals: [], panel: null };

const views = [...document.querySelectorAll('.view')];
document.querySelectorAll('nav button').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('nav button').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    views.forEach((v) => v.classList.remove('active'));
    document.getElementById(btn.dataset.view).classList.add('active');
  });
});

async function loadDataset() {
  const res = await fetch('/api/master-dataset');
  state.dataset = await res.json();
}

async function runScan() {
  const horizon = document.getElementById('horizon').value;
  const minConfidence = document.getElementById('minConfidence').value;
  const res = await fetch(`/api/signals?horizon=${horizon}&min_confidence=${minConfidence}`);
  const data = await res.json();
  state.signals = data.signals;
  renderAll();
  loadPanel();
}

async function loadPanel() {
  const res = await fetch('/api/ai-trader-panel');
  state.panel = await res.json();
  renderTraderPanel();
}

function signalFor(symbol) {
  return state.signals.find((s) => s.symbol === symbol) || {};
}

function renderGrid() {
  const root = document.getElementById('grid');
  root.innerHTML = '';
  state.dataset.stocks.forEach((stock) => {
    const sig = signalFor(stock.symbol);
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <h3>${stock.stock_name} (${stock.symbol})</h3>
      <p>${stock.exchange} • ${stock.sector} • ${stock.market_cap_category}</p>
      <p class="price ${stock.percent_change >= 0 ? 'up' : 'down'}">₹${stock.current_price} (${stock.percent_change}%)</p>
      <details>
        <summary>AI Recommendation</summary>
        <p><b>${sig.signal || 'N/A'}</b> • Confidence: ${sig.confidence_score || '-'}%</p>
        <p>Target: ₹${sig.target_price || '-'} | Stop: ₹${sig.stop_loss || '-'}</p>
        <p>Entry: ${sig.entry_range ? `₹${sig.entry_range[0]} - ₹${sig.entry_range[1]}` : '-'}</p>
      </details>
    `;
    root.appendChild(card);
  });
}

function renderHeatmap(key, elId) {
  const box = document.getElementById(elId);
  box.className = 'view active heatmap';
  const groups = {};
  state.dataset.stocks.forEach((s) => {
    const keys = Array.isArray(s[key]) ? s[key] : [s[key]];
    keys.forEach((k) => {
      if (!groups[k]) groups[k] = [];
      groups[k].push(s.percent_change);
    });
  });
  box.innerHTML = Object.entries(groups).map(([k, arr]) => {
    const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
    const color = avg >= 0 ? `rgba(43,214,123,${Math.min(Math.abs(avg) / 4, 0.9)})` : `rgba(255,94,118,${Math.min(Math.abs(avg) / 4, 0.9)})`;
    return `<div class="tile" style="background:${color}">${k}<br/><b>${avg.toFixed(2)}%</b></div>`;
  }).join('');
}

function renderScanner() {
  const root = document.getElementById('scanner');
  root.innerHTML = '<div class="scanner-row"><b>Symbol</b><b>RSI</b><b>MACD</b><b>Volatility</b><b>Signal</b></div>';
  [...state.dataset.stocks]
    .sort((a, b) => b.technical_indicators.rsi - a.technical_indicators.rsi)
    .forEach((s) => {
      const sig = signalFor(s.symbol);
      root.innerHTML += `<div class="scanner-row"><span>${s.symbol}</span><span>${s.technical_indicators.rsi}</span><span>${s.technical_indicators.macd}</span><span>${s.volatility}</span><span>${sig.signal || '-'}</span></div>`;
    });
}

function renderFeed() {
  const root = document.getElementById('feed');
  root.innerHTML = state.signals.map((s) => `
    <div class="feed-item">
      <b>${s.symbol} • ${s.signal}</b>
      <p>${s.reasoning_summary}</p>
      <small>${new Date(s.recommended_at).toLocaleString()} | Target ₹${s.target_price} | Stop ₹${s.stop_loss}</small>
    </div>
  `).join('');
}

function renderTraderPanel() {
  const root = document.getElementById('trader');
  if (!state.panel) return;
  const p = state.panel.panel;
  root.innerHTML = `
    <div class="stats">
      <div class="stat">Total Predictions<br/><b>${p.total_predictions}</b></div>
      <div class="stat">Accuracy %<br/><b>${p.accuracy_pct}</b></div>
      <div class="stat">Win/Loss<br/><b>${p.win_loss_ratio}</b></div>
      <div class="stat">Avg Return<br/><b>${p.average_return_per_trade}%</b></div>
      <div class="stat">Best Sector<br/><b>${p.best_performing_sector}</b></div>
      <div class="stat">Worst Sector<br/><b>${p.worst_performing_sector}</b></div>
      <div class="stat">Live Open Signals<br/><b>${p.live_open_signals}</b></div>
    </div>
    <h3>Equity Curve</h3>
    <p>${p.equity_curve.join(' → ') || 'Insufficient closed signals'}</p>
    <h3>Monthly Performance Report</h3>
    <pre>${JSON.stringify(p.monthly_performance, null, 2)}</pre>
    <h3>Strategy Breakdown</h3>
    <pre>${JSON.stringify(p.strategy_breakdown, null, 2)}</pre>
  `;
}

function renderAll() {
  renderGrid();
  renderHeatmap('sector', 'heatmap-sector');
  renderHeatmap('index_membership', 'heatmap-index');
  renderScanner();
  renderFeed();
}

document.getElementById('load').addEventListener('click', runScan);

(async function init() {
  await loadDataset();
  await runScan();
})();
