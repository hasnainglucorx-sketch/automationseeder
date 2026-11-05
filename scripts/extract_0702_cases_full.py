"""
Extract full PRT-0702 case content from Word docx.
Produces output/console-update/PRT-0702-cases.json in the same compact schema as PRT-0701.

Document structure discovered:
  - Each case has: Test Case ID, Requirements tested, Test Data ID,
    Test Equipment or test data (preconditions), then a 4-column table:
      Test Steps | Expected Result | Evidence(...) | Test Result(...)
    Rows are interleaved: 1-action, 1-expected, 2-action, 2-expected, ...
  - Case titles appear in the text as "CASE-ID - Title text" before each case block.

Compact fields:
  r      - run order (1-based)
  sec    - section label
  id     - case ID
  t      - title (from document)
  method - always "Manual - Web Browser"
  req    - requirement string
  pre    - preconditions
  proc   - procedure (numbered, one step per line)
  exp    - expected result (numbered, matching proc steps)
  ev     - evidence
"""
import sys, re, zipfile, json, os
sys.stdout.reconfigure(encoding='utf-8')

DOCX = r"C:\Users\Hasnain\Downloads\PRT-0702_Web_Portal_Verification_Protocol_V0.docx"
OUT  = r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update\PRT-0702-cases.json"


# ── Read raw text from document.xml (preserving paragraph breaks) ────────────
def read_paragraphs(path):
    with zipfile.ZipFile(path) as z:
        for n in sorted(n for n in z.namelist() if re.match(r'word/(document|document\d+)\.xml', n)):
            xml = z.read(n).decode('utf-8', errors='replace')
            for p in re.split(r'<w:p[ >]', xml):
                text = re.sub(r'<[^>]+>', '', p)
                text = re.sub(r'[ \t]+', ' ', text).strip()
                if text:
                    yield text


paras = list(read_paragraphs(DOCX))
stream = '\n'.join(paras)

# ── Pre-extract all case titles from "CASE-ID - Title text" lines ────────────
CASE_ID_RE = re.compile(
    r'([A-Z][A-Z0-9]{1,15}-(?:[A-Z0-9]+-)*\d{3})', re.I)

TITLE_LINE_RE = re.compile(
    r'([A-Z][A-Z0-9]{1,15}-(?:[A-Z0-9]+-)*\d{3})\s+-\s+(.+)', re.I)

title_map = {}
for m in TITLE_LINE_RE.finditer(stream):
    cid = m.group(1).strip().upper()
    title = m.group(2).strip()
    if cid not in title_map:
        title_map[cid] = title

# ── Split into per-case chunks ────────────────────────────────────────────────
chunks = re.split(r'(?=\nTest Case ID\s)', stream)

# ── Accessibility IDs to exclude ─────────────────────────────────────────────
EXCL = re.compile(r'^(PAT-A11Y|TAL-A11Y|PORTAL-A11Y)', re.I)

# ── Field regexes ─────────────────────────────────────────────────────────────
CHUNK_ID_RE = re.compile(
    r'Test Case ID\s+([A-Z][A-Z0-9]{1,15}-(?:[A-Z0-9]+-)*\d{3})', re.I)

REQ_RE = re.compile(
    r'Requirements?\s+tested\s*[:\-]?\s*(.*?)(?=Test Data ID|Test Equipment|$)',
    re.DOTALL | re.I)

PRE_RE = re.compile(
    r'Test Equipment or test data\s*(.*?)(?=Test Steps|$)',
    re.DOTALL | re.I)

# Steps section: after the four column-header lines, before "Overall Result"
STEPS_SECTION_RE = re.compile(
    r'Test Steps\s*\nExpected Result[^\n]*\n[^\n]*\n[^\n]*\n(.*?)(?=Overall Result|\Z)',
    re.DOTALL | re.I)

NUMBERED_LINE_RE = re.compile(r'^(\d+)\.\s+(.+)', re.M)

EV_RE = re.compile(
    r'(?:Evidence|Pass criteria)\s*[:\-]?\s*(.*?)(?=Test Case ID|$)',
    re.DOTALL | re.I)

DIDO_PAIR_RE = re.compile(r'(DI-\d+)\s*[→\->]+\s*(DO-\d+)|(DI-\d+)(?!\s*[→\->])', re.I)


