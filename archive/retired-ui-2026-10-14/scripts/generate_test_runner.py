"""
Generate PRT-0701-TestRunner.html with cases pre-embedded from the latest
compact JSON. Opening the file in any browser goes straight to run setup —
no file import step needed.

Run this script whenever the PRT console cases are updated.
"""
import json, re
from pathlib import Path
from datetime import datetime

ROOT         = Path(__file__).resolve().parents[1]
CASES_PATH   = ROOT / "output/console-update/PRT-0701-cases.json"
RUNNER_OUT   = ROOT / "PRT-0701-TestRunner.html"

cases  = json.loads(CASES_PATH.read_text(encoding="utf-8-sig"))
total  = len(cases)
gen_dt = datetime.now().strftime("%Y-%m-%d %H:%M")

# Embed cases as a JS literal (escape < to avoid closing script tags)
cases_js = (json.dumps(cases, ensure_ascii=False, separators=(",",":"))
            .replace("<", "\\u003c"))

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PRT-0701 Test Runner</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px;background:#f1f5f9;color:#1e293b;height:100vh;overflow:hidden;display:flex;flex-direction:column}

/* ── SETUP SCREEN ─────────────────────────────────── */
#setup-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;background:#0f172a;color:#e2e8f0;gap:16px}
#setup-screen h1{font-size:22px;font-weight:700;color:#f8fafc}
.case-source-badge{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:8px 18px;font-size:12px;color:#64748b;display:flex;align-items:center;gap:8px}
.case-source-badge strong{color:#22c55e}
#run-setup{background:#1e293b;border-radius:12px;padding:28px 32px;display:flex;flex-direction:column;gap:14px;width:440px}
#run-setup h2{color:#f1f5f9;font-size:15px;font-weight:600}
#run-setup input,#run-setup select{background:#0f172a;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:13px;outline:none;width:100%}
#run-setup input:focus{border-color:#3b82f6}
#run-setup label{color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px;display:block}
.field-row{display:flex;gap:12px}.field-row>div{flex:1}
#btn-start-run{background:#22c55e;color:#fff;border:none;border-radius:8px;padding:11px;font-size:13px;font-weight:700;cursor:pointer;width:100%;margin-top:4px;transition:background .2s}
#btn-start-run:hover{background:#16a34a}
.resume-divider{color:#334155;font-size:11px;text-align:center;width:440px}
#resume-box{background:#1e293b;border-radius:12px;padding:16px 20px;width:440px;max-height:220px;overflow-y:auto;display:none}
#resume-box h3{color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.run-item{padding:9px 12px;background:#0f172a;border-radius:8px;margin-bottom:7px;cursor:pointer;display:flex;align-items:center;gap:10px;transition:background .15s}
.run-item:hover{background:#172032}
.run-item-name{flex:1;color:#e2e8f0;font-size:12px;font-weight:600}
.run-item-meta{font-size:10px;color:#64748b}
.run-item-pct{font-size:12px;font-weight:700;color:#22c55e}
.run-item-del{background:transparent;border:none;color:#475569;cursor:pointer;font-size:14px;padding:0 4px}
.run-item-del:hover{color:#ef4444}

/* ── APP LAYOUT ───────────────────────────────────── */
#app{display:none;flex-direction:column;height:100vh}

/* HEADER */
#header{background:#0f172a;color:#e2e8f0;padding:0 14px;height:50px;display:flex;align-items:center;gap:12px;flex-shrink:0;border-bottom:1px solid #1e293b;position:relative}
#header h1{font-size:14px;font-weight:700;color:#f8fafc;white-space:nowrap}
.run-badge{background:#1e293b;border-radius:5px;padding:3px 9px;font-size:11px;color:#94a3b8;white-space:nowrap}
.run-badge strong{color:#e2e8f0}
.spacer{flex:1}
.stat-pill{display:flex;align-items:center;gap:4px;background:#1e293b;border-radius:5px;padding:3px 9px;font-size:12px;font-weight:700}
.stat-pill .lbl{font-size:9px;font-weight:400;color:#475569;text-transform:uppercase}
.vp{color:#22c55e}.vf{color:#ef4444}.vb{color:#f97316}.vs{color:#94a3b8}.vn{color:#475569}
#progress-wrap{width:100px;height:5px;background:#1e293b;border-radius:3px;overflow:hidden}
#progress-bar{height:100%;background:#22c55e;border-radius:3px;transition:width .3s}
#hdr-pct{font-size:11px;color:#64748b;white-space:nowrap}
.btn-hdr{background:#1e3a5f;color:#60a5fa;border:1px solid #1d4ed8;border-radius:5px;padding:4px 11px;font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap}
.btn-hdr:hover{background:#1d4ed8;color:#fff}
#btn-end-run{background:#1e293b;color:#64748b;border:1px solid #334155;border-radius:5px;padding:4px 9px;font-size:11px;cursor:pointer}
#btn-end-run:hover{background:#334155;color:#e2e8f0}

/* BODY */
#body{display:flex;flex:1;overflow:hidden}

/* SIDEBAR */
#sidebar{width:222px;flex-shrink:0;background:#fff;border-right:1px solid #e2e8f0;overflow-y:auto;display:flex;flex-direction:column}
#sb-head{padding:9px 11px;border-bottom:1px solid #e2e8f0;position:sticky;top:0;background:#fff;z-index:1}
#sb-head h3{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#64748b;margin-bottom:5px}
#search-box{width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px;padding:5px 8px;font-size:12px;outline:none;color:#1e293b}
#search-box:focus{border-color:#3b82f6}
.bi{padding:5px 11px;cursor:pointer;border-left:3px solid transparent;display:flex;align-items:center;gap:7px;transition:all .12s}
.bi:hover{background:#f8fafc}
.bi.active{background:#eff6ff;border-left-color:#3b82f6}
.bi-label{flex:1;font-size:11px;color:#64748b;line-height:1.3}
.bi.active .bi-label{color:#1d4ed8;font-weight:600}
.bi-bar{width:26px;height:4px;background:#e2e8f0;border-radius:2px;overflow:hidden;flex-shrink:0}
.bi-fill{height:100%;background:#22c55e;border-radius:2px}
.bi-cnt{font-size:10px;color:#94a3b8;flex-shrink:0}

/* STATUS FILTER */
#sf-bar{padding:7px 11px;display:flex;gap:5px;flex-wrap:wrap;border-bottom:1px solid #e2e8f0;background:#fafafa;flex-shrink:0}
.sf{padding:3px 9px;border-radius:10px;border:1px solid #e2e8f0;font-size:11px;font-weight:600;cursor:pointer;background:#fff;transition:all .12s}
.sf.aA{background:#1e293b;color:#fff;border-color:#1e293b}
.sf.aP{background:#dcfce7;color:#15803d;border-color:#86efac}
.sf.aF{background:#fee2e2;color:#b91c1c;border-color:#fca5a5}
.sf.aB{background:#ffedd5;color:#c2410c;border-color:#fdba74}
.sf.aS{background:#f1f5f9;color:#475569;border-color:#cbd5e1}
.sf.aN{background:#f1f5f9;color:#475569;border-color:#cbd5e1}

/* CASE LIST */
#case-area{display:flex;flex:1;overflow:hidden}
#case-list{flex:1;overflow-y:auto;background:#fff}
.cr{display:flex;align-items:center;padding:7px 13px;border-bottom:1px solid #f1f5f9;cursor:pointer;gap:9px;transition:background .1s}
.cr:hover{background:#f8fafc}
.cr.sel{background:#eff6ff;border-left:3px solid #3b82f6;padding-left:10px}
.cr-run{font-size:10px;color:#94a3b8;width:26px;text-align:right;flex-shrink:0}
.cr-id{font-size:10px;color:#64748b;width:155px;flex-shrink:0;font-family:monospace}
.cr-title{flex:1;font-size:12px;color:#1e293b;line-height:1.3}
.dot{width:21px;height:21px;border-radius:4px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700}
.dP{background:#dcfce7;color:#15803d}.dF{background:#fee2e2;color:#b91c1c}
.dB{background:#ffedd5;color:#c2410c}.dS{background:#f1f5f9;color:#64748b}.dN{background:#f1f5f9;color:#cbd5e1}

/* DETAIL */
#detail{width:430px;flex-shrink:0;background:#fff;border-left:1px solid #e2e8f0;display:none;flex-direction:column;overflow:hidden}
#detail.open{display:flex}
#dh{padding:11px 14px;border-bottom:1px solid #e2e8f0;flex-shrink:0;background:#fafafa;position:relative}
#d-id{font-size:10px;font-family:monospace;color:#64748b}
#d-title{font-size:14px;font-weight:600;color:#1e293b;margin:2px 0 4px}
#d-meta{display:flex;gap:6px;flex-wrap:wrap}
.mtag{font-size:10px;background:#f1f5f9;color:#475569;padding:2px 7px;border-radius:10px}
#db{flex:1;overflow-y:auto;padding:13px 14px;display:flex;flex-direction:column;gap:13px}
.sl{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#94a3b8;font-weight:600;margin-bottom:4px}
.sc{font-size:12px;color:#334155;line-height:1.6;white-space:pre-wrap}
.sc ol{padding-left:17px}.sc li{margin-bottom:3px}
#ev-sec{display:flex;flex-direction:column;gap:7px}
.el{font-size:11px;color:#64748b;margin-bottom:1px}
#ev-ss,#ev-def,#ev-notes{width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:5px;padding:6px 9px;font-size:12px;color:#1e293b;outline:none;font-family:inherit}
#ev-ss:focus,#ev-def:focus,#ev-notes:focus{border-color:#3b82f6}
#ev-notes{resize:vertical;min-height:55px}
#ev-ts{font-size:10px;color:#94a3b8;font-style:italic;min-height:14px}
#df{padding:11px 14px;border-top:1px solid #e2e8f0;flex-shrink:0;background:#fafafa}
#st-btns{display:flex;gap:7px;margin-bottom:8px}
.sb{flex:1;padding:8px 4px;border:2px solid transparent;border-radius:7px;font-size:12px;font-weight:700;cursor:pointer;transition:all .15s}
.sbP{background:#f0fdf4;color:#15803d;border-color:#86efac}
.sbF{background:#fef2f2;color:#b91c1c;border-color:#fca5a5}
.sbB{background:#fff7ed;color:#c2410c;border-color:#fdba74}
.sbS{background:#f8fafc;color:#475569;border-color:#cbd5e1}
.sbP.act,.sbP:hover{background:#22c55e;color:#fff;border-color:#22c55e}
.sbF.act,.sbF:hover{background:#ef4444;color:#fff;border-color:#ef4444}
.sbB.act,.sbB:hover{background:#f97316;color:#fff;border-color:#f97316}
.sbS.act,.sbS:hover{background:#64748b;color:#fff;border-color:#64748b}
#nav-btns{display:flex;gap:7px}
.nb{flex:1;padding:6px;background:#f1f5f9;color:#475569;border:1px solid #e2e8f0;border-radius:5px;font-size:11px;font-weight:600;cursor:pointer}
.nb:hover{background:#e2e8f0}
#close-det{background:transparent;border:none;color:#94a3b8;cursor:pointer;font-size:17px;position:absolute;right:12px;top:12px}
#close-det:hover{color:#475569}

/* EXPORT MENU */
#exp-menu{position:absolute;right:8px;top:50px;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:5px;display:none;z-index:200;min-width:210px;box-shadow:0 8px 24px rgba(0,0,0,.4)}
#exp-menu.open{display:block}
.ei{padding:8px 11px;color:#e2e8f0;font-size:12px;cursor:pointer;border-radius:5px;transition:background .12s}
.ei:hover{background:#334155}

/* EMPTY */
#empty{display:flex;align-items:center;justify-content:center;height:180px;color:#94a3b8;font-size:12px}
@media print{#header,#sidebar,#sf-bar,#detail,#exp-menu{display:none!important}body{overflow:auto}#app{height:auto}#body{overflow:visible}}
</style>
</head>
<body>

<!-- SETUP SCREEN -->
<div id="setup-screen">
  <h1>PRT-0701 Test Runner</h1>
  <div class="case-source-badge">
    ✓ <strong>""" + str(total) + r""" cases</strong> loaded &nbsp;·&nbsp; Generated """ + gen_dt + r"""
  </div>

  <div id="run-setup">
    <h2>Start New Execution</h2>
    <div class="field-row">
      <div><label>Run name / ID</label><input id="inp-name" placeholder="e.g. Sprint-42 Run 1"></div>
      <div><label>Tester</label><input id="inp-tester" placeholder="Your name"></div>
    </div>
    <div class="field-row">
      <div><label>Device / build</label><input id="inp-device" placeholder="e.g. iPhone 15 iOS 17.5"></div>
      <div><label>App version</label><input id="inp-ver" placeholder="e.g. 1.4.2"></div>
    </div>
    <button id="btn-start">▶ Start Execution</button>
  </div>

  <div class="resume-divider">— or resume a saved run —</div>
  <div id="resume-box">
    <h3>Saved runs</h3>
    <div id="resume-items"></div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <div id="header">
    <h1>PRT-0701 Test Runner</h1>
    <div class="run-badge" id="hdr-run"></div>
    <div class="run-badge" id="hdr-info"></div>
    <div class="spacer"></div>
    <div class="stat-pill"><span class="lbl">P</span><span class="vp" id="cp">0</span></div>
    <div class="stat-pill"><span class="lbl">F</span><span class="vf" id="cf">0</span></div>
    <div class="stat-pill"><span class="lbl">B</span><span class="vb" id="cb">0</span></div>
    <div class="stat-pill"><span class="lbl">S</span><span class="vs" id="cs">0</span></div>
    <div class="stat-pill"><span class="lbl">—</span><span class="vn" id="cn">0</span></div>
    <div id="progress-wrap"><div id="progress-bar" style="width:0%"></div></div>
    <span id="hdr-pct">0%</span>
    <button class="btn-hdr" id="btn-exp-tog">Export ▾</button>
    <button id="btn-end-run">End run</button>
    <div id="exp-menu">
      <div class="ei" onclick="exportSummary()">📄 Printable Summary</div>
      <div class="ei" onclick="exportCSV()">📊 CSV Download</div>
      <div class="ei" onclick="exportFull()">📋 Full Evidence Report</div>
    </div>
  </div>

  <div id="body">
    <div id="sidebar">
      <div id="sb-head">
        <h3>Batches</h3>
        <input id="search-box" type="search" placeholder="Search ID or title…">
      </div>
      <div class="bi active" data-b="all" onclick="filterBatch('all',this)">
        <span class="bi-label" style="font-weight:600;color:#1e293b">All cases</span>
        <span class="bi-cnt" id="all-cnt">0</span>
      </div>
      <div id="batch-list"></div>
    </div>

    <div id="case-area">
      <div style="display:flex;flex-direction:column;flex:1;overflow:hidden">
        <div id="sf-bar">
          <button class="sf aA" onclick="fStatus(null,this)">All</button>
          <button class="sf" onclick="fStatus('P',this)">Pass</button>
          <button class="sf" onclick="fStatus('F',this)">Fail</button>
          <button class="sf" onclick="fStatus('B',this)">Blocked</button>
          <button class="sf" onclick="fStatus('S',this)">Skip</button>
          <button class="sf" onclick="fStatus('N',this)">Not run</button>
        </div>
        <div id="case-list"></div>
      </div>

      <div id="detail">
        <div id="dh">
          <div id="d-id"></div>
          <div id="d-title"></div>
          <div id="d-meta"></div>
          <button id="close-det" onclick="closeDetail()">✕</button>
        </div>
        <div id="db">
          <div><div class="sl">Preconditions</div><div id="d-pre" class="sc"></div></div>
          <div><div class="sl">Procedure</div><div id="d-proc" class="sc"></div></div>
          <div><div class="sl">Expected Result</div><div id="d-exp" class="sc"></div></div>
          <div><div class="sl">Evidence Required</div><div id="d-ev" class="sc"></div></div>
          <div id="ev-sec">
            <div class="sl">Execution Evidence</div>
            <div><div class="el">Screenshot filename / path</div><input id="ev-ss" placeholder="e.g. IMG_0042.PNG" oninput="saveEv()"></div>
            <div><div class="el">Defect / Ticket ID</div><input id="ev-def" placeholder="e.g. BUG-1234" oninput="saveEv()"></div>
            <div><div class="el">Notes</div><textarea id="ev-notes" placeholder="Additional observations…" oninput="saveEv()"></textarea></div>
            <div id="ev-ts"></div>
          </div>
        </div>
        <div id="df">
          <div id="st-btns">
            <button class="sb sbP" onclick="setSt('P')">✓ Pass</button>
            <button class="sb sbF" onclick="setSt('F')">✗ Fail</button>
            <button class="sb sbB" onclick="setSt('B')">⊘ Blocked</button>
            <button class="sb sbS" onclick="setSt('S')">→ Skip</button>
          </div>
          <div id="nav-btns">
            <button class="nb" onclick="navCase(-1)">◀ Previous</button>
            <button class="nb" onclick="navCase(1)">Next ▶</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
// ── EMBEDDED CASES ────────────────────────────────────────────────────────────
const ALL_CASES = """ + cases_js + r""";
const GENERATED = '""" + gen_dt + r"""';
const TOTAL = ALL_CASES.length;

// ── STATE ─────────────────────────────────────────────────────────────────────
let runInfo = {}, results = {}, runId = null;
let fBatch = 'all', fStatus = null, fSearch = '';
let selId = null, filteredIds = [];

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const d = new Date(); // default run name
  document.getElementById('inp-name').value =
    'Run-' + d.toISOString().slice(0,10);
  loadResumeList();
});

// ── RESUME LIST ───────────────────────────────────────────────────────────────
function loadResumeList() {
  let runs = [];
  try { runs = JSON.parse(localStorage.getItem('PRT0701_runs')||'[]'); } catch(e){}
  if (!runs.length) return;
  const box = document.getElementById('resume-box');
  const cont = document.getElementById('resume-items');
  box.style.display = 'block';
  cont.innerHTML = '';
  runs.slice().reverse().forEach(r => {
    const saved = JSON.parse(localStorage.getItem('PRT0701_run_'+r.id)||'{}');
    const res = saved.results || {};
    const done = Object.keys(res).length;
    const pct = TOTAL ? Math.round(done/TOTAL*100) : 0;
    const div = document.createElement('div');
    div.className = 'run-item';
    div.innerHTML = `<div style="flex:1"><div class="run-item-name">${esc(r.name)}</div>
<div class="run-item-meta">${esc(r.tester)} · ${esc(r.device||'')} · ${esc(r.date||'')}</div></div>
<span class="run-item-pct">${pct}%</span>
<button class="run-item-del" title="Delete run" onclick="delRun(event,'${r.id}')">🗑</button>`;
    div.onclick = e => { if(!e.target.closest('.run-item-del')) resumeRun(r.id); };
    cont.appendChild(div);
  });
}

function delRun(e, id) {
  e.stopPropagation();
  if (!confirm('Delete this run? Results will be lost.')) return;
  localStorage.removeItem('PRT0701_run_'+id);
  let runs = [];
  try { runs = JSON.parse(localStorage.getItem('PRT0701_runs')||'[]'); } catch(e){}
  runs = runs.filter(r => r.id !== id);
  localStorage.setItem('PRT0701_runs', JSON.stringify(runs));
  loadResumeList();
}

function resumeRun(id) {
  const saved = JSON.parse(localStorage.getItem('PRT0701_run_'+id)||'{}');
  if (!saved.runInfo) return;
  runId = id; runInfo = saved.runInfo; results = saved.results || {};
  startApp();
}

// ── START NEW RUN ─────────────────────────────────────────────────────────────
document.getElementById('btn-start').onclick = () => {
  const name = document.getElementById('inp-name').value.trim() || 'Unnamed Run';
  const tester = document.getElementById('inp-tester').value.trim() || '';
  const device = document.getElementById('inp-device').value.trim() || '';
  const ver    = document.getElementById('inp-ver').value.trim() || '';
  runId = 'run_' + Date.now();
  runInfo = { id:runId, name, tester, device, version:ver, date:new Date().toLocaleDateString() };
  results = {};
  let runs = [];
  try { runs = JSON.parse(localStorage.getItem('PRT0701_runs')||'[]'); } catch(e){}
  runs.push(runInfo);
  localStorage.setItem('PRT0701_runs', JSON.stringify(runs));
  saveRun();
  startApp();
};

// ── SAVE ──────────────────────────────────────────────────────────────────────
function saveRun() {
  if (runId) localStorage.setItem('PRT0701_run_'+runId, JSON.stringify({runInfo,results}));
}

// ── START APP ─────────────────────────────────────────────────────────────────
function startApp() {
  document.getElementById('setup-screen').style.display = 'none';
  document.getElementById('app').style.display = 'flex';
  document.getElementById('hdr-run').innerHTML = '<strong>'+esc(runInfo.name)+'</strong>';
  document.getElementById('hdr-info').textContent =
    [runInfo.tester, runInfo.device, runInfo.version].filter(Boolean).join(' · ');
  buildBatches();
  renderList();
  updateStats();
}

document.getElementById('btn-end-run').onclick = () => {
  if (!confirm('End this run and return to start screen?')) return;
  document.getElementById('app').style.display = 'none';
  document.getElementById('setup-screen').style.display = 'flex';
  selId = null; fBatch='all'; fStatus=null; fSearch='';
  loadResumeList();
};

// ── BATCHES ───────────────────────────────────────────────────────────────────
let batches = [];
function buildBatches() {
  const map = {};
  ALL_CASES.forEach(c => { if (!map[c.sec]) map[c.sec]=[]; map[c.sec].push(c.id); });
  batches = Object.keys(map).map(s=>({sec:s,ids:map[s]}));
  const cont = document.getElementById('batch-list');
  cont.innerHTML = '';
  batches.forEach(b => {
    const div = document.createElement('div');
    div.className='bi'; div.dataset.b=b.sec;
    div.onclick=()=>filterBatch(b.sec,div);
    div.innerHTML=`<span class="bi-label">${esc(b.sec)}</span>
<div class="bi-bar"><div class="bi-fill" id="bf-${CSS.escape(b.sec)}" style="width:0%"></div></div>
<span class="bi-cnt">${b.ids.length}</span>`;
    cont.appendChild(div);
  });
  document.getElementById('all-cnt').textContent = TOTAL;
  updateMinis();
}

function updateMinis() {
  batches.forEach(b=>{
    const done=b.ids.filter(id=>results[id]).length;
    const pct=b.ids.length?Math.round(done/b.ids.length*100):0;
    const el=document.getElementById('bf-'+CSS.escape(b.sec));
    if(el)el.style.width=pct+'%';
  });
}

// ── FILTERS ───────────────────────────────────────────────────────────────────
function filterBatch(batch, el) {
  fBatch=batch;
  document.querySelectorAll('.bi').forEach(e=>e.classList.remove('active'));
  if(el)el.classList.add('active');
  renderList();
}

function fStatus(st,el) {
  fStatus=st;
  document.querySelectorAll('.sf').forEach(e=>e.className='sf');
  if(el)el.className='sf '+(st?'a'+st:'aA');
  renderList();
}

document.getElementById('search-box').oninput=e=>{
  fSearch=e.target.value.toLowerCase(); renderList();
};

// ── RENDER LIST ───────────────────────────────────────────────────────────────
const SL={P:'P',F:'F',B:'B',S:'S',N:'—'};
function renderList() {
  let vis=ALL_CASES;
  if(fBatch!=='all') vis=vis.filter(c=>c.sec===fBatch);
  if(fStatus){
    if(fStatus==='N') vis=vis.filter(c=>!results[c.id]);
    else vis=vis.filter(c=>results[c.id]&&results[c.id].status===fStatus);
  }
  if(fSearch) vis=vis.filter(c=>c.id.toLowerCase().includes(fSearch)||c.t.toLowerCase().includes(fSearch));
  filteredIds=vis.map(c=>c.id);
  const list=document.getElementById('case-list');
  list.innerHTML='';
  if(!vis.length){list.innerHTML='<div id="empty">No cases match the filter.</div>';return;}
  vis.forEach(c=>{
    const r=results[c.id]; const st=r?r.status:'N';
    const row=document.createElement('div');
    row.className='cr'+(selId===c.id?' sel':'');
    row.dataset.id=c.id; row.onclick=()=>openDetail(c.id);
    row.innerHTML=`<span class="cr-run">${c.r}</span><span class="cr-id">${esc(c.id)}</span><span class="cr-title">${esc(c.t)}</span><span class="dot d${st}">${SL[st]}</span>`;
    list.appendChild(row);
  });
}

// ── DETAIL ────────────────────────────────────────────────────────────────────
function openDetail(id) {
  selId=id;
  document.querySelectorAll('.cr').forEach(r=>r.classList.toggle('sel',r.dataset.id===id));
  const c=ALL_CASES.find(x=>x.id===id); if(!c)return;
  document.getElementById('detail').classList.add('open');
  document.getElementById('d-id').textContent=c.id+'  ·  Run '+c.r;
  document.getElementById('d-title').textContent=c.t;
  document.getElementById('d-meta').innerHTML=
    (c.req?`<span class="mtag">${esc(c.req)}</span>`:'')+
    (c.method?`<span class="mtag">${esc(c.method)}</span>`:'')+
    `<span class="mtag">${esc(c.sec)}</span>`;
  document.getElementById('d-pre').innerHTML=fmtText(c.pre);
  document.getElementById('d-proc').innerHTML=fmtNum(c.proc);
  document.getElementById('d-exp').innerHTML=fmtNum(c.exp);
  document.getElementById('d-ev').innerHTML=fmtText(c.ev);
  const r=results[id]||{};
  document.getElementById('ev-ss').value=r.screenshot||'';
  document.getElementById('ev-def').value=r.defect||'';
  document.getElementById('ev-notes').value=r.notes||'';
  document.getElementById('ev-ts').textContent=r.timestamp?'Last saved: '+r.timestamp:'';
  hlSt(r.status||null);
}

function closeDetail(){
  document.getElementById('detail').classList.remove('open');
  selId=null;
  document.querySelectorAll('.cr').forEach(r=>r.classList.remove('sel'));
}

function hlSt(st){
  document.querySelectorAll('.sb').forEach(b=>b.classList.remove('act'));
  if(st){ const b=document.querySelector('.sb'+st); if(b)b.classList.add('act'); }
}

function setSt(st) {
  if(!selId)return;
  if(!results[selId])results[selId]={};
  const ts=new Date().toLocaleString();
  Object.assign(results[selId],{
    status:st,timestamp:ts,
    screenshot:document.getElementById('ev-ss').value,
    defect:document.getElementById('ev-def').value,
    notes:document.getElementById('ev-notes').value
  });
  document.getElementById('ev-ts').textContent='Saved: '+ts;
  hlSt(st); saveRun(); updateStats(); updateMinis();
  const row=document.querySelector(`.cr[data-id="${CSS.escape(selId)}"]`);
  if(row){const dot=row.querySelector('.dot');if(dot){dot.className='dot d'+st;dot.textContent=SL[st];}}
}

function saveEv() {
  if(!selId)return;
  if(!results[selId])results[selId]={};
  const ts=new Date().toLocaleString();
  Object.assign(results[selId],{
    screenshot:document.getElementById('ev-ss').value,
    defect:document.getElementById('ev-def').value,
    notes:document.getElementById('ev-notes').value,
    timestamp:results[selId].timestamp||ts
  });
  document.getElementById('ev-ts').textContent='Edited: '+results[selId].timestamp;
  saveRun();
}

function navCase(dir) {
  if(!selId)return;
  const i=filteredIds.indexOf(selId); if(i===-1)return;
  const next=filteredIds[i+dir]; if(next)openDetail(next);
}

// ── STATS ─────────────────────────────────────────────────────────────────────
function updateStats() {
  let P=0,F=0,B=0,S=0;
  ALL_CASES.forEach(c=>{ const r=results[c.id]; if(!r)return; if(r.status==='P')P++; else if(r.status==='F')F++; else if(r.status==='B')B++; else if(r.status==='S')S++; });
  const done=P+F+B+S, pct=TOTAL?Math.round(done/TOTAL*100):0;
  document.getElementById('cp').textContent=P;
  document.getElementById('cf').textContent=F;
  document.getElementById('cb').textContent=B;
  document.getElementById('cs').textContent=S;
  document.getElementById('cn').textContent=TOTAL-done;
  document.getElementById('progress-bar').style.width=pct+'%';
  document.getElementById('hdr-pct').textContent=pct+'%';
}

// ── EXPORT ────────────────────────────────────────────────────────────────────
document.getElementById('btn-exp-tog').onclick=e=>{
  e.stopPropagation();
  document.getElementById('exp-menu').classList.toggle('open');
};
document.addEventListener('click',()=>document.getElementById('exp-menu').classList.remove('open'));

function exportCSV() {
  const rows=[['Run','Tester','Device','App Version','Case ID','Batch','Title','Requirement','Method','Status','Screenshot','Defect ID','Notes','Timestamp']];
  ALL_CASES.forEach(c=>{ const r=results[c.id]||{}; rows.push([runInfo.name,runInfo.tester,runInfo.device,runInfo.version,c.id,c.sec,c.t,c.req||'',c.method||'',r.status||'',r.screenshot||'',r.defect||'',r.notes||'',r.timestamp||'']); });
  const csv=rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n');
  dl(csv,'text/csv','PRT-0701-'+runInfo.name.replace(/\s+/g,'-')+'.csv');
}

function exportSummary() {
  let P=0,F=0,B=0,S=0,N=0; const bs={};
  ALL_CASES.forEach(c=>{ const r=results[c.id]; const st=r?r.status:'N';
    if(st==='P')P++;else if(st==='F')F++;else if(st==='B')B++;else if(st==='S')S++;else N++;
    if(!bs[c.sec])bs[c.sec]={P:0,F:0,B:0,S:0,N:0,total:0};
    bs[c.sec][st]++;bs[c.sec].total++;
  });
  const done=P+F+B+S, pr=done?Math.round(P/done*100):0;
  let h=`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PRT-0701 Summary</title>
<style>body{font-family:-apple-system,sans-serif;font-size:12px;margin:24px 32px;color:#1e293b}
h1{font-size:18px}p{color:#64748b;font-size:11px;margin:4px 0 20px}
.stats{display:flex;gap:16px;margin-bottom:20px}
.box{text-align:center;padding:12px 18px;border-radius:8px;min-width:70px}
.bp{background:#dcfce7}.bf{background:#fee2e2}.bb{background:#ffedd5}.bs{background:#f1f5f9}.bn{background:#f8fafc}
.box .n{font-size:24px;font-weight:700}.box .l{font-size:10px;text-transform:uppercase;color:#64748b}
table{width:100%;border-collapse:collapse;font-size:11px}
th{background:#f1f5f9;padding:6px 8px;text-align:left;border-bottom:2px solid #e2e8f0}
td{padding:4px 8px;border-bottom:1px solid #f1f5f9}
.bar{height:5px;background:#e2e8f0;border-radius:3px;width:70px}
.bf2{height:100%;background:#22c55e;border-radius:3px}
@media print{@page{margin:12mm}}</style></head><body>
<h1>PRT-0701 Test Execution Summary</h1>
<p>Run: <b>${esc(runInfo.name)}</b> &nbsp;·&nbsp; Tester: <b>${esc(runInfo.tester)}</b> &nbsp;·&nbsp; Device: <b>${esc(runInfo.device||'')} ${esc(runInfo.version||'')}</b> &nbsp;·&nbsp; Date: <b>${runInfo.date}</b> &nbsp;·&nbsp; Total: <b>${TOTAL}</b> &nbsp;·&nbsp; Pass rate: <b>${pr}%</b></p>
<div class="stats">
<div class="box bp"><div class="n">${P}</div><div class="l">Pass</div></div>
<div class="box bf"><div class="n">${F}</div><div class="l">Fail</div></div>
<div class="box bb"><div class="n">${B}</div><div class="l">Blocked</div></div>
<div class="box bs"><div class="n">${S}</div><div class="l">Skip</div></div>
<div class="box bn"><div class="n">${N}</div><div class="l">Not run</div></div>
</div>
<table><tr><th>Batch</th><th>Total</th><th>P</th><th>F</th><th>B</th><th>S</th><th>—</th><th>Progress</th></tr>`;
  Object.entries(bs).forEach(([s,v])=>{
    const pct=v.total?Math.round((v.P+v.F+v.B+v.S)/v.total*100):0;
    h+=`<tr><td>${esc(s)}</td><td>${v.total}</td><td>${v.P}</td><td>${v.F}</td><td>${v.B}</td><td>${v.S}</td><td>${v.N}</td><td><div class="bar"><div class="bf2" style="width:${pct}%"></div></div></td></tr>`;
  });
  h+=`</table></body></html>`;
  pw(h);
}

function exportFull() {
  const exec=ALL_CASES.filter(c=>results[c.id]);
  let h=`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PRT-0701 Evidence Report</title>
<style>body{font-family:-apple-system,sans-serif;font-size:11px;margin:16px 24px;color:#1e293b}
h1{font-size:16px}p{color:#64748b;font-size:11px;margin:3px 0 14px}
.cb{border:1px solid #e2e8f0;border-radius:6px;margin-bottom:10px;page-break-inside:avoid}
.ch{background:#f8fafc;padding:7px 11px;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;gap:9px;border-radius:6px 6px 0 0}
.ci{font-family:monospace;font-size:10px;color:#475569}.ct{flex:1;font-size:12px;font-weight:600}
.sb2{padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700}
.sP{background:#dcfce7;color:#15803d}.sF{background:#fee2e2;color:#b91c1c}.sB{background:#ffedd5;color:#c2410c}.sS{background:#f1f5f9;color:#475569}
.cbody{padding:7px 11px;display:grid;grid-template-columns:1fr 1fr;gap:7px}
.fl{font-size:9px;text-transform:uppercase;letter-spacing:.5px;color:#94a3b8;margin-bottom:2px}
.fv{color:#334155;line-height:1.4;white-space:pre-wrap;font-size:11px}
.er{background:#fffbeb;border-top:1px solid #e2e8f0;padding:5px 11px;display:flex;gap:14px;font-size:10px}
.er span{color:#64748b}.er b{color:#1e293b}
@media print{@page{margin:10mm}}</style></head><body>
<h1>PRT-0701 Full Evidence Report</h1>
<p>Run: <b>${esc(runInfo.name)}</b> · Tester: <b>${esc(runInfo.tester)}</b> · Device: <b>${esc(runInfo.device||'')} ${esc(runInfo.version||'')}</b> · Date: <b>${runInfo.date}</b> · Executed: <b>${exec.length}/${TOTAL}</b> · Generated: ${GENERATED}</p>`;
  exec.forEach(c=>{
    const r=results[c.id]; const st=r.status||'N';
    h+=`<div class="cb"><div class="ch"><span class="ci">${esc(c.id)}</span><span class="ct">${esc(c.t)}</span><span class="sb2 s${st}">${st}</span></div>
<div class="cbody">
<div><div class="fl">Preconditions</div><div class="fv">${esc(c.pre||'')}</div></div>
<div><div class="fl">Expected Result</div><div class="fv">${esc(c.exp||'')}</div></div>
<div style="grid-column:1/-1"><div class="fl">Procedure</div><div class="fv">${esc(c.proc||'')}</div></div>
</div>
<div class="er"><span>Screenshot: <b>${esc(r.screenshot||'—')}</b></span><span>Defect: <b>${esc(r.defect||'—')}</b></span><span>Notes: <b>${esc(r.notes||'—')}</b></span><span style="margin-left:auto">Recorded: <b>${r.timestamp||''}</b></span></div>
</div>`;
  });
  h+=`</body></html>`; pw(h);
}

// ── HELPERS ───────────────────────────────────────────────────────────────────
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function fmtText(s){return `<pre style="white-space:pre-wrap;font-size:12px;font-family:inherit;color:#334155;line-height:1.6">${esc(s||'')}</pre>`}
function fmtNum(s){
  if(!s)return '<em style="color:#94a3b8;font-size:11px">None</em>';
  const lines=s.split('\n');
  if(lines.some(l=>/^\d+\./.test(l.trim()))){
    const items=[];let cur='';
    lines.forEach(l=>{ if(/^\d+\./.test(l.trim())){if(cur)items.push(cur.trim());cur=l.replace(/^\d+\.\s*/,'')}else cur+='\n'+l; });
    if(cur)items.push(cur.trim());
    return '<ol style="padding-left:17px;line-height:1.6;font-size:12px;color:#334155">'+items.map(i=>'<li>'+esc(i)+'</li>').join('')+'</ol>';
  }
  return fmtText(s);
}
function pw(html){const w=window.open('','_blank','width=900,height=700');w.document.write(html);w.document.close();setTimeout(()=>w.print(),600)}
function dl(content,type,name){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
</script>
</body>
</html>"""

RUNNER_OUT.write_text(HTML, encoding="utf-8")
print(f"Generated: {RUNNER_OUT}")
print(f"Cases embedded: {total}  |  Generated: {gen_dt}")
