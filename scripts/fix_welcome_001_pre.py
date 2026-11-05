"""Fix VP-APP-WELCOME-001 precondition: first-launch only, not sign-out."""
import json, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'
ID      = 'VP-APP-WELCOME-001'

NEW_PRE = 'The app is freshly installed and has not been previously launched.'

for path, key_pre in [(COMPACT, 'pre'), (RO, 'preconditions')]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    c = next((x for x in data if x['id'] == ID), None)
    if not c:
        sys.exit(f'ERROR: {ID} not found in {path}')
    c[key_pre] = NEW_PRE
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{path.name} updated')

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)
print('console regenerated')
