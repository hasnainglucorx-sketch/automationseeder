"""
Remove all references to '(QA Workbook)' from both JSON files.
Pattern: 'Test data (QA Workbook): ...' → 'Test data: ...'

Run with: python -I scripts/remove_qa_workbook.py
"""
import json, pathlib, subprocess, sys

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'

FIELDS_COMPACT = ['pre', 'proc', 'exp', 'ev']
FIELDS_RO      = ['preconditions', 'procedure', 'expected', 'evidence']

def strip_workbook(text):
    return text.replace(' (QA Workbook)', '').replace('(QA Workbook) ', '').replace('(QA Workbook)', '')

changed = []

# ── compact ───────────────────────────────────────────────────────────────────
with open(COMPACT, encoding='utf-8') as f:
    compact_data = json.load(f)

for case in compact_data:
    for field in FIELDS_COMPACT:
        val = case.get(field, '')
        if 'QA Workbook' in val or 'QA workbook' in val:
            case[field] = strip_workbook(val)
            changed.append(f'{case["id"]}.{field}')

with open(COMPACT, 'w', encoding='utf-8') as f:
    json.dump(compact_data, f, ensure_ascii=False, indent=2)

# ── run-order ─────────────────────────────────────────────────────────────────
with open(RO, encoding='utf-8') as f:
    ro_data = json.load(f)

for case in ro_data:
    for field in FIELDS_RO:
        val = case.get(field, '')
        if 'QA Workbook' in val or 'QA workbook' in val:
            case[field] = strip_workbook(val)
            changed.append(f'{case["id"]}.{field} (ro)')

with open(RO, 'w', encoding='utf-8') as f:
    json.dump(ro_data, f, ensure_ascii=False, indent=2)

print(f'Removed QA Workbook from {len(changed)} fields:')
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
