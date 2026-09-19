const state = { period: 'ALL', rows: [], allRows: [], chart: null, candleSeries: null, replayIndex: 0, replayTimer: null };
const $ = (selector) => document.querySelector(selector);
let supabaseClient = null;
let authSession = null;
let authMode = 'signup';

function updateAuthNav() {
  const signupLink = document.querySelector('.public-nav a[data-view="signup"]');
  if (signupLink) signupLink.hidden = Boolean(authSession);
}

function setAuthMode(mode) {
  authMode = mode;
  const signup = mode === 'signup';
  $('#auth-title').textContent = signup ? 'Create your Pulse account' : 'Welcome back to Pulse';
  $('#auth-description').textContent = signup ? 'It takes less than a minute.' : 'Sign in to open your workspace.';
  $('#name-field').hidden = !signup;
  $('#terms-field').hidden = !signup;
  $('#signup-name').required = signup;
  $('#terms-field input').required = signup;
  $('#signup-password').autocomplete = signup ? 'new-password' : 'current-password';
  $('#auth-submit').innerHTML = signup ? 'Create account <span>↗</span>' : 'Sign in <span>↗</span>';
  $('#auth-switch-copy').textContent = signup ? 'Already have an account?' : 'Need an account?';
  $('#auth-switch').textContent = signup ? 'Sign in' : 'Create one';
  $('#auth-error').textContent = '';
}

function showAuthError(message) { $('#auth-error').textContent = message; }

async function initAuth() {
  try {
    const config = await request('/api/auth/config');
    if (!config.url || !config.anon_key) return;
    const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
    supabaseClient = createClient(config.url, config.anon_key);
    supabaseClient.auth.onAuthStateChange((_event, session) => {
      authSession = session;
      updateAuthNav();
      if (session) {
        localStorage.removeItem('pulse-user');
        showView('dashboard');
      }
    });
    const { data: { session } } = await supabaseClient.auth.getSession();
    authSession = session;
    updateAuthNav();
    if (session) showView('dashboard');
  } catch (error) {
    showAuthError('Supabase is not configured yet. Add the auth environment variables to continue.');
  }
}

function showView(view) {
  document.querySelectorAll('.public-view').forEach((section) => { section.hidden = section.id !== `${view}-view`; });
  document.querySelector('.public-topbar').classList.toggle('dashboard-nav', view === 'dashboard');
  if (view === 'dashboard' && !state.chart) { makeChart(); loadPeriod(); }
  if (view !== 'dashboard' && state.chart) { state.chart.applyOptions({ width: 0, height: 0 }); }
  window.location.hash = view === 'home' ? '' : view;
}

document.querySelectorAll('[data-view]').forEach((control) => control.addEventListener('click', () => showView(control.dataset.view)));
$('#auth-switch').addEventListener('click', () => setAuthMode(authMode === 'signup' ? 'signin' : 'signup'));
$('#signup-form').addEventListener('submit', (event) => {
  event.preventDefault();
  showAuthError('');
  if (!supabaseClient) { showAuthError('Supabase is not configured yet.'); return; }
  const email = $('#signup-email').value.trim();
  const password = $('#signup-password').value;
  const name = $('#signup-name').value.trim();
  const submit = $('#auth-submit');
  submit.disabled = true;
  (async () => {
    try {
      const result = authMode === 'signup'
        ? await supabaseClient.auth.signUp({ email, password, options: { data: { full_name: name } } })
        : await supabaseClient.auth.signInWithPassword({ email, password });
      if (result.error) throw result.error;
      if (authMode === 'signup' && !result.data.session) {
        showToast('Check your email to confirm your account.');
        setAuthMode('signin');
      } else {
        showToast(`Welcome${name ? `, ${name.split(' ')[0]}` : ''}.`);
        showView('dashboard');
      }
    } catch (error) { showAuthError(error.message || 'Authentication failed.'); }
    finally { submit.disabled = false; }
  })();
});

function chartSize() {
  const container = $('#chart');
  const styles = getComputedStyle(container);
  const horizontalPadding = parseFloat(styles.paddingLeft) + parseFloat(styles.paddingRight);
  const verticalPadding = parseFloat(styles.paddingTop) + parseFloat(styles.paddingBottom);
  return {
    width: Math.max(0, container.clientWidth - horizontalPadding),
    height: Math.max(0, container.clientHeight - verticalPadding),
  };
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || 'Request failed');
  return payload;
}

