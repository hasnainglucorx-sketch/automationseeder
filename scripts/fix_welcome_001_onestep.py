"""VP-APP-WELCOME-001: merge back to one step (same pattern as SPLASH-001)."""
import json, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'
ID      = 'VP-APP-WELCOME-001'

NEW_PRE  = 'The app is freshly installed and has not been previously launched.'
NEW_PROC = '1. Launch CGMx 1 and inspect the Welcome screen.'
NEW_EXP  = (
    '1. The Welcome screen is displayed and shows the GlucoRx CGMx™ 1 product image, '
    'the heading “See your glucose, clearly.”, the supporting text '
    '“Real-time readings, smart alerts, and sharing that helps you stay in range — every day.”, '
    'three benefit rows each with their icon (Live readings every few minutes; '
    'Alerts you can act on — even on Silent; Share with the people who matter), '
    'the privacy notice “Your data is private and secure.” with a Learn more link, '
    'and Get started and Sign in buttons. '
    'No content is missing, clipped, overlapping or corrupted.'
)
NEW_EV = 'Screenshot of the Welcome screen; execution record.'

for path, kpre, kproc, kexp, kev in [
    (COMPACT, 'pre',           'proc',      'exp',      'ev'),
    (RO,      'preconditions', 'procedure', 'expected', 'evidence'),
]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    c = next((x for x in data if x['id'] == ID), None)
    if not c:
        sys.exit(f'ERROR: {ID} not in {path.name}')
    c[kpre]  = NEW_PRE
    c[kproc] = NEW_PROC
    c[kexp]  = NEW_EXP
    c[kev]   = NEW_EV
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{path.name} updated')

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr); sys.exit(1)
