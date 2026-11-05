"""
Add a Test Assets panel to the PRT-0701 Console.

Injects:
  1. A toolbar "QR / Assets" icon button (#btn-assets).
  2. CSS for the QR card grid inside .sheet2 overlays.
  3. The full test-assets overlay HTML (sensor QR codes + Nobe device reference).
  4. QRCode.js library <script> tag.
  5. Event-listener JS to open the overlay and generate QR codes on first open.
  6. Copies the result to the root updated HTML.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "output/console-update"
HTML_PATH = OUT / "PRT-0701-Console-source.html"
ROOT_HTML = ROOT / "PRT-0701-Console-source.updated.html"

# ── 1. Read current file ────────────────────────────────────────────────────
html = HTML_PATH.read_text(encoding="utf-8-sig")
original = html  # keep for assertion

# ── 2. Toolbar button ───────────────────────────────────────────────────────
SETUP_BTN = '''        <button class="icon-btn" id="btn-setup" title="Run setup">'''

ASSETS_BTN = '''        <button class="icon-btn" id="btn-assets" title="Test assets &amp; QR codes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        </button>
        <button class="icon-btn" id="btn-setup" title="Run setup">'''

assert SETUP_BTN in html, "ABORT: btn-setup anchor not found"
html = html.replace(SETUP_BTN, ASSETS_BTN, 1)

# ── 3. CSS — QR asset cards ─────────────────────────────────────────────────
CSS_ANCHOR = "  #loading{display:flex; align-items:center; justify-content:center; min-height:60vh; color:var(--text-faint); font-size:13px;}\n</style>"

QR_CSS = """  /* ---- Test-assets overlay ---- */
  .asset-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; margin-bottom:14px;}
  .asset-card{background:var(--surface-2); border:1px solid var(--border); border-radius:11px; padding:14px; display:flex; flex-direction:column; align-items:center; gap:10px;}
  .asset-card h5{margin:0; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--text-faint); align-self:flex-start;}
  .asset-card .qr-box{width:160px; height:160px; display:flex; align-items:center; justify-content:center;}
  .asset-card .qr-box canvas,.asset-card .qr-box img{max-width:160px;max-height:160px;display:block;}
  .asset-card .qr-fields{width:100%; display:flex; flex-direction:column; gap:4px;}
  .asset-card .qf{display:flex; justify-content:space-between; gap:6px; font-size:11.5px;}
  .asset-card .qf .ql{color:var(--text-faint);}
  .asset-card .qf .qv{font-weight:600; font-variant-numeric:tabular-nums; word-break:break-all; text-align:right;}
  .asset-card .asset-tag{font-size:10px; font-weight:700; padding:2px 8px; border-radius:100px; letter-spacing:.03em; align-self:flex-start;}
  .asset-card .asset-tag.primary{background:var(--accent-weak); color:var(--accent);}
  .asset-card .asset-tag.secondary{background:var(--notrun-weak); color:var(--notrun);}
  .asset-card .asset-tag.negative{background:var(--blocked-weak); color:var(--blocked);}
  .asset-copy-btn{width:100%; padding:7px; background:var(--accent); color:var(--accent-ink); border:none; border-radius:8px; font-size:12px; font-weight:700; cursor:pointer; font-family:inherit;}
  .asset-copy-btn:active{opacity:.85;}
  .asset-note{font-size:11px; color:var(--text-faint); text-align:center; line-height:1.5; margin:0;}
  .device-ref{background:var(--surface-2); border:1px solid var(--border); border-radius:11px; padding:12px 14px; margin-bottom:14px;}
  .device-ref h5{margin:0 0 8px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--text-faint);}
  .device-ref table{width:100%; border-collapse:collapse; font-size:12.5px;}
  .device-ref td{padding:4px 6px; border-bottom:1px solid var(--border); vertical-align:top;}
  .device-ref td:first-child{font-family:"IBM Plex Mono",monospace; font-weight:600; white-space:nowrap; color:var(--accent); width:120px;}
  .device-ref tr:last-child td{border-bottom:none;}
  .warmup-tip{background:var(--pass-weak); border:1px solid var(--pass); border-radius:9px; padding:9px 12px; font-size:12.5px; color:var(--pass); margin-bottom:14px; line-height:1.5;}
  .warmup-tip strong{display:block; margin-bottom:2px;}
