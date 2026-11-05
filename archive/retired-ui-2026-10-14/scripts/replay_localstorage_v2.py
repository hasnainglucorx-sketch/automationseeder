"""
Improved replay: properly parses single-quoted JS object literals.
Extracts all final field values from the 60 localStorage calls and applies
them directly to both JSON files.

Run with: python -I scripts/replay_localstorage_v2.py
"""
import json, pathlib, re, subprocess, sys

ROOT       = pathlib.Path(__file__).parent.parent
COMPACT    = ROOT / 'output/console-update/PRT-0701-cases.json'
RO         = ROOT / 'output/console-update/PRT-0701-run_order.json'
TRANSCRIPT = pathlib.Path(
    r'C:\Users\Hasnain\.claude\projects\C--Users-Hasnain-Downloads-Automation-seeder'
    r'\bd4fa740-4bc8-4b70-b80c-de693e30b6bb.jsonl'
)

# ── 1. extract JS calls ───────────────────────────────────────────────────────
lines = TRANSCRIPT.read_text(encoding='utf-8').splitlines()
js_calls = []
for line in lines:
    if 'PRT0701_review_edits' not in line:
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    msg = obj.get('message', {})
    content = msg.get('content', [])
    if not isinstance(content, list):
        continue
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get('type') != 'tool_use':
            continue
        if 'javascript' not in block.get('name', '').lower():
            continue
        code = block.get('input', {}).get('text', '')
        if 'PRT0701_review_edits' in code and 'localStorage.setItem' in code:
            js_calls.append(code)

print(f'Extracted {len(js_calls)} JS calls')

# ── 2. JS single-quoted string parser ─────────────────────────────────────────

KNOWN_FIELDS = {'t', 'pre', 'proc', 'exp', 'ev', 'req', 'method', 'sec'}
# regex: field: 'value'  (single-quoted, handles \' and \n escapes)
FIELD_RE = re.compile(
    r'\b(t|pre|proc|exp|ev|req|method|sec)\s*:\s*'
    r"'((?:[^'\\]|\\.)*)'"
)
# also handle double-quoted values
FIELD_RE2 = re.compile(
    r'\b(t|pre|proc|exp|ev|req|method|sec)\s*:\s*'
    r'"((?:[^"\\]|\\.)*)"'
)

def unescape(s):
    return (s.replace("\\'", "'")
             .replace('\\"', '"')
             .replace('\\n', '\n')
             .replace('\\t', '\t')
             .replace('\\\\', '\\'))

def parse_fields(text):
    """Extract {field: value} from a block of JS text."""
    found = {}
    for m in FIELD_RE.finditer(text):
        found[m.group(1)] = unescape(m.group(2))
    for m in FIELD_RE2.finditer(text):
        if m.group(1) not in found:   # single-quoted wins
            found[m.group(1)] = unescape(m.group(2))
    return found

# ── 3. replay every operation in sequence ─────────────────────────────────────

stored = {}   # simulates localStorage['PRT0701_review_edits']

ID_RE = re.compile(r"(?:stored|s|existing)\['(VP-APP-[^']+)'\]")

