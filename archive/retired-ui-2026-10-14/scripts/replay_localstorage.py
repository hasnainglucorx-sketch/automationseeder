"""
Replays all 60 localStorage setItem/delete calls from the previous session's transcript
and rebuilds the final state. Then applies every changed field directly to the JSON files.

Run with: python -I scripts/replay_localstorage.py
"""
import json, pathlib, re, sys

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'
TRANSCRIPT = pathlib.Path(r'C:\Users\Hasnain\.claude\projects\C--Users-Hasnain-Downloads-Automation-seeder\bd4fa740-4bc8-4b70-b80c-de693e30b6bb.jsonl')

# ── Step 1: extract all JS setItem calls from transcript ──────────────────────

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

print(f"Extracted {len(js_calls)} JS calls from transcript")

# ── Step 2: rebuild localStorage state by replaying operations in Python ──────
# We translate each JS pattern to Python dict operations.

stored = {}  # simulates localStorage['PRT0701_review_edits']

def apply_js(code):
    """Translate a single JS block into Python dict mutations."""

    # Pattern: delete stored['ID']  or  delete s['ID']  or  delete existing['ID']
    for m in re.finditer(r"delete\s+\w+\['(VP-APP-[^']+)'\]", code):
        _id = m.group(1)
        stored.pop(_id, None)

    # Pattern: s['ID'] = { ... } or existing['ID'] = { ... } or stored['ID'] = { ... }
    # We handle full-object assignments
    for m in re.finditer(r"\w+\['(VP-APP-[^']+)'\]\s*=\s*\{", code):
        _id = m.group(1)
        # Find the start of the opening {
        start = m.end() - 1
        # Find matching closing }
        depth = 0
        end = start
        in_str = False
        str_char = None
        for i in range(start, len(code)):
            c = code[i]
            if in_str:
                if c == '\\':
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
        obj_str = code[start:end]
        # Convert JS object literal to something we can parse
        # Replace single-quoted string delimiters with double quotes
        # and fix escape sequences
        try:
            # Try direct JSON parse after minimal fixup
            json_str = re.sub(r"(?<![\\])'", '"', obj_str)
            # Fix \n inside strings - already escaped, leave
            obj = json.loads(json_str)
            if _id not in stored:
                stored[_id] = {}
            stored[_id].update(obj)
        except Exception:
            pass  # Will catch via field-level patterns below

    # Pattern: s['ID'].field = '...'  (single/double quoted, possibly multiline)
    # Handle all field assignments
    field_pattern = re.compile(
        r"\w+\['(VP-APP-[^']+)'\]\.(t|pre|proc|exp|ev|req|method|sec)\s*=\s*"
        r"('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")"
    )
    for m in field_pattern.finditer(code):
        _id    = m.group(1)
        field  = m.group(2)
        raw    = m.group(3)
        value  = raw[1:-1]  # strip outer quotes
        # unescape \\n -> \n, \\' -> ', \\" -> "
        value = value.replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
        if _id not in stored:
            stored[_id] = {}
        stored[_id][field] = value

apply_js.__doc__  # just to reference it

for call in js_calls:
    apply_js(call)

print(f"Replay complete. Final stored IDs: {sorted(stored.keys())}")
print(f"Total IDs with edits: {len(stored)}")

# ── Step 3: apply changes to compact JSON ─────────────────────────────────────

COMPACT_FIELD = {'t': 't', 'pre': 'pre', 'proc': 'proc', 'exp': 'exp', 'ev': 'ev', 'req': 'req'}

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
        if field in COMPACT_FIELD:
            if case.get(field) != value:
                case[field] = value
                changed_compact.append(f"  {_id}.{field}")

if missing_compact:
    print(f"WARNING: these IDs not in compact JSON (skipped): {missing_compact}")

with open(COMPACT, 'w', encoding='utf-8') as f:
    json.dump(compact_data, f, ensure_ascii=False, indent=2)
print(f"Compact JSON updated. Changed fields ({len(changed_compact)}):")
for c in changed_compact:
    print(c)

# ── Step 4: apply changes to run-order JSON ───────────────────────────────────

RO_FIELD_MAP = {'t': 'title', 'pre': 'preconditions', 'proc': 'procedure',
                'exp': 'expected', 'ev': 'evidence', 'req': 'requirement'}

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
    for compact_field, value in edits.items():
        ro_field = RO_FIELD_MAP.get(compact_field)
        if ro_field and case.get(ro_field) != value:
            case[ro_field] = value
            changed_ro.append(f"  {_id}.{ro_field}")

if missing_ro:
    print(f"WARNING: these IDs not in run-order JSON (skipped): {missing_ro}")

with open(RO, 'w', encoding='utf-8') as f:
    json.dump(ro_data, f, ensure_ascii=False, indent=2)
print(f"Run-order JSON updated. Changed fields ({len(changed_ro)}):")
for c in changed_ro:
    print(c)

print("\nDone. Run python -I scripts/generate_unified_console.py next.")
