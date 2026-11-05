"""Create the two-column evidence-to-console lookup without changing results."""
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'output/portal-fixtures/execution-report-blocked-142.json').read_text(encoding='utf-8'))
cases = json.loads((ROOT / 'output/console-update/PRT-0702-cases.json').read_text(encoding='utf-8'))
lookup = {c['id']: c for c in cases}
html = (ROOT / 'output/console-update/PRT-0701-Console-source.html').read_text(encoding='utf-8')
embedded = json.loads(re.search(r'const ALL_PORTAL_CASES = (.*?);\n', html).group(1))
assert embedded == cases
assert len(source['cases']) == len({c['id'] for c in source['cases']}) == 142
rows = []
for old in source['cases']:
    ident = old['id']
    left = [ident, old['title_at_execution'], f"Execution report: BLOCKED • page {old['report_page']}", 'Blocker note: ' + (old['blocker_note'] or 'None supplied.')]
    match = lookup.get(ident)
    if match:
        title = match['t'].removeprefix(ident).lstrip(' —-')
        right = [ident, title, 'Section: ' + match['sec'], 'Same ID. Search this ID in Portal.']
    elif ident == 'CLINIC-AUTH-008':
        match = lookup['CLINIC-AUTH-007']
        right = [match['id'], match['t'].removeprefix(match['id']).lstrip(' —-'), 'Section: ' + match['sec'], 'Merged coverage: the old report title explicitly names CLINIC-AUTH-007. CLINIC-AUTH-008 is absent.']
    else:
        right = ['NO CURRENT MATCH', 'This ID is absent from the 574 current Portal cases. No replacement ID is confirmed by the available sources.']
    rows.append((left, right))

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin = sec.bottom_margin = Inches(.65)
sec.left_margin = sec.right_margin = Inches(.65)
normal = doc.styles['Normal']
normal.font.name = 'Calibri'
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(5)
doc.styles['Title'].font.color.rgb = RGBColor(0,0,0)
doc.add_paragraph('Blocked web tests compared with the current console', 'Title')
intro = [
    'All 142 blocked tests from the YN Test Run dated 21 September 2026 are listed below beside their current Portal console match, checked on 12 October 2026.',
    '139 tests keep the same ID. One test has explicitly merged coverage under CLINIC-AUTH-007. Two tests have no confirmed current match. A matching or rewritten case does not establish a new Pass result; the left column preserves the original Blocked outcome.',
    'To find a case, open the local PRT console, select Portal, clear section and status filters, and enter the current ID in “Search case ID or title”. For CLINIC-QR-012, use the same ID under Clinic Administrator Portal — QR Code / Invitation. Its current title is “Clinic QR download failure is controlled”.',
    'Sources: PAT-0701 · Web Portal Verification Protocol · Web portal.pdf (page references in the left column), its execution-report-blocked-142.json extraction, and the current PRT-0702-cases.json verified against the Portal cases embedded in PRT-0701-Console-source.html. Rows follow the evidence report order.'
]
for p in intro: doc.add_paragraph(p)
table = doc.add_table(rows=1, cols=2)
table.style = 'Table Grid'
table.autofit = False
for cell in table.rows[0].cells: cell.width = Inches(3.6)
for cell, text in zip(table.rows[0].cells, ['Original blocked execution report', 'Current Portal console test case']):
    cell.text = text
    cell.paragraphs[0].runs[0].bold = True
    shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), 'E8EEF5'); cell._tc.get_or_add_tcPr().append(shade)
repeat = OxmlElement('w:tblHeader'); table.rows[0]._tr.get_or_add_trPr().append(repeat)
for left, right in rows:
    row = table.add_row()
    row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    for cell, lines in zip(row.cells, [left, right]):
        cell.width = Inches(3.6)
        for i, text in enumerate(lines):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(text)
            if i == 0: run.bold = True
            if i >= 2: run.font.size = Pt(10)
footer = sec.footer.paragraphs[0]
footer.add_run('Blocked web test comparison • 12 October 2026 • Page ')
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
footer.style = doc.styles['Caption']
dest = ROOT / 'output/Blocked-142-to-current-Portal-console.docx'
doc.save(dest)
md = ['# Blocked web tests compared with the current console', *intro, '| Original blocked execution report | Current Portal console test case |', '| --- | --- |']
for left,right in rows:
    md.append('| ' + ' | '.join('<br>'.join(s.replace('|',' / ') for s in lines) for lines in [left,right]) + ' |')
dest.with_suffix('.md').write_text('\n\n'.join(md[:5]) + '\n\n' + '\n'.join(md[5:]), encoding='utf-8')
assert len(Document(dest).tables[0].rows) == 143
print(f'Created {dest}; 142 comparison rows; 139 exact matches, 1 explicit merge, 2 unmatched.')