for call in js_calls:
    # Delete operations
    for m in re.finditer(r"delete\s+\w+\['(VP-APP-[^']+)'\]", call):
        stored.pop(m.group(1), None)

    # Find all VP-APP-IDs referenced in this call — including dict-key form
    # e.g. const fixes = { 'VP-APP-SCAN-008': {...} }
    DICT_KEY_RE = re.compile(r"'(VP-APP-[A-Z0-9-]+)'\s*:\s*\{")
    touched = sorted(set(ID_RE.findall(call)) | set(DICT_KEY_RE.findall(call)))
    for _id in touched:
        escaped_id = re.escape(_id)

        # (A) Field-level assignments: s['ID'].field = 'value'  (always check)
        field_pat = re.compile(
            r"(?:stored|s|existing)\['" + escaped_id + r"'\]"
            r"\.(t|pre|proc|exp|ev|req|method|sec)\s*=\s*"
            r"'((?:[^'\\]|\\.)*)'",
            re.DOTALL
        )
        for fm in field_pat.finditer(call):
            field = fm.group(1)
            value = unescape(fm.group(2))
            if _id not in stored:
                stored[_id] = {}
            stored[_id][field] = value

        # Also double-quoted field assignments
        field_pat2 = re.compile(
            r"(?:stored|s|existing)\['" + escaped_id + r"'\]"
            r"\.(t|pre|proc|exp|ev|req|method|sec)\s*=\s*"
            r'"((?:[^"\\]|\\.)*)"',
            re.DOTALL
        )
        for fm in field_pat2.finditer(call):
            field = fm.group(1)
            # single-quoted already wins for this field in this call
            if _id in stored and field in stored[_id]:
                existing_val = stored[_id].get(field)
                # only skip if set by single-quote in THIS call
            value = unescape(fm.group(2))
            if _id not in stored:
                stored[_id] = {}
            stored[_id].setdefault(field, value)

        # (B) Full-object assignment — two forms:
        #   existing['ID'] = { ... }       (direct assignment)
        #   'ID': { ... }                  (key in fixes dict)
        pat = re.compile(
            r"(?:(?:stored|s|existing)\['" + escaped_id + r"'\]\s*=\s*\{"
            r"|'" + escaped_id + r"'\s*:\s*\{)",
            re.DOTALL
        )
        for m in pat.finditer(call):
            start = m.end() - 1   # position of opening {
            depth = 0
            end = start
            in_str = False
            str_char = None
            i = start
            while i < len(call):
                c = call[i]
                if in_str:
                    if c == '\\':
                        i += 2
                        continue
                    if c == str_char:
                        in_str = False
                else:
                    if c in ('"', "'"):
                        in_str = True
                        str_char = c
                    elif c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                i += 1
            obj_text = call[start:end]
            fields = parse_fields(obj_text)
            if fields:   # non-empty object — overrides field-level
                if _id not in stored:
                    stored[_id] = {}
                stored[_id].update(fields)

# Remove any IDs that have no useful edits (empty or only _savedAt)
stored = {
    k: {f: v for f, v in v.items() if f in KNOWN_FIELDS}
    for k, v in stored.items()
}
stored = {k: v for k, v in stored.items() if v}

print(f'Final stored IDs ({len(stored)}):')
for _id in sorted(stored.keys()):
    fields = ', '.join(sorted(stored[_id].keys()))
    print(f'  {_id}: [{fields}]')

# ── 4. apply to compact JSON ──────────────────────────────────────────────────

with open(COMPACT, encoding='utf-8') as f:
    compact_data = json.load(f)
compact_index = {c['id']: c for c in compact_data}

changed_compact = []
missing_compact = []
for _id, edits in stored.items():
    if _id not in compact_index:
        missing_compact.append(_id)
        continue
    case = compact_index[_id]
    for field, value in edits.items():
        if case.get(field) != value:
            case[field] = value
            changed_compact.append(f'{_id}.{field}')

if missing_compact:
    print(f'\nWARNING: not in compact JSON (skipped): {missing_compact}')

with open(COMPACT, 'w', encoding='utf-8') as f:
    json.dump(compact_data, f, ensure_ascii=False, indent=2)
print(f'\nCompact: {len(changed_compact)} fields updated')

# ── 5. apply to run-order JSON ─────────────────────────────────────────────────

RO_MAP = {
    't': 'title', 'pre': 'preconditions', 'proc': 'procedure',
    'exp': 'expected', 'ev': 'evidence', 'req': 'requirement'
}

with open(RO, encoding='utf-8') as f:
    ro_data = json.load(f)
ro_index = {c['id']: c for c in ro_data}

changed_ro = []
missing_ro = []
for _id, edits in stored.items():
    if _id not in ro_index:
        missing_ro.append(_id)
        continue
    case = ro_index[_id]
    for field, value in edits.items():
        ro_field = RO_MAP.get(field)
        if ro_field and case.get(ro_field) != value:
            case[ro_field] = value
            changed_ro.append(f'{_id}.{ro_field}')

if missing_ro:
    print(f'WARNING: not in run-order JSON (skipped): {missing_ro}')

with open(RO, 'w', encoding='utf-8') as f:
    json.dump(ro_data, f, ensure_ascii=False, indent=2)
print(f'Run-order: {len(changed_ro)} fields updated')

# ── 6. regenerate console ─────────────────────────────────────────────────────

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print('\n' + result.stdout.strip())
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)

print('\nDone.')
