"""Fix all VP-APP-WELCOME-* preconditions: remove 'signed out' framing."""
import json, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'

# Map: id -> new precondition
FIXES = {
    'VP-APP-WELCOME-002':     'The Welcome screen is displayed.',
    'VP-APP-WELCOME-003':     'Android only. The Welcome screen is displayed.',
    'VP-APP-WELCOME-004':     'The Welcome screen is displayed.',
    'VP-APP-WELCOME-005':     'The Welcome screen is displayed.',
    'VP-APP-WELCOME-NAV-001': 'The Welcome screen is displayed.',
    'VP-APP-WELCOME-NAV-002': 'The Welcome screen is displayed.',
    'VP-APP-WELCOME-NAV-003': 'The Welcome screen is displayed.',
    'VP-APP-WELCOME-NAV-004': 'The Welcome screen is displayed.',
}

changed = []

for path, key_pre in [(COMPACT, 'pre'), (RO, 'preconditions')]:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for c in data:
        if c['id'] in FIXES:
            old = c[key_pre]
            new = FIXES[c['id']]
            if old != new:
                c[key_pre] = new
                if path == COMPACT:
                    changed.append(c['id'])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{path.name}: updated {len([x for x in data if x["id"] in FIXES])} cases')

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)
print('changed IDs:', changed)
