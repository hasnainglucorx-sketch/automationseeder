"""Publish individually reviewed readiness findings without changing execution results."""
import csv
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

old = read('output/portal-fixtures/execution-report-blocked-142.json')
current = read('output/console-update/PRT-0702-cases.json')
case_map = {x['id']: x for x in current}
catalog = read('output/portal-test-assets.json')
accounts = {x['reference']: x for x in catalog['accounts']}
resources = {x['reference']: x for x in catalog['resources']}
manifest = read('output/portal-fixtures/fixture-manifest.json')
with (OUT / 'blocked-142-review-notes.tsv').open(encoding='utf-8') as f:
    notes = {int(x['row']): x for x in csv.DictReader(f, delimiter='\t')}
assert set(notes) == set(range(1, 143))
assert len(old['cases']) == len({x['id'] for x in old['cases']}) == 142
console = (OUT / 'console-update/PRT-0701-Console-source.html').read_text(encoding='utf-8')
assert json.loads(re.search(r'const ALL_PORTAL_CASES = (.*?);\n', console).group(1)) == current

# Human-reviewed additional issues that the earlier alias-only checker missed.
repair = {3,4,14,16,17,19,20,22,24,25,26,27,43,44,54,76,78,79,137,138}
extra_blocked = {75,128,141,142}
dated = {2,4,5,6,7,8,9,12,15,16,17,23,25,27,28,29,30,31,33,
         35,36,37,38,39,40,41,42,44,45,46,47,48,49,50,51,52,53,54,
         55,56,57,58,59,60,125,138}
offline = {32,34}
product_blocked = {80,82}
historical = {}
for file in ['output/hcp-list-004-execution.json', 'output/hcp-data-019-execution.json']:
    d = read(file)
    historical[d['case_id']] = {'date':d['executed_on'], 'result':d['overall_result'],
                               'source':file, 'detail':d.get('defect_summary','See per-step observations in the source.'),
                               'evidence_present':all((ROOT/p).exists() for p in d['evidence'])}
d = read('output/hcp-profile-review-2026-10-08.json')
for entry in d['results']:
    historical[entry['case_id']] = {'date':d['executed_on'], 'result':entry['result'],
        'source':'output/hcp-profile-review-2026-10-08.json', 'detail':entry['actual'],
        'evidence_present':all((ROOT/p).exists() for p in d['evidence'])}

rows=[]
for n, entry in enumerate(old['cases'],1):
    ident = entry['id']
    target = 'CLINIC-AUTH-007' if ident=='CLINIC-AUTH-008' else ident
    c = case_map.get(target)
    note = notes[n]
    blockers=[]
    available=[]
    refs=[]
    if c:
        text=' '.join(c.get(k,'') for k in ['pre','proc','exp','ev'])
        aliases=sorted(set(re.findall(r'\bQA-PORTAL-[A-Z0-9-]+\b',text)))
        for alias in aliases:
            a=accounts.get(alias,{})
            if a.get('availability') in {'Configured','Verified fixture'}:
                available.append(alias+' ('+a['availability']+' in local register)')
            else:
                blockers.append(alias+': '+a.get('kind','account/fixture')+' not supplied in the local register')
        refs=sorted({v.rstrip('.') for v in re.findall(r'Portal Test Assets\s*>\s*([A-Z0-9.-]+)',text,re.I)})
        for ref in refs:
            if resources.get(ref,{}).get('availability')!='Embedded in console':
                blockers.append(ref+': concrete controlled value/evidence not embedded')
        assert re.findall(r'(?m)^\d+\.',c['proc']) == re.findall(r'(?m)^\d+\.',c['exp']), ident
    if not c:
        verdict='NO CURRENT MATCH'
    elif target!=ident:
        verdict='MERGED — REPLACEMENT STILL NEEDS SETUP'
    elif n in product_blocked:
        verdict='BLOCKED — PRIOR PRODUCT DEFECT'
    elif blockers or n in extra_blocked:
        verdict='BLOCKED — PREREQUISITES NOT SUPPLIED'
    elif n in repair:
        verdict='NEEDS TEST REPAIR'
    elif n in dated:
        verdict='BLOCKED — REFRESH DATED FIXTURE'
    elif n in offline:
        verdict='EXECUTABLE OFFLINE'
    else:
        verdict='CONDITIONAL — CONFIRM LIVE SETUP'
    if n in dated:
        blockers.append('The saved fixture is anchored to 7 October 2026 (sparse account: 8 October), not the 12 October review date. Refresh/reverify the fixture and expected tables before current rolling presets; match the Europe/London time zone.')
    trace = c.get('req','') if c else ''
    formal = ('Requirement gap still shown in the current mapping; behavioral execution does not establish formal approval.'
              if re.search(r'gap',trace,re.I) else 'Check the cited requirement against the approved build; this review does not grant approval.')
    rows.append({'row':n, 'old_id':ident, 'old_title':entry['title_at_execution'],
        'old_blocker':entry['blocker_note'] or 'No blocker note supplied.', 'report_page':entry['report_page'],
        'current_id':target if c else None, 'current_title':c['t'] if c else None,
        'section':c['sec'] if c else None, 'verdict':verdict,
        'what_is_now_specified':note['current_change_or_clarification'],
        'remaining_issue_and_next_action':note['remaining_review_issue'],
        'missing_or_stale_prerequisites':blockers, 'locally_available':available,
        'references':refs, 'traceability':trace, 'formal_scope':formal,
        'prior_execution':historical.get(ident), 'current_definition':c})