def clean(s):
    if not s:
        return ''
    s = re.sub(r'\n{3,}', '\n\n', s.strip())
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()


def extract_req(chunk):
    m = REQ_RE.search(chunk)
    if not m:
        return '—'
    raw = m.group(1).strip()
    if re.search(r'no direct di/do|supporting test|requirement gap', raw, re.I):
        gap = re.search(r'(GAP-[\w-]+)', raw, re.I)
        if gap:
            return f'—  (gap: {gap.group(1)})'
        return '—'
    pairs = []
    for pm in DIDO_PAIR_RE.finditer(raw):
        if pm.group(1) and pm.group(2):
            pairs.append(f"{pm.group(1)} → {pm.group(2)}")
        elif pm.group(3):
            pairs.append(f"{pm.group(3)} → (GAP)")
    return ' · '.join(pairs) if pairs else '—'


def extract_pre(chunk):
    m = PRE_RE.search(chunk)
    if not m:
        return ''
    raw = clean(m.group(1))
    raw = re.sub(r'\(TD-[\w\-\.]+\)', '', raw)
    raw = re.sub(r'[ \t]+', ' ', raw)   # re-collapse spaces left by TD removal
    return raw.strip()


def extract_steps_exp(chunk):
    """Return (proc_str, exp_str) by parsing interleaved numbered rows."""
    m = STEPS_SECTION_RE.search(chunk)
    if not m:
        return '', ''

    block = m.group(1)
    lines = NUMBERED_LINE_RE.findall(block)

    # First occurrence of number N → procedure; second → expected
    seen = {}
    proc_steps = {}
    exp_steps = {}

    for num_str, text in lines:
        num = int(num_str)
        seen[num] = seen.get(num, 0) + 1
        if seen[num] == 1:
            proc_steps[num] = text.strip()
        elif seen[num] == 2:
            exp_steps[num] = text.strip()

    max_n = max(seen.keys()) if seen else 0
    proc = '\n'.join(f'{n}. {proc_steps[n]}' for n in range(1, max_n + 1) if n in proc_steps)
    exp  = '\n'.join(f'{n}. {exp_steps[n]}' for n in range(1, max_n + 1) if n in exp_steps)
    return proc, exp


def extract_ev(chunk):
    # PRT-0702 uses an Evidence column in the table (filled during execution).
    # The column header "Evidence(screenshot/link)" is not evidence text.
    # Always return the standard default.
    return 'Screenshot(s) or recording; execution record'


# ── Portal → section label mapping ───────────────────────────────────────────
SECTION_MAP = {
    'PAT':      'Patient Portal',
    'HCP':      'HCP Portal',
    'CLINIC':   'Clinic Administrator Portal',
    'ADMIN':    'Modus Admin Portal',
    'SADMIN':   'Super Admin Portal',
    'FOLLOWER': 'Follower / Supporting',
    'STAFF':    'Staff / Supporting',
    'SUP':      'Cross-Portal Supporting',
}

FUNC_LABEL = {
    'AUTH': 'Authentication',
    'SESSION': 'Session Management',
    'HOME': 'Home Screen',
    'GRAPH': 'CGM Graph',
    'OGP': 'Overview Graph Panel',
    'HISTORY': 'History View',
    'PROFILE': 'Profile',
    'SETTING': 'Settings',
    'SETTINGS': 'Settings',
    'ALERT': 'Alert Configuration',
    'ACCOUNT': 'Account Management',
    'SHARE': 'Share / Follow',
    'REPORT': 'Reports',
    'HELP': 'Help',
    'RESP': 'Responsiveness',
    'ERROR': 'Error Handling',
    'SEC': 'Security',
    'EDGE': 'Edge Cases',
    'DATA': 'Data Display',
    'CALC': 'Calculations',
    'TIR': 'Time in Range',
    'UNIT': 'Unit Conversion',
    'FILTER': 'Data Filtering',
    'CHART': 'Chart Display',
    'COMPARE': 'Data Comparison',
    'EXPORT': 'Data Export',
    'TIMEZONE': 'Timezone',
    'EVENT': 'Event Data',
    'OVERVIEW': 'Overview Dashboard',
    'OVERLAY': 'Overlay Panel',
    'CROSS': 'Cross-Portal Data',
    'TIME': 'Time Data',
    'DIDO': 'DI/DO Traceability',
    'NFR': 'Non-Functional Requirements',
    'PERF': 'Performance',
    'APP': 'Application Management',
    'DASH': 'Dashboard',
    'PAT': 'Patient List',
    'HCP': 'HCP Management',
    'QR': 'QR Code / Invitation',
    'DIR': 'Clinic Directory',
    'USERS': 'User Management',
    'AUTHZ': 'Authorization',
    'DELETE': 'Account Deletion',
    'PASS': 'Password Management',
    'NOTIF': 'Notifications',
    'LINK': 'Link / Invite',
    'INVITE': 'Invite',
    'SENSOR': 'Sensor',
    'TRANSMIT': 'Transmission',
    'CGMX': 'CGMx',
    'CLINIC': 'Clinic',
}