"""

assert CSS_ANCHOR in html, "ABORT: CSS anchor not found"
html = html.replace(CSS_ANCHOR, QR_CSS + "  #loading{display:flex; align-items:center; justify-content:center; min-height:60vh; color:var(--text-faint); font-size:13px;}\n</style>", 1)

# ── 4. Test-assets overlay HTML ─────────────────────────────────────────────
OVERLAY_ANCHOR = '<div class="saved-flash" id="saved-flash">Saved</div>'

ASSETS_OVERLAY = """<!-- Test-assets overlay -->
<div class="overlay hidden" id="overlay-assets">
  <div class="sheet2">
    <div class="closebar"><h2>Test assets &amp; QR codes</h2><button class="icon-btn" id="assets-close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button></div>
    <div class="desc">Scan these QR codes with the Step 14/22 sensor camera scanner. The raw GS1 strings are also available for generating printed stickers.</div>

    <div class="warmup-tip">
      <strong>Warm-up bypass (debug mode)</strong>
      In debug builds: tap the build / version number <strong>10 times</strong> on the app's About or Splash screen to activate debug mode and skip the 60-minute warm-up.
    </div>

    <div class="asset-grid" id="qr-grid">
      <!-- Cards injected by JS -->
    </div>

    <div class="device-ref">
      <h5>Nobe glucose simulator — control reference</h5>
      <table>
        <tr><td>SW1 / SW2</td><td>Potentiometers — turn to set glucose output level (Critical Low / Normal / High)</td></tr>
        <tr><td>SW3 · On</td><td>Power on / start transmitting</td></tr>
        <tr><td>SW3 · Off</td><td>Power off / stop transmitting</td></tr>
        <tr><td>SW3 · Reset</td><td>Reset simulator to default state</td></tr>
        <tr><td>LED1–3</td><td>Mode indicators showing current operating state</td></tr>
        <tr><td>nRF52-DK</td><td>BLE transmitter board (blue, PCA10040) — firmware installed via JFlash. Powers the BLE link to the iOS app.</td></tr>
      </table>
    </div>

    <div class="device-ref">
      <h5>Supported glucose reading types</h5>
      <table>
        <tr><td>Critical Low</td><td>SW1/SW2 turned to lowest position — triggers Urgent Low alarm and critical alert display</td></tr>
        <tr><td>Normal</td><td>SW1/SW2 mid position — standard CGM session, Home screen value, trend arrows</td></tr>
        <tr><td>High</td><td>SW1/SW2 turned to highest position — triggers High alert and high threshold alarm</td></tr>
      </table>
    </div>

    <div class="help-block">
      <h4>QA-HISTORY-01 fixture note</h4>
      This account requires a backend re-seed before execution of any history or reports cases. Confirm with the backend team that the fixture is current before running the batch.
    </div>
  </div>
</div>