# These are independent local arithmetic checks, not new Portal execution results.
h=next(x for x in manifest['fixtures'] if x['alias']=='QA-PORTAL-HISTORY-01')['ranges']['7_days']
tir=[round(h[k]/h['reading_count']*100,1) for k in ['below_70_count','in_70_180_count','above_180_count']]
assert tir==[15.0,70.0,15.0]
values=[45,50,63,70,100,120,140,154,156,180,200,240,300]
conversions=[round(v/18.0182,1) for v in values]
assert conversions==[2.5,2.8,3.5,3.9,5.5,6.7,7.8,8.5,8.7,10.0,11.1,13.3,16.6]
counts=Counter(x['verdict'] for x in rows)
sources=['output/portal-fixtures/execution-report-blocked-142.json','output/console-update/PRT-0702-cases.json',
         'output/portal-test-assets.json','output/portal-fixtures/fixture-manifest.json',
         'output/blocked-142-review-notes.tsv']
report={'review_date':'2026-10-12','scope':'Individual definition and local evidence review; no new live Portal execution.',
        'counts':dict(counts),'cases_reviewed':142,'prior_execution_records':len(historical),
        'dated_fixture_cases':len(dated),'offline_arithmetic':{'PAT-TIR-001':tir,'PAT-UNIT-001':conversions},
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'cases':rows}
(OUT/'Blocked-142-execution-readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
intro=[
 'Each of the 142 originally blocked tests has been reviewed against its current Portal definition, the old blocker note, the local account/resource register, fixture tables and available execution evidence.',
 'This is an execution-readiness review, not a new live test run. “Configured” means an account is listed locally, not that its login, role or MFA worked today. Values entered only in a browser Run Setup or held in an external controlled source are not confirmed by this review.',
 'The earlier 71 count combined 63 rewritten definitions and 8 prior executions. It must not be read as 71 passing tests or 71 tests executable today. The older readiness checker only looked for aliases, numbered steps and references; it missed unnamed tools, missing acceptance criteria, dated fixtures and known product failures.',
 'The History fixture anchor is 7 October 2026; sparse and other fixtures use 8 October. Current rolling date presets cannot safely use those original expected counts on 12 October. Refresh and reverify the data and expected tables before those tests. Historical custom-date tests may use the retained absolute dates if the records remain available.',
 'CLINIC-QR-012 keeps its ID. Find it in Portal → Clinic Administrator Portal — QR Code / Invitation, or clear filters and search the ID. It is still blocked in the supplied evidence: the Clinic Admin account and fault rule are not supplied, and the export mechanism must be confirmed.',
 'Sources: YN Test Run dated 21 September 2026, extracted into execution-report-blocked-142.json; current PRT-0702-cases.json checked against the embedded console data; portal-test-assets.json; fixture-manifest.json; and the three 8 October execution files cited in individual rows. “Now specified” describes the current remedy to the old blocker, not a proven application-code fix.'
]
md=['# Readiness review of 142 previously blocked web tests','',*sum(([x,''] for x in intro),[]),'| Readiness decision | Cases |','| --- | ---: |']
md += [f'| {k} | {v} |' for k,v in counts.items()]
md += ['', 'Offline arithmetic was checked: PAT-TIR-001 gives 15/70/15 percent; all 13 PAT-UNIT-001 conversions match. No console execution result was changed.', '', '## Individual findings','']

def esc(x):return html.escape(str(x or ''))
cards=[]
for r in rows:
    oldcell=f"{r['old_id']} — {r['old_title']}<br>Report page {r['report_page']}; original result BLOCKED.<br>Old blocker: {r['old_blocker']}"
    needs='; '.join(r['missing_or_stale_prerequisites']) or 'No additional missing alias/reference detected; follow the individual setup conditions.'
    past=r['prior_execution']
    pasttext=(f"{past['date']}: {past['result']}. {past['detail']} Source: {past['source']}" if past else 'No later case-specific execution result found in the reviewed execution files.')
    newlines=[r['current_title'] or 'No current match',r['verdict'],'Now specified: '+r['what_is_now_specified'],
              'Remaining / next action: '+r['remaining_issue_and_next_action'],'Prerequisites: '+needs,
              'Previous execution evidence: '+pasttext]
    md += [f"### {r['row']} {r['old_id']}",'','| Previous blocked report | Current console and readiness |','| --- | --- |',
           '| '+oldcell.replace('|',' / ')+' | '+'<br><br>'.join(x.replace('|',' / ').replace('\n',' ') for x in newlines)+' |','']
    c=r['current_definition']
    details=''
    if c:
        details='<details><summary>Read current test and source checks</summary>'+''.join('<h4>'+esc(label)+'</h4><pre>'+esc(c[key])+'</pre>' for label,key in [('Preconditions','pre'),('Procedure','proc'),('Expected result','exp')])+'<p>'+esc(r['formal_scope'])+'</p><p>Locally listed: '+esc('; '.join(r['locally_available']) or 'None')+'</p></details>'
    cards.append('<tr data-status="'+esc(r['verdict'])+'"><td><b>'+esc(str(r['row'])+'. '+r['old_id'])+'</b><p>'+esc(r['old_title'])+'</p><p>Report page '+str(r['report_page'])+' · BLOCKED</p><p><strong>Old blocker</strong><br>'+esc(r['old_blocker'])+'</p></td><td><b>'+esc(r['current_title'] or 'No current match')+'</b><p class="status">'+esc(r['verdict'])+'</p><p><strong>Now specified</strong><br>'+esc(r['what_is_now_specified'])+'</p><p><strong>Remaining issue and next action</strong><br>'+esc(r['remaining_issue_and_next_action'])+'</p><p><strong>Missing or stale prerequisites</strong><br>'+esc(needs)+'</p><p><strong>Previous execution evidence</strong><br>'+esc(pasttext)+'</p>'+details+'</td></tr>')
(OUT/'Blocked-142-execution-readiness.md').write_text('\n'.join(md),encoding='utf-8')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>142 blocked web tests — readiness review</title><style>
body{font:16px/1.5 system-ui,sans-serif;color:#17212c;background:#f5f7fa;margin:0}main{max-width:1200px;margin:32px auto;padding:28px;background:white}h1{font-size:30px;line-height:1.2}p{margin:10px 0}table{width:100%;border-collapse:collapse;margin:20px 0}th,td{border:1px solid #ccd4df;padding:18px;vertical-align:top;text-align:left}th{background:#e8eef5}td:first-child{width:35%}td:nth-child(2){width:65%}.status{font-weight:700;color:#804b00}pre{white-space:pre-wrap;font:inherit}summary{cursor:pointer;color:#164f8c}input,select{padding:10px;font:inherit;max-width:95%}.controls{position:sticky;top:0;background:white;padding:12px 0;border-bottom:1px solid #ccd4df;display:flex;flex-wrap:wrap;gap:12px}small{color:#536273}@media print{body{background:white}main{padding:0;margin:0}.controls{display:none}tr{break-inside:avoid}thead{display:table-header-group}details{display:none}}
</style><main><h1>Readiness review of 142 previously blocked web tests</h1><p><b>12 October 2026 · All 142 rows reviewed individually</b></p>'''
page+=''.join('<p>'+esc(x)+'</p>' for x in intro)
page+='<ul>'+''.join('<li><b>'+str(v)+'</b> '+esc(k)+'</li>' for k,v in counts.items())+'</ul><p>Offline arithmetic checked: PAT-TIR-001 = 15/70/15 percent; all 13 PAT-UNIT-001 conversions match. No live execution status was changed.</p>'
page+='<div class="controls"><input id="search" placeholder="Search ID, blocker or tool" aria-label="Search cases"><select id="filter" aria-label="Filter readiness"><option value="">All readiness decisions</option>'+''.join('<option>'+esc(k)+'</option>' for k in counts)+'</select><span id="count">142 cases</span></div><table><thead><tr><th>Previous blocked execution report</th><th>Current console and execution readiness</th></tr></thead><tbody>'+''.join(cards)+'</tbody></table></main><script>function filter(){const q=document.querySelector("#search").value.toLowerCase(),s=document.querySelector("#filter").value;let n=0;document.querySelectorAll("tbody tr").forEach(r=>{r.hidden=!(r.textContent.toLowerCase().includes(q)&&(!s||r.dataset.status===s));if(!r.hidden)n++});document.querySelector("#count").textContent=n+" cases"}document.querySelector("#search").oninput=filter;document.querySelector("#filter").onchange=filter;</script></html>'
(OUT/'Blocked-142-execution-readiness.html').write_text(page,encoding='utf-8')
assert len(rows)==142 and sum(counts.values())==142
print(json.dumps({'reviewed':142,'counts':dict(counts),'dated_fixture_cases':len(dated),'prior_evidence':len(historical),'offline_checks':'passed'},indent=2))