function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.style.borderColor = isError ? 'var(--coral)' : 'var(--teal-dim)';
  toast.style.color = isError ? 'var(--coral)' : 'var(--teal)';
  toast.classList.add('visible');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('visible'), 2800);
}

function makeChart() {
  const container = $('#chart');
  const size = chartSize();
  container.insertAdjacentHTML('beforeend', '<div class="chart-empty" id="chart-empty">Fetch a stock symbol or import a CSV to begin.</div>');
  if (state.chart) state.chart.remove();
  state.chart = LightweightCharts.createChart(container, {
    width: size.width,
    height: size.height,
    layout: { background: { type: 'solid', color: '#111820' }, textColor: '#89919b', fontFamily: 'DM Sans' },
    grid: { vertLines: { color: '#202a33' }, horzLines: { color: '#202a33' } },
    rightPriceScale: { borderColor: '#25303a', scaleMargins: { top: 0.12, bottom: 0.1 } },
    timeScale: { borderColor: '#25303a', timeVisible: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  });
  state.candleSeries = state.chart.addCandlestickSeries({
    upColor: '#42e1bd', downColor: '#ff6c75', borderUpColor: '#42e1bd', borderDownColor: '#ff6c75', wickUpColor: '#42e1bd', wickDownColor: '#ff6c75',
  });
  state.chart.timeScale().fitContent();
}

function renderChart(rows = state.rows) {
  if (!state.chart) makeChart();
  $('#chart-empty').hidden = rows.length > 0;
  state.candleSeries.setData(rows.map(({ time, open, high, low, close }) => ({ time, open, high, low, close })));
  const markers = rows.filter((row) => ['LONG', 'SHORT'].includes(row.direction)).map((row) => ({ time: row.time, position: row.direction === 'LONG' ? 'belowBar' : 'aboveBar', color: row.direction === 'LONG' ? '#42e1bd' : '#ff6c75', shape: row.direction === 'LONG' ? 'arrowUp' : 'arrowDown', text: row.direction }));
  state.candleSeries.setMarkers(markers);
  state.chart.timeScale().fitContent();
}

function formatNumber(value, digits = 2) { return Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits }); }
function formatVolume(value) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 }); }

function renderSummary(summary) {
  if (!summary || !summary.total_days) {
    $('#metric-days').textContent = '—';
    $('#metric-average').textContent = '—';
    $('#metric-signals').textContent = '—';
    $('#metric-long').textContent = '—';
    $('#metric-short').textContent = '—';
    $('#metric-change').textContent = '—';
    $('#metric-change').style.color = 'var(--ink)';
    $('#metric-range').textContent = 'No data loaded';
    $('#metric-period').textContent = `${state.period} period`;
    return;
  }
  $('#metric-days').textContent = Number(summary.total_days).toLocaleString();
  $('#metric-average').textContent = `$${formatNumber(summary.avg_price)}`;
  $('#metric-signals').textContent = `${summary.long_signals}:${summary.short_signals}`;
  $('#metric-long').textContent = summary.long_signals;
  $('#metric-short').textContent = summary.short_signals;
  const change = Number(summary.price_change);
  $('#metric-change').textContent = `${change >= 0 ? '+' : ''}${formatNumber(change)}%`;
  $('#metric-change').style.color = change >= 0 ? 'var(--teal)' : 'var(--coral)';
  $('#metric-range').textContent = `High $${formatNumber(summary.max_price)} / Low $${formatNumber(summary.min_price)}`;
  $('#metric-period').textContent = `${state.period} period`;
}

function renderTable(rows) {
  const tbody = $('#data-table');
  tbody.innerHTML = rows.slice(-12).reverse().map((row) => {
    const signalClass = row.direction === 'LONG' ? 'signal-long' : row.direction === 'SHORT' ? 'signal-short' : 'signal-neutral';
    const range = ((row.high - row.low) / row.low * 100).toFixed(2);
    return `<tr><td>${row.time}</td><td>$${formatNumber(row.close)}</td><td>${range}%</td><td>${formatVolume(row.volume)}</td><td><span class="signal ${signalClass}">${row.direction}</span></td></tr>`;
  }).join('');
  $('#row-count').textContent = `${rows.length.toLocaleString()} rows`;
}

