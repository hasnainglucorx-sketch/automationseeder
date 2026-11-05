"""
Add all account references to the Test Assets panel and add QA-MAIN-01.

Changes:
  1. Add QA-MAIN-01 row to the Setup overlay account table.
  2. Add accountMain to ACCOUNT_DEFAULTS in JS.
  3. Add accountMain to setup-load and setup-save JS blocks.
  4. Add CSS for account cards in the assets panel.
  5. Inject an Accounts section (live-reading from stored meta) into the
     Test Assets overlay, above the QR grid.
  6. Add refreshAccountDisplay() call when the assets overlay opens.
  7. Copy to root HTML and verify byte-identity.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "output/console-update"
HTML_PATH = OUT / "PRT-0701-Console-source.html"
ROOT_HTML = ROOT / "PRT-0701-Console-source.updated.html"

html = HTML_PATH.read_text(encoding="utf-8-sig")

# ── 1. Add QA-MAIN-01 row to Setup overlay table ───────────────────────────
OLD_SETUP_TABLE = (
    '          <tr><td><code>QA-HISTORY-01</code></td>'
    '<td>Historical, reports and restoration</td>'
    '<td><input type="text" id="f-account-history" autocomplete="off"></td></tr>\n'
    '          <tr><td><code>QA-NODATA-01</code></td>'
    '<td>Empty 24 Hours / populated 3 Days</td>'
    '<td><input type="text" id="f-account-nodata" autocomplete="off"></td></tr>\n'
    '          <tr><td><code>QA-REGION-US-01</code></td>'
    '<td>US regional configuration</td>'
    '<td><input type="text" id="f-account-region" autocomplete="off"></td></tr>'
)
NEW_SETUP_TABLE = (
    '          <tr><td><code>QA-MAIN-01</code></td>'
    '<td>Primary active session (Sign In → Sensor → Warmup → Home)</td>'
    '<td><input type="text" id="f-account-main" placeholder="email alias" autocomplete="off"></td></tr>\n'
    '          <tr><td><code>QA-HISTORY-01</code></td>'
    '<td>Historical, reports and restoration</td>'
    '<td><input type="text" id="f-account-history" autocomplete="off"></td></tr>\n'
    '          <tr><td><code>QA-NODATA-01</code></td>'
    '<td>Empty 24 Hours / populated 3 Days</td>'
    '<td><input type="text" id="f-account-nodata" autocomplete="off"></td></tr>\n'
    '          <tr><td><code>QA-REGION-US-01</code></td>'
    '<td>US regional configuration</td>'
    '<td><input type="text" id="f-account-region" autocomplete="off"></td></tr>'
)
assert OLD_SETUP_TABLE in html, "ABORT: Setup table anchor not found"
html = html.replace(OLD_SETUP_TABLE, NEW_SETUP_TABLE, 1)

# ── 2. Add accountMain to ACCOUNT_DEFAULTS ──────────────────────────────────
OLD_DEFAULTS = (
    '  var ACCOUNT_DEFAULTS = {\n'
    '    accountHistory: "rekod43112@maxtanie.com",\n'
    '    accountNoData: "similoh324@caps7.com",\n'
    '    accountRegion: "362qq@aristocrtic.live"\n'
    '  };'
)
NEW_DEFAULTS = (
    '  var ACCOUNT_DEFAULTS = {\n'
    '    accountMain: "",\n'
    '    accountHistory: "rekod43112@maxtanie.com",\n'
    '    accountNoData: "similoh324@caps7.com",\n'
    '    accountRegion: "362qq@aristocrtic.live"\n'
    '  };'
)
assert OLD_DEFAULTS in html, "ABORT: ACCOUNT_DEFAULTS anchor not found"
html = html.replace(OLD_DEFAULTS, NEW_DEFAULTS, 1)

# ── 3. Add accountMain to setup-load block ──────────────────────────────────
OLD_SETUP_LOAD = (
    '    document.getElementById("f-account-history").value = meta.accountHistory || ACCOUNT_DEFAULTS.accountHistory;\n'
    '    document.getElementById("f-account-nodata").value = meta.accountNoData || ACCOUNT_DEFAULTS.accountNoData;\n'
    '    document.getElementById("f-account-region").value = meta.accountRegion || ACCOUNT_DEFAULTS.accountRegion;'
)
NEW_SETUP_LOAD = (
    '    document.getElementById("f-account-main").value = meta.accountMain || ACCOUNT_DEFAULTS.accountMain;\n'
    '    document.getElementById("f-account-history").value = meta.accountHistory || ACCOUNT_DEFAULTS.accountHistory;\n'
    '    document.getElementById("f-account-nodata").value = meta.accountNoData || ACCOUNT_DEFAULTS.accountNoData;\n'
    '    document.getElementById("f-account-region").value = meta.accountRegion || ACCOUNT_DEFAULTS.accountRegion;'
)
assert OLD_SETUP_LOAD in html, "ABORT: setup-load JS anchor not found"
html = html.replace(OLD_SETUP_LOAD, NEW_SETUP_LOAD, 1)

# ── 4. Add accountMain to setup-save block ──────────────────────────────────
OLD_SETUP_SAVE = (
    '        accountHistory: document.getElementById("f-account-history").value.trim(),\n'
    '        accountNoData: document.getElementById("f-account-nodata").value.trim(),\n'
    '        accountRegion: document.getElementById("f-account-region").value.trim()'
)
NEW_SETUP_SAVE = (
    '        accountMain: document.getElementById("f-account-main").value.trim(),\n'
    '        accountHistory: document.getElementById("f-account-history").value.trim(),\n'
    '        accountNoData: document.getElementById("f-account-nodata").value.trim(),\n'
    '        accountRegion: document.getElementById("f-account-region").value.trim()'
)
assert OLD_SETUP_SAVE in html, "ABORT: setup-save JS anchor not found"
html = html.replace(OLD_SETUP_SAVE, NEW_SETUP_SAVE, 1)

# ── 5. Add CSS for account cards ────────────────────────────────────────────
OLD_WARMUP_CSS = '  .warmup-tip strong{display:block; margin-bottom:2px;}'
NEW_WARMUP_CSS = (
    '  .warmup-tip strong{display:block; margin-bottom:2px;}\n'
    '  .acct-table{width:100%; border-collapse:collapse; font-size:12.5px; margin-bottom:14px;}\n'
    '  .acct-table th{text-align:left; padding:5px 8px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:var(--text-faint); border-bottom:2px solid var(--border);}\n'
    '  .acct-table td{padding:7px 8px; border-bottom:1px solid var(--border); vertical-align:middle;}\n'
    '  .acct-table tr:last-child td{border-bottom:none;}\n'
    '  .acct-table td:first-child{font-family:"IBM Plex Mono",monospace; font-weight:700; color:var(--accent); white-space:nowrap;}\n'
    '  .acct-table td:nth-child(2){color:var(--text-dim); font-size:12px;}\n'
    '  .acct-table td:nth-child(3){font-family:"IBM Plex Mono",monospace; font-size:12px; word-break:break-all;}\n'
    '  .acct-copy{padding:3px 8px; background:var(--surface-2); border:1px solid var(--border); border-radius:6px; font-size:11px; font-weight:600; color:var(--text-dim); cursor:pointer; font-family:inherit; white-space:nowrap;}\n'
    '  .acct-copy:active{background:var(--accent-weak); color:var(--accent);}\n'
    '  .acct-hint{font-size:11.5px; color:var(--text-faint); margin-bottom:14px; line-height:1.5;}'
)
assert OLD_WARMUP_CSS in html, "ABORT: CSS warmup anchor not found"
html = html.replace(OLD_WARMUP_CSS, NEW_WARMUP_CSS, 1)

# ── 6. Inject Accounts section into assets overlay (before QR grid) ─────────
OLD_ASSETS_BODY = (
    '    <div class="asset-grid" id="qr-grid">\n'
    '      <!-- Cards injected by JS -->\n'
    '    </div>'
)
NEW_ASSETS_BODY = (
    '    <div class="device-ref" id="acct-section">\n'
    '      <h5>Test account references</h5>\n'
    '      <p class="acct-hint">Emails are set in <strong>Run Setup ⚙</strong>. Tap a row to copy the email. Never record passwords here.</p>\n'
    '      <table class="acct-table" id="acct-table">\n'
    '        <thead><tr><th>Reference</th><th>Purpose</th><th>Current email</th><th></th></tr></thead>\n'
    '        <tbody id="acct-tbody">\n'
    '          <!-- Rows injected by refreshAccountDisplay() -->\n'
    '        </tbody>\n'
    '      </table>\n'
    '    </div>\n'
    '\n'
    '    <div class="asset-grid" id="qr-grid">\n'
    '      <!-- Cards injected by JS -->\n'
    '    </div>'
)
assert OLD_ASSETS_BODY in html, "ABORT: assets overlay body anchor not found"
html = html.replace(OLD_ASSETS_BODY, NEW_ASSETS_BODY, 1)

# ── 7. Add refreshAccountDisplay() and wire it to overlay open ──────────────
OLD_ASSETS_BTN_JS = (
    '    document.getElementById("btn-assets").addEventListener("click", function(){\n'
    '      document.getElementById("overlay-assets").classList.remove("hidden");'
)
NEW_ASSETS_BTN_JS = (
    '    var ACCT_DEFS = [\n'
    '      { key:"accountMain",    ref:"QA-MAIN-01",    purpose:"Primary active session" },\n'
    '      { key:"accountHistory", ref:"QA-HISTORY-01", purpose:"Historical / reports (needs re-seed)" },\n'
    '      { key:"accountNoData",  ref:"QA-NODATA-01",  purpose:"Empty 24 h state" },\n'
    '      { key:"accountRegion",  ref:"QA-REGION-US-01", purpose:"US regional config" }\n'
    '    ];\n'
    '\n'
    '    function refreshAccountDisplay() {\n'
    '      var saved = {};\n'
    '      try { saved = JSON.parse(localStorage.getItem("prt0701-run-meta") || "{}"); } catch(e) {}\n'
    '      var tbody = document.getElementById("acct-tbody");\n'
    '      if (!tbody) return;\n'
    '      tbody.innerHTML = "";\n'
    '      ACCT_DEFS.forEach(function(a) {\n'
    '        var email = saved[a.key] || ACCOUNT_DEFAULTS[a.key] || "—";\n'
    '        var tr = document.createElement("tr");\n'
    '        tr.innerHTML =\n'
    '          "<td>" + esc(a.ref) + "</td>" +\n'
    '          "<td>" + esc(a.purpose) + "</td>" +\n'
    '          "<td id=\\"acct-val-" + a.key + "\\">" + esc(email) + "</td>" +\n'
    '          "<td><button class=\\"acct-copy\\" data-key=\\"" + a.key + "\\">Copy</button></td>";\n'
    '        tbody.appendChild(tr);\n'
    '      });\n'
    '      tbody.querySelectorAll(".acct-copy").forEach(function(btn) {\n'
    '        btn.addEventListener("click", function() {\n'
    '          var k = btn.getAttribute("data-key");\n'
    '          var val = document.getElementById("acct-val-" + k);\n'
    '          var text = val ? val.textContent : "";\n'
    '          if (!text || text === "—") return;\n'
    '          var orig = btn.textContent;\n'
    '          if (navigator.clipboard && navigator.clipboard.writeText) {\n'
    '            navigator.clipboard.writeText(text).then(function() {\n'
    '              btn.textContent = "Copied!";\n'
    '              setTimeout(function() { btn.textContent = orig; }, 1800);\n'
    '            }).catch(function() {});\n'
    '          }\n'
    '        });\n'
    '      });\n'
    '    }\n'
    '\n'
    '    document.getElementById("btn-assets").addEventListener("click", function(){\n'
    '      document.getElementById("overlay-assets").classList.remove("hidden");\n'
    '      refreshAccountDisplay();'
)
assert OLD_ASSETS_BTN_JS in html, "ABORT: btn-assets JS anchor not found"
html = html.replace(OLD_ASSETS_BTN_JS, NEW_ASSETS_BTN_JS, 1)

# ── 8. Write files ───────────────────────────────────────────────────────────
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

# ── 9. Verify ────────────────────────────────────────────────────────────────
verify = HTML_PATH.read_text(encoding="utf-8")
root_v  = ROOT_HTML.read_text(encoding="utf-8")
assert verify == root_v,                     "ERROR: files not byte-identical"
assert "QA-MAIN-01" in verify,               "ERROR: QA-MAIN-01 not found"
assert "f-account-main" in verify,           "ERROR: f-account-main not found"
assert "accountMain" in verify,              "ERROR: accountMain key not found"
assert "acct-tbody" in verify,               "ERROR: acct-tbody not found"
assert "refreshAccountDisplay" in verify,    "ERROR: refreshAccountDisplay not found"
assert "ACCT_DEFS" in verify,               "ERROR: ACCT_DEFS not found"

print("OK — Accounts section injected into Test Assets panel")
print("QA-MAIN-01 added to Setup overlay and JS")
print("Both HTML files updated and byte-identical")
