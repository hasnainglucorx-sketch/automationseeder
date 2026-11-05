"""Publish the exact current 71 definitions as a searchable QA companion."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
update = json.loads((ROOT/'output/manual-qa-71-update.json').read_text(encoding='utf-8'))
all_cases = json.loads((ROOT/'output/console-update/PRT-0702-cases.json').read_text(encoding='utf-8'))
cases = [c for c in all_cases if c['id'] in update['case_ids']]
assert len(cases) == 71
esc = html.escape
intro = '''71 Portal cases — manual QA guide

Updated 13 October 2026. These are revised instructions, not 71 new passes. Existing execution outcomes are unchanged. The old 142-case readiness report remains a dated review; use these current definitions for this set of 71 IDs.

Start in the PRT console, select Web Portal, clear other filters and search the exact test ID below. IDs have not changed. Read Preconditions before starting. Missing account access, current data, a numeric reference or a prepared fault rule means Blocked: name the missing item. If the required setup is available but the application behaves incorrectly, use Fail and describe the difference.

The History fixture currently has anchor 2026-10-07. Rolling-range cases require fresh data and matching expected tables for the test date. Do not change the anchor label to pretend that the dataset is fresh. The setup owner must refresh, verify and publish the matching reference values before those cases run. Fixed historical-date cases use the dates written in their steps.

Evidence: create a folder using the test ID. Use the E01, E02 and other filenames specified by the case. Include date, build, account alias, browser/version, step number, expected value, actual value and outcome. A screenshot must show the relevant page, selected period, unit and result. Numeric cases also need the expected/actual comparison sheet. Hide passwords, tokens and unrelated personal details. No evidence means a result cannot be independently checked.

Follow the procedure in order. Each procedure number matches the same expected-result number. Capture evidence before leaving a failure state. Perform cleanup even after a failure: turn off local rules and restore changed profile values, time zone and cache settings. Note any cleanup that could not complete.

Failure-simulation setup: the 11 cases listed below need a setup owner to supply and demonstrate the local rule. The instructions do not mean that those rules already exist. The setup sheet must give the exact URL and method from the current QA build, the account and target data, how to enable/disable the rule, and proof that normal loading works with it off. Intercept locally; do not modify the server. For synthetic save failures, prevent the request reaching the server. QA should not guess request URLs or write interception code during execution.
'''

parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>71 Portal cases — manual QA guide</title>',
'''<style>body{font:16px/1.55 system-ui;margin:32px auto;max-width:1150px;padding:0 24px;color:#182334;background:#f6f8fb}h1,h2{line-height:1.25}article,section{background:white;padding:24px;border:1px solid #d6dfec;border-radius:12px;margin:20px 0}table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{border:1px solid #d6dfec;padding:12px;vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:#edf2fa}li{padding:5px}input{padding:12px;width:90%;font:inherit}pre{white-space:pre-wrap}a{color:#2056a8}@media print{input{display:none}article{break-before:page}tr{break-inside:avoid}}</style>''',
 '<h1>71 Portal cases — manual QA guide</h1><p><a href="PRT-0701-Console-source.html">Open PRT console</a></p><section>']
parts.extend('<p>'+esc(p)+'</p>' for p in intro.split('\n\n')[1:])
parts.append('</section><section><h2>Prepared rule checklist</h2><table><tr><th>Case / rule names</th><th>Required local behavior</th></tr>')
for cid, card in update['fault_setup_cards'].items():
    parts.append('<tr><td>'+esc(cid+' — '+', '.join(card['rule_names']))+'</td><td>'+esc(', '.join(card['request_names'])+'; '+card['mode'])+'<br>Provisioning is not confirmed.</td></tr>')
parts.append('</table></section><h2>Find a case</h2><input id="find" placeholder="Search ID or words in the case" aria-label="Search cases"><p id="count">71 cases</p>')
md = [intro]
for c in cases:
    proc=c['proc'].splitlines(); exp=c['exp'].splitlines()
    assert len(proc)==len(exp),c['id']
    parts.append('<article><h2>'+esc(c['t'])+'</h2><h3>Preconditions</h3><p>'+esc(c['pre'])+'</p><table><tr><th>Procedure</th><th>Expected result</th></tr>')
    for p,e in zip(proc,exp):parts.append('<tr><td>'+esc(p)+'</td><td>'+esc(e)+'</td></tr>')
    parts.append('</table><h3>Evidence to keep</h3><ol>')
    for e in c['ev'].splitlines():parts.append('<li>'+esc(e.split('. ',1)[-1])+'</li>')
    parts.append('</ol></article>')
    md += ['\n## '+c['t']+'\n\n'+c['pre']+'\n\n| Procedure | Expected result |\n|---|---|']
    md += ['| '+p.replace('|','\\|')+' | '+e.replace('|','\\|')+' |' for p,e in zip(proc,exp)]
    md += ['\nEvidence:\n\n'+c['ev']+'\n']
parts.append('''<script>document.getElementById('find').addEventListener('input',function(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!a.textContent.toLowerCase().includes(this.value.toLowerCase());if(!a.hidden)n++});document.getElementById('count').textContent=n+' cases'});</script></html>''')
for dest in [ROOT/'output/Portal-71-manual-QA-guide.html',ROOT/'output/console-update/Portal-71-manual-QA-guide.html']:
    dest.write_text('\n'.join(parts),encoding='utf-8')
(ROOT/'output/Portal-71-manual-QA-guide.md').write_text('\n'.join(md),encoding='utf-8')
print('Published 71 current definitions with matched steps/results and evidence lists.')