async function loadPeriod(period = state.period) {
  state.period = period;
  document.querySelectorAll('.period-button').forEach((button) => button.classList.toggle('active', button.dataset.period === period));
  try {
    const [data, summary] = await Promise.all([request(`/api/data?period=${period}`), request(`/api/summary?period=${period}`)]);
    state.rows = data.rows;
    state.allRows = period === 'ALL' ? data.rows : state.allRows;
    const symbol = data.symbol || 'No symbol';
    $('#symbol-name').textContent = symbol;
    $('#chart-symbol').textContent = symbol;
    document.title = data.symbol ? `${data.symbol} | Pulse` : 'Pulse | Stock Intelligence';
    renderChart(); renderSummary(summary); renderTable(state.rows);
    $('#last-updated').textContent = `Updated ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    resetReplay();
  } catch (error) { showToast(error.message, true); }
}

async function fetchSymbol(symbol) {
  const submit = $('#symbol-submit');
  submit.disabled = true;
  submit.textContent = 'Loading...';
  try {
    const response = await request('/api/data/alphavantage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol }),
    });
    await loadPeriod('ALL');
  } catch (error) {
    showToast(error.message, true);
  } finally {
    submit.disabled = false;
    submit.textContent = 'Fetch';
  }
}

function addChat(question, answer) {
  const history = $('#chat-history');
  const empty = history.querySelector('.empty-chat');
  if (empty) empty.remove();
  const item = document.createElement('div'); item.className = 'chat-item';
  item.innerHTML = `<p class="chat-question">${question}</p><p class="chat-answer"></p>`;
  item.querySelector('.chat-answer').textContent = answer;
  history.prepend(item);
}

async function ask(question) {
  if (!question.trim()) return;
  $('#question').value = question;
  try {
    const response = await request('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, period: state.period }) });
    addChat(question, response.answer);
  } catch (error) { addChat(question, error.message); }
}

function updateReplay() {
  const visibleRows = state.rows.slice(0, state.replayIndex + 1);
  renderChart(visibleRows);
  const total = state.rows.length;
  const progress = total ? (visibleRows.length / total) * 100 : 0;
  $('#replay-bar').style.width = `${progress}%`;
  $('#replay-count').textContent = `${visibleRows.length} / ${total}`;
  $('#replay-label').textContent = visibleRows.length ? visibleRows[visibleRows.length - 1].time : 'Ready';
}
function resetReplay() { window.clearInterval(state.replayTimer); state.replayTimer = null; state.replayIndex = 0; $('#replay-toggle').textContent = 'Start replay'; if (state.rows.length) updateReplay(); }
function toggleReplay() {
  if (state.replayTimer) { window.clearInterval(state.replayTimer); state.replayTimer = null; $('#replay-toggle').textContent = 'Resume replay'; return; }
  if (state.replayIndex >= state.rows.length - 1) state.replayIndex = 0;
  $('#replay-toggle').textContent = 'Pause replay';
  state.replayTimer = window.setInterval(() => { state.replayIndex += 1; updateReplay(); if (state.replayIndex >= state.rows.length - 1) { window.clearInterval(state.replayTimer); state.replayTimer = null; $('#replay-toggle').textContent = 'Replay complete'; } }, Number($('#replay-speed').value));
}

window.addEventListener('resize', () => { if (state.chart) state.chart.applyOptions(chartSize()); });
document.querySelectorAll('.period-button').forEach((button) => button.addEventListener('click', () => loadPeriod(button.dataset.period)));
document.querySelectorAll('.question-chip').forEach((button) => button.addEventListener('click', () => ask(button.textContent)));
$('#ask-form').addEventListener('submit', (event) => { event.preventDefault(); ask($('#question').value); });
$('#symbol-form').addEventListener('submit', (event) => { event.preventDefault(); fetchSymbol($('#symbol-input').value.trim().toUpperCase()); });
$('#refresh-button').addEventListener('click', () => loadPeriod());
$('#replay-toggle').addEventListener('click', toggleReplay);
$('#replay-reset').addEventListener('click', resetReplay);
$('#csv-upload').addEventListener('change', async (event) => { const [file] = event.target.files; if (!file) return; const body = new FormData(); body.append('file', file); try { const response = await request('/api/data/upload', { method: 'POST', body }); showToast(`${response.symbol} loaded`); await loadPeriod('ALL'); } catch (error) { showToast(error.message, true); } });

showView(window.location.hash.slice(1) || 'home');
setAuthMode('signup');
initAuth();