def section_label(case_id):
    parts = case_id.split('-')
    portal = SECTION_MAP.get(parts[0], parts[0])
    func = parts[1] if len(parts) > 1 else ''
    # Handle extended IDs like PAT-ACCOUNT-DELETE
    func_key = func
    func_lbl = FUNC_LABEL.get(func_key, func_key)
    return f"{portal} — {func_lbl}"


# ── Sort order: portal prefix only; preserve document order within each portal ─
PORTAL_ORDER = {
    'PAT': 0, 'HCP': 1, 'CLINIC': 2, 'ADMIN': 3,
    'SADMIN': 4, 'FOLLOWER': 5, 'STAFF': 6, 'SUP': 7,
}

# ── Parse each chunk — record document position for ordering ─────────────────
results = []
seen_ids = set()
doc_pos = 0  # position in document

for chunk in chunks:
    m = CHUNK_ID_RE.search(chunk)
    if not m:
        continue
    case_id = m.group(1).strip().upper()
    if EXCL.match(case_id):
        continue
    if case_id in seen_ids:
        continue
    seen_ids.add(case_id)

    req       = extract_req(chunk)
    pre       = extract_pre(chunk)
    proc, exp = extract_steps_exp(chunk)
    ev        = extract_ev(chunk)
    sec       = section_label(case_id)

    # Use title from document; fall back to computed label
    doc_title = title_map.get(case_id, '')
    if doc_title:
        t = f"{case_id} — {doc_title}"
    else:
        t = section_label(case_id) + ' ' + case_id.split('-')[-1]

    results.append({
        'id':      case_id,
        'sec':     sec,
        't':       t,
        'req':     req,
        'pre':     pre,
        'proc':    proc,
        'exp':     exp,
        'ev':      ev,
        '_pos':    doc_pos,   # document position — removed before output
        '_portal': PORTAL_ORDER.get(case_id.split('-')[0], 99),
    })
    doc_pos += 1


def sort_key(c):
    # Group by portal prefix; within each portal keep document order
    return (c['_portal'], c['_pos'])


results.sort(key=sort_key)

# add run order and method
for i, c in enumerate(results, 1):
    c['r'] = i
    c['method'] = 'Manual - Web Browser'

# reorder fields, drop internal tracking keys
ordered = []
for c in results:
    ordered.append({
        'r':      c['r'],
        'sec':    c['sec'],
        'id':     c['id'],
        't':      c['t'],
        'method': c['method'],
        'req':    c['req'],
        'pre':    c['pre'],
        'proc':   c['proc'],
        'exp':    c['exp'],
        'ev':     c['ev'],
    })


os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(ordered)} cases → {OUT}")

# Quality check
missing_exp = sum(1 for c in ordered if not c['exp'].strip())
missing_proc = sum(1 for c in ordered if not c['proc'].strip())
no_title = sum(1 for c in ordered if not title_map.get(c['id']))
print(f"Missing exp: {missing_exp}  Missing proc: {missing_proc}  No-doc-title: {no_title}")

# Sample check
for c in ordered[:3]:
    print(f"\n{'─'*60}")
    print(f"ID:   {c['id']}")
    print(f"T:    {c['t'][:80]}")
    print(f"Proc: {c['proc'][:120]}")
    print(f"Exp:  {c['exp'][:120]}")
