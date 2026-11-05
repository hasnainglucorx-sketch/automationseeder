"""
Extract PRT-0702 DI/DO mapping — one row per case ID, sorted by section.
Outputs a CSV and a formatted text table.
"""
import sys, re, zipfile, csv, io
sys.stdout.reconfigure(encoding='utf-8')

DOCX = r"C:\Users\Hasnain\Downloads\PRT-0702_Web_Portal_Verification_Protocol_V0.docx"

# ── 1. Read raw text from docx ──────────────────────────────────────────────
def read_docx_text(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        parts = []
        for n in sorted(n for n in names if re.match(r'word/(document|document\d+)\.xml', n)):
            xml = z.read(n).decode('utf-8', errors='replace')
            xml = re.sub(r'<[^>]+>', ' ', xml)
            xml = re.sub(r'[ \t]+', ' ', xml)
            parts.append(xml)
        return '\n'.join(parts)

text = read_docx_text(DOCX)

# ── 2. Split into per-case chunks on "Test Case ID" boundary ────────────────
chunks = re.split(r'(?=Test Case ID\s*[:\-]?\s*)', text)

# ── 3. Accessibility IDs to exclude ─────────────────────────────────────────
EXCL = re.compile(r'^(PAT-A11Y|TAL-A11Y|PORTAL-A11Y)', re.I)

# ── 4. Parse each chunk ──────────────────────────────────────────────────────
CASE_ID_RE  = re.compile(r'Test Case ID\s*[:\-]?\s*([A-Z][A-Z0-9]{1,15}-(?:[A-Z0-9]+-)*\d{3})', re.I)
REQ_RE      = re.compile(r'Requirements?\s+tested\s*[:\-]?\s*(.*?)(?:Test Data ID|$)', re.DOTALL | re.I)
DIDO_PAIR_RE = re.compile(r'(DI-\d+)\s*[→\->]+\s*(DO-\d+)|(DI-\d+)(?!\s*[→\->])', re.I)

results = []
seen_ids = set()

for chunk in chunks:
    m = CASE_ID_RE.search(chunk)
    if not m:
        continue
    case_id = m.group(1).strip().upper()
    if EXCL.match(case_id):
        continue

    # extract requirements block
    req_m = REQ_RE.search(chunk)
    req_text = req_m.group(1).strip() if req_m else ''

    # find all DI→DO pairs in the requirements block
    pairs = []
    for pm in DIDO_PAIR_RE.finditer(req_text):
        if pm.group(1) and pm.group(2):
            pairs.append(f"{pm.group(1).upper()} → {pm.group(2).upper()}")
        elif pm.group(3):
            pairs.append(f"{pm.group(3).upper()} → (no DO — GAP)")
    dido = ' · '.join(pairs) if pairs else '—'

    # deduplicate: keep first occurrence
    if case_id in seen_ids:
        continue
    seen_ids.add(case_id)
    results.append((case_id, dido))

# ── 5. Sort: by portal prefix, then sub-section, then number ────────────────
PORTAL_ORDER = {
    'PAT': 0,
    'HCP': 1,
    'CLINIC': 2,
    'ADMIN': 3,
    'SADMIN': 4,
    'FOLLOWER': 5,
    'STAFF': 6,
    'SUP': 7,
}
def sort_key(row):
    cid = row[0]
    parts = cid.split('-')
    portal = PORTAL_ORDER.get(parts[0], 99)
    sub = parts[1] if len(parts) > 1 else ''
    rest = parts[2:] if len(parts) > 2 else []
    # last part is the numeric index
    try:
        num = int(rest[-1]) if rest else int(parts[-1])
        if rest:
            rest[-1] = f'{num:04d}'
    except (ValueError, IndexError):
        pass
    return (portal, sub, *rest)

results.sort(key=sort_key)

# ── 6. Write CSV ─────────────────────────────────────────────────────────────
CSV_OUT = r"C:\Users\Hasnain\Downloads\Automation seeder\output\PRT-0702-dido-flat.csv"
import os
os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
with open(CSV_OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Case ID', 'DI → DO'])
    w.writerows(results)

# ── 7. Print table ───────────────────────────────────────────────────────────
current_section = None
section_count = 0
total = 0

print(f"{'Case ID':<35}  {'DI → DO'}")
print('-' * 100)

for case_id, dido in results:
    parts = case_id.split('-')
    # section = portal + first sub-label (e.g. PAT-AUTH, NIC-APP, MIN-DIDO)
    section = '-'.join(parts[:2])
    if section != current_section:
        if current_section is not None:
            print(f"   [{section_count} cases]")
        print(f"\n── {section} ──────────────────────────────────────────────")
        current_section = section
        section_count = 0
    print(f"  {case_id:<33}  {dido}")
    section_count += 1
    total += 1

if section_count:
    print(f"   [{section_count} cases]")

print(f"\n{'='*100}")
print(f"Total cases: {total}  (accessibility cases excluded)")
print(f"\nCSV written to: {CSV_OUT}")