"""

assert OVERLAY_ANCHOR in html, "ABORT: saved-flash anchor not found"
html = html.replace(OVERLAY_ANCHOR, ASSETS_OVERLAY + OVERLAY_ANCHOR, 1)

# ── 5. QRCode.js library script tag ─────────────────────────────────────────
JSZIP_TAG = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>'
assert JSZIP_TAG in html, "ABORT: jszip script tag not found"
html = html.replace(
    JSZIP_TAG,
    JSZIP_TAG + '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>',
    1
)

# ── 6. JS — overlay open/close + QR generation ──────────────────────────────
# Inject before the closing of the IIFE — find the last event-listener block
JS_ANCHOR = "    document.getElementById(\"btn-help\").addEventListener(\"click\", function(){"

ASSETS_JS = """    // ---- Test-assets overlay ----
    var _qrGenerated = false;
    var GS = String.fromCharCode(0x1D);
    var QR_ASSETS = [
      {
        id: "qr-asset-0",
        label: "Valid Sensor — No Lot",
        tag: "primary",
        tagText: "PRIMARY",
        text: "01095060001343521730123121SN0001234",
        raw: "01095060001343521730123121SN0001234",
        fields: [["Sensor ID","SN0001234"],["Expiry","31 Dec 2030"],["GTIN","09506000134352"]]
      },
      {
        id: "qr-asset-1",
        label: "Valid Sensor — With Lot",
        tag: "secondary",
        tagText: "SECONDARY",
        text: "01095060001343521730123110LOT42\x1d21SN0001234",
        raw: "(01)09506000134352(17)301231(10)LOT42(21)SN0001234",
        fields: [["Sensor ID","SN0001234"],["Lot","LOT42"],["Expiry","31 Dec 2030"]]
      },
      {
        id: "qr-asset-2",
        label: "Expired Sensor",
        tag: "negative",
        tagText: "NEGATIVE TEST",
        text: "01095060001343521722123121SN0009999",
        raw: "01095060001343521722123121SN0009999",
        fields: [["Sensor ID","SN0009999"],["Expiry","31 Dec 2022 ✕"]]
      }
    ];

    function buildQrCards() {
      if (_qrGenerated) return;
      _qrGenerated = true;
      var grid = document.getElementById("qr-grid");
      if (!grid) return;
      var dark = window.matchMedia && window.matchMedia("(prefers-color-scheme:dark)").matches;
      QR_ASSETS.forEach(function(asset) {
        var card = document.createElement("div");
        card.className = "asset-card";
        var fields = asset.fields.map(function(f){
          return "<div class=\\"qf\\"><span class=\\"ql\\">" + esc(f[0]) + "</span><span class=\\"qv\\">" + esc(f[1]) + "</span></div>";
        }).join("");
        card.innerHTML =
          "<h5>" + esc(asset.label) + "</h5>" +
          "<span class=\\"asset-tag " + asset.tag + "\\">" + esc(asset.tagText) + "</span>" +
          "<div class=\\"qr-box\\" id=\\"" + asset.id + "\\"></div>" +
          "<div class=\\"qr-fields\\">" + fields + "</div>" +
          "<button class=\\"asset-copy-btn\\" data-raw=\\"" + asset.id + "\\">Copy raw string</button>";
        grid.appendChild(card);
        try {
          new QRCode(document.getElementById(asset.id), {
            text: asset.text,
            width: 160,
            height: 160,
            colorDark: dark ? "#e8eaf0" : "#1a2233",
            colorLight: dark ? "#171b24" : "#ffffff",
            correctLevel: QRCode.CorrectLevel.M
          });
        } catch(e) {}
      });
      grid.querySelectorAll(".asset-copy-btn").forEach(function(btn){
        btn.addEventListener("click", function(){
          var rawId = btn.getAttribute("data-raw");
          var idx = QR_ASSETS.findIndex(function(a){ return a.id === rawId; });
          if (idx < 0) return;
          var text = QR_ASSETS[idx].raw;
          var orig = btn.textContent;
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function(){
              btn.textContent = "Copied!";
              setTimeout(function(){ btn.textContent = orig; }, 1800);
            }).catch(function(){ btn.textContent = "Copy the raw value above"; });
          } else {
            btn.textContent = "Copy: " + text;
          }
        });
      });
    }

    document.getElementById("btn-assets").addEventListener("click", function(){
      document.getElementById("overlay-assets").classList.remove("hidden");
      if (typeof QRCode !== "undefined") { buildQrCards(); }
      else {
        var s = document.createElement("script");
        s.src = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js";
        s.onload = buildQrCards;
        document.head.appendChild(s);
      }
    });
    document.getElementById("assets-close").addEventListener("click", function(){
      document.getElementById("overlay-assets").classList.add("hidden");
    });
    document.getElementById("overlay-assets").addEventListener("click", function(e){
      if (e.target === this) document.getElementById("overlay-assets").classList.add("hidden");
    });

    document.getElementById("btn-help").addEventListener("click", function(){"""

assert JS_ANCHOR in html, "ABORT: btn-help JS anchor not found"
html = html.replace(JS_ANCHOR, ASSETS_JS, 1)

# ── 7. Write files ───────────────────────────────────────────────────────────
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

# ── 8. Verify ────────────────────────────────────────────────────────────────
verify = HTML_PATH.read_text(encoding="utf-8")
root_verify = ROOT_HTML.read_text(encoding="utf-8")
assert verify == root_verify, "ERROR: files not byte-identical"
assert "btn-assets" in verify, "ERROR: btn-assets not found"
assert "overlay-assets" in verify, "ERROR: overlay-assets not found"
assert "qr-grid" in verify, "ERROR: qr-grid not found"
assert "qrcode.min.js" in verify, "ERROR: QRCode.js not found"
assert "buildQrCards" in verify, "ERROR: buildQrCards not found"
assert "Nobe glucose simulator" in verify, "ERROR: device reference not found"

print("OK — Test Assets panel injected")
print("Both HTML files updated and byte-identical")
