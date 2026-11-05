"""Remove VP-APP-WELCOME-NAV-004 (duplicate of VP-APP-WELCOME-003)."""
import json, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'
REMOVE  = 'VP-APP-WELCOME-NAV-004'

for path in [COMPACT, RO]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    before = len(data)
    data = [x for x in data if x['id'] != REMOVE]
    after = len(data)
    if before == after:
        sys.exit(f'ERROR: {REMOVE} not found in {path.name}')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{path.name}: removed {REMOVE} ({before} -> {after} cases)')

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr); sys.exit(1)
