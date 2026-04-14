'use strict';

// ── Tab navigation ──
function showTab(id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.ntab').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  document.querySelectorAll('.ntab').forEach(b => {
    const map = {predict:'predict',history:'history',model:'model'};
    if (b.getAttribute('onclick').includes(id)) b.classList.add('active');
  });
  if (id === 'history') loadHistory();
  if (id === 'model')   loadMetrics();
}

// ── Home type sync ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[name="home_type"]').forEach(r => {
    r.addEventListener('change', () => {
      document.getElementById('home_type_input').value = r.value;
    });
  });
  // Init slider gradient fills
  ['s-temp','s-irr','s-hum','s-wind'].forEach(updateSliderFill);
});

// ── Slider / input sync ──
function syncNum(inputId, valId, val, unit) {
  document.getElementById(inputId).value = val;
  document.getElementById(valId).textContent = val + unit;
  updateSliderFill(
    {temp:'s-temp',irradiance:'s-irr',humidity:'s-hum',windspeed:'s-wind'}[inputId] ||
    document.getElementById(inputId).closest('.field').querySelector('.aero-slider').id
  );
}
function syncSlider(inputId, sliderId, val, unit) {
  document.getElementById(sliderId).value = val;
  const labelMap = {temperature:'v-temp',irradiance:'v-irr',humidity:'v-hum',windspeed:'v-wind'};
  if (labelMap[inputId]) document.getElementById(labelMap[inputId]).textContent = val + unit;
  updateSliderFill(sliderId);
}
function updateSliderFill(sliderId) {
  const sl = typeof sliderId === 'string' ? document.getElementById(sliderId) : sliderId;
  if (!sl) return;
  const pct = ((sl.value - sl.min) / (sl.max - sl.min)) * 100;
  sl.style.setProperty('--pct', pct + '%');
  sl.style.background = `linear-gradient(90deg,var(--gold) ${pct}%,rgba(255,255,255,0.1) ${pct}%)`;
}

// ── Prediction ──
let miniChart = null;

async function runPrediction(e) {
  e.preventDefault();
  const btn = document.getElementById('run-btn');
  btn.classList.add('loading');
  document.getElementById('btn-text').innerHTML = '<span class="spinner"></span> Analysing…';

  const fd = new FormData(document.getElementById('predict-form'));

  try {
    const res  = await fetch('/predict', { method: 'POST', body: fd });
    const d    = await res.json();
    if (d.error) throw new Error(d.error);
    renderResults(d);
    buildChart(parseFloat(fd.get('irradiance')), d.actual_kw, d.capacity_kwp);
  } catch(err) {
    alert('Error: ' + err.message);
  } finally {
    btn.classList.remove('loading');
    document.getElementById('btn-text').innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg> Analyse Solar Potential';
  }
}

function inr(n) {
  return '₹' + Math.round(n).toLocaleString('en-IN');
}
function num(n, d=1) { return Number(n).toFixed(d); }

function renderResults(d) {
  document.getElementById('empty-state').style.display = 'none';
  document.getElementById('result-cards').style.display = 'flex';

  // Hero
  document.getElementById('r-home-label').textContent = d.home_label;
  document.getElementById('r-kw').textContent          = num(d.actual_kw, 3);
  document.getElementById('r-daily').textContent       = num(d.daily_kwh, 1);
  document.getElementById('r-monthly-gen').textContent = num(d.monthly_gen, 0);
  document.getElementById('r-eff').textContent         = num(d.efficiency_pct, 0);

  // Efficiency ring
  const circ = 251.2;
  const offset = circ - (d.efficiency_pct / 100) * circ;
  const arc = document.getElementById('eff-arc');
  if (arc) { arc.style.strokeDashoffset = offset; }

  // Coverage bar
  document.getElementById('r-cover').textContent   = d.cover_pct + '%';
  document.getElementById('cov-bar').style.width   = Math.min(d.cover_pct, 100) + '%';
  document.getElementById('r-gen-units').textContent = num(d.offset_kwh, 0);
  document.getElementById('r-use-units').textContent = d.monthly_use;

  // Bills
  document.getElementById('r-normal-bill').textContent  = inr(d.normal_bill);
  document.getElementById('r-remaining').textContent    = inr(d.remaining_bill);
  document.getElementById('r-savings').textContent      = inr(d.savings_monthly);

  // Stats
  document.getElementById('r-yr-savings').textContent = inr(d.savings_yearly);
  document.getElementById('r-co2').textContent         = num(d.co2_monthly, 1);
  document.getElementById('r-trees').textContent       = num(d.trees_equiv, 1);
  document.getElementById('r-tilt').textContent        = d.tilt_angle + '°';

  // Reco
  document.getElementById('r-time').textContent      = d.best_time;
  document.getElementById('r-time-desc').textContent = d.time_desc;
  document.getElementById('r-tip').textContent       = d.efficiency_tip;
}

