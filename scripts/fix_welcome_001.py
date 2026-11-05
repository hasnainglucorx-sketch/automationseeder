"""Fix VP-APP-WELCOME-001: add launch step, state-only preconditions."""
import json, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'

ID = 'VP-APP-WELCOME-001'

NEW_PRE  = 'The app is installed, the user is signed out, and the app is fully closed.'
NEW_PROC = ('1. Launch CGMx 1.\n'
            '2. Inspect the Welcome screen from top to bottom.')
NEW_EXP  = ('1. The app launches and the Welcome screen is displayed.\n'
            '2. The screen shows the GlucoRx CGMx™ 1 product image, '
            'the heading “See your glucose, clearly.”, the supporting text '
            '“Real-time readings, smart alerts, and sharing that helps you stay in range — every day.”, '
            'three benefit rows each with their icon (Live readings every few minutes; '
            'Alerts you can act on — even on Silent; Share with the people who matter), '
            'the privacy notice “Your data is private and secure.” with a Learn more link, '
            'and Get started and Sign in buttons. '
            'No content is missing, clipped, overlapping or corrupted.')
NEW_EV   = 'Screenshot of the Welcome screen; execution record.'

# ── compact ──────────────────────────────────────────────────────────────────
with open(COMPACT, encoding='utf-8') as f:
    cases = json.load(f)
c = next((x for x in cases if x['id'] == ID), None)
if not c:
    sys.exit(f'ERROR: {ID} not found in compact JSON')

c['pre']  = NEW_PRE
c['proc'] = NEW_PROC
c['exp']  = NEW_EXP
c['ev']   = NEW_EV

with open(COMPACT, 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)
print('compact updated')

# ── run-order ─────────────────────────────────────────────────────────────────
with open(RO, encoding='utf-8') as f:
    ro = json.load(f)
r = next((x for x in ro if x['id'] == ID), None)
if not r:
    sys.exit(f'ERROR: {ID} not found in run-order JSON')

r['preconditions'] = NEW_PRE
r['procedure']     = NEW_PROC
r['expected']      = NEW_EXP
r['evidence']      = NEW_EV

with open(RO, 'w', encoding='utf-8') as f:
    json.dump(ro, f, ensure_ascii=False, indent=2)
print('run-order updated')

# ── regenerate console ────────────────────────────────────────────────────────
result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)
print('console regenerated')
