"""
Fix the cases not recovered by the forEach-pattern parser:
  - WELCOME-003/004/005: pre from edit-1 forEach
  - SIGNIN-002/004A/004B: pre from edit-11 forEach
  - LOGOUT-003: ev mismatch between compact and run-order

Run with: python -I scripts/fix_foreach_gaps.py
"""
import json, pathlib, subprocess, sys

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'

# Exact pre values from the forEach calls in the transcript
FOREACH_FIXES = {
    'VP-APP-WELCOME-003': {'pre': 'Android only. The app is freshly installed and the Welcome screen is displayed.'},
    'VP-APP-WELCOME-004': {'pre': 'The app is freshly installed and the Welcome screen is displayed.'},
    'VP-APP-WELCOME-005': {'pre': 'The app is freshly installed and the Welcome screen is displayed.'},
    'VP-APP-SIGNIN-002':  {'pre': 'The Welcome back screen is displayed and internet is available.'},
    'VP-APP-SIGNIN-004A': {'pre': 'Android only. The Welcome back screen is displayed.'},
    'VP-APP-SIGNIN-004B': {'pre': 'iOS only. The Welcome back screen is displayed.'},
}

# LOGOUT-003 ev: use compact value as the authority (it was set by the transcript)
LOGOUT_EV_COMPACT = 'screenshots, execution record'

RO_MAP = {'pre': 'preconditions', 'ev': 'evidence', 't': 'title',
          'proc': 'procedure', 'exp': 'expected', 'req': 'requirement'}

# ── load ──────────────────────────────────────────────────────────────────────
with open(COMPACT, encoding='utf-8') as f:
    compact_data = json.load(f)
with open(RO, encoding='utf-8') as f:
    ro_data = json.load(f)

ci = {c['id']: c for c in compact_data}
ri = {c['id']: c for c in ro_data}

changed = []

# ── apply forEach fixes to both files ─────────────────────────────────────────
for _id, fields in FOREACH_FIXES.items():
    if _id not in ci:
        print(f'WARNING: {_id} not in compact'); continue
    if _id not in ri:
        print(f'WARNING: {_id} not in run-order'); continue
    for field, value in fields.items():
        if ci[_id].get(field) != value:
            ci[_id][field] = value
            changed.append(f'{_id}.{field} (compact)')
        ro_field = RO_MAP[field]
        if ri[_id].get(ro_field) != value:
            ri[_id][ro_field] = value
            changed.append(f'{_id}.{ro_field} (run-order)')

# ── fix LOGOUT-003 ev mismatch ─────────────────────────────────────────────────
cev = ci['VP-APP-LOGOUT-003'].get('ev')
if cev != LOGOUT_EV_COMPACT:
    ci['VP-APP-LOGOUT-003']['ev'] = LOGOUT_EV_COMPACT
    changed.append('VP-APP-LOGOUT-003.ev (compact)')

if ri['VP-APP-LOGOUT-003'].get('evidence') != LOGOUT_EV_COMPACT:
    ri['VP-APP-LOGOUT-003']['evidence'] = LOGOUT_EV_COMPACT
    changed.append('VP-APP-LOGOUT-003.evidence (run-order)')

# ── write ──────────────────────────────────────────────────────────────────────
with open(COMPACT, 'w', encoding='utf-8') as f:
    json.dump(compact_data, f, ensure_ascii=False, indent=2)
with open(RO, 'w', encoding='utf-8') as f:
    json.dump(ro_data, f, ensure_ascii=False, indent=2)

print(f'Applied {len(changed)} field changes:')
for c in changed:
    print(f'  {c}')

# ── regenerate console ─────────────────────────────────────────────────────────
result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print('\n' + result.stdout.strip())
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)

print('\nDone.')
