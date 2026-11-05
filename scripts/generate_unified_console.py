"""
Generate CGMX1-Console.html — unified test-case console + execution runner.

Design: matches the existing PRT console (IBM Plex, CSS variables, card style).
Modes in one file:
  Test Cases — read-only case browser (the original console look)
  Execution  — start / resume runs, record results with evidence

Protocols: Modus App UIRS Test Cases (PRT-0392) | Modus Portal UIRS Test Cases (PRT-0396)
Execution data lives only in localStorage — EMBEDDED_CASES is never written to.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

ROOT         = Path(__file__).resolve().parents[1]
OUT          = ROOT / "output/console-update"
CASES_PATH   = OUT / "PRT-0701-cases.json"
PORTAL_PATH  = OUT / "PRT-0702-cases.json"
PORTAL_FIXTURE_PATH = ROOT / "output" / "portal-fixtures" / "fixture-manifest.json"
PORTAL_ASSET_CATALOG_PATH = ROOT / "output" / "portal-test-assets.json"
PORTAL_ACCOUNTS_PATH = ROOT / ".secrets" / "portal-test-accounts.json"
DEST         = ROOT / "CGMX1-Console.html"

if "--help" in sys.argv or "-h" in sys.argv:
    print("Usage: python scripts/generate_unified_console.py")
    print("Generates the CGMX1 Console for PRT-0392 and PRT-0396.")
    raise SystemExit(0)

cases  = json.loads(CASES_PATH.read_text(encoding="utf-8-sig"))
total  = len(cases)

portal_cases = json.loads(PORTAL_PATH.read_text(encoding="utf-8")) if PORTAL_PATH.exists() else []
portal_total = len(portal_cases)

gen_dt = datetime.now().strftime("%Y-%m-%d %H:%M")
cases_js = (json.dumps(cases, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c"))
portal_cases_js = (json.dumps(portal_cases, ensure_ascii=False, separators=(",", ":"))
                   .replace("<", "\\u003c"))
portal_fixture_manifest = (json.loads(PORTAL_FIXTURE_PATH.read_text(encoding="utf-8"))
                           if PORTAL_FIXTURE_PATH.exists() else {"fixtures": []})
portal_fixture_js = (json.dumps(portal_fixture_manifest, ensure_ascii=False, separators=(",", ":"))
                     .replace("<", "\\u003c"))
portal_asset_catalog = (json.loads(PORTAL_ASSET_CATALOG_PATH.read_text(encoding="utf-8"))
                        if PORTAL_ASSET_CATALOG_PATH.exists() else {"accounts": [], "resources": []})
portal_asset_catalog_js = (json.dumps(portal_asset_catalog, ensure_ascii=False, separators=(",", ":"))
                           .replace("<", "\\u003c"))
portal_account_emails = {}
if PORTAL_ACCOUNTS_PATH.exists():
    for account in json.loads(PORTAL_ACCOUNTS_PATH.read_text(encoding="utf-8")):
        if account.get("alias") and account.get("email"):
            portal_account_emails[account["alias"]] = account["email"]
portal_account_emails_js = (json.dumps(portal_account_emails, ensure_ascii=False, separators=(",", ":"))
                            .replace("<", "\\u003c"))

html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CGMX1 Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f4f5f8; --surface:#ffffff; --surface-2:#eef0f5; --border:#dfe3ea;
  --text:#1a2233; --text-dim:#667085; --text-faint:#8992a3;
  --accent:#3457d5; --accent-weak:#e8ecfb; --accent-ink:#ffffff;
  --pass:#1f9e64; --pass-weak:#e3f7ec;
  --fail:#d6434e; --fail-weak:#fbe7e8;
  --blocked:#c9821e; --blocked-weak:#faedd7;
  --notrun:#78829a; --notrun-weak:#edeff3;
  --shadow: 0 1px 2px rgba(20,24,38,.06), 0 8px 24px -12px rgba(20,24,38,.18);
  color-scheme: light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0f1218; --surface:#171b24; --surface-2:#1e232e; --border:#2a3040;
    --text:#e8eaf0; --text-dim:#9aa3b5; --text-faint:#6e7789;
    --accent:#7290ff; --accent-weak:#202a4a; --accent-ink:#0f1218;
    --pass:#3fcb86; --pass-weak:#153726;
    --fail:#ff7b83; --fail-weak:#3a1e20;
    --blocked:#f0ad4e; --blocked-weak:#3a2d14;
    --notrun:#8b93a3; --notrun-weak:#232833;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
    color-scheme: dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0f1218; --surface:#171b24; --surface-2:#1e232e; --border:#2a3040;
  --text:#e8eaf0; --text-dim:#9aa3b5; --text-faint:#6e7789;
  --accent:#7290ff; --accent-weak:#202a4a; --accent-ink:#0f1218;
  --pass:#3fcb86; --pass-weak:#153726;
  --fail:#ff7b83; --fail-weak:#3a1e20;
  --blocked:#f0ad4e; --blocked-weak:#3a2d14;
  --notrun:#8b93a3; --notrun-weak:#232833;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
  color-scheme: dark;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:"IBM Plex Sans",system-ui,sans-serif;height:100vh;overflow:hidden;display:flex;flex-direction:column}
button{font-family:inherit;cursor:pointer}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}

/* ── TOP BAR ─────────────────────────────────────────────────────── */
#topbar{
  background:var(--surface);border-bottom:1px solid var(--border);
  flex-shrink:0;position:relative;z-index:30
}
#tb-row1{display:flex;align-items:center;gap:8px;padding:10px 14px 8px}
#tb-brand{font-size:15px;font-weight:700;letter-spacing:.01em;white-space:nowrap}
#tb-sep{width:1px;height:22px;background:var(--border);flex-shrink:0}

/* Protocol pills */
.proto-pill{
  display:flex;align-items:center;gap:5px;padding:4px 11px;border-radius:100px;
  border:1px solid var(--border);background:var(--surface-2);font-size:12px;
  font-weight:600;color:var(--text-dim);white-space:nowrap;transition:all .15s
}
.proto-pill:hover{border-color:var(--accent);color:var(--accent)}
.proto-pill.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.proto-pill .cnt{font-family:"IBM Plex Mono",monospace;font-size:11px}

/* Mode tabs */
#mode-tabs{display:flex;gap:2px;background:var(--surface-2);border-radius:9px;padding:3px;margin-left:4px}
.mode-tab{
  padding:4px 13px;border-radius:7px;border:none;background:transparent;
  font-size:12px;font-weight:600;color:var(--text-dim);transition:all .15s
}
.mode-tab:hover{color:var(--text)}
.mode-tab.active{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(20,24,38,.12)}

#tb-spacer{flex:1}

/* Exec stats chips */
#exec-stats{display:none;align-items:center;gap:5px}
.stat-chip{display:flex;align-items:center;gap:3px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px;padding:3px 8px;font-size:12px;font-weight:700}
.stat-chip .lbl{font-size:9px;color:var(--text-faint);font-weight:400;text-transform:uppercase}
.sc-p{color:var(--pass)}.sc-f{color:var(--fail)}.sc-b{color:var(--blocked)}.sc-n{color:var(--notrun)}

/* Icon buttons */
.icon-btn{width:32px;height:32px;border-radius:9px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.icon-btn:hover{border-color:var(--accent);color:var(--accent)}
.icon-btn svg{width:16px;height:16px}

/* Progress bar row */
#tb-row2{padding:0 14px 8px;display:none}
#tb-row2.show{display:block}
#prog-wrap{display:flex;align-items:center;gap:8px}
#prog-track{flex:1;height:6px;border-radius:4px;background:var(--surface-2);overflow:hidden;display:flex}
#prog-track div{height:100%}
#prog-lbl{font-size:11px;color:var(--text-dim);font-family:"IBM Plex Mono",monospace;white-space:nowrap;min-width:56px;text-align:right}

/* Filter pills row */
#tb-row3{padding:0 14px 10px;display:flex;gap:6px;overflow-x:auto;scrollbar-width:none}
#tb-row3::-webkit-scrollbar{display:none}
.filter-pill{
  flex:none;display:flex;align-items:center;gap:5px;padding:4px 10px;border-radius:100px;
  border:1px solid var(--border);background:var(--surface-2);font-size:11.5px;font-weight:600;
  color:var(--text-dim);white-space:nowrap;transition:all .15s
}
.filter-pill .dot{width:7px;height:7px;border-radius:50%}
.filter-pill .n{font-family:"IBM Plex Mono",monospace}
.filter-pill.active{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.filter-pill.active .dot{background:var(--accent-ink)!important}

/* Search row */
#tb-row4{padding:0 14px 10px;position:relative;display:none}
#tb-row4.show{display:block}
#tb-search{width:100%;padding:7px 11px 7px 30px;border-radius:9px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);font-size:12.5px;font-family:inherit;outline:none}
#tb-search::placeholder{color:var(--text-faint)}
#tb-search:focus{outline:2px solid var(--accent);outline-offset:-1px}
#tb-row4 svg{position:absolute;left:22px;top:50%;transform:translateY(-50%);width:13px;height:13px;color:var(--text-faint)}

/* Export menu */
#exp-menu{position:absolute;right:14px;top:calc(100% + 4px);background:var(--surface);border:1px solid var(--border);border-radius:11px;padding:5px;z-index:100;min-width:200px;box-shadow:var(--shadow);display:none}
#exp-menu.open{display:block}
.em-item{padding:8px 11px;border-radius:7px;font-size:12.5px;color:var(--text);transition:background .12s}
.em-item:hover{background:var(--surface-2)}

/* ── BODY ─────────────────────────────────────────────────────────── */
#body{display:flex;flex:1;overflow:hidden}

/* ── SIDEBAR ─────────────────────────────────────────────────────── */
#sidebar{
  width:224px;flex-shrink:0;background:var(--surface);
  border-right:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column
}
#sb-head{padding:9px 10px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--surface);z-index:1}
#sb-head-lbl{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint);font-weight:700;margin-bottom:5px}
#sb-search{width:100%;padding:5px 9px;border-radius:8px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);font-size:12px;font-family:inherit;outline:none}
#sb-search::placeholder{color:var(--text-faint)}
#sb-search:focus{outline:2px solid var(--accent);outline-offset:-1px}
.sb-item{
  padding:6px 10px;border-left:3px solid transparent;display:flex;
  align-items:center;gap:7px;transition:all .12s
}
.sb-item:hover{background:var(--surface-2)}
.sb-item.active{background:var(--accent-weak);border-left-color:var(--accent)}
.sb-label{flex:1;font-size:11.5px;color:var(--text-dim);line-height:1.3}
.sb-item.active .sb-label{color:var(--accent);font-weight:600}
.sb-cnt{font-size:10.5px;color:var(--text-faint);flex-shrink:0;font-family:"IBM Plex Mono",monospace}
/* Exec mini-bars */
.sb-bar{width:24px;height:4px;background:var(--surface-2);border-radius:2px;overflow:hidden;flex-shrink:0;display:none}
.sb-bar.show{display:block}
.sb-fill{height:100%;background:var(--pass);border-radius:2px}

/* ── CASE LIST ───────────────────────────────────────────────────── */
#list-area{display:flex;flex:1;overflow:hidden;flex-direction:column}
#case-list{flex:1;overflow-y:auto;padding:6px 10px 80px}
.sec-hdr{padding:12px 4px 4px;font-size:10.5px;font-weight:700;color:var(--text-faint);text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;background:var(--bg);z-index:2}
.row{
  display:flex;align-items:center;gap:9px;background:var(--surface);
  border:1px solid var(--border);border-radius:10px;padding:9px 10px;
  margin-bottom:5px;transition:background .1s;box-shadow:0 1px 0 rgba(20,24,38,.02)
}
.row:hover{background:var(--surface-2)}
.row.sel{border-color:var(--accent);background:var(--accent-weak)}
.row .runno{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--text-faint);width:24px;text-align:right;flex-shrink:0}
.row .sdot{width:8px;height:8px;border-radius:50%;flex-shrink:0;border:2px solid var(--notrun);background:var(--notrun-weak)}
.row .mid{flex:1;min-width:0}
.row .rid{font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--text-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .ttl{font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:1px}
.row .badge{flex:none;font-size:10px;font-weight:700;padding:2px 7px;border-radius:100px;letter-spacing:.02em}
.sdot-P{background:var(--pass);border-color:var(--pass)}
.sdot-F{background:var(--fail);border-color:var(--fail)}
.sdot-B{background:var(--blocked);border-color:var(--blocked)}
.st-P{background:var(--pass-weak);color:var(--pass)}
.st-F{background:var(--fail-weak);color:var(--fail)}
.st-B{background:var(--blocked-weak);color:var(--blocked)}
.st-NR{background:var(--notrun-weak);color:var(--notrun)}
#list-empty{text-align:center;color:var(--text-faint);padding:50px 20px;font-size:13px}

/* ── DETAIL PANEL ────────────────────────────────────────────────── */
#detail{
  width:420px;flex-shrink:0;background:var(--surface);
  border-left:1px solid var(--border);display:none;flex-direction:column;overflow:hidden;
  position:relative;min-width:320px;max-width:95vw
}
#detail.open{display:flex}
#detail.maximized{width:92vw!important}
#det-resize{
  position:absolute;left:-4px;top:0;bottom:0;width:8px;cursor:col-resize;z-index:20;
  background:transparent
}
#det-resize:hover,#det-resize.active{background:var(--accent)}
#det-head{
  padding:11px 13px;border-bottom:1px solid var(--border);
  flex-shrink:0;background:var(--surface);position:relative
}
#det-id{font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--text-faint)}
#det-title{font-size:14px;font-weight:700;color:var(--text);margin:3px 0 6px;line-height:1.3;padding-right:60px}
#det-meta{display:flex;gap:5px;flex-wrap:wrap}
.chip{font-size:10.5px;font-weight:600;color:var(--text-dim);background:var(--surface-2);border:1px solid var(--border);padding:2px 8px;border-radius:100px}
#det-expand{position:absolute;right:45px;top:11px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:13px}
#det-expand:hover{background:var(--surface-3,var(--surface-2));color:var(--text)}
#det-close{position:absolute;right:11px;top:11px;background:var(--surface-2);border:1px solid var(--border);border-radius:7px;width:26px;height:26px;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:14px}
#det-close:hover{background:var(--fail-weak);color:var(--fail);border-color:var(--fail)}
#det-body{flex:1;overflow-y:auto;padding:12px 13px 16px;display:flex;flex-direction:column;gap:13px}
.det-block h3{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint);margin-bottom:5px}
.det-content{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:10px 11px;font-size:13px;line-height:1.5;color:var(--text-dim)}
.det-content ol{padding-left:16px}.det-content li{margin-bottom:3px}
.steps-list{list-style:none;padding:0;margin:0;counter-reset:step}
.steps-list li{display:flex;gap:8px;padding:5px 0}
.steps-list li:not(:last-child){border-bottom:1px dashed var(--border)}
.step-num{flex:none;width:18px;height:18px;border-radius:50%;background:var(--accent-weak);color:var(--accent);font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;font-family:"IBM Plex Mono",monospace;margin-top:1px}
.step-txt{flex:1;font-size:13px;line-height:1.45;color:var(--text-dim)}

/* Merged step cards: procedure + expected + evidence controls together */
.step-card{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:10px 11px;margin-bottom:8px}
.step-card:last-child{margin-bottom:0}
.step-row{display:flex;gap:8px}
.step-row .step-num{margin-top:2px}
.step-proc{flex:1;font-size:13px;line-height:1.5;color:var(--text)}
.step-exp{margin-top:7px;margin-left:26px;font-size:12.5px;line-height:1.5;color:var(--text-dim);background:var(--surface);border-left:3px solid var(--pass);padding:6px 9px;border-radius:0 7px 7px 0}
.step-exp-lbl{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--pass);margin-bottom:2px}
.step-ev-row{margin-top:8px;margin-left:26px}
.step-ev-row .ev-thumb,.step-ev-row .ev-add{width:56px;height:56px}

/* Evidence / exec fields (only in exec mode) */
#det-ev-sec{display:none;flex-direction:column;gap:12px}
#det-ev-sec.show{display:flex}
#det-ev-sec h3{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint)}
.ev-lbl{font-size:11px;font-weight:600;color:var(--text-dim);margin-bottom:4px;display:block}
#ev-def,#ev-notes{width:100%;border:1px solid var(--border);background:var(--surface-2);color:var(--text);border-radius:9px;padding:8px 10px;font-size:13px;font-family:inherit;outline:none}
#ev-notes{resize:vertical;min-height:58px}
#ev-def:focus,#ev-notes:focus{outline:2px solid var(--accent);outline-offset:-1px}
#ev-ts{font-size:10.5px;color:var(--text-faint);font-style:italic;min-height:15px}
/* Per-step evidence upload groups */
#evidence-groups{display:flex;flex-wrap:wrap;gap:16px 14px}
.ev-group{flex:none}
.ev-group-title{font-size:11px;font-weight:700;color:var(--text-dim);margin-bottom:7px;text-transform:uppercase;letter-spacing:.03em}
.ev-group-row{display:flex;flex-wrap:wrap;gap:8px}
.ev-thumb{position:relative;width:72px;height:72px;border-radius:9px;overflow:hidden;border:1px solid var(--border);background:var(--surface-2)}
.ev-thumb img,.ev-thumb video{width:100%;height:100%;object-fit:cover;display:block}
.ev-thumb .rm{position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;border:none;cursor:pointer}
.ev-thumb .dl{position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:rgba(0,0,0,.55);color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;border:none;cursor:pointer}
.ev-add{width:72px;height:72px;border-radius:9px;border:1.5px dashed var(--border);background:var(--surface);display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--text-faint);font-size:10px;gap:3px;cursor:pointer;text-align:center}
.ev-add svg{width:18px;height:18px}

/* Status buttons (exec) */
#det-foot{padding:10px 13px;border-top:1px solid var(--border);flex-shrink:0;background:var(--surface);display:none}
#det-foot.show{display:block}
.rbtn-row{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px}
.rbtn{padding:9px 4px;border-radius:10px;border:1.5px solid var(--border);background:var(--surface);font-size:12px;font-weight:700;color:var(--text-dim);text-align:center}
.rbtn small{display:block;font-size:9.5px;font-weight:500;color:var(--text-faint);margin-top:1px}
.rbtn:hover{border-color:var(--accent);color:var(--accent)}
.rbtn.sel-P{background:var(--pass-weak);border-color:var(--pass);color:var(--pass)}
.rbtn.sel-F{background:var(--fail-weak);border-color:var(--fail);color:var(--fail)}
.rbtn.sel-B{background:var(--blocked-weak);border-color:var(--blocked);color:var(--blocked)}
.rbtn.sel-NR{background:var(--notrun-weak);border-color:var(--notrun);color:var(--notrun)}
.nav-row{display:flex;gap:6px}
.nbtn{flex:1;padding:6px;background:var(--surface-2);color:var(--text-dim);border:1px solid var(--border);border-radius:8px;font-size:11.5px;font-weight:600}
.nbtn:hover{border-color:var(--accent);color:var(--accent)}

/* ── EXEC SETUP SCREEN ───────────────────────────────────────────── */
#exec-setup{
  display:none;flex:1;align-items:center;justify-content:center;
  flex-direction:column;gap:14px;background:var(--bg)
}
#exec-setup.show{display:flex}
#exec-setup h2{font-size:17px;font-weight:700}
.src-badge{
  display:flex;align-items:center;gap:7px;background:var(--surface);
  border:1px solid var(--border);border-radius:9px;padding:7px 14px;
  font-size:12px;color:var(--text-dim)
}
.src-badge strong{color:var(--pass)}
#exec-form{
  background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:22px 26px;display:flex;flex-direction:column;gap:12px;width:420px;
  box-shadow:var(--shadow)
}
#exec-form h3{font-size:14px;font-weight:700}
#exec-form label{font-size:11px;font-weight:600;color:var(--text-dim);margin-bottom:3px;display:block;text-transform:uppercase;letter-spacing:.04em}
#exec-form input{width:100%;border:1px solid var(--border);background:var(--surface-2);color:var(--text);border-radius:9px;padding:8px 10px;font-size:13px;font-family:inherit;outline:none}
#exec-form input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.primary-btn{background:var(--accent);color:var(--accent-ink);border:none;border-radius:10px;padding:10px;font-size:13.5px;font-weight:700;width:100%;margin-top:4px}
.primary-btn:hover{opacity:.9}
.divider-lbl{font-size:11px;color:var(--text-faint);text-align:center;width:420px}
#resume-box{
  background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:12px 16px;width:420px;max-height:210px;overflow-y:auto;display:none;
  box-shadow:var(--shadow)
}
#resume-box h4{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint);margin-bottom:8px}
.run-item{
  display:flex;align-items:center;gap:9px;padding:8px 10px;
  background:var(--surface-2);border:1px solid var(--border);border-radius:9px;
  margin-bottom:7px;transition:border-color .12s
}
.run-item:hover{border-color:var(--accent)}
.run-name{flex:1;font-size:12px;font-weight:600}
.run-meta{font-size:10.5px;color:var(--text-dim)}
.run-pct{font-size:12px;font-weight:700;color:var(--pass);font-family:"IBM Plex Mono",monospace}
.run-del{background:transparent;border:none;color:var(--text-faint);font-size:14px;padding:0 2px}
.run-del:hover{color:var(--fail)}

/* Protocol selector inside exec setup */
.exec-proto-row{display:flex;gap:8px;justify-content:center}
.exec-proto-btn{
  flex:1;padding:9px 12px;border-radius:10px;border:1.5px solid var(--border);
  background:var(--surface);font-size:13px;font-weight:600;color:var(--text-dim);
  display:flex;flex-direction:column;align-items:center;gap:3px;transition:all .15s;
  max-width:180px
}
.exec-proto-btn .ep-name{font-size:13px;font-weight:700}
.exec-proto-btn .ep-cnt{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--text-faint)}
.exec-proto-btn:hover{border-color:var(--accent);color:var(--accent)}
.exec-proto-btn:hover .ep-cnt{color:var(--accent)}
.exec-proto-btn.active{border-color:var(--accent);background:var(--accent-weak);color:var(--accent)}
.exec-proto-btn.active .ep-cnt{color:var(--accent)}
.exec-proto-btn.disabled{opacity:.45;cursor:not-allowed}
.exec-proto-btn.disabled:hover{border-color:var(--border);color:var(--text-dim)}
.exec-proto-btn.disabled:hover .ep-cnt{color:var(--text-faint)}

/* No-cases placeholder */
#no-cases{display:none;flex:1;align-items:center;justify-content:center;flex-direction:column;gap:10px;color:var(--text-faint);text-align:center;padding:30px}
#no-cases.show{display:flex}
#no-cases p{font-size:13px;max-width:300px;line-height:1.6}

/* ── OVERLAYS ─────────────────────────────────────────────────────── */
.overlay{position:fixed;inset:0;background:rgba(10,12,18,.5);z-index:150;display:flex;align-items:flex-end;justify-content:center}
.overlay.hidden{display:none}
.sheet2{background:var(--surface);border-radius:16px 16px 0 0;width:100%;max-width:680px;max-height:86vh;overflow-y:auto;padding:20px 24px 32px;box-shadow:var(--shadow)}
.closebar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.closebar h2{font-size:16px;font-weight:700}
.fld{font-size:11px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:3px}
.field-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px}
.field-row.full{grid-template-columns:1fr}
.sheet2 input[type=text]{width:100%;border:1px solid var(--border);background:var(--surface-2);color:var(--text);border-radius:8px;padding:7px 10px;font-size:12.5px;font-family:inherit;outline:none}
.sheet2 input[type=text]:focus{outline:2px solid var(--accent);outline-offset:-1px}
.help-block{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:13px 15px;margin-top:12px}
.help-block h4{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint);margin-bottom:6px}
.codes-table{border-collapse:collapse;width:100%;font-size:12.5px}
.codes-table td,.codes-table th{padding:5px 9px;vertical-align:top;border-bottom:1px solid var(--border)}
.codes-table td:first-child,.codes-table th:first-child{font-family:"IBM Plex Mono",monospace;font-weight:700;white-space:nowrap;padding-right:12px}
.codes-table th{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--text-faint)}
.account-table-wrap{overflow-x:auto}
.account-table input{font-size:12px;padding:4px 8px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--text);width:100%;font-family:inherit;outline:none}
.account-table input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.sheet2 .desc{font-size:12px;color:var(--text-dim);margin-bottom:12px;line-height:1.5}
.warmup-tip{background:var(--accent-weak);border:1px solid var(--accent);border-radius:8px;padding:10px 13px;font-size:12px;color:var(--text);margin-bottom:12px;line-height:1.5}
.asset-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin:12px 0 14px}
.asset-card{background:var(--surface-2);border:1px solid var(--border);border-radius:11px;padding:14px;display:flex;flex-direction:column;align-items:center;gap:10px}
.asset-card h5{margin:0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-faint);align-self:flex-start}
.asset-card .qr-box{width:160px;height:160px;display:flex;align-items:center;justify-content:center;background:#fff;border-radius:4px;padding:4px}
.asset-card .qr-box canvas,.asset-card .qr-box img{max-width:160px;max-height:160px;display:block}
.asset-card .qr-fields{width:100%;display:flex;flex-direction:column;gap:4px}
.asset-card .qf{display:flex;justify-content:space-between;gap:6px;font-size:11.5px}
.asset-card .qf .ql{color:var(--text-faint)}
.asset-card .qf .qv{font-weight:600;font-variant-numeric:tabular-nums;word-break:break-all;text-align:right}
.asset-card .asset-tag{font-size:10px;font-weight:700;padding:2px 8px;border-radius:100px;letter-spacing:.03em;align-self:flex-start}
.asset-card .asset-tag.primary{background:var(--accent-weak);color:var(--accent)}
.asset-card .asset-tag.secondary{background:var(--notrun-weak);color:var(--notrun)}
.asset-card .asset-tag.negative{background:var(--blocked-weak);color:var(--blocked)}
.asset-raw{width:100%;font-family:"IBM Plex Mono",monospace;font-size:9.5px;line-height:1.35;word-break:break-all;color:var(--text-dim);background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:6px}
.asset-copy-btn{width:100%;padding:7px;background:var(--accent);color:var(--accent-ink);border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit}
.asset-copy-btn:active{opacity:.85}
.device-ref{margin-top:14px;font-size:12px;line-height:1.5;color:var(--text-dim)}
.device-ref h5{font-size:11.5px;font-weight:700;color:var(--text);margin-bottom:7px}
.device-ref table{border-collapse:collapse;width:100%;font-size:12px}
.device-ref table td{padding:4px 9px;border-bottom:1px solid var(--border);vertical-align:top}
.device-ref table td:first-child{font-family:"IBM Plex Mono",monospace;font-weight:600;white-space:nowrap;min-width:90px;color:var(--text)}
.acct-hint{font-size:11.5px;color:var(--text-dim);margin-bottom:8px;line-height:1.4}
.acct-table{border-collapse:collapse;width:100%;font-size:12px}
.acct-table td,.acct-table th{padding:5px 9px;border-bottom:1px solid var(--border);vertical-align:middle}
.acct-table th{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--text-faint);font-weight:700}
#saved-flash{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--pass);color:#fff;padding:8px 20px;border-radius:100px;font-size:12.5px;font-weight:700;display:none;z-index:200}
#saved-flash.show{display:block}

@media print{
  #topbar,#sidebar,#det-foot,#exp-menu{display:none!important}
  body{overflow:auto;height:auto}
  #body{overflow:visible}
}
</style>
</head>
<body>

<!-- ── TOP BAR ──────────────────────────────────────────────────────────── -->
<div id="topbar">
  <div id="tb-row1">
    <span id="tb-brand">CGMX1 Console</span>
    <div id="tb-sep"></div>

    <!-- Protocols -->
    <button class="proto-pill active" id="pt-app" onclick="switchProto('app')">
      PRT-0392 · Modus App UIRS Test Cases <span class="cnt">""" + str(total) + r"""</span>
    </button>
    <button class="proto-pill" id="pt-portal" onclick="switchProto('portal')">
      PRT-0396 · Modus Portal UIRS Test Cases <span class="cnt">""" + str(portal_total) + r"""</span>
    </button>

    <!-- Modes -->
    <div id="mode-tabs">
      <button class="mode-tab active" id="mt-cases" onclick="switchMode('cases')">Test Cases</button>
      <button class="mode-tab" id="mt-exec"  onclick="switchMode('exec')">Execution</button>
    </div>

    <div id="tb-spacer"></div>

    <!-- Exec stats -->
    <div id="exec-stats">
      <div class="stat-chip"><span class="lbl">P</span><span class="sc-p" id="h-p">0</span></div>
      <div class="stat-chip"><span class="lbl">F</span><span class="sc-f" id="h-f">0</span></div>
      <div class="stat-chip"><span class="lbl">B</span><span class="sc-b" id="h-b">0</span></div>
      <div class="stat-chip"><span class="lbl">NR</span><span class="sc-n" id="h-n">0</span></div>
    </div>

    <!-- Test Cases mode icon buttons (hidden in exec mode) -->
    <div id="cases-btns" style="display:flex;align-items:center;gap:4px">
      <button class="icon-btn" id="btn-cases-csv" title="Export CSV of cases">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>
      </button>
      <button class="icon-btn" id="btn-cases-doc" title="Export Word doc">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M9 15h6"/><path d="M9 11h6"/></svg>
      </button>
      <button class="icon-btn" id="btn-help" title="Protocol rules">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2 1.7-2 3.3"/><path d="M12 17h.01"/></svg>
      </button>
      <button class="icon-btn" id="btn-assets" title="Test assets &amp; QR codes">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      </button>
      <button class="icon-btn" id="btn-setup" title="Run setup">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1 1.51h.09a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1 1.49Z"/></svg>
      </button>
    </div>
    <!-- Execution mode controls (hidden in cases mode) -->
    <div id="exec-btns" style="display:none;align-items:center;gap:4px">
      <button class="icon-btn" id="btn-exp-tog" title="Export">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg>
      </button>
      <button class="icon-btn" id="btn-end-run" title="End run" style="display:none">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
      </button>
    </div>
  </div>

  <!-- Progress bar (exec active) -->
  <div id="tb-row2">
    <div id="prog-wrap">
      <div id="prog-track">
        <div id="pt-pass" style="background:var(--pass)"></div>
        <div id="pt-fail" style="background:var(--fail)"></div>
        <div id="pt-blocked" style="background:var(--blocked)"></div>
      </div>
      <div id="prog-lbl" class="mono">0 / """ + str(total) + r"""</div>
    </div>
  </div>

  <!-- Filter pills (cases mode) -->
  <div id="tb-row3">
    <div class="filter-pill active" id="fp-all" onclick="setFilter('all',this)">All <span class="n" id="fp-cnt-all">""" + str(total) + r"""</span></div>
    <div class="filter-pill" id="fp-P"   onclick="setFilter('P',this)"><span class="dot sdot-P"></span>Pass <span class="n" id="fp-cnt-P">0</span></div>
    <div class="filter-pill" id="fp-F"   onclick="setFilter('F',this)"><span class="dot sdot-F"></span>Fail <span class="n" id="fp-cnt-F">0</span></div>
    <div class="filter-pill" id="fp-B"   onclick="setFilter('B',this)"><span class="dot" style="background:var(--blocked)"></span>Blocked <span class="n" id="fp-cnt-B">0</span></div>
    <div class="filter-pill" id="fp-NR"  onclick="setFilter('NR',this)"><span class="dot" style="background:var(--notrun)"></span>Not run <span class="n" id="fp-cnt-NR">0</span></div>
  </div>

  <!-- Search -->
  <div id="tb-row4">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input id="tb-search" type="search" placeholder="Search case ID or title…">
  </div>

  <!-- Export dropdown -->
  <div id="exp-menu">
    <div class="em-item" onclick="exportSummary()">📄 Printable Summary</div>
    <div class="em-item" onclick="exportCSV()">📊 CSV Download</div>
    <div class="em-item" onclick="exportFull()">📋 Full Evidence Report</div>
    <div class="em-item" onclick="exportEvidenceZip()">🖼️ Evidence Files (.zip)</div>
  </div>
</div>

<!-- ── BODY ──────────────────────────────────────────────────────────────── -->
<div id="body">

  <!-- Sidebar -->
  <div id="sidebar">
    <div id="sb-head">
      <div id="sb-head-lbl">Batches</div>
      <input id="sb-search" type="search" placeholder="Filter batches…">
    </div>
    <div class="sb-item active" data-b="all" onclick="setBatch('all',this)">
      <span class="sb-label" style="font-weight:600;color:var(--text)">All cases</span>
      <span class="sb-cnt" id="sb-cnt-all">""" + str(total) + r"""</span>
    </div>
    <div id="sb-list"></div>
  </div>

  <!-- Main: case list + detail -->
  <div id="list-area">
    <div id="case-list"></div>
    <div id="list-empty" style="display:none">No cases match.</div>
  </div>

  <!-- Detail panel -->
  <div id="detail">
    <div id="det-resize" title="Drag to resize"></div>
    <div id="det-head">
      <div id="det-id"></div>
      <div id="det-title"></div>
      <div id="det-meta"></div>
      <button id="det-expand" onclick="toggleDetailMaximize()" title="Expand/collapse panel">⤢</button>
      <button id="det-close" onclick="closeDetail()">✕</button>
    </div>
    <div id="det-body">
      <div class="det-block"><h3>Preconditions</h3><div id="d-pre" class="det-content"></div></div>
      <div class="det-block"><h3>Steps</h3><div id="d-steps"></div></div>
      <div class="det-block"><h3>Evidence Required</h3><div id="d-ev" class="det-content"></div></div>
      <!-- Evidence inputs (exec only) -->
      <div id="det-ev-sec">
        <h3>General evidence (not tied to one step)</h3>
        <div id="evidence-general"></div>
        <input type="file" id="file-input" accept="image/*,video/*" multiple style="display:none">
        <div id="evidence-folder-row" style="font-size:11.5px;padding:4px 0;display:flex;align-items:center;gap:8px">
          <span id="evidence-folder-label" style="color:var(--text-faint)">Evidence folder: not connected</span>
          <a href="javascript:void(0)" onclick="chooseEvidenceFolder()" style="color:var(--accent);font-weight:600">Choose folder…</a>
        </div>
        <div style="font-size:11.5px;color:var(--text-faint);padding:4px 0">Photos/screen recordings attach per step. When an evidence folder is connected, each file is written to disk immediately on attach, in addition to this browser's cache.</div>
        <div><label class="ev-lbl">Defect / Ticket ID</label><input id="ev-def" type="text" placeholder="e.g. BUG-1234" oninput="saveEv()"></div>
        <div><label class="ev-lbl">Notes</label><textarea id="ev-notes" placeholder="Additional observations…" oninput="saveEv()"></textarea></div>
        <div id="ev-ts"></div>
      </div>
    </div>
    <div id="det-foot">
      <div class="rbtn-row">
        <button class="rbtn" onclick="setSt('P')">✓ Pass<small>passed</small></button>
        <button class="rbtn" onclick="setSt('F')">✗ Fail<small>defect</small></button>
        <button class="rbtn" onclick="setSt('B')">⊘ Block<small>blocked</small></button>
        <button class="rbtn" onclick="setSt('NR')">— N/R<small>not run</small></button>
      </div>
      <div class="nav-row">
        <button class="nbtn" onclick="navCase(-1)">◀ Previous</button>
        <button class="nbtn" onclick="navCase(1)">Next ▶</button>
      </div>
    </div>
  </div>

  <!-- Exec setup (replaces list-area when no active run) -->
  <div id="exec-setup">
    <h2>Start Execution</h2>
    <div class="src-badge">✓ <strong id="src-cnt">""" + str(total) + r"""</strong> cases · <span id="src-proto">PRT-0392 · Modus App UIRS Test Cases</span> · Generated """ + gen_dt + r"""</div>
    <div id="exec-form">
      <h3>New Execution</h3>
      <div>
        <label>Protocol</label>
        <div class="exec-proto-row" style="margin-top:6px">
          <button class="exec-proto-btn active" id="ep-app" onclick="execSetProto('app')">
            <span class="ep-name">PRT-0392 · Modus App UIRS Test Cases</span>
            <span class="ep-cnt">""" + str(total) + r""" cases</span>
          </button>
          <button class="exec-proto-btn" id="ep-portal" onclick="execSetProto('portal')">
            <span class="ep-name">PRT-0396 · Modus Portal UIRS Test Cases</span>
            <span class="ep-cnt">""" + str(portal_total) + r""" cases</span>
          </button>
        </div>
      </div>
      <div class="form-row">
        <div><label>Run name / ID</label><input id="inp-name" placeholder="e.g. Sprint-42 Run 1"></div>
        <div><label>Tester</label><input id="inp-tester" placeholder="Your name"></div>
      </div>
      <div class="form-row">
        <div><label>Device / Build</label><input id="inp-device" placeholder="e.g. iPhone 15 iOS 17.5"></div>
        <div><label>App version</label><input id="inp-ver" placeholder="e.g. 1.4.2"></div>
      </div>
      <button class="primary-btn" id="exec-start-btn" onclick="startRun()">▶ Start Execution — PRT-0392 · Modus App UIRS Test Cases</button>
    </div>
    <div class="divider-lbl">— or resume a saved run —</div>
    <div id="resume-box">
      <h4>Saved runs</h4>
      <div id="resume-items"></div>
    </div>
  </div>

  <!-- No-cases placeholder (shown only when no run is active) -->
  <div id="no-cases">
    <h3 style="font-size:16px">No active run</h3>
    <p>Switch to Execution mode and start or resume a run to record results.</p>
  </div>
</div>

<script>
// ── DATA (read-only) ──────────────────────────────────────────────────────────
const ALL_APP_CASES    = """ + cases_js + r""";
const ALL_PORTAL_CASES = """ + portal_cases_js + r""";
const PORTAL_FIXTURE_MANIFEST = """ + portal_fixture_js + r""";
const PORTAL_ASSET_CATALOG = """ + portal_asset_catalog_js + r""";
const PORTAL_ACCOUNT_EMAILS = """ + portal_account_emails_js + r""";
var   ALL_CASES = ALL_APP_CASES;
var   TOTAL     = ALL_CASES.length;

// ── STATE ─────────────────────────────────────────────────────────────────────
let proto = 'app', mode = 'cases';
let batchFilter = 'all', statusFilter = 'all', searchQ = '';
let selId = null, filteredIds = [];
let runInfo = {}, results = {}, runId = null, runActive = false;
let batches = [];

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('inp-name').value = 'Run-' + new Date().toISOString().slice(0,10);
  buildSidebar();
  renderList();
  loadResumeList();
  document.getElementById('tb-search').oninput = e => { searchQ = e.target.value.toLowerCase(); renderList(); };
  document.getElementById('sb-search').oninput = e => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('#sb-list .sb-item').forEach(el => {
      el.style.display = el.querySelector('.sb-label').textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  };
  document.getElementById('btn-end-run').onclick = () => {
    if (!confirm('End this run and return to setup?')) return;
    stopScreenCapture();
    runActive = false; runId = null; runInfo = {}; results = {};
    batchFilter = 'all'; statusFilter = 'all'; searchQ = ''; selId = null;
    loadResumeList();
    refreshView();
    updateStats();
  };
});

// ── PROTO / MODE ──────────────────────────────────────────────────────────────
function switchProto(p) {
  proto = p;
  ALL_CASES = p === 'portal' ? ALL_PORTAL_CASES : ALL_APP_CASES;
  TOTAL = ALL_CASES.length;
  batchFilter = 'all'; statusFilter = 'all'; searchQ = '';
  document.getElementById('pt-app').classList.toggle('active', p === 'app');
  document.getElementById('pt-portal').classList.toggle('active', p === 'portal');
  document.getElementById('src-proto').textContent = p === 'app' ? 'PRT-0392 · Modus App UIRS Test Cases' : 'PRT-0396 · Modus Portal UIRS Test Cases';
  document.getElementById('tb-brand').textContent = 'CGMX1 Console';
  document.title = 'CGMX1 Console';
  document.getElementById('src-cnt').textContent = TOTAL;
  // update assets overlay title and btn tooltip
  var assetsTitle = document.getElementById('assets-overlay-title');
  if (assetsTitle) assetsTitle.textContent = p === 'portal' ? 'Modus Portal — Test Assets' : 'Modus App — Test Assets & QR Codes';
  var assetsBtn = document.getElementById('btn-assets');
  if (assetsBtn) assetsBtn.title = p === 'portal' ? 'Portal test accounts & environment' : 'Test assets & QR codes';
  // refresh assets panel if it's open
  if (!document.getElementById('overlay-assets').classList.contains('hidden')) refreshAccountDisplay();
  const si = document.getElementById('search-inp'); if (si) si.value = '';
  _syncExecProtoBtns(p);
  buildSidebar();
  loadResumeList();
  refreshView();
}

function execSetProto(p) {
  switchProto(p);
}

function _syncExecProtoBtns(p) {
  const btnApp    = document.getElementById('ep-app');
  const btnPortal = document.getElementById('ep-portal');
  if (!btnApp) return;
  btnApp.classList.toggle('active', p === 'app');
  btnPortal.classList.toggle('active', p === 'portal');
  const startBtn = document.getElementById('exec-start-btn');
  if (startBtn) startBtn.textContent = '▶ Start Execution — ' + (p === 'app' ? 'PRT-0392 · Modus App UIRS Test Cases' : 'PRT-0396 · Modus Portal UIRS Test Cases');
}

function switchMode(m) {
  mode = m;
  document.getElementById('mt-cases').classList.toggle('active', m === 'cases');
  document.getElementById('mt-exec').classList.toggle('active', m === 'exec');
  document.getElementById('tb-row3').style.display = m === 'cases' ? '' : 'none';  // pills only for cases
  document.getElementById('tb-row4').classList.toggle('show', true);               // search always
  document.getElementById('exec-stats').style.display = m === 'exec' ? 'flex' : 'none';
  document.getElementById('cases-btns').style.display = m === 'cases' ? 'flex' : 'none';
  document.getElementById('exec-btns').style.display  = m === 'exec'  ? 'flex' : 'none';
  refreshView();
}

function refreshView() {
  const listArea   = document.getElementById('list-area');
  const execSetup  = document.getElementById('exec-setup');
  const noCases    = document.getElementById('no-cases');
  const sidebar    = document.getElementById('sidebar');
  const detail     = document.getElementById('detail');

  // Show/hide exec stats progress bar
  document.getElementById('tb-row2').classList.toggle('show', mode === 'exec' && runActive);
  document.getElementById('btn-end-run').style.display = (mode === 'exec' && runActive) ? '' : 'none';

  if (mode === 'cases') {
    noCases.classList.remove('show');
    execSetup.classList.remove('show');
    listArea.style.display = 'flex';
    sidebar.style.display = '';
    document.getElementById('det-ev-sec').classList.remove('show');
    document.getElementById('det-foot').classList.remove('show');
    // Update mini-bars hidden
    document.querySelectorAll('.sb-bar').forEach(b => b.classList.remove('show'));
    renderList();
  } else {
    // exec mode
    if (!runActive) {
      noCases.classList.remove('show');
      execSetup.classList.add('show');
      listArea.style.display = 'none';
      sidebar.style.display = 'none';
    } else {
      noCases.classList.remove('show');
      execSetup.classList.remove('show');
      listArea.style.display = 'flex';
      sidebar.style.display = '';
      document.getElementById('det-ev-sec').classList.add('show');
      document.getElementById('det-foot').classList.add('show');
      document.querySelectorAll('.sb-bar').forEach(b => b.classList.add('show'));
      renderList();
      updateMinis();
    }
  }
}

// ── SIDEBAR ───────────────────────────────────────────────────────────────────
function buildSidebar() {
  const map = {};
  ALL_CASES.forEach(c => { if (!map[c.sec]) map[c.sec]=[]; map[c.sec].push(c.id); });
  batches = Object.keys(map).map(s => ({sec:s, ids:map[s]}));
  const cont = document.getElementById('sb-list');
  cont.innerHTML = '';
  batches.forEach(b => {
    const div = document.createElement('div');
    div.className = 'sb-item'; div.dataset.b = b.sec;
    div.onclick = () => setBatch(b.sec, div);
    div.innerHTML = `<span class="sb-label">${esc(b.sec)}</span>
<div class="sb-bar"><div class="sb-fill" id="sbf-${CSS.escape(b.sec)}" style="width:0%"></div></div>
<span class="sb-cnt">${b.ids.length}</span>`;
    cont.appendChild(div);
  });
}

function setBatch(b, el) {
  batchFilter = b;
  document.querySelectorAll('.sb-item').forEach(e => e.classList.remove('active'));
  if (el) el.classList.add('active');
  renderList();
}

function setFilter(f, el) {
  statusFilter = f;
  document.querySelectorAll('.filter-pill').forEach(e => e.classList.remove('active'));
  if (el) el.classList.add('active');
  renderList();
}

function updateMinis() {
  batches.forEach(b => {
    const done = b.ids.filter(id => results[id]).length;
    const pct  = b.ids.length ? Math.round(done/b.ids.length*100) : 0;
    const el   = document.getElementById('sbf-' + CSS.escape(b.sec));
    if (el) el.style.width = pct + '%';
  });
}

// ── CASE LIST ─────────────────────────────────────────────────────────────────
function renderList() {
  let vis = ALL_CASES;
  if (batchFilter !== 'all') vis = vis.filter(c => c.sec === batchFilter);
  if (mode === 'exec' && runActive) {
    if (statusFilter === 'P')  vis = vis.filter(c => results[c.id]?.status === 'P');
    else if (statusFilter === 'F') vis = vis.filter(c => results[c.id]?.status === 'F');
    else if (statusFilter === 'B') vis = vis.filter(c => results[c.id]?.status === 'B');
    else if (statusFilter === 'NR') vis = vis.filter(c => results[c.id]?.status === 'NR' || !results[c.id]);
  }
  if (searchQ) vis = vis.filter(c => c.id.toLowerCase().includes(searchQ) || c.t.toLowerCase().includes(searchQ));
  filteredIds = vis.map(c => c.id);

  const list  = document.getElementById('case-list');
  const empty = document.getElementById('list-empty');
  list.innerHTML = '';
  if (!vis.length) { empty.style.display = ''; list.style.display = 'none'; return; }
  empty.style.display = 'none'; list.style.display = '';

  let lastSec = null;
  vis.forEach(c => {
    if (c.sec !== lastSec) {
      const hdr = document.createElement('div');
      hdr.className = 'sec-hdr'; hdr.textContent = c.sec;
      list.appendChild(hdr); lastSec = c.sec;
    }
    const r  = results[c.id];
    const st = r ? r.status : null;
    const row = document.createElement('div');
    row.className = 'row' + (selId === c.id ? ' sel' : '');
    row.dataset.id = c.id; row.onclick = () => openDetail(c.id);
    const dotCls = st ? 'sdot sdot-'+st : 'sdot';
    const badge  = st ? `<span class="badge st-${st}">${st}</span>` : '';
    row.innerHTML = `<span class="runno mono">${c.r}</span><span class="${dotCls}"></span><div class="mid"><div class="rid mono">${esc(c.id)}</div><div class="ttl">${esc(c.t)}</div></div>${badge}`;
    list.appendChild(row);
  });

  // Update filter pill counts (cases mode)
  if (mode === 'cases') updateFilterCounts(vis);
}

function updateFilterCounts(visAll) {
  const all  = ALL_CASES.filter(c => !batchFilter || batchFilter==='all' || c.sec===batchFilter);
  let P=0,F=0,B=0,NR=0;
  all.forEach(c => {
    const st = results[c.id]?.status;
    if (st==='P') P++; else if (st==='F') F++; else if (st==='B') B++; else NR++;
  });
  document.getElementById('fp-cnt-all').textContent = all.length;
  document.getElementById('fp-cnt-P').textContent   = P;
  document.getElementById('fp-cnt-F').textContent   = F;
  document.getElementById('fp-cnt-B').textContent   = B;
  document.getElementById('fp-cnt-NR').textContent  = NR;
}

// ── DETAIL ────────────────────────────────────────────────────────────────────
function openDetail(id) {
  selId = id;
  document.querySelectorAll('.row').forEach(r => r.classList.toggle('sel', r.dataset.id === id));
  const c = ALL_CASES.find(x => x.id === id); if (!c) return;
  document.getElementById('detail').classList.add('open');
  document.getElementById('det-id').textContent = c.id + '  ·  Run ' + c.r;
  document.getElementById('det-title').textContent = c.t;
  document.getElementById('det-meta').innerHTML =
    (c.req ? `<span class="chip">${esc(c.req)}</span>` : '') +
    `<span class="chip">${esc(c.sec)}</span>`;
  document.getElementById('d-pre').innerHTML  = fmtNum(c.pre);
  document.getElementById('d-ev').innerHTML   = fmtNum(c.ev);
  const execLive = mode === 'exec' && runActive;
  const r = execLive ? (results[id] || {}) : {};
  renderSteps(c, execLive ? (r.evidence || []) : null);
  if (execLive) {
    document.getElementById('ev-def').value   = r.defect || '';
    document.getElementById('ev-notes').value = r.notes  || '';
    document.getElementById('ev-ts').textContent = r.timestamp ? 'Last saved: ' + r.timestamp : '';
    renderGeneralEvidence(r.evidence || []);
    hlSt(r.status || null);
  }
}

function closeDetail() {
  document.getElementById('detail').classList.remove('open');
  selId = null;
  document.querySelectorAll('.row').forEach(r => r.classList.remove('sel'));
}

// ── DETAIL PANEL RESIZE / EXPAND ──────────────────────────────────────────────
(function initDetailResize(){
  var panel = document.getElementById('detail');
  var handle = document.getElementById('det-resize');
  if (!panel || !handle) return;

  var saved = parseInt(localStorage.getItem('detailPanelWidth') || '', 10);
  if (saved && saved >= 320) panel.style.width = Math.min(saved, Math.floor(window.innerWidth*0.95)) + 'px';

  var dragging = false, startX = 0, startW = 0;
  handle.addEventListener('mousedown', function(e){
    if (panel.classList.contains('maximized')) return;
    dragging = true; startX = e.clientX; startW = panel.getBoundingClientRect().width;
    handle.classList.add('active');
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  window.addEventListener('mousemove', function(e){
    if (!dragging) return;
    var dx = startX - e.clientX; // dragging left (negative clientX delta) widens the panel
    var w = Math.max(320, Math.min(startW + dx, Math.floor(window.innerWidth*0.95)));
    panel.style.width = w + 'px';
  });
  window.addEventListener('mouseup', function(){
    if (!dragging) return;
    dragging = false;
    handle.classList.remove('active');
    document.body.style.userSelect = '';
    localStorage.setItem('detailPanelWidth', Math.round(panel.getBoundingClientRect().width));
  });
})();

function toggleDetailMaximize(){
  var panel = document.getElementById('detail');
  panel.classList.toggle('maximized');
  document.getElementById('det-expand').textContent = panel.classList.contains('maximized') ? '⤡' : '⤢';
}

function openCaseInExec() {
  if (!selId) return;
  switchMode('exec');
  if (runActive) {
    setTimeout(() => {
      openDetail(selId);
      const row = document.querySelector(`.row[data-id="${CSS.escape(selId)}"]`);
      if (row) row.scrollIntoView({block:'center'});
    }, 50);
  }
}

function hlSt(st) {
  document.querySelectorAll('.rbtn').forEach(b => {
    b.classList.remove('sel-P','sel-F','sel-B','sel-NR');
  });
  if (st) {
    const idx = {P:0,F:1,B:2,NR:3}[st];
    if (idx !== undefined) document.querySelectorAll('.rbtn')[idx]?.classList.add('sel-'+st);
  }
}

// ── EXEC: START / RESUME ──────────────────────────────────────────────────────
function startRun() {
  const name   = document.getElementById('inp-name').value.trim()   || 'Unnamed Run';
  const tester = document.getElementById('inp-tester').value.trim() || '';
  const device = document.getElementById('inp-device').value.trim() || '';
  const ver    = document.getElementById('inp-ver').value.trim()    || '';
  runId = 'run_' + Date.now();
  const runProto = proto;
  const lsKey    = runProto === 'portal' ? 'PRT0702_runs' : 'PRT0701_runs';
  runInfo = {id:runId,name,tester,device,version:ver,date:new Date().toLocaleDateString(),proto:runProto,lsKey};
  results = {};
  let runs=[]; try{runs=JSON.parse(localStorage.getItem(lsKey)||'[]');}catch(e){}
  runs.push(runInfo);
  localStorage.setItem(lsKey, JSON.stringify(runs));
  saveRun(); runActive = true;
  refreshView(); updateStats(); updateEvidenceFolderLabel();
}

function loadResumeList() {
  const lsKey = proto === 'portal' ? 'PRT0702_runs' : 'PRT0701_runs';
  let runs=[]; try{runs=JSON.parse(localStorage.getItem(lsKey)||'[]');}catch(e){}
  const box  = document.getElementById('resume-box');
  const cont = document.getElementById('resume-items');
  box.style.display = 'none'; cont.innerHTML = '';
  if (!runs.length) return;
  box.style.display = 'block'; cont.innerHTML = '';
  runs.slice().reverse().forEach(r => {
    const rKey  = r.lsKey || (r.proto==='portal'?'PRT0702_runs':'PRT0701_runs');
    const saved = JSON.parse(localStorage.getItem((r.proto==='portal'?'PRT0702':'PRT0701')+'_run_'+r.id)||'{}');
    const done  = Object.keys(saved.results||{}).length;
    const pct   = TOTAL ? Math.round(done/TOTAL*100) : 0;
    const div   = document.createElement('div');
    div.className = 'run-item';
    div.innerHTML = `<div style="flex:1"><div class="run-name">${esc(r.name)}</div><div class="run-meta">${esc(r.tester||'')} · ${esc(r.device||'')} · ${esc(r.date||'')}</div></div><span class="run-pct">${pct}%</span><button class="run-del" onclick="delRun(event,'${r.id}')">🗑</button>`;
    div.onclick = e => { if(!e.target.closest('.run-del')) resumeRun(r.id); };
    cont.appendChild(div);
  });
}

function resumeRun(id) {
  const saved = JSON.parse(localStorage.getItem('PRT0701_run_'+id)||
                           localStorage.getItem('PRT0702_run_'+id)||'{}');
  if (!saved.runInfo) return;
  runId=id; runInfo=saved.runInfo; results=saved.results||{};
  // sync protocol to match the resumed run
  if (runInfo.proto && runInfo.proto !== proto) switchProto(runInfo.proto);
  runActive=true; refreshView(); updateStats(); updateEvidenceFolderLabel();
}

function delRun(e,id) {
  e.stopPropagation();
  if (!confirm('Delete this run?')) return;
  const pfx = proto === 'portal' ? 'PRT0702' : 'PRT0701';
  localStorage.removeItem(pfx+'_run_'+id);
  const lsKey = pfx+'_runs';
  let runs=[]; try{runs=JSON.parse(localStorage.getItem(lsKey)||'[]');}catch(e){}
  runs=runs.filter(r=>r.id!==id);
  localStorage.setItem(lsKey,JSON.stringify(runs));
  loadResumeList();
}

function saveRun() {
  if (runId) {
    const pfx = (runInfo.proto||proto)==='portal' ? 'PRT0702' : 'PRT0701';
    localStorage.setItem(pfx+'_run_'+runId,JSON.stringify({runInfo,results}));
  }
}

// ── EXEC: RECORD RESULT ───────────────────────────────────────────────────────
function setSt(st) {
  if (!selId || !runActive) return;
  if (!results[selId]) results[selId]={};
  const ts = new Date().toLocaleString();
  const cur = results[selId] || {};
  Object.assign(results[selId],{
    status:st,timestamp:ts,
    defect:document.getElementById('ev-def').value,
    notes:document.getElementById('ev-notes').value,
    evidence: cur.evidence || []
  });
  document.getElementById('ev-ts').textContent='Saved: '+ts;
  hlSt(st); saveRun(); updateStats(); updateMinis();
  const row=document.querySelector(`.row[data-id="${CSS.escape(selId)}"]`);
  if (row) {
    const dot=row.querySelector('.sdot');
    if (dot){dot.className='sdot sdot-'+st;}
    let badge=row.querySelector('.badge');
    if (!badge){badge=document.createElement('span');row.appendChild(badge);}
    badge.className='badge st-'+st; badge.textContent=st;
  }
}

function saveEv() {
  if (!selId||!runActive) return;
  if (!results[selId]) results[selId]={};
  const ts=results[selId].timestamp||new Date().toLocaleString();
  Object.assign(results[selId],{
    defect:document.getElementById('ev-def').value,
    notes:document.getElementById('ev-notes').value,
    timestamp:ts
  });
  document.getElementById('ev-ts').textContent='Edited: '+ts;
  saveRun();
}

function navCase(dir) {
  if (!selId) return;
  const i=filteredIds.indexOf(selId); if(i===-1)return;
  const next=filteredIds[i+dir]; if(next) openDetail(next);
}

// ── PER-STEP EVIDENCE UPLOAD ──────────────────────────────────────────────────
var pendingTag = null;
var idbDb = null;
var evidenceDirHandle = null; // FileSystemDirectoryHandle, when connected

(function openIDB(){
  var req = indexedDB.open('PRT_EVIDENCE', 2);
  req.onupgradeneeded = function(e){
    var db = e.target.result;
    if (!db.objectStoreNames.contains('blobs')) db.createObjectStore('blobs');
    if (!db.objectStoreNames.contains('handles')) db.createObjectStore('handles');
  };
  req.onsuccess = function(e){ idbDb = e.target.result; restoreEvidenceFolder(); };
})();

function idbPut(id, blob){ if(!idbDb) return; var tx=idbDb.transaction('blobs','readwrite'); tx.objectStore('blobs').put(blob,id); }
function idbDel(id){ if(!idbDb) return; var tx=idbDb.transaction('blobs','readwrite'); tx.objectStore('blobs').delete(id); }
function idbGet(id){ return new Promise(function(res){ if(!idbDb){res(null);return;} var tx=idbDb.transaction('blobs','readonly'); var req=tx.objectStore('blobs').get(id); req.onsuccess=function(){res(req.result||null);}; req.onerror=function(){res(null);}; }); }

// ── Evidence folder: direct-to-disk save on attach (File System Access API) ──
// Browser pages can't write to an arbitrary path silently; the user picks a
// folder once (a native permission grant), the handle is cached in IndexedDB,
// and every subsequent attach writes straight into it with no extra prompt
// (until the browser revokes the permission, e.g. after a restart).
function updateEvidenceFolderLabel(){
  var el = document.getElementById('evidence-folder-label');
  if (!el) return;
  if (!evidenceDirHandle) {
    el.textContent = window.showDirectoryPicker ? 'Evidence folder: not connected' : 'Evidence folder: not supported in this browser';
    return;
  }
  var sub = runInfo && runInfo.name ? sanitizeFolderName(runInfo.name) : null;
  el.textContent = 'Evidence folder: ' + evidenceDirHandle.name + (sub ? ('\\' + sub + ' (saving on attach)') : ' (pick a run to start saving)');
}

async function restoreEvidenceFolder(){
  if (!idbDb || !window.showDirectoryPicker) { updateEvidenceFolderLabel(); return; }
  try {
    var tx = idbDb.transaction('handles','readonly');
    var req = tx.objectStore('handles').get('evidenceDir');
    req.onsuccess = async function(){
      var handle = req.result;
      if (!handle) { updateEvidenceFolderLabel(); return; }
      try {
        var perm = await handle.queryPermission({mode:'readwrite'});
        if (perm === 'granted') { evidenceDirHandle = handle; }
        // 'prompt'/'denied': leave disconnected; user re-picks via the link (needs a click to re-grant).
      } catch(e) {}
      updateEvidenceFolderLabel();
    };
    req.onerror = function(){ updateEvidenceFolderLabel(); };
  } catch(e) { updateEvidenceFolderLabel(); }
}

async function chooseEvidenceFolder(){
  if (!window.showDirectoryPicker) { alert('This browser does not support saving straight to a folder. Use the console\'s Export menu instead.'); return; }
  try {
    var handle = await window.showDirectoryPicker({ id: 'prt-evidence', mode: 'readwrite' });
    evidenceDirHandle = handle;
    if (idbDb) { var tx = idbDb.transaction('handles','readwrite'); tx.objectStore('handles').put(handle, 'evidenceDir'); }
    updateEvidenceFolderLabel();
  } catch(e) { /* user cancelled the picker */ }
}

var runDirHandles = {}; // runId -> FileSystemDirectoryHandle, one subfolder per execution

function sanitizeFolderName(s){
  return String(s||'run').replace(/[\\/:*?"<>|]/g, '-').replace(/\s+/g,' ').trim().slice(0,80) || 'run';
}

async function getRunEvidenceDir(){
  if (!evidenceDirHandle || !runId) return null;
  if (runDirHandles[runId]) return runDirHandles[runId];
  var folderName = sanitizeFolderName((runInfo && runInfo.name) || runId);
  try {
    var dir = await evidenceDirHandle.getDirectoryHandle(folderName, {create:true});
    runDirHandles[runId] = dir;
    return dir;
  } catch(e) { console.warn('could not create run evidence folder', folderName, e); return null; }
}

async function writeEvidenceToDisk(name, blob){
  var dir = await getRunEvidenceDir();
  if (!dir) return;
  try {
    var fh = await dir.getFileHandle(name, {create:true});
    var ws = await fh.createWritable();
    await ws.write(blob);
    await ws.close();
  } catch(e) { console.warn('evidence disk-write failed for', name, e); }
}

function evThumbHtml(ev, label){
  var isVid = (ev.contentType||'').indexOf('video')===0;
  var src = ev.url || '';
  return '<div class="ev-thumb" data-evid="'+esc(ev.id)+'" title="'+esc(ev.name||label)+'">'
    +(isVid?'<video src="'+esc(src)+'" muted></video>':'<img src="'+esc(src)+'" alt="">')
    +'<button class="dl" data-dl="'+esc(ev.id)+'" title="Download">&#x2B07;</button>'
    +'<button class="rm" data-rm="'+esc(ev.id)+'" title="Remove">&#x2715;</button>'
    +'</div>';
}

function evAddCapButtons(tag){
  return '<div class="ev-add" data-addtag="'+esc(tag||'')+'">'
    +'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>Add</div>'
    +'<div class="ev-add" data-captag="'+esc(tag||'')+'" title="Capture a screen/window (e.g. a mirrored phone)">'
    +'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>Capture</div>';
}

// Procedure + Expected Result rendered as one card per step, with that
// step's evidence (thumbnails + Add/Capture) right there — not scrolled
// off in a separate section — when a run is active.
function renderSteps(c, evidence){
  var wrap = document.getElementById('d-steps');
  if (!wrap) return;
  var procItems = splitNumbered(c.proc||'');
  var expItems  = splitNumbered(c.exp||'');
  var showEv = !!evidence;
  if (!procItems && !expItems) {
    wrap.innerHTML = '<div class="det-content" style="margin-bottom:8px"><div class="step-exp-lbl" style="margin-bottom:3px">Procedure</div>'+fmtText(c.proc||'')+'</div>'
      + '<div class="det-content"><div class="step-exp-lbl" style="margin-bottom:3px">Expected Result</div>'+fmtText(c.exp||'')+'</div>';
    return;
  }
  procItems = procItems || [];
  expItems = expItems || [];
  var count = Math.max(procItems.length, expItems.length);
  var html = '';
  for (var i=1; i<=count; i++){
    var tag = 'step-'+i;
    var items = (evidence||[]).filter(function(e){ return (e.tag||null)===tag; });
    var thumbs = items.map(function(ev){ return evThumbHtml(ev, 'Step '+i); }).join('');
    html += '<div class="step-card">'
      + '<div class="step-row"><div class="step-num">'+i+'</div><div class="step-proc">'+esc(procItems[i-1]||'')+'</div></div>'
      + (expItems[i-1] ? ('<div class="step-exp"><div class="step-exp-lbl">Expected</div>'+esc(expItems[i-1])+'</div>') : '')
      + (showEv ? ('<div class="ev-group-row step-ev-row">'+thumbs+evAddCapButtons(tag)+'</div>') : '')
      + '</div>';
  }
  wrap.innerHTML = html;
  if (showEv) restoreEvidenceThumbs(evidence, wrap);
}

function renderGeneralEvidence(evidence){
  var wrap = document.getElementById('evidence-general');
  if (!wrap) return;
  var items = (evidence||[]).filter(function(e){ return !e.tag; });
  var thumbs = items.map(function(ev){ return evThumbHtml(ev, 'General'); }).join('');
  wrap.innerHTML = '<div class="ev-group-row">'+thumbs+evAddCapButtons(null)+'</div>';
  restoreEvidenceThumbs(evidence, wrap);
}

// Restore object URLs from IDB for any items that lost theirs (page reload)
function restoreEvidenceThumbs(evidence, scope){
  (evidence||[]).forEach(function(ev){
    if (!ev.url) {
      idbGet(ev.id).then(function(blob){
        if (!blob) return;
        ev.url = URL.createObjectURL(blob);
        var img = scope.querySelector('[data-evid="'+ev.id+'"] img, [data-evid="'+ev.id+'"] video');
        if (img) img.src = ev.url;
      });
    }
  });
}

// One delegated listener covers Add/Capture/Remove/Download buttons
// wherever they're rendered (per-step cards or the General group).
document.addEventListener('DOMContentLoaded', function(){
  var body = document.getElementById('det-body');
  if (!body) return;
  body.addEventListener('click', function(e){
    var addBtn = e.target.closest('[data-addtag]');
    if (addBtn) { pendingTag = addBtn.getAttribute('data-addtag') || null; document.getElementById('file-input').click(); return; }
    var capBtn = e.target.closest('[data-captag]');
    if (capBtn) { captureScreenForTag(capBtn.getAttribute('data-captag') || null); return; }
    var rmBtn = e.target.closest('[data-rm]');
    if (rmBtn) { e.stopPropagation(); removeEvidence(rmBtn.getAttribute('data-rm')); return; }
    var dlBtn = e.target.closest('[data-dl]');
    if (dlBtn) {
      e.stopPropagation();
      var evId = dlBtn.getAttribute('data-dl');
      var cur = results[selId] || {};
      var ev = (cur.evidence||[]).find(function(x){ return x.id===evId; });
      if (ev && ev.url){ var a=document.createElement('a'); a.href=ev.url; a.download=ev.name||evId; a.click(); }
    }
  });
});

function refreshEvidenceUI(c){
  var evidence = (results[selId]||{}).evidence || [];
  renderSteps(c, evidence);
  renderGeneralEvidence(evidence);
}

function removeEvidence(evId){
  if (!selId) return;
  var cur = results[selId] || {};
  var ev = (cur.evidence||[]).find(function(x){ return x.id===evId; });
  if (ev && ev.url) URL.revokeObjectURL(ev.url);
  results[selId].evidence = (cur.evidence||[]).filter(function(e){ return e.id!==evId; });
  idbDel(evId);
  refreshEvidenceUI(ALL_CASES.find(function(x){return x.id===selId;})||{});
  saveRun();
}

document.addEventListener('DOMContentLoaded', function(){
  var fi = document.getElementById('file-input');
  if (fi) fi.addEventListener('change', function(e){ handleFiles(e.target.files); fi.value=''; });
});

function attachEvidenceFile(file, tag, extOverride){
  var id = selId;
  var c = ALL_CASES.find(function(x){return x.id===id;}) || {};
  var evId = 'ev_' + Date.now() + '_' + Math.random().toString(36).slice(2,7);
  var url = URL.createObjectURL(file);
  var tagSlug = tag ? tag : 'general';
  var sameTag = ((results[id]||{}).evidence||[]).filter(function(e){ return (e.tag||null)===tag; }).length;
  var ext = extOverride || file.name.split('.').pop() || 'jpg';
  var name = (c.id||id) + '_' + tagSlug + (sameTag ? '_'+(sameTag+1) : '') + '.' + ext;
  var entry = {id:evId, url:url, contentType:file.type, tag:tag||undefined, name:name};
  if (!results[id]) results[id]={};
  if (!results[id].evidence) results[id].evidence=[];
  results[id].evidence.push(entry);
  idbPut(evId, file);
  writeEvidenceToDisk(name, file);
  refreshEvidenceUI(c);
  saveRun();
}

function handleFiles(fileList){
  if (!selId || !runActive) return;
  var tag = pendingTag || null;
  pendingTag = null;
  Array.prototype.slice.call(fileList).forEach(function(file){ attachEvidenceFile(file, tag); });
}

// ── SCREEN/WINDOW CAPTURE ─────────────────────────────────────────────────────
// Grabs a still frame from a screen/window the browser's own picker lets the
// user choose (e.g. a phone-mirroring app's window — QuickTime for iOS,
// scrcpy/Vysor/manufacturer mirroring for Android). No cable protocol is
// implemented here; the phone must already be mirrored to a visible window.
var captureStream = null;

async function captureScreenForTag(tag){
  if (!selId || !runActive) { alert('Open a case and start a run first.'); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
    alert('This browser does not support screen capture. Use Add to attach a file instead.');
    return;
  }
  try {
    if (!captureStream || !captureStream.getVideoTracks()[0] || captureStream.getVideoTracks()[0].readyState === 'ended') {
      captureStream = await navigator.mediaDevices.getDisplayMedia({video:{cursor:'never'}, audio:false});
      captureStream.getVideoTracks()[0].addEventListener('ended', function(){ captureStream = null; });
    }
    var track = captureStream.getVideoTracks()[0];
    var video = document.createElement('video');
    video.srcObject = captureStream;
    await video.play();
    await new Promise(function(r){ if (video.videoWidth) r(); else video.onloadedmetadata = r; });
    var canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    video.pause(); video.srcObject = null;
    var blob = await new Promise(function(res){ canvas.toBlob(res, 'image/png'); });
    if (!blob) { alert('Capture failed — no frame grabbed.'); return; }
    var file = new File([blob], 'capture.png', {type:'image/png'});
    attachEvidenceFile(file, tag, 'png');
  } catch(e) {
    if (e && e.name === 'NotAllowedError') return; // user cancelled the picker
    console.warn('screen capture failed', e);
    alert('Screen capture failed: ' + (e && e.message ? e.message : e));
  }
}

function stopScreenCapture(){
  if (captureStream) { captureStream.getTracks().forEach(function(t){ t.stop(); }); captureStream = null; }
}

// ── STATS ─────────────────────────────────────────────────────────────────────
function updateStats() {
  let P=0,F=0,B=0;
  ALL_CASES.forEach(c=>{
    const st=results[c.id]?.status;
    if(st==='P')P++;else if(st==='F')F++;else if(st==='B')B++;
  });
  const done=P+F+B, nr=TOTAL-done;
  document.getElementById('h-p').textContent=P;
  document.getElementById('h-f').textContent=F;
  document.getElementById('h-b').textContent=B;
  document.getElementById('h-n').textContent=nr;
  document.getElementById('pt-pass').style.width=(TOTAL?P/TOTAL*100:0)+'%';
  document.getElementById('pt-fail').style.width=(TOTAL?F/TOTAL*100:0)+'%';
  document.getElementById('pt-blocked').style.width=(TOTAL?B/TOTAL*100:0)+'%';
  document.getElementById('prog-lbl').textContent=done+' / '+TOTAL;
  updateFilterCounts(ALL_CASES);
}

// ── EXPORT ────────────────────────────────────────────────────────────────────
document.getElementById('btn-exp-tog').onclick=e=>{
  e.stopPropagation();
  document.getElementById('exp-menu').classList.toggle('open');
};
document.addEventListener('click',()=>document.getElementById('exp-menu').classList.remove('open'));

function exportCSV(){
  const rows=[['Run','Tester','Device','App Version','Case ID','Batch','Title','Requirement','Status','Screenshot','Defect ID','Notes','Timestamp']];
  ALL_CASES.forEach(c=>{
    const r=results[c.id]||{};
    rows.push([runInfo.name||'',runInfo.tester||'',runInfo.device||'',runInfo.version||'',c.id,c.sec,c.t,c.req||'',r.status||'',r.screenshot||'',r.defect||'',r.notes||'',r.timestamp||'']);
  });
  const csv=rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n');
  const reportProtocol = (runInfo.proto||proto)==='portal' ? 'PRT-0396' : 'PRT-0392';
  dl(csv,'text/csv',reportProtocol+'-'+(runInfo.name||'run').replace(/\s+/g,'-')+'.csv');
}

function exportSummary(){
  const reportProtocol = (runInfo.proto||proto)==='portal' ? 'PRT-0396' : 'PRT-0392';
  let P=0,F=0,B=0,NR=0; const bs={};
  ALL_CASES.forEach(c=>{
    const st=results[c.id]?.status||'NR';
    if(st==='P')P++;else if(st==='F')F++;else if(st==='B')B++;else NR++;
    if(!bs[c.sec])bs[c.sec]={P:0,F:0,B:0,NR:0,t:0};
    bs[c.sec][st]++;bs[c.sec].t++;
  });
  const done=P+F+B,pr=done?Math.round(P/done*100):0;
  let h=`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${reportProtocol} Summary</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>body{font-family:"IBM Plex Sans",sans-serif;font-size:12px;margin:24px 32px;color:#1a2233;background:#f4f5f8}
h1{font-size:18px;margin:0 0 4px}p{color:#667085;font-size:11.5px;margin:0 0 18px}
.stats{display:flex;gap:12px;margin-bottom:18px}
.box{text-align:center;padding:12px 16px;border-radius:10px;border:1px solid #dfe3ea;background:#fff;min-width:68px}
.n{font-size:22px;font-weight:700;font-family:"IBM Plex Mono",monospace}
.l{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#667085}
.p{color:#1f9e64}.f{color:#d6434e}.b{color:#c9821e}.nr{color:#78829a}
table{width:100%;border-collapse:collapse;font-size:11.5px;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #dfe3ea}
th{background:#eef0f5;padding:6px 9px;text-align:left;border-bottom:2px solid #dfe3ea;font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:#667085}
td{padding:5px 9px;border-bottom:1px solid #eef0f5}
@media print{@page{margin:12mm}}</style></head><body>
<h1>${reportProtocol} Test Execution Summary</h1>
<p>Run: <b>${esc(runInfo.name||'')}</b> · Tester: <b>${esc(runInfo.tester||'')}</b> · Device: <b>${esc((runInfo.device||'')+' '+(runInfo.version||''))}</b> · Date: <b>${esc(runInfo.date||'')}</b> · Total: <b>${TOTAL}</b> · Pass rate: <b>${pr}%</b></p>
<div class="stats">
<div class="box"><div class="n p">${P}</div><div class="l">Pass</div></div>
<div class="box"><div class="n f">${F}</div><div class="l">Fail</div></div>
<div class="box"><div class="n b">${B}</div><div class="l">Blocked</div></div>
<div class="box"><div class="n nr">${NR}</div><div class="l">Not run</div></div>
</div>
<table><tr><th>Batch</th><th>Total</th><th>P</th><th>F</th><th>B</th><th>NR</th></tr>`;
  Object.entries(bs).forEach(([s,v])=>h+=`<tr><td>${esc(s)}</td><td>${v.t}</td><td>${v.P}</td><td>${v.F}</td><td>${v.B}</td><td>${v.NR}</td></tr>`);
  h+=`</table></body></html>`;pw(h);
}

function exportFull(){
  const reportProtocol = (runInfo.proto||proto)==='portal' ? 'PRT-0396' : 'PRT-0392';
  const exec=ALL_CASES.filter(c=>results[c.id]);
  let h=`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${reportProtocol} Evidence</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>body{font-family:"IBM Plex Sans",sans-serif;font-size:11px;margin:16px 24px;color:#1a2233;background:#f4f5f8}
h1{font-size:16px;margin:0 0 3px}p{color:#667085;font-size:11px;margin:0 0 12px}
.cb{border:1px solid #dfe3ea;border-radius:10px;margin-bottom:9px;background:#fff;page-break-inside:avoid}
.ch{background:#eef0f5;padding:7px 11px;border-bottom:1px solid #dfe3ea;display:flex;align-items:center;gap:8px;border-radius:10px 10px 0 0}
.ci{font-family:"IBM Plex Mono",monospace;font-size:10px;color:#667085}
.ct{flex:1;font-size:12px;font-weight:600}
.sb{padding:2px 7px;border-radius:100px;font-size:10px;font-weight:700}
.sP{background:#e3f7ec;color:#1f9e64}.sF{background:#fbe7e8;color:#d6434e}
.sB{background:#faedd7;color:#c9821e}.sNR{background:#edeff3;color:#78829a}
.cbody{padding:7px 11px;display:grid;grid-template-columns:1fr 1fr;gap:7px}
.fl{font-size:9px;text-transform:uppercase;letter-spacing:.05em;color:#8992a3;margin-bottom:2px;font-weight:700}
.fv{color:#1a2233;line-height:1.4;white-space:pre-wrap;font-size:11px}
.er{background:#f4f5f8;border-top:1px solid #dfe3ea;padding:5px 11px;display:flex;gap:12px;font-size:10px;color:#667085;border-radius:0 0 10px 10px}
.er b{color:#1a2233}
@media print{@page{margin:10mm}}</style></head><body>
<h1>${reportProtocol} Full Evidence Report</h1>
<p>Run: <b>${esc(runInfo.name||'')}</b> · Tester: <b>${esc(runInfo.tester||'')}</b> · ${esc((runInfo.device||'')+' '+(runInfo.version||''))} · ${esc(runInfo.date||'')} · ${exec.length}/${TOTAL} executed</p>`;
  exec.forEach(c=>{
    const r=results[c.id];const st=r.status||'NR';
    h+=`<div class="cb"><div class="ch"><span class="ci">${esc(c.id)}</span><span class="ct">${esc(c.t)}</span><span class="sb s${st}">${st}</span></div>
<div class="cbody">
<div><div class="fl">Preconditions</div><div class="fv">${esc(c.pre||'')}</div></div>
<div><div class="fl">Expected Result</div><div class="fv">${esc(c.exp||'')}</div></div>
<div style="grid-column:1/-1"><div class="fl">Procedure</div><div class="fv">${esc(c.proc||'')}</div></div>
</div>
<div class="er"><span>Screenshot: <b>${esc(r.screenshot||'—')}</b></span><span>Defect: <b>${esc(r.defect||'—')}</b></span><span>Notes: <b>${esc(r.notes||'—')}</b></span><span style="margin-left:auto">Recorded: <b>${r.timestamp||''}</b></span></div>
</div>`;
  });
  h+=`</body></html>`;pw(h);
}

// Evidence files actually live in IndexedDB (PRT_EVIDENCE/blobs), keyed by
// evidence id; results[].evidence[] only carries metadata. None of the
// exports above ever read the blobs, so attached images/videos never left
// the browser. This walks every saved run (not just the active one) and
// zips every blob it can find, named from its evidence metadata.
async function exportEvidenceZip(){
  const statusFlash = (msg) => { const fl=document.getElementById('saved-flash'); if(!fl) return; fl.textContent=msg; fl.classList.add('show'); setTimeout(()=>fl.classList.remove('show'),2500); };
  if (typeof JSZip === 'undefined') { alert('JSZip failed to load (no internet access?). Evidence files remain in this browser only.'); return; }
  if (!idbDb) { alert('Evidence database is not open yet. Try again in a moment.'); return; }

  const idx = {};
  ['PRT0701_runs','PRT0702_runs'].forEach(lsKey => {
    let runs = []; try { runs = JSON.parse(localStorage.getItem(lsKey) || '[]'); } catch(e) {}
    const pfx = lsKey.startsWith('PRT0701') ? 'PRT0701' : 'PRT0702';
    runs.forEach(r => {
      let saved = {}; try { saved = JSON.parse(localStorage.getItem(pfx+'_run_'+r.id) || '{}'); } catch(e) {}
      Object.keys(saved.results||{}).forEach(caseId => {
        (saved.results[caseId].evidence||[]).forEach(e => {
          idx[e.id] = { caseId, name: e.name || (e.id+'.bin'), runName: r.name || r.id };
        });
      });
    });
  });

  const tx = idbDb.transaction('blobs','readonly');
  const store = tx.objectStore('blobs');
  const items = await new Promise(resolve => {
    const out = []; const req = store.openCursor();
    req.onsuccess = e => { const cur = e.target.result; if (cur) { out.push({key:cur.key, blob:cur.value}); cur.continue(); } else resolve(out); };
    req.onerror = () => resolve(out);
  });

  if (!items.length) { alert('No evidence files found in this browser.'); return; }

  const zip = new JSZip();
  const used = {};
  items.forEach(({key, blob}) => {
    const meta = idx[key] || {};
    let name = meta.name || (String(key) + '.bin');
    if (used[name]) { used[name]++; name = name.replace(/(\.[^.]+)?$/, '_'+used[name]+'$1'); } else used[name] = 1;
    zip.file(name, blob);
  });
  statusFlash('Zipping ' + items.length + ' evidence file(s)…');
  const content = await zip.generateAsync({type:'blob'});
  const url = URL.createObjectURL(content);
  const a = document.createElement('a');
  a.href = url; a.download = 'PRT-evidence-' + new Date().toISOString().slice(0,10) + '.zip';
  document.body.appendChild(a); a.click(); a.remove();
  statusFlash('Downloaded ' + items.length + ' evidence file(s).');
}

// ── CASES MODE: EXPORT ────────────────────────────────────────────────────────
// These buttons exist above the script tag so can be wired immediately.
document.getElementById('btn-cases-csv').onclick = exportCasesCsv;
document.getElementById('btn-cases-doc').onclick = exportCasesDocx;

function csvField(v){
  v=(v==null?'':String(v));
  if(/[",\n]/.test(v))v='"'+v.replace(/"/g,'""')+'"';
  return v;
}

function exportCasesCsv(){
  const rows=[['Run #','Case ID','Section','Requirement','Title','Preconditions','Procedure','Expected Result','Evidence']];
  ALL_CASES.forEach(c=>{
    rows.push([c.r,c.id,c.sec||'',c.req||'',c.t||'',c.pre||'',c.proc||'',c.exp||'',c.ev||'']);
  });
  const csv=rows.map(r=>r.map(csvField).join(',')).join('\r\n');
  var fname = proto==='portal' ? 'PRT-0396-Modus-Portal-UIRS-Test-Cases.csv' : 'PRT-0392-Modus-App-UIRS-Test-Cases.csv';
  dl(csv,'text/csv',fname);
}

// -- Word (.docx) export for cases mode (OOXML via JSZip) --
function escXml(s){return(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

var TC_W=[720,2380,2450,1900,800,1100];
var SPAN2_W=TC_W[0]+TC_W[1];
var SPAN4_W=TC_W[2]+TC_W[3]+TC_W[4]+TC_W[5];
var MID2_W=TC_W[2]+TC_W[3];
var TAIL2_W=TC_W[4]+TC_W[5];
var TBL_GRID='<w:tblGrid>'+TC_W.map(function(w){return'<w:gridCol w:w="'+w+'"/>';}).join('')+'</w:tblGrid>';
var TBL_PR='<w:tblPr><w:tblW w:type="auto" w:w="0"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tblBorders><w:tblLayout w:type="fixed"/><w:jc w:val="center"/></w:tblPr>';

function stepRangeLabel(n){return n===1?'1':'1–'+n;}
function docxRun(txt,bold){return'<w:r>'+(bold?'<w:rPr><w:b/></w:rPr>':'')+'<w:t xml:space="preserve">'+escXml(txt)+'</w:t></w:r>';}
function docxRunsWithBreaks(txt){
  if(!txt)return docxRun('');
  var lines=String(txt).split('\n');
  return lines.map(function(l,i){return docxRun(l)+(i<lines.length-1?'<w:br/>':'');}).join('');
}
function docxCell(txt,w,bold,shade,span){
  var sp=span&&span>1?'<w:gridSpan w:val="'+span+'"/>':'';
  var pr='<w:tcPr><w:tcW w:type="dxa" w:w="'+w+'"/>'+sp+(shade?'<w:shd w:val="clear" w:color="auto" w:fill="EEF0F5"/></w:tcPr>':'</w:tcPr>');
  return'<w:tc>'+pr+'<w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'+(txt?'<w:r>'+(bold?'<w:rPr><w:b/></w:rPr>':'')+'<w:t xml:space="preserve">'+escXml(txt)+'</w:t></w:r>':'<w:r><w:t/></w:r>')+'</w:p></w:tc>';
}
function docxCellLines(txt,w,span){
  var sp=span&&span>1?'<w:gridSpan w:val="'+span+'"/>':'';
  return'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="'+w+'"/>'+sp+'</w:tcPr><w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'+docxRunsWithBreaks(txt)+'</w:p></w:tc>';
}
function docxBatchHeadingPara(sec){
  var total=TC_W.reduce(function(a,b){return a+b;},0);
  return'<w:p><w:pPr><w:spacing w:before="200" w:after="80"/><w:pStyle w:val="Normal"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr><w:t>'+escXml(sec)+'</w:t></w:r></w:p>';
}
function docxCaseTitlePara(c){
  // c.t for portal cases already includes the case ID (e.g. "PAT-AUTH-001 — Title text").
  // Use c.t directly to avoid printing the ID twice in the heading paragraph.
  return'<w:p><w:pPr><w:spacing w:before="80" w:after="40"/></w:pPr><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">'+escXml(c.t)+'</w:t></w:r></w:p>';
}
function buildCaseTable(c){
  return proto==='portal' ? buildPortalCaseTable(c) : buildAppCaseTable(c);
}

// Shared 4-column table grid for both App and Portal DOCX exports
// PT_W = [label/step, action/content, expected/evidence, result] = 9350 twips total
var PT_W=[1500,3500,2800,1550];
var PT_GRID='<w:tblGrid>'+PT_W.map(function(w){return'<w:gridCol w:w="'+w+'"/>';}).join('')+'</w:tblGrid>';
var PT_PR='<w:tblPr><w:tblW w:type="auto" w:w="0"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tblBorders><w:tblLayout w:type="fixed"/><w:jc w:val="center"/></w:tblPr>';
function ptCell(txt,w,bold,shade,span){
  var sp=span&&span>1?'<w:gridSpan w:val="'+span+'"/>':'';
  var pr='<w:tcPr><w:tcW w:type="dxa" w:w="'+w+'"/>'+sp+(shade?'<w:shd w:val="clear" w:color="auto" w:fill="EEF0F5"/></w:tcPr>':'</w:tcPr>');
  return'<w:tc>'+pr+'<w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'+(txt?'<w:r>'+(bold?'<w:rPr><w:b/></w:rPr>':'')+'<w:t xml:space="preserve">'+escXml(txt)+'</w:t></w:r>':'<w:r><w:t/></w:r>')+'</w:p></w:tc>';
}
function ptCellLines(txt,w,span){
  var sp=span&&span>1?'<w:gridSpan w:val="'+span+'"/>':'';
  return'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="'+w+'"/>'+sp+'</w:tcPr><w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'+docxRunsWithBreaks(txt)+'</w:p></w:tc>';
}

// App DOCX: label rows on top, then 4-column step table (Step | Action | Expected Result | Test Result)
function buildAppCaseTable(c){
  var CONT_W=PT_W[1]+PT_W[2]+PT_W[3]; // 7850 — content spans cols 2-3-4
  var steps=c.proc?c.proc.split('\n').filter(function(l){return/^\d+\./.test(l.trim());}):[];
  var rows='';
  rows+='<w:tr>'+ptCell('Test Case ID',PT_W[0],true,true,1)+ptCellLines(c.id,CONT_W,3)+'</w:tr>';
  rows+='<w:tr>'+ptCell('Requirement',PT_W[0],true,true,1)+ptCellLines(c.req||'',CONT_W,3)+'</w:tr>';
  rows+='<w:tr>'+ptCell('Preconditions',PT_W[0],true,true,1)+ptCellLines(c.pre||'',CONT_W,3)+'</w:tr>';
  rows+='<w:tr>'+ptCell('Required Evidence',PT_W[0],true,true,1)+ptCellLines(c.ev||'',CONT_W,3)+'</w:tr>';
  rows+='<w:tr>'+ptCell('Step',PT_W[0],true,true,1)+ptCell('Action',PT_W[1],true,true,1)+ptCell('Expected Result',PT_W[2],true,true,1)+ptCell('Test Result (Pass/Fail)',PT_W[3],true,true,1)+'</w:tr>';
  if(steps.length){
    steps.forEach(function(step,i){
      var expLines=c.exp?c.exp.split('\n').filter(function(l){return/^\d+\./.test(l.trim());}):[];
      var expTxt=expLines[i]?expLines[i].replace(/^\d+\.\s*/,''):'';
      var actTxt=step.replace(/^\d+\.\s*/,'');
      rows+='<w:tr>'+ptCell(String(i+1),PT_W[0],false,false,1)+ptCellLines(actTxt,PT_W[1],1)+ptCellLines(expTxt,PT_W[2],1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
    });
  }else{
    rows+='<w:tr>'+ptCell('',PT_W[0],false,false,1)+ptCellLines(c.proc||'',PT_W[1],1)+ptCellLines(c.exp||'',PT_W[2],1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
  }
  rows+='<w:tr>'+ptCell('Overall Result (Pass/Fail/Blocked/NR)',PT_W[0]+PT_W[1],true,true,2)+ptCell('Tester',PT_W[2],true,true,1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
  rows+='<w:tr>'+ptCell('',PT_W[0]+PT_W[1],false,false,2)+ptCell('Date',PT_W[2],true,true,1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
  rows+='<w:tr>'+ptCell('',PT_W[0],false,false,1)+ptCell('',PT_W[1],false,false,1)+ptCell('',PT_W[2],false,false,1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
  return'<w:tbl>'+PT_PR+PT_GRID+rows+'</w:tbl>';
}

// Portal DOCX table — matches the PRT-0396 protocol 4-column format:
// Test Case ID | value | Requirements tested: | DI/DO
// Test Equipment or test data | precondition (span 3)
// Test Steps | Expected Result | Evidence (screenshot/link) | Test Result (Pass/Fail)
// step rows…
// Overall Result (P/F/B/NR) | Tester | Date | Build / Environment
function buildPortalCaseTable(c){
  // PT_W=[1500,3500,2800,1550]
  // Portal columns: label/Test Steps(1500) | Expected Result(3500) | Evidence(2800) | Test Result(1550)
  // For portal, Test Steps (col1+col2 merged) is wide; keep same 4-col grid as App
  var STEPS_W=PT_W[0]+PT_W[1]; // 5000 — Test Steps column spans col1+col2
  var EV_W=PT_W[2];             // 2800 — Evidence
  var TR_W=PT_W[3];             // 1550 — Test Result
  var steps=c.proc?c.proc.split('\n').filter(function(l){return/^\d+\./.test(l.trim());}):[];
  var rows='';
  // Header: Test Case ID | value | Requirements tested: | DI/DO
  rows+='<w:tr>'+ptCell('Test Case ID',PT_W[0],true,true,1)+ptCell(c.id,PT_W[1],false,false,1)+ptCell('Requirements tested:',PT_W[2],true,true,1)+ptCell(c.req||'',PT_W[3],false,false,1)+'</w:tr>';
  // Preconditions spanning full width
  rows+='<w:tr>'+ptCell('Test Equipment or test data',PT_W[0],true,true,1)+ptCellLines(c.pre||'',PT_W[1]+PT_W[2]+PT_W[3],3)+'</w:tr>';
  // Column headers: Test Steps (span2) | Expected Result (span1) | Evidence | Test Result
  rows+='<w:tr>'+ptCell('Test Steps',STEPS_W,true,true,2)+ptCell('Expected Result',EV_W,true,true,1)+ptCell('Evidence (screenshot/link)',TR_W,true,true,1)+'</w:tr>';
  // Step rows: step text (span2) | expected text | blank evidence | blank test result
  if(steps.length){
    steps.forEach(function(step,i){
      var expLines=c.exp?c.exp.split('\n').filter(function(l){return/^\d+\./.test(l.trim());}):[];
      var expTxt=expLines[i]?expLines[i].replace(/^\d+\.\s*/,''):'';
      var actTxt=(i+1)+'. '+step.replace(/^\d+\.\s*/,'');
      rows+='<w:tr>'+ptCellLines(actTxt,STEPS_W,2)+ptCellLines(expTxt,EV_W,1)+ptCell('',TR_W,false,false,1)+'</w:tr>';
    });
  }else{
    rows+='<w:tr>'+ptCellLines(c.proc||'',STEPS_W,2)+ptCellLines(c.exp||'',EV_W,1)+ptCell('',TR_W,false,false,1)+'</w:tr>';
  }
  // Result rows
  rows+='<w:tr>'+ptCell('Overall Result (Pass/Fail/Blocked/NR)',STEPS_W,true,true,2)+ptCell('Tester',EV_W,true,true,1)+ptCell('',TR_W,false,false,1)+'</w:tr>';
  rows+='<w:tr>'+ptCell('',PT_W[0],false,false,1)+ptCell('Date',PT_W[1],true,true,1)+ptCell('Build / Environment',EV_W,true,true,1)+ptCell('',TR_W,false,false,1)+'</w:tr>';
  rows+='<w:tr>'+ptCell('',PT_W[0],false,false,1)+ptCell('',PT_W[1],false,false,1)+ptCell('',PT_W[2],false,false,1)+ptCell('',PT_W[3],false,false,1)+'</w:tr>';
  return'<w:tbl>'+PT_PR+PT_GRID+rows+'</w:tbl>';
}
function buildDocxBody(){
  var isPortal = proto==='portal';
  var docTitle = isPortal ? 'PRT-0396: Modus Portal UIRS Test Cases' : 'PRT-0392: Modus App UIRS Test Cases';
  var body='';
  body+='<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>'+escXml(docTitle)+'</w:t></w:r></w:p>';
  var lastSec=null;
  ALL_CASES.forEach(function(c){
    if(c.sec!==lastSec){body+=docxBatchHeadingPara(c.sec);lastSec=c.sec;}
    body+=docxCaseTitlePara(c);
    body+=buildCaseTable(c);
    body+='<w:p><w:pPr><w:spacing w:after="80"/></w:pPr></w:p>';
  });
  return'<w:body>'+body+'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/></w:sectPr></w:body>';
}
function exportCasesDocx(){
  if(typeof JSZip==='undefined'){alert('JSZip library not loaded — cannot export Word file.');return;}
  var isPortal = proto==='portal';
  var docTitle  = isPortal ? 'PRT-0396: Modus Portal UIRS Test Cases' : 'PRT-0392: Modus App UIRS Test Cases';
  var filename  = isPortal ? 'PRT-0396-Modus-Portal-UIRS-Test-Cases.docx' : 'PRT-0392-Modus-App-UIRS-Test-Cases.docx';
  var appLabel  = 'CGMX1 Console';
  var now=new Date().toISOString().replace(/\.\d{3}Z$/,'Z');
  var documentXml='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'+buildDocxBody()+'</w:document>';
  var contentTypes='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>';
  var rootRels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>';
  var docRels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>';
  var coreProps='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>'+escXml(docTitle)+'</dc:title><dc:creator>'+escXml(appLabel)+'</dc:creator><cp:lastModifiedBy>'+escXml(appLabel)+'</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">'+now+'</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">'+now+'</dcterms:modified></cp:coreProperties>';
  var appProps='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>'+escXml(appLabel)+'</Application></Properties>';
  var stylesXml='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="20"/></w:rPr></w:rPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="240"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style></w:styles>';
  try{
    var zip=new JSZip();
    zip.file('[Content_Types].xml',contentTypes);
    zip.folder('_rels').file('.rels',rootRels);
    zip.folder('docProps').file('core.xml',coreProps);
    zip.folder('docProps').file('app.xml',appProps);
    var wordFolder=zip.folder('word');
    wordFolder.file('document.xml',documentXml);
    wordFolder.file('styles.xml',stylesXml);
    wordFolder.folder('_rels').file('document.xml.rels',docRels);
    zip.generateAsync({type:'blob',mimeType:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}).then(function(blob){
      var url=URL.createObjectURL(blob);
      var a=document.createElement('a');a.href=url;a.download=filename;
      document.body.appendChild(a);a.click();document.body.removeChild(a);
      setTimeout(function(){URL.revokeObjectURL(url);},5000);
    }).catch(function(err){console.warn('docx build failed',err);alert("Couldn’t build the Word file: "+err.message);});
  }catch(e){console.warn('docx export error',e);alert("Couldn’t build the Word file: "+e.message);}
}

// ── OVERLAYS (wired after full DOM is ready) ──────────────────────────────────
// The overlay HTML is placed after this script block, so element refs
// must be resolved inside DOMContentLoaded, not at script-parse time.
document.addEventListener('DOMContentLoaded', function(){

  var SETUP_KEY='prt0701-setup-meta';
  var ACCOUNT_DEFAULTS={accountMain:'faran@glucorx.co.uk',accountHistory:'rekod43112@maxtanie.com',accountNoData:'similoh324@caps7.com',accountRegion:'362qq@aristocrtic.live',portalHistory:'',portalSparse:'',portalMmol:'',portalSecondary:'',portalTimezone:'',portalHcp:'',portalClinicAdmin:'',portalAdmin:'',portalSuperAdmin:''};

  function loadSetup(){
    var m={}; try{m=JSON.parse(localStorage.getItem(SETUP_KEY)||'{}');}catch(e){}
    document.getElementById('f-exec').value      = m.executionId   || '';
    document.getElementById('f-tester').value    = m.tester        || '';
    document.getElementById('f-platform').value  = m.platform      || '';
    document.getElementById('f-phone').value     = m.phone         || '';
    document.getElementById('f-os').value        = m.osVersion     || '';
    document.getElementById('f-build').value     = m.appBuild      || '';
    document.getElementById('f-backend').value   = m.backend       || '';
    document.getElementById('f-d0').value        = m.d0            || '';
    document.getElementById('f-mailbox').value   = m.mailbox       || '';
    var acc=m.accounts||ACCOUNT_DEFAULTS;
    document.getElementById('f-account-main').value    = acc.accountMain    || '';
    document.getElementById('f-account-history').value = acc.accountHistory || ACCOUNT_DEFAULTS.accountHistory;
    document.getElementById('f-account-nodata').value  = acc.accountNoData  || ACCOUNT_DEFAULTS.accountNoData;
    document.getElementById('f-account-region').value  = acc.accountRegion  || ACCOUNT_DEFAULTS.accountRegion;
    document.getElementById('f-portal-history').value = acc.portalHistory || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-HISTORY-01'] || '';
    document.getElementById('f-portal-sparse').value = acc.portalSparse || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-SPARSE-01'] || '';
    document.getElementById('f-portal-mmol').value = acc.portalMmol || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-MMOL-01'] || '';
    document.getElementById('f-portal-secondary').value = acc.portalSecondary || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-SECONDARY-01'] || '';
    document.getElementById('f-portal-timezone').value = acc.portalTimezone || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-TIMEZONE-01'] || '';
    document.getElementById('f-portal-hcp').value = acc.portalHcp || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-HCP-01'] || '';
    document.getElementById('f-portal-clinic-admin').value = acc.portalClinicAdmin || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-CLINIC-ADMIN-01'] || '';
    document.getElementById('f-portal-admin').value = acc.portalAdmin || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-ADMIN-01'] || '';
    document.getElementById('f-portal-super-admin').value = acc.portalSuperAdmin || PORTAL_ACCOUNT_EMAILS['QA-PORTAL-SUPER-ADMIN-01'] || '';
  }

  // Setup overlay
  document.getElementById('btn-setup').addEventListener('click',function(){
    loadSetup();
    document.getElementById('overlay-setup').classList.remove('hidden');
  });
  document.getElementById('setup-close').addEventListener('click',function(){
    document.getElementById('overlay-setup').classList.add('hidden');
  });
  document.getElementById('overlay-setup').addEventListener('click',function(e){
    if(e.target===this) this.classList.add('hidden');
  });
  document.getElementById('setup-save').addEventListener('click',function(){
    var m={
      executionId: document.getElementById('f-exec').value.trim(),
      tester:      document.getElementById('f-tester').value.trim(),
      platform:    document.getElementById('f-platform').value.trim(),
      phone:       document.getElementById('f-phone').value.trim(),
      osVersion:   document.getElementById('f-os').value.trim(),
      appBuild:    document.getElementById('f-build').value.trim(),
      backend:     document.getElementById('f-backend').value.trim(),
      d0:          document.getElementById('f-d0').value.trim(),
      mailbox:     document.getElementById('f-mailbox').value.trim(),
      accounts:{
        accountMain:    document.getElementById('f-account-main').value.trim(),
        accountHistory: document.getElementById('f-account-history').value.trim(),
        accountNoData:  document.getElementById('f-account-nodata').value.trim(),
        accountRegion:  document.getElementById('f-account-region').value.trim(),
        portalHistory: document.getElementById('f-portal-history').value.trim(),
        portalSparse: document.getElementById('f-portal-sparse').value.trim(),
        portalMmol: document.getElementById('f-portal-mmol').value.trim(),
        portalSecondary: document.getElementById('f-portal-secondary').value.trim(),
        portalTimezone: document.getElementById('f-portal-timezone').value.trim(),
        portalHcp: document.getElementById('f-portal-hcp').value.trim(),
        portalClinicAdmin: document.getElementById('f-portal-clinic-admin').value.trim(),
        portalAdmin: document.getElementById('f-portal-admin').value.trim(),
        portalSuperAdmin: document.getElementById('f-portal-super-admin').value.trim()
      }
    };
    localStorage.setItem(SETUP_KEY,JSON.stringify(m));
    document.getElementById('overlay-setup').classList.add('hidden');
    var fl=document.getElementById('saved-flash');
    fl.classList.add('show'); setTimeout(function(){fl.classList.remove('show');},1800);
  });

  // Help overlay
  document.getElementById('btn-help').addEventListener('click',function(){
    document.getElementById('overlay-help').classList.remove('hidden');
  });
  document.getElementById('help-close').addEventListener('click',function(){
    document.getElementById('overlay-help').classList.add('hidden');
  });
  document.getElementById('overlay-help').addEventListener('click',function(e){
    if(e.target===this) this.classList.add('hidden');
  });

  // Assets overlay
  document.getElementById('btn-assets').addEventListener('click',function(){
    document.getElementById('overlay-assets').classList.remove('hidden');
    refreshAccountDisplay();
  });
  document.getElementById('assets-close').addEventListener('click',function(){
    document.getElementById('overlay-assets').classList.add('hidden');
  });
  document.getElementById('overlay-assets').addEventListener('click',function(e){
    if(e.target===this) this.classList.add('hidden');
  });

}); // end DOMContentLoaded (overlays)

function refreshAccountDisplay(){
  var panel=document.getElementById('assets-panel-content');
  if(!panel)return;
  if(proto==='portal'){
    _renderPortalAssets(panel);
  } else {
    _renderAppAssets(panel);
  }
}

var QR_ASSETS=[
  {id:'qr-asset-0',label:'Valid Sensor — No Lot',tag:'primary',tagText:'PRIMARY',text:'01095060001343521730123121SN0001234',raw:'01095060001343521730123121SN0001234',fields:[['Sensor ID','SN0001234'],['Expiry','31 Dec 2030'],['GTIN','09506000134352']]},
  {id:'qr-asset-1',label:'Valid Sensor — With Lot',tag:'secondary',tagText:'SECONDARY',text:'01095060001343521730123110LOT42\x1d21SN0001234',raw:'(01)09506000134352(17)301231(10)LOT42(21)SN0001234',fields:[['Sensor ID','SN0001234'],['Lot','LOT42'],['Expiry','31 Dec 2030']]},
  {id:'qr-asset-2',label:'Expired Sensor',tag:'negative',tagText:'NEGATIVE TEST',text:'01095060001343521722123121SN0009999',raw:'01095060001343521722123121SN0009999',fields:[['Sensor ID','SN0009999'],['Expiry','31 Dec 2022 ✕']]}
];

function populateQrGrid(){
  var grid=document.getElementById('qr-grid');
  if(!grid)return;
  grid.innerHTML='';
  QR_ASSETS.forEach(function(asset){
    var fields=asset.fields.map(function(f){return '<div class="qf"><span class="ql">'+esc(f[0])+'</span><span class="qv">'+esc(f[1])+'</span></div>';}).join('');
    var card=document.createElement('div');
    card.className='asset-card';
    card.innerHTML='<h5>'+esc(asset.label)+'</h5><span class="asset-tag '+asset.tag+'">'+esc(asset.tagText)+'</span><div class="qr-box" id="'+asset.id+'"></div><div class="qr-fields">'+fields+'</div><div class="asset-raw">'+esc(asset.raw)+'</div><button class="asset-copy-btn" type="button">Copy raw string</button>';
    grid.appendChild(card);
    card.querySelector('.asset-copy-btn').addEventListener('click',function(){
      var btn=this,orig=btn.textContent;
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(asset.raw).then(function(){btn.textContent='Copied!';setTimeout(function(){btn.textContent=orig;},1800);}).catch(function(){btn.textContent='Raw value shown above';});}
      else{btn.textContent='Raw value shown above';}
    });
    if(typeof QRCode!=='undefined'){
      try{new QRCode(document.getElementById(asset.id),{text:asset.text,width:152,height:152,colorDark:'#1a2233',colorLight:'#ffffff',correctLevel:QRCode.CorrectLevel.M});}catch(e){}
    }else{
      document.getElementById(asset.id).innerHTML='<span class="asset-note">QR library loading…</span>';
    }
  });
}

function _renderAppAssets(panel){
  var m={}; try{m=JSON.parse(localStorage.getItem('prt0701-setup-meta')||'{}');}catch(e){}
  var acc=m.accounts||{};
  var DEFAULTS={accountMain:'faran@glucorx.co.uk',accountHistory:'rekod43112@maxtanie.com',accountNoData:'similoh324@caps7.com',accountRegion:'362qq@aristocrtic.live'};
  var refs=[
    {ref:'QA-MAIN-01',     purpose:'Primary active session',        key:'accountMain'},
    {ref:'QA-HISTORY-01',  purpose:'Historical, reports and restoration', key:'accountHistory'},
    {ref:'QA-NODATA-01',   purpose:'Empty 24 Hours / populated 3 Days',   key:'accountNoData'},
    {ref:'QA-REGION-US-01',purpose:'US regional configuration',     key:'accountRegion'},
    {ref:'QA-RESET-01',    purpose:'Password-reset account (RESET-001); inbox access required'},
    {ref:'QA-SHARE-A-01',  purpose:'Sharing sender, Account A (SHARE-001 to SHARE-011); inbox access required'},
    {ref:'QA-SHARE-B-01',  purpose:'Sharing recipient, Account B (SHARE-001 to SHARE-011); inbox access required'},
    {ref:'QA-UNVERIFIED-01',purpose:'Registered, email never verified (HOSTED-SIGNIN-005); inbox access required'},
    {ref:'QA-FRESH-01',    purpose:'Never completed onboarding (HOSTED-SIGNIN-011); new account each run'},
    {ref:'QA-REG-EMAIL-A', purpose:'Fresh registration + verification (HOSTED-REG-003); unused address, inbox access required'},
    {ref:'QA-REG-EMAIL-B', purpose:'Expired-link and resend checks (HOSTED-REG-004); unused address, inbox access required'},
    {ref:'QA-REG-EMAIL-C', purpose:'Language/region mismatch check (HOSTED-REG-007); unused address, inbox access required'},
    {ref:'QA-REG-REGION-UK-01',purpose:'United Kingdom region check (HOSTED-REG-005); reused by ONBOARD-ALERT-001, HOSTED-SIGNIN-010; unused address, inbox access required'},
    {ref:'QA-REG-REGION-US-01',purpose:'United States region check (HOSTED-REG-006); unused address, inbox access required'},
    {ref:'QA-EMAIL-CHANGE-01',purpose:'Change Email check (SECURITY-003); account + replacement, both inboxes accessible'},
    {ref:'QA-DELETE-01',   purpose:'Account deletion (DELETE-001 to DELETE-006); new disposable account each run'},
    {ref:'QA-DELETE-REPL-01',purpose:"Replacement account that tries to use the deleted account's transmitter (DELETE-006)"},
    {ref:'CLINIC-CODE-01', purpose:'Valid test clinic for Clinic Connect (CLINIC-005, CLINIC-006)'}
  ];
  var rows='';
  refs.forEach(function(row){
    var email=row.key?(acc[row.key]||DEFAULTS[row.key]||''):'';
    var copyBtn=email?'<button class="icon-btn" style="width:24px;height:24px" title="Copy" onclick="navigator.clipboard.writeText(\''+esc(email)+'\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2v1"/></svg></button>':'';
    rows+='<tr><td><code>'+esc(row.ref)+'</code></td><td>'+esc(row.purpose)+'</td><td>'+(email?esc(email):'&#x2014;')+'</td><td>'+copyBtn+'</td></tr>';
  });
  var dataSetRows='';
  [
    {ref:'REG-FORM-DATA',purpose:'Registration form values (HOSTED-REG-001, 002, 003, 007) &#x2014; dummy values, not credentials for any real account'},
    {ref:'RESET-FORM-DATA',purpose:'Forgot/reset password form values (RESET-001) &#x2014; dummy values, not credentials for any real account'},
    {ref:'PROFILE-DATA',purpose:'Profile Setup values (PROFILE-001); unit follows Country automatically'},
    {ref:'REG-MISMATCH',purpose:'Language/region combination that triggers the mismatch warning (HOSTED-REG-007)'},
    {ref:'RESET-LINK-VALIDITY',purpose:'Reset link validity period (RESET-001) &#x2014; read from Realm Settings &gt; Tokens before the run'},
    {ref:'REG-LINK-VALIDITY',purpose:'Verification link validity period (HOSTED-REG-004) &#x2014; read from Realm Settings &gt; Tokens before the run'}
  ].forEach(function(row){dataSetRows+='<tr><td><code>'+esc(row.ref)+'</code></td><td>'+row.purpose+'</td></tr>';});
  var sensorRows='';
  [
    {ref:'SENSOR-VALID-01',purpose:'GS1 01095060001343521730123121SN0001234; Sensor ID SN0001234; expires 31 Dec 2030 &#x2014; valid in-date sensor'},
    {ref:'SENSOR-VALID-01 (with lot)',purpose:'GS1 (01)09506000134352(17)301231(10)LOT42(21)SN0001234; Lot LOT42 &#x2014; GS1 lot and serial parsing'},
    {ref:'SENSOR-EXPIRED-01',purpose:'GS1 01095060001343521722123121SN0009999; Sensor ID SN0009999; expired 31 Dec 2022 &#x2014; expired sensor rejection'},
    {ref:'SENSOR-RECALLED-01',purpose:'Quality-approved recalled sensor identifier; recall record active before execution &#x2014; recalled sensor rejection'},
    {ref:'SENSOR-INVALID-01',purpose:'Quality-approved invalid/known-nonexistent sensor identifier &#x2014; manual Sensor ID negative input'},
    {ref:'BARCODE-WRONGTYPE-01',purpose:'Quality-approved valid barcode for a different product type &#x2014; wrong-product scan rejection'},
    {ref:'TX-RECALLED-01',purpose:'Quality-approved recalled transmitter identifier; recall record active before execution &#x2014; recalled transmitter rejection'},
    {ref:'TX-B-01',purpose:'Transmitter B, registered to QA-DELETE-01 before deletion (DELETE-006)'}
  ].forEach(function(row){sensorRows+='<tr><td><code>'+esc(row.ref)+'</code></td><td>'+row.purpose+'</td></tr>';});
  var conditionRows='';
  [
    {ref:'DRIFT-SEQ-01',purpose:'Future-timestamp drift (60s): turn off automatic time, set the clock back 60s, keep Bluetooth on; restore automatic time after the test'},
    {ref:'SERVER-FAIL-01',purpose:'Server check failure while the CGM sensor stays connected: Wi-Fi off and Mobile Data off, keep Bluetooth on (not Airplane Mode); restore after the test'}
  ].forEach(function(row){conditionRows+='<tr><td><code>'+esc(row.ref)+'</code></td><td>'+row.purpose+'</td></tr>';});
  var simRows='';
  [
    {ref:'SIM-NORMAL-01',purpose:'SW1/SW2 middle position; consecutive live readings 70&#x2013;180 mg/dL &#x2014; Normal (In Range)'},
    {ref:'SIM-LOW-01',purpose:'SW1/SW2 toward low end, reading &gt;56 and &lt;70 mg/dL (target 63; use 70 for the exact threshold) &#x2014; non-critical Low'},
    {ref:'SIM-SEVERE-LOW-01',purpose:'SW1/SW2 lowest output; reading &#x2264;56 mg/dL &#x2014; Critical/Severe Low'},
    {ref:'SIM-HIGH-01',purpose:'SW1/SW2 toward highest output (target 200; use 180 for the exact threshold) &#x2014; High'},
    {ref:'SIM-NODATA-01',purpose:'SW3 Off stops transmission; recover with SW3 On, or Reset then On &#x2014; No data / transmitter off'},
    {ref:'SIM-STEADY-01',purpose:'SW1/SW2 unchanged across successive cycles until Steady appears'},
    {ref:'SIM-RISING-01',purpose:'SW1/SW2 turned up once per cycle: small = Slowly Rising, larger = Rising, largest sustained = Rapidly Rising; return to SIM-NORMAL-01 to reset'},
    {ref:'SIM-FALLING-01',purpose:'SW1/SW2 turned down once per cycle: small = Slowly Falling, larger = Falling, largest sustained = Rapidly Falling; return to SIM-NORMAL-01 to reset'}
  ].forEach(function(row){simRows+='<tr><td><code>'+esc(row.ref)+'</code></td><td>'+row.purpose+'</td></tr>';});
  panel.innerHTML=
    '<div class="desc">Scan these QR codes with the Step 14/22 sensor camera scanner. The raw GS1 strings are also available for generating printed stickers.</div>'+
    '<div class="warmup-tip"><strong>Warm-up bypass (debug mode)</strong> In debug builds: tap the build / version number <strong>10 times</strong> on the app&#x2019;s About or Splash screen to activate debug mode and skip the 60-minute warm-up.</div>'+
    '<div class="device-ref"><h5>Test account references</h5>'+
    '<p class="acct-hint">Emails are set in <strong>Run Setup &#x2699;</strong> where a field exists; the rest are tracked outside this console in the controlled credential source. Never record passwords here.</p>'+
    '<table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th><th>Current email</th><th></th></tr></thead><tbody>'+rows+'</tbody></table></div>'+
    '<details class="device-ref"><summary><strong>Form data sets &amp; link-validity references</strong></summary><table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th></tr></thead><tbody>'+dataSetRows+'</tbody></table></details>'+
    '<div class="asset-grid" id="qr-grid"></div>'+
    '<details class="device-ref"><summary><strong>Sensor, barcode &amp; transmitter identifiers</strong></summary><table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th></tr></thead><tbody>'+sensorRows+'</tbody></table></details>'+
    '<details class="device-ref"><summary><strong>Test conditions</strong></summary><table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th></tr></thead><tbody>'+conditionRows+'</tbody></table></details>'+
    '<div class="device-ref"><h5>Glucose simulator &#x2014; control reference</h5><table>'+
    '<tr><td>SW1 / SW2</td><td>Potentiometers &#x2014; turn to set glucose output level (Critical Low / Normal / High)</td></tr>'+
    '<tr><td>SW3 &#xB7; On</td><td>Power on / start transmitting</td></tr>'+
    '<tr><td>SW3 &#xB7; Off</td><td>Power off / stop transmitting</td></tr>'+
    '<tr><td>SW3 &#xB7; Reset</td><td>Reset simulator to default state</td></tr>'+
    '<tr><td>LED1&#x2013;3</td><td>Mode indicators showing current operating state</td></tr>'+
    '<tr><td>nRF52-DK</td><td>BLE transmitter board (blue, PCA10040) &#x2014; firmware installed via JFlash. Powers the BLE link to the iOS app.</td></tr>'+
    '</table></div>'+
    '<details class="device-ref"><summary><strong>Simulator conditions (SW1/SW2/SW3)</strong></summary><p class="acct-hint">Each condition is judged by the confirmed live glucose value shown in the app, not by dial position. Record the SW1/SW2 position and the resulting glucose value in the execution evidence.</p><table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th></tr></thead><tbody>'+simRows+'</tbody></table></details>'+
    '<div class="help-block"><h4>QA-HISTORY-01 fixture note</h4>This account requires a backend re-seed before execution of any history or reports cases. Confirm with the backend team that the fixture is current before running the batch.</div>';
  // re-populate QR grid after innerHTML reset
  if(typeof populateQrGrid==='function') populateQrGrid();
}

function _renderPortalAssets(panel){
  var m={}; try{m=JSON.parse(localStorage.getItem('prt0701-setup-meta')||'{}');}catch(e){}
  var acc=m.accounts||{};
  var PORTAL_REFS=[
    {ref:'QA-PORTAL-HISTORY-01', role:'Patient', purpose:'Verified 90-day readings, events and calibration', key:'portalHistory'},
    {ref:'QA-PORTAL-SPARSE-01', role:'Patient', purpose:'One-reading and insufficient-data states', key:'portalSparse'},
    {ref:'QA-PORTAL-MMOL-01', role:'Patient', purpose:'Known readings for mmol/L display', key:'portalMmol'},
    {ref:'QA-PORTAL-SECONDARY-01', role:'Patient', purpose:'Sharing and cross-account isolation', key:'portalSecondary'},
    {ref:'QA-PORTAL-TIMEZONE-01', role:'Patient', purpose:'Winter, summer and daylight-saving timestamps', key:'portalTimezone'},
    {ref:'QA-PORTAL-HCP-01', role:'HCP', purpose:'Shared-patient HCP access', key:'portalHcp'},
    {ref:'QA-PORTAL-CLINIC-ADMIN-01', role:'Clinic Admin', purpose:'Clinic and member management', key:'portalClinicAdmin'},
    {ref:'QA-PORTAL-ADMIN-01', role:'Modus Admin', purpose:'Admin management functions', key:'portalAdmin'},
    {ref:'QA-PORTAL-SUPER-ADMIN-01', role:'Super Admin', purpose:'Cross-clinic and platform controls', key:'portalSuperAdmin'}
  ];
  var rows='';
  PORTAL_REFS.forEach(function(row){
    rows+='<tr><td><code>'+esc(row.ref)+'</code></td><td><span style="font-size:11px;padding:2px 6px;border-radius:3px;background:var(--bg-row);color:var(--text-dim)">'+esc(row.role)+'</span></td><td>'+esc(row.purpose)+'</td><td>'+esc(acc[row.key]||PORTAL_ACCOUNT_EMAILS[row.ref]||'—')+'</td></tr>';
  });
  var fixtureRows='';
  (PORTAL_FIXTURE_MANIFEST.fixtures||[]).forEach(function(item){
    fixtureRows+='<tr><td><code>'+esc(item.alias)+'</code></td><td>'+esc(item.anchor)+'</td><td>'+esc(item.reading_count)+'</td><td>'+esc(item.minimum_mg_dl==null?'—':item.minimum_mg_dl+'–'+item.maximum_mg_dl+' mg/dL')+'</td></tr>';
  });
  var fixtureDetails='';
  (PORTAL_FIXTURE_MANIFEST.fixtures||[]).forEach(function(item){
    var profile=item.patient_profile||{};
    var profileText=[profile.given_names,profile.family_name,profile.date_of_birth,profile.country,profile.diabetes_type].filter(Boolean).join(' · ');
    var body='<p class="acct-hint"><strong>Profile:</strong> '+esc(profileText||'—')+'</p>';
    if(item.ranges){
      var rangeRows='';
      Object.keys(item.ranges).forEach(function(key){var v=item.ranges[key]; rangeRows+='<tr><td>'+esc(key.replace('_',' '))+'</td><td>'+esc(v.reading_count)+'</td><td>'+esc(v.latest_mg_dl)+'</td><td>'+esc(v.average_mg_dl)+'</td><td>'+esc(v.minimum_mg_dl)+'–'+esc(v.maximum_mg_dl)+'</td><td>'+esc(v.below_70_percent)+' / '+esc(v.in_70_180_percent)+' / '+esc(v.above_180_percent)+'</td><td>'+esc(v.severe_low_percent)+' / '+esc(v.low_percent)+' / '+esc(v.high_percent)+' / '+esc(v.urgent_high_percent)+'</td><td>'+esc(v.device_usage_percent)+'</td><td>'+esc(v.sd_population_mg_dl)+' / '+esc(v.cv_population_percent)+' / '+esc(v.mean_absolute_deviation_mg_dl)+'</td><td>'+esc(v.gmi_percent)+' / '+esc(v.adag_estimated_a1c_percent)+'</td></tr>';});
      body+='<h5>Range calculations</h5><table class="acct-table"><thead><tr><th>Range</th><th>Readings</th><th>Latest</th><th>Average</th><th>Min–max</th><th>Below / in / above %</th><th>Severe low / low / high / urgent high %</th><th>Usage %</th><th>SD / CV% / avg deviation</th><th>GMI / ADAG A1c %</th></tr></thead><tbody>'+rangeRows+'</tbody></table>';
    }
    if(item.controlled_states){
      var s=item.controlled_states;
      body+='<h5>Controlled states</h5><p class="acct-hint">Empty days before anchor: '+esc((s.empty_days_before_anchor||[]).join(', '))+'. Gap: D0-'+esc(s.gap.days_before_anchor)+' '+esc(s.gap.start_local)+'–'+esc(s.gap.end_local)+'. High: D0-'+esc(s.high_marker.days_before_anchor)+' '+esc(s.high_marker.start_local)+' = '+esc(s.high_marker.mg_dl)+' mg/dL. Low: D0-'+esc(s.low_marker.days_before_anchor)+' '+esc(s.low_marker.start_local)+' = '+esc(s.low_marker.mg_dl)+' mg/dL. Calibration: D0-'+esc(s.calibration.days_before_anchor)+' '+esc(s.calibration.local_time)+' = '+esc(s.calibration.mg_dl)+' mg/dL.</p>';
      if(s.events){body+='<p class="acct-hint"><strong>Events:</strong> '+s.events.map(function(v){return 'D0-'+esc(v.days_before_anchor)+' '+esc(v.local_time)+' '+esc(v.type);}).join(' · ')+'</p>';}
    }
    if(item.daily_history_7_days){
      var dailyRows=''; item.daily_history_7_days.forEach(function(v){dailyRows+='<tr><td>D0-'+esc(v.days_before_anchor)+'</td><td>'+esc(v.first_local)+'</td><td>'+esc(v.last_local)+'</td><td>'+esc(v.minimum_mg_dl)+'</td><td>'+esc(v.maximum_mg_dl)+'</td></tr>';});
      body+='<h5>Expected daily History values (7 days)</h5><table class="acct-table"><thead><tr><th>Day</th><th>First</th><th>Last</th><th>Min mg/dL</th><th>Max mg/dL</th></tr></thead><tbody>'+dailyRows+'</tbody></table>';
    }
    if(item.ogp_hourly){
      ['7_days','90_days'].forEach(function(key){var ogpRows=''; (item.ogp_hourly[key]||[]).forEach(function(v){ogpRows+='<tr><td>'+esc(v.hour_local)+'</td><td>'+esc(v.reading_count)+'</td><td>'+esc(v.p10_mg_dl)+'</td><td>'+esc(v.p25_mg_dl)+'</td><td>'+esc(v.median_mg_dl)+'</td><td>'+esc(v.p75_mg_dl)+'</td><td>'+esc(v.p90_mg_dl)+'</td></tr>';}); body+='<h5>Expected OGP percentiles — '+esc(key.replace('_',' '))+'</h5><p class="acct-hint">'+esc(item.ogp_hourly.method)+'</p><table class="acct-table"><thead><tr><th>Local hour</th><th>n</th><th>P10</th><th>P25</th><th>P50</th><th>P75</th><th>P90</th></tr></thead><tbody>'+ogpRows+'</tbody></table>';});
    }
    if(item.controlled_readings){
      var readingRows=''; item.controlled_readings.forEach(function(v){readingRows+='<tr><td>'+esc(v.days_before_anchor==null?(v.utc||'—'):'D0-'+v.days_before_anchor)+'</td><td>'+esc(v.local_time||v.local_period||v.europe_london||'—')+'</td><td>'+esc(v.mg_dl)+'</td></tr>';});
      body+='<h5>Controlled readings</h5><table class="acct-table"><thead><tr><th>UTC / day</th><th>Local time / period</th><th>mg/dL</th></tr></thead><tbody>'+readingRows+'</tbody></table>';
    }
    fixtureDetails+='<details class="help-block"><summary><strong>'+esc(item.alias)+'</strong> — verified fixture details</summary>'+body+'</details>';
  });
  var referencedAccountRows='';
  (PORTAL_ASSET_CATALOG.accounts||[]).forEach(function(item){
    referencedAccountRows+='<tr><td><code>'+esc(item.reference)+'</code></td><td>'+esc(item.kind||'login account')+'</td><td>'+esc(item.purpose)+'</td><td>'+esc(item.availability)+'</td><td>'+esc((item.cases||[]).length)+'</td></tr>';
  });
  var referencedResourceRows='';
  (PORTAL_ASSET_CATALOG.resources||[]).forEach(function(item){
    var caseList=(item.cases||[]).slice(0,6).join(', ');
    if((item.cases||[]).length>6) caseList+=' +'+((item.cases||[]).length-6)+' more';
    referencedResourceRows+='<tr><td><code>'+esc(item.reference)+'</code></td><td>'+esc(item.purpose)+'</td><td>'+esc(item.availability)+'</td><td>'+esc(caseList)+'</td></tr>';
  });
  panel.innerHTML=
    '<div class="desc">Modus Portal (PRT-0396) test environment accounts. Use a supported desktop browser. Never record passwords here — use the controlled credential source.</div>'+
    '<div class="device-ref"><h5>Portal test accounts</h5>'+
    '<p class="acct-hint">One account per role. Credential management via the controlled credential source. Aliases here are stable; underlying emails may rotate.</p>'+
    '<table class="acct-table"><thead><tr><th>Reference</th><th>Role</th><th>Purpose</th><th>Current email</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+ 
    '<details class="device-ref" open><summary><strong>Complete QA alias register</strong></summary><p class="acct-hint">Every QA alias used by the 574 Modus Portal cases is listed here. Login accounts must be provisioned before execution. Data fixtures are records created or supplied in the test environment and do not require separate sign-in credentials.</p><table class="acct-table"><thead><tr><th>Reference</th><th>Type</th><th>Purpose</th><th>Availability</th><th>Cases</th></tr></thead><tbody>'+referencedAccountRows+'</tbody></table></details>'+ 
    '<details class="device-ref"><summary><strong>Complete controlled-resource register</strong></summary><p class="acct-hint">Every named Test Asset row used by a Modus Portal case is listed here. Check the named row in the approved controlled source before execution; if its value is absent, mark the case Blocked and name the missing reference.</p><table class="acct-table"><thead><tr><th>Reference</th><th>Purpose</th><th>Availability rule</th><th>Used by</th></tr></thead><tbody>'+referencedResourceRows+'</tbody></table></details>'+ 
    '<div class="device-ref"><h5>Portal fixture verification</h5><p class="acct-hint">Generated anchor: '+esc(PORTAL_FIXTURE_MANIFEST.fixture_anchor||'not generated')+'. Refresh immediately before a formal run.</p><table class="acct-table"><thead><tr><th>Alias</th><th>Anchor</th><th>Readings</th><th>Range</th></tr></thead><tbody>'+fixtureRows+'</tbody></table></div>'+fixtureDetails+ 
    '<div class="device-ref"><h5>Browser &amp; environment setup</h5><table>'+
    '<tr><td>Protected Patient Overview URL</td><td><a href="https://frontend.grxdiscovery.link/Overview" target="_blank" rel="noopener noreferrer">https://frontend.grxdiscovery.link/Overview</a></td></tr>'+
    '<tr><td>Supported browsers</td><td>Chrome (latest stable), Firefox (latest stable), Edge (latest stable)</td></tr>'+
    '<tr><td>Window size</td><td>1280 &#xD7; 800 minimum for desktop-layout tests; resize to 375 &#xD7; 812 for mobile-responsiveness cases</td></tr>'+
    '<tr><td>Incognito / Private</td><td>Use a private window to avoid cached sessions unless the case specifies a returning-user state</td></tr>'+
    '<tr><td>Cache &amp; cookies</td><td>Clear between authentication test cases; leave intact for session-persistence cases</td></tr>'+
    '<tr><td>Network</td><td>Standard broadband; throttle to Slow 3G only for performance/offline cases as noted in the case</td></tr>'+
    '</table></div>'+
    '<div class="device-ref"><h5>SSO / Hosted Sign In notes</h5><table>'+
    '<tr><td>Identity provider</td><td>Keycloak-hosted sign-in page (same as Modus App &#x2014; shared IdP)</td></tr>'+
    '<tr><td>Session cookie scope</td><td>Cookie is scoped to the portal domain; a portal sign-in does not affect the mobile app session</td></tr>'+
    '<tr><td>MFA</td><td>TOTP codes must be retrieved from the controlled credential source for accounts with MFA enabled</td></tr>'+
    '</table></div>'+
    '<div class="help-block"><h4>Patient fixture note</h4>Run the direct API fixture seeder and verify its manifest before history, report, graph and comparison cases.</div>'+ 
    '<div class="help-block"><h4>Role account note</h4>HCP and administrator roles require approved administrative provisioning; Patient self-registration cannot create them.</div>';
}

// ── HELPERS ───────────────────────────────────────────────────────────────────
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

function fmtText(s){
  return `<div style="white-space:pre-wrap;font-size:13px;line-height:1.5;color:var(--text-dim)">${esc(s||'')}</div>`;
}

function splitNumbered(s){
  if(!s) return null;
  const lines=s.split('\n');
  if(!lines.some(l=>/^\d+\./.test(l.trim()))) return null;
  const items=[];let cur='';
  lines.forEach(l=>{if(/^\d+\./.test(l.trim())){if(cur)items.push(cur.trim());cur=l.replace(/^\d+\.\s*/,'')}else cur+='\n'+l;});
  if(cur)items.push(cur.trim());
  return items;
}

function fmtNum(s){
  if(!s)return `<div style="color:var(--text-faint);font-size:12px;font-style:italic">None</div>`;
  const items=splitNumbered(s);
  if(items) return `<ul class="steps-list">${items.map((i,index)=>`<li><span class="step-num">${index+1}</span><span class="step-txt">${esc(i)}</span></li>`).join('')}</ul>`;
  return fmtText(s);
}

function pw(html){const w=window.open('','_blank','width=900,height=700');w.document.write(html);w.document.close();setTimeout(()=>w.print(),600)}
function dl(content,type,name){
  var url=URL.createObjectURL(new Blob([content],{type:type}));
  var a=document.createElement('a');a.href=url;a.download=name;
  document.body.appendChild(a);a.click();document.body.removeChild(a);
  setTimeout(function(){URL.revokeObjectURL(url);},5000);
}
</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" onload="if(document.getElementById('qr-grid'))populateQrGrid()"></script>

<!-- Setup overlay -->
<div class="overlay hidden" id="overlay-setup">
  <div class="sheet2">
    <div class="closebar"><h2>Run setup</h2><button class="icon-btn" id="setup-close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button></div>
    <div class="desc">Run metadata and replaceable account aliases for this console. Never put passwords in this tool.</div>
    <div class="field-row">
      <div><label class="fld">Execution ID</label><input type="text" id="f-exec" placeholder="EX-iOS-001"></div>
      <div><label class="fld">Tester name</label><input type="text" id="f-tester" placeholder=""></div>
    </div>
    <div class="field-row">
      <div><label class="fld">Platform</label><input type="text" id="f-platform" placeholder="iOS / Android"></div>
      <div><label class="fld">Phone model</label><input type="text" id="f-phone" placeholder=""></div>
    </div>
    <div class="field-row">
      <div><label class="fld">OS version</label><input type="text" id="f-os" placeholder=""></div>
      <div><label class="fld">App build</label><input type="text" id="f-build" placeholder=""></div>
    </div>
    <div class="field-row">
      <div><label class="fld">Backend</label><input type="text" id="f-backend" placeholder=""></div>
      <div><label class="fld">D0 date</label><input type="text" id="f-d0" placeholder="YYYY-MM-DD"></div>
    </div>
    <div class="field-row full">
      <div><label class="fld">Tester mailbox</label><input type="text" id="f-mailbox" placeholder=""></div>
    </div>
    <div class="help-block">
      <h4>Controlled test account references</h4>
      <div class="desc">Test cases use these stable references. Change an email here when an account is replaced; never put passwords in this table.</div>
      <div class="account-table-wrap"><table class="codes-table account-table">
        <thead><tr><th>Reference</th><th>Purpose</th><th>Current email</th></tr></thead>
        <tbody>
          <tr><td><code>QA-MAIN-01</code></td><td>Primary active session (Sign In &#x2192; Sensor &#x2192; Warmup &#x2192; Home)</td><td><input type="text" id="f-account-main" placeholder="email alias" autocomplete="off"></td></tr>
          <tr><td><code>QA-HISTORY-01</code></td><td>Historical, reports and restoration</td><td><input type="text" id="f-account-history" autocomplete="off"></td></tr>
          <tr><td><code>QA-NODATA-01</code></td><td>Empty 24 Hours / populated 3 Days</td><td><input type="text" id="f-account-nodata" autocomplete="off"></td></tr>
          <tr><td><code>QA-REGION-US-01</code></td><td>US regional configuration</td><td><input type="text" id="f-account-region" autocomplete="off"></td></tr>
        </tbody>
      </table></div>
    </div>
    <h4 style="margin:16px 0 8px">Other Section 9.3 Test Data references (not editable here)</h4>
    <div class="desc">Tracked in the controlled credential source / Assets panel &#x2014; shown here only for completeness. See the Assets &amp; QR codes overlay for the full list and purposes.</div>
    <div class="account-table-wrap"><table class="codes-table account-table">
        <tbody>
          <tr><td><code>QA-RESET-01</code></td><td>RESET-001 password-reset account</td></tr>
          <tr><td><code>QA-SHARE-A-01</code> / <code>QA-SHARE-B-01</code></td><td>Sharing sender / recipient (SHARE-001 to SHARE-011)</td></tr>
          <tr><td><code>QA-UNVERIFIED-01</code></td><td>Incomplete email activation (HOSTED-SIGNIN-005)</td></tr>
          <tr><td><code>QA-FRESH-01</code></td><td>Never completed onboarding (HOSTED-SIGNIN-011)</td></tr>
          <tr><td><code>QA-REG-EMAIL-A/B/C</code></td><td>Fresh registration/verification addresses (HOSTED-REG-003/004/007)</td></tr>
          <tr><td><code>QA-REG-REGION-UK-01</code> / <code>QA-REG-REGION-US-01</code></td><td>Region registration checks (HOSTED-REG-005/006)</td></tr>
          <tr><td><code>QA-EMAIL-CHANGE-01</code></td><td>Change Email check (SECURITY-003)</td></tr>
          <tr><td><code>QA-DELETE-01</code> / <code>QA-DELETE-REPL-01</code></td><td>Account deletion (DELETE-001 to DELETE-006)</td></tr>
          <tr><td><code>CLINIC-CODE-01</code></td><td>Clinic Connect (CLINIC-005, CLINIC-006)</td></tr>
        </tbody>
    </table></div>
    <h4 style="margin:16px 0 8px">Portal account references</h4>
    <div class="desc">These emails may be replaced without changing PRT-0396 cases.</div>
    <div class="account-table-wrap"><table class="codes-table account-table">
        <thead><tr><th>Reference</th><th>Purpose</th><th>Current email</th></tr></thead>
        <tbody>
          <tr><td><code>QA-PORTAL-HISTORY-01</code></td><td>90-day history fixture</td><td><input type="text" id="f-portal-history" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-SPARSE-01</code></td><td>Sparse-data fixture</td><td><input type="text" id="f-portal-sparse" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-MMOL-01</code></td><td>mmol/L fixture</td><td><input type="text" id="f-portal-mmol" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-SECONDARY-01</code></td><td>Sharing and isolation</td><td><input type="text" id="f-portal-secondary" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-TIMEZONE-01</code></td><td>Time-zone fixture</td><td><input type="text" id="f-portal-timezone" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-HCP-01</code></td><td>HCP role</td><td><input type="text" id="f-portal-hcp" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-CLINIC-ADMIN-01</code></td><td>Clinic Admin role</td><td><input type="text" id="f-portal-clinic-admin" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-ADMIN-01</code></td><td>Modus Admin role</td><td><input type="text" id="f-portal-admin" autocomplete="off"></td></tr>
          <tr><td><code>QA-PORTAL-SUPER-ADMIN-01</code></td><td>Super Admin role</td><td><input type="text" id="f-portal-super-admin" autocomplete="off"></td></tr>
        </tbody>
    </table></div>
    <button class="primary-btn" id="setup-save" style="margin-top:16px">Save</button>
  </div>
    </div>

<!-- Help overlay -->
<div class="overlay hidden" id="overlay-help">
  <div class="sheet2">
    <div class="closebar"><h2>Recording &amp; execution rules</h2><button class="icon-btn" id="help-close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button></div>
    <div class="help-block">
      <h4>Result codes</h4>
      <table class="codes-table">
        <tr><td>P</td><td>Pass &#x2014; all expected results were observed.</td></tr>
        <tr><td>F</td><td>Fail &#x2014; at least one expected result was not observed. Record the defect / deviation reference.</td></tr>
        <tr><td>B</td><td>Blocked &#x2014; execution could not proceed because a required precondition, test data item or test-kit state was not available. Blocked is not a Pass.</td></tr>
        <tr><td>NR</td><td>Not Run &#x2014; the test case was not executed in this run.</td></tr>
      </table>
    </div>
    <div class="help-block">
      <h4>How to run each case</h4>
      Establish the Preconditions, then perform the Procedure steps exactly as written. Compare what you observe with the Expected Result and capture the Required Evidence. Record the Overall Result (P/F/B/NR), tester and date, and raise a defect/deviation for any Fail.
    </div>
    <div class="help-block">
      <h4>Secrets</h4>
      Do not record passwords, OTP seeds or other authentication secrets in this protocol, its evidence, or your notes here &#x2014; use the controlled credential source.
    </div>
    <div class="help-block">
      <h4>About this console</h4>
      This is a personal aid for running the selected protocol and keeping evidence handy &#x2014; it is not the official protocol document. Transcribe final P/F/B/NR results, evidence references and defect IDs into the controlled record.
    </div>
  </div>
</div>

<!-- Test-assets overlay -->
<div class="overlay hidden" id="overlay-assets">
  <div class="sheet2">
    <div class="closebar"><h2 id="assets-overlay-title">Test assets &amp; QR codes</h2><button class="icon-btn" id="assets-close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button></div>
    <div id="assets-panel-content"></div>
  </div>
</div>

<div id="saved-flash">Saved</div>
</body>
</html>"""

DEST.write_text(html, encoding="utf-8")
print(f"Generated: {DEST}")
print(f"Cases embedded: {total}  |  Date: {gen_dt}")