function buildChart(curIrrad, curKw, capacityKwp) {
  const ctx = document.getElementById('mini-chart').getContext('2d');
  const slope = capacityKwp / 1000;
  const curve = [];
  for (let i = 0; i <= 1000; i += 50)
    curve.push({ x: i, y: parseFloat((i * slope * 0.75).toFixed(3)) });

  if (miniChart) miniChart.destroy();
  miniChart = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [
        {
          label: 'Typical output curve',
          data: curve,
          borderColor: 'rgba(245,166,35,0.7)',
          backgroundColor: 'rgba(245,166,35,0.06)',
          borderWidth: 1.5, pointRadius: 0, fill: true, tension: 0.4,
        },
        {
          label: 'Your reading',
          data: [{ x: curIrrad, y: parseFloat(curKw.toFixed(3)) }],
          borderColor: '#2ee8a0', backgroundColor: '#2ee8a0',
          borderWidth: 2, pointRadius: 8, showLine: false,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { type:'linear',
             title:{ display:true, text:'Irradiance (W/m²)', color:'#3a4560', font:{size:10} },
             grid:{ color:'rgba(255,255,255,0.04)' },
             ticks:{ color:'#3a4560', font:{size:10} } },
        y: { title:{ display:true, text:'Output (kW)', color:'#3a4560', font:{size:10} },
             grid:{ color:'rgba(255,255,255,0.04)' },
             ticks:{ color:'#3a4560', font:{size:10} }, min:0 },
      },
      plugins: {
        legend:{ display:false },
        tooltip:{
          backgroundColor:'rgba(10,14,28,0.9)',
          borderColor:'rgba(255,255,255,0.1)', borderWidth:1,
          titleColor:'#dde4f0', bodyColor:'#7a8aaa',
        },
      },
    },
  });
}

// ── History ──
async function loadHistory() {
  const tb = document.getElementById('hist-body');
  tb.innerHTML = '<tr><td colspan="10" class="empty-cell">Loading…</td></tr>';
  try {
    const rows = await (await fetch('/history')).json();
    if (!rows.length) {
      tb.innerHTML = '<tr><td colspan="10" class="empty-cell">No predictions yet.</td></tr>';
      return;
    }
    tb.innerHTML = rows.map(r => `
      <tr>
        <td>${r.id}</td>
        <td>${(r.timestamp||'').replace('T',' ').slice(0,19)}</td>
        <td style="text-transform:uppercase;color:var(--gold)">${r.home_type||'—'}</td>
        <td>${(+r.temperature).toFixed(1)}°C</td>
        <td>${(+r.humidity).toFixed(0)}%</td>
        <td>${(+r.windspeed).toFixed(1)}</td>
        <td>${(+r.irradiance).toFixed(0)}</td>
        <td style="color:var(--gold);font-weight:600">${(+r.actual_kw).toFixed(3)}</td>
        <td style="color:var(--green)">₹${Math.round(+r.savings_monthly).toLocaleString('en-IN')}</td>
        <td>${(+r.co2_reduction).toFixed(1)}</td>
      </tr>`).join('');
  } catch(err) {
    tb.innerHTML = `<tr><td colspan="10" class="empty-cell">Error: ${err.message}</td></tr>`;
  }
}

// ── Model metrics ──
async function loadMetrics() {
  const div = document.getElementById('metrics-div');
  div.textContent = 'Loading…';
  try {
    const m = await (await fetch('/metrics')).json();
    const pill = t => `<span class="best-pill">${t}</span>`;
    const block = (title, data, best) => `
      <div class="mblock">
        <div class="mblock-title">${title} ${best ? pill('Best') : ''}</div>
        ${Object.entries(data).map(([k,v])=>`
          <div class="mrow"><span class="lbl">${k.toUpperCase()}</span>
          <span class="val">${Number(v).toFixed(4)}</span></div>`).join('')}
      </div>`;
    div.innerHTML = `
      <p style="font-size:13px;color:var(--text2);margin-bottom:14px">
        Trained on <strong style="color:var(--text)">${(m.training_samples||0).toLocaleString()}</strong> samples ·
        Test set <strong style="color:var(--text)">${(m.test_samples||0).toLocaleString()}</strong>
      </p>
      <div class="metrics-grid">
        ${block('Multiple Linear Regression', m.linear||{}, m.best_model==='linear')}
        ${block('Polynomial Regression (deg 2)', m.polynomial||{}, m.best_model==='polynomial')}
      </div>
      <p style="font-size:11px;color:var(--text3);margin-top:12px;font-family:var(--fm)">
        Features: ${(m.features||[]).join(' · ')}
      </p>`;
  } catch(err) {
    div.innerHTML = `<span style="color:var(--red)">Failed: ${err.message}</span>`;
  }
}

// ── Solar panel background canvas ──
(function initBg() {
  const canvas = document.getElementById('bg-canvas');
  const ctx    = canvas.getContext('2d');
  let W, H;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    drawPanels();
  }

  function drawPanels() {
    ctx.clearRect(0, 0, W, H);
    const cols = Math.ceil(W / 80) + 1;
    const rows = Math.ceil(H / 56) + 1;
    ctx.strokeStyle = 'rgba(245,166,35,0.6)';
    ctx.lineWidth   = 0.5;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = c * 80;
        const y = r * 56;
        // Panel outline
        ctx.strokeRect(x + 4, y + 4, 72, 48);
        // Internal cell lines (3 cols x 2 rows = 6 cells per panel)
        for (let ci = 1; ci < 3; ci++) {
          ctx.beginPath();
          ctx.moveTo(x + 4 + ci * 24, y + 4);
          ctx.lineTo(x + 4 + ci * 24, y + 52);
          ctx.stroke();
        }
        ctx.beginPath();
        ctx.moveTo(x + 4, y + 28);
        ctx.lineTo(x + 76, y + 28);
        ctx.stroke();
      }
    }
  }

  window.addEventListener('resize', resize);
  resize();
})();