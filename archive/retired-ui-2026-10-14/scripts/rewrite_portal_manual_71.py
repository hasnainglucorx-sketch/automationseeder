"""Plain-language QA instructions for the previously identified 63+8 cases.

Only definitions change. Fixtures, credentials and execution results do not.
"""
import datetime as dt
import json
import re
import runpy
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'output/console-update/PRT-0702-cases.json'
MANIFEST=json.loads((ROOT/'output/portal-fixtures/fixture-manifest.json').read_text(encoding='utf-8'))
FIX={x['alias']:x for x in MANIFEST['fixtures']}
H=FIX['QA-PORTAL-HISTORY-01']
ANCHOR=dt.date.fromisoformat(H['anchor'])
def day(n): return (ANCHOR-dt.timedelta(days=n)).isoformat()
def numbered(items): return '\n'.join(f'{n}. {v}' for n,v in enumerate(items,1))
U={}
SUPPORT='QA step and evidence guide'
BASE='QA-PORTAL-HISTORY-01 is available through the controlled credential source. Patient Portal address: https://frontend.grxdiscovery.link/Overview. The account uses mg/dL. Expected fixture times use Europe/London.'
DATE_GATE=f'The saved History fixture anchor is {H["anchor"]}. Rolling-preset cases require a fixture verified for the test date and matching expected tables. An old fixture is a setup blocker, not a Portal failure. The setup owner must refresh and read back the fixture; changing the displayed date alone is not a refresh.'
VALUE_RULE='Compare each number after rounding the expected value to the decimal places displayed on the page. Write expected and actual values side by side. A missing required value is a failure; an inaccessible numeric chart value needs an approved data view before its numeric accuracy can be judged.'

def put(cid,title,pre,pairs,evidence,gate=False):
    pairs=list(pairs)
    if gate:
        pairs.insert(0,(f'In this console, open Test Assets and expand QA-PORTAL-HISTORY-01. Compare its anchor ({H["anchor"]}) with the test date. If the dates differ, stop and set Blocked: "History fixture needs refresh".',
                        'The fixture anchor and test date match, and the refreshed expected tables are available. Otherwise no glucose comparison is attempted.'))
        pre+=' '+DATE_GATE
    ev=[f'Create an evidence folder named {cid}. Include the test date, Portal build, browser/version, account alias and actual outcome in the execution note.']
    ev += [f'{cid}-E{i:02d}: {item}' for i,item in enumerate(evidence,1)]
    ev += ['For any failed step, include the step number, expected result, actual result and a screenshot of the problem. For a blocked step, name the missing item. Do not include passwords, cookies or access tokens in evidence.']
    U[cid]={'t':cid+' — '+title,'pre':pre,'proc':numbered([p for p,e in pairs]),'exp':numbered([e for p,e in pairs]),'ev':numbered(ev)}

def login(page='Overview'):
    return (f'Sign in as QA-PORTAL-HISTORY-01 and open {page}.',f'{page} belongs to QA-PORTAL-HISTORY-01; no other Patient is selected.')

LABELS={'latest_mg_dl':'Latest glucose','average_mg_dl':'Average glucose','minimum_mg_dl':'Lowest glucose','maximum_mg_dl':'Highest glucose',
 'below_70_percent':'Below range %','in_70_180_percent':'In range %','above_180_percent':'Above range %',
 'severe_low_percent':'Severe Low %','low_percent':'Low %','high_percent':'High %','urgent_high_percent':'Urgent High %',
 'sd_population_mg_dl':'Population SD','cv_population_percent':'CV %','mean_absolute_deviation_mg_dl':'Mean absolute deviation',
 'device_usage_percent':'CGM usage %','gmi_percent':'GMI %','adag_estimated_a1c_percent':'ADAG estimated A1c %'}
CORE=['latest_mg_dl','average_mg_dl','minimum_mg_dl','maximum_mg_dl']
BANDS=['severe_low_percent','low_percent','in_70_180_percent','high_percent','urgent_high_percent']
ADV=['sd_population_mg_dl','cv_population_percent','mean_absolute_deviation_mg_dl']
def vals(days,keys):
    row=H['ranges'][f'{days}_days']
    return '; '.join(f'{LABELS[k]} = {row[k]}' for k in keys)+'.'

def metrics(cid,title,page,days,keys,extra=''):
    pairs=[login(page),(f'Set Range A to {days} days.' if page=='Compare' else f'Select {days} days.',f'The page shows {days} days as the selected period.'),
        ('Compare these values one at a time with the matching Test Assets row: '+', '.join(LABELS[k] for k in keys)+'.', vals(days,keys)+' '+VALUE_RULE)]
    if extra:pairs.append(('Check the formula label or the approved calculation note supplied with this run.',extra))
    put(cid,title,BASE+' The matching numeric reference table is available. Formula-specific checks require a confirmed formula; a missing definition means Blocked.',pairs,[f'Screenshot showing {page}, account identity and the selected {days}-day period.',
        'Screenshots of all values being compared, with the corresponding Test Assets row.',
        'A written expected/actual comparison for every named metric; include units and decimal places.'],True)

# Authentication and ordinary profile work.
put('PAT-AUTH-002','Portal data removal and sign-in session behavior',
    'QA-PORTAL-HISTORY-01 is available. The supported desktop browser has site-data controls for individual domains. The protected address is https://frontend.grxdiscovery.link/Overview.',[
    ("Sign in as QA-PORTAL-HISTORY-01 and open https://frontend.grxdiscovery.link/Overview.",'Overview is visible for the correct Patient.'),
    ('In the browser site-data controls, remove local storage, session storage, IndexedDB and cache for frontend.grxdiscovery.link only. Leave keycloak.dev.platform.glucorx.co.uk cookies unchanged.','Only Portal storage is cleared; the separate sign-in session cookies remain.'),
    ('Open https://frontend.grxdiscovery.link/Overview again.','Overview opens for the same Patient without requesting the email and password again.'),
    ('Remove cookies and site data for keycloak.dev.platform.glucorx.co.uk using the browser site-data controls.','The separate sign-in session data is cleared.'),
    ('Remove frontend.grxdiscovery.link storage and cache again.','The Portal data created after the previous visit is cleared.'),
    ('Open https://frontend.grxdiscovery.link/Overview again.','The sign-in page appears before protected Patient content. A new sign-in is required.')],
    ['Overview before clearing data; mask unrelated identity details.','Selected domain and data categories for each clearing action; never show cookie values.','Overview after Portal-only clearing and the sign-in page after clearing both domains.'])
put('PAT-HOME-009','Save and restore an editable Patient profile field',BASE+' A QA-provided field choice and valid replacement value are required. Given name, family name and date of birth are excluded. The original value must be restorable. If no supported field/value is supplied, this case is Blocked.',[
    login(),('Open Profile.','The profile belongs to the signed-in Patient and matches the profile in Test Assets.'),
    ('Select Edit Profile.','Editable fields can be distinguished from disabled/read-only fields.'),
    ('Write the supplied field name and its original value in the execution note.','The exact original value is available for cleanup.'),
    ('Enter the supplied valid replacement in that field only.','Only the intended field changes in the form.'),
    ('Select Save.','The save succeeds without changing read-only fields.'),
    ('Reopen Profile.','The replacement value is still shown.'),
    ('Restore the original value using Edit Profile and Save.','The original value is saved again.'),
    ('Reopen Profile once more.','The original value is visible and the test leaves no profile change behind.')],
    ['Original profile and a list of editable/read-only fields.','Replacement after Save and reopening.','Restored value after reopening; include the exact test field and replacement in the note.'])

# Controlled failure tests: ordinary QA operates a prepared, scoped rule.
FAULTS={}
def fault(cid,title,page,requests,affected,status='500',account='QA-PORTAL-HISTORY-01',baseline='The page has its normal data.',gate=False):
    rules=[f'{cid}-{i}' for i in range(1,len(requests)+1)]
    FAULTS[cid]={'rule_names':rules,'request_names':requests,'mode':status,
        'scope':'Only the exact QA request URL and method confirmed during setup; no server-side changes.',
        'provisioned':False}
    pre=f'{account} is available and {page} can load normally. A setup owner must provide disabled browser rules '+', '.join(rules)+', matched to '+', '.join(requests)+'. The rules must simulate '+('a cancelled network request' if status=='abort' else 'HTTP '+status)+' locally. Rule details and enable/disable controls must be demonstrated to the tester. Without these prepared rules, the case is Blocked. '
    if account.startswith('QA-PORTAL-HCP'):pre+='The HCP has active shares from QA-PORTAL-HISTORY-01 and QA-PORTAL-SECONDARY-01. '
    pairs=[(f'Sign in as {account} and open {page}.',baseline),
           ('Take a screenshot of the normal page before enabling a rule.','The baseline shows the account, selected date range and the data that should return after recovery.')]
    for rule,request in zip(rules,requests):
        pairs.extend([(f'Enable only the prepared rule {rule} for {request}.',f'The rule is enabled for {request}; all other failure rules remain off.'),
          (f'Reload {page} or repeat the page-opening action used for the baseline.',f'The intended {request} '+('is cancelled' if status=='abort' else 'returns HTTP '+status)+f'. The page clearly shows that {affected} could not load, remains usable and does not show a successful empty state or old data as a successful refresh. Unaffected sections remain usable.'),
          (f'Disable rule {rule}.','No failure rule for this case remains enabled.'),
          (f'Reload {page} again.','Normal data returns for the same account and range without an unnecessary new sign-in.')])
    put(cid,title,pre,pairs,['Normal page with account and range.','For each rule: its name and scope, the failed request status and the stable error state. Mask credentials and tokens.','Recovered page and proof that all rules are off.'],gate)

fault('PAT-HOME-004','Overview statistics recover after a failed request','Overview',['GetGlucoseStatistics'],'the glucose statistics',baseline='The 7-day period is selected and Latest, Average, Lowest and Highest values are populated.',gate=True)
fault('PAT-ERROR-001','History handles event and session request failures','History',['ListEvents','ListSessions'],'the affected events or sessions',baseline='A date range containing the supplied events and sessions is selected; those items and glucose readings are visible.')
fault('PAT-ERROR-002','Sharing recovers after a failed list request','Share Management',['ListGrants','ListIncomingGrants'],'the affected sharing list',baseline='The setup sheet lists at least one known outgoing and incoming relationship; both are visible.')
fault('PAT-ERROR-003','Settings recover after a failed request','Settings',['GetPatientSettings'],'Patient settings')
fault('PAT-ERROR-004','Calibration failure leaves other History data usable','History',['ListCalibrations'],'calibration data',baseline=f'The custom date {day(3)} is selected; the 09:30 calibration, readings and any expected events are visible in Europe/London time.')
fault('PAT-EDGE-004','The glucose page recovers after a service-unavailable response','Overview',['QueryReadings'],'glucose readings',status='503',baseline='A populated period is selected and its readings and date range are visible.')
fault('PAT-EDGE-005','Overview stays usable when a Patient request is cancelled','Overview',['ListPatients'],'Patient context',status='abort')
fault('HCP-LIST-004','The HCP Patient List recovers after a request failure','Patient List',['ListPatients'],'the Patient List',account='QA-PORTAL-HCP-01',baseline='Total is 2; QA Portal History and QA Portal Secondary each appear once.')
fault('HCP-DATA-019','Shared Patient data recovers after a request failure','QA Portal History from Patient List',['QueryReadings'],'shared Patient glucose data',account='QA-PORTAL-HCP-01',baseline='The page identifies QA Portal History and shows the historical-data notice, chart and calculated sections for a populated range.')
U['HCP-DATA-019']['exp']=U['HCP-DATA-019']['exp'].replace('The page clearly shows that shared Patient glucose data could not load','The page keeps the correct Patient identity and shows “Failed to fetch patient shared data” and “No glucose data available”')
FAULTS['PAT-DATA-ERROR-001']={'rule_names':['PAT-DATA-ERROR-001-1'],'request_names':['QueryReadings'],'mode':'remove glucoseCentiMgDl from one nonempty reading','provisioned':False}
put('PAT-DATA-ERROR-001','History does not turn a missing glucose value into a real reading',BASE+' A disabled local response rule PAT-DATA-ERROR-001-1 is required. The setup owner must identify one QueryReadings response item, its timestamp/index and glucoseCentiMgDl field, and provide a rule removing only that field. Its timestamp and index must remain unchanged. A populated custom date and exact target reading must be written on the setup sheet. No prepared rule or target means Blocked.',[
    login('History'),('Select the custom date named on the setup sheet.','The target reading appears with its original valid glucose value.'),
    ('Take a screenshot of the target reading.','The baseline includes its date, time, value and unit.'),
    ('Enable PAT-DATA-ERROR-001-1.','The rule affects one reading only; no server data changes.'),
    ('Reload History for the same date.','The modified response is used by the page.'),
    ('Find the target timestamp.','The missing value is not shown as zero or a plausible glucose reading. It has an unavailable/error indication, or is omitted with a clear data-quality indication; other valid readings remain usable.'),
    ('Disable PAT-DATA-ERROR-001-1.','The rule is off.'),
    ('Reload the same History date.','The original valid reading returns.')],['Target reading before the fault.','Sanitized response showing the missing field and the affected History point/row.','Recovered reading and disabled rule.'])

# Offline helper coverage is explicit and independent of a live Portal screen.
put('PAT-OGP-CALC-001','Calculate hourly median and percentiles','No sign-in is required. The controlled one-hour sample contains 60 values: three at 50, six at 63, forty-two at 156 and nine at 240 mg/dL. Percentile position uses 1 + 59 × p, with linear interpolation between adjacent positions. A calculator and a blank calculation note are available.',[
    ('Write the four values and their counts in ascending order.','Counts total 60; positions 1–3 are 50, 4–9 are 63, 10–51 are 156 and 52–60 are 240.'),
    ('Find values at positions 30 and 31.','Both values are 156 mg/dL.'),
    ('Add those two values and divide by 2.','The median is 156 mg/dL.'),
    ('Calculate the positions for P10, P25, P75 and P90 using p = 0.10, 0.25, 0.75 and 0.90.','Positions are 6.9, 15.75, 45.25 and 54.1. The adjacent values around each position are identical, giving 63, 156, 156 and 240 mg/dL respectively.'),
    ('Compare all five results with the 7-day hourly Test Assets table.','P10/P25/P50/P75/P90 are 63/156/156/156/240 mg/dL. This checks the helper calculation only, not a live chart.')],['The count/position calculation and median and percentile arithmetic.','The matching hourly percentile table row.'])
put('PAT-CALC-001','Check which readings belong inside a date range','No sign-in is required. All times are Europe/London. Requested range: 2026-10-01 00:00 through 2026-10-06 23:59 inclusive. Supplied samples: 2026-09-30 23:59; 2026-10-01 00:00; 2026-10-03 12:00; 2026-10-06 23:59; 2026-10-07 00:00.',[
    ('Write each supplied timestamp in a five-row table.','All five supplied readings have a separate row.'),
    ('Mark each timestamp Included or Excluded using the stated boundaries.','The first and fifth timestamps are Excluded; the second, third and fourth are Included.'),
    ('Check the timestamps exactly on the start and end.','Both boundary readings are Included. There are three included readings.')],['The five-row Included/Excluded calculation with the stated start/end and time zone.'])
put('PAT-CALC-002','Calculate latest lowest highest and average from unsorted readings','No sign-in is required. A calculator is available. Supplied readings on one day, intentionally unsorted: 10:03 = 180; 10:00 = 100; 10:04 = 120; 10:01 = 70; 10:02 = 240 mg/dL.',[
    ('Sort the five readings by time on a calculation sheet.','Order is 10:00=100, 10:01=70, 10:02=240, 10:03=180, 10:04=120.'),
    ('Choose the reading with the latest timestamp.','Latest is 120 mg/dL at 10:04; it is not the last item in the supplied unsorted list.'),
    ('Find the smallest and largest glucose values.','Lowest is 70 mg/dL; highest is 240 mg/dL.'),
    ('Add the five values and divide by five.','Total is 710 mg/dL; average is 142 mg/dL.')],['Original unsorted list, sorted list and all four calculations.'])
put('PAT-TIR-001','Calculate below in and above range percentages','No sign-in is required. Test Assets supplies 8640 readings: 1296 below 70, 6048 from 70 through 180 inclusive, and 1296 above 180 mg/dL. A calculator is available.',[
    ('Calculate 1296 divided by 8640, multiplied by 100.','Below range is 15.0%.'),
    ('Calculate 6048 divided by 8640, multiplied by 100.','In range is 70.0%.'),
    ('Calculate the above-range percentage using the same method.','Above range is 15.0%.'),
    ('Add the percentages and identify where values of exactly 70 and 180 belong.','Total is 100.0%; both boundaries belong to In range.')],['All arithmetic, the source counts and the boundary classification.'])
put('PAT-UNIT-001','Convert the supplied glucose values to mmol/L','No sign-in is required. A calculator is available. Input values in mg/dL: 45, 50, 63, 70, 100, 120, 140, 154, 156, 180, 200, 240, 300.',[
    ('For each input, divide by 18.0182.','There is one calculated mmol/L value for every input.'),
    ('Round each result to one decimal place.','Results in the same order are 2.5, 2.8, 3.5, 3.9, 5.5, 6.7, 7.8, 8.5, 8.7, 10.0, 11.1, 13.3 and 16.6.'),
    ('Compare your 13 results with the expected sequence.','All 13 match; any mismatch is listed individually.')],['A 13-row sheet showing input, division result and one-decimal result.'])

# Chart and source comparisons.
def ogp(cid,days,all_hours):
    hours=[f'{i:02}:00' for i in range(24)] if all_hours else ['00:00','03:00','10:00','15:00','23:00']
    put(cid,f'Compare {days}-day OGP values with the hourly reference table',BASE+' The chart tooltip or accessible table must expose numeric P10, P25, P50, P75 and P90 values'+(' and bucket reading counts' if all_hours else '')+'. If it does not, QA needs an approved numeric data view; visual guessing cannot establish numeric accuracy.',[
        login('OGP'),(f'Select {days} days.',f'The selected period is {days} days.'),
        (f'In console Test Assets, expand QA-PORTAL-HISTORY-01 and find Expected OGP percentiles — {days} days.','The table lists Local hour, n, P10, P25, P50, P75 and P90.'),
        ('Read the chart/table at each of these hours: '+', '.join(hours)+'.','Each required local-hour bucket is identifiable.'),
        ('Write expected and actual P10, P25, P50, P75 and P90 for each checked hour'+(' and its reading count' if all_hours else '')+'.',VALUE_RULE+' P50 is the median, P25–P75 the inner band and P10–P90 the outer band.')],
        ['Selected range and chart legend.','Hourly expected/actual table for every specified hour; include numeric tooltip/table screenshots.'],True)
ogp('PAT-OGP-CALC-002',7,False);ogp('PAT-OGP-DATA-002',7,True);ogp('PAT-OGP-DATA-004',90,True)
put('PAT-OGP-DATA-003','OGP explains when there is too little data','QA-PORTAL-SPARSE-01 is available. Its fixture must be verified for the test date, with one reading at noon three days before that date. The saved sparse anchor is '+FIX['QA-PORTAL-SPARSE-01']['anchor']+'.',[
    ('Check the sparse fixture anchor in console Test Assets against the test date. Stop with Blocked if it is old.','The single reading will be inside the current 7-day range; an old sparse dataset is not used.'),
    ('Sign in as QA-PORTAL-SPARSE-01.','The sparse Patient is selected.'),
    ('Open OGP.','OGP opens without using another Patient’s data.'),
    ('Select 7 days.','The page gives a clear insufficient-data indication and does not present the single reading as a reliable percentile band.')],['Sparse fixture date and one-reading summary.','OGP with selected 7-day period and its sufficiency message.'])
for cid,n in [('PAT-CALC-004',7),('PAT-CALC-005',15),('PAT-CALC-006',30),('PAT-CALC-007',90),('PAT-OVERVIEW-DATA-005',30),('PAT-OVERVIEW-DATA-006',90)]:
    metrics(cid,f'Compare {n}-day Overview summary values','Overview',n,CORE+BANDS+ADV+['device_usage_percent'] if cid.startswith('PAT-OVERVIEW') else CORE)
for cid,key in [('PAT-OVERVIEW-DATA-002','average_mg_dl'),('PAT-OVERVIEW-DATA-003','minimum_mg_dl'),('PAT-OVERVIEW-DATA-004','maximum_mg_dl')]:
    pairs=[login()]
    for n in [7,15,30,90]:
        pairs.extend([(f'Select {n} days.',f'{n} days is selected.'),(f'Compare {LABELS[key]} with the {n}-day Test Assets row.',vals(n,[key])+' '+VALUE_RULE)])
    put(cid,f'Check {LABELS[key].lower()} for each date range',BASE,pairs,['One screenshot for each of the four periods showing the range and value.','Four-row expected/actual comparison.'],True)
for cid,key in [('PAT-OVERVIEW-DATA-011','sd_population_mg_dl'),('PAT-OVERVIEW-DATA-012','cv_population_percent'),('PAT-OVERVIEW-DATA-013','mean_absolute_deviation_mg_dl'),('PAT-OVERVIEW-DATA-017','device_usage_percent')]:
    metrics(cid,'Check '+LABELS[key].lower(),'Overview',7,[key], 'The approved calculation definition must match the reference table. If the definition differs or is unavailable, flag the formula decision before judging the number.')
for cid,page in [('PAT-REPORT-DATA-004','Assessment Report'),('PAT-COMPARE-DATA-004','Compare')]:
    metrics(cid,'Check the glucose range percentages',page,7,BANDS)
metrics('PAT-TIR-002','Check the stored glucose thresholds and range percentages','Assessment Report',7,['below_70_percent','in_70_180_percent','above_180_percent'])
U['PAT-TIR-002']['pre']+=' Stored thresholds must be verified as Low 70 and High 180 mg/dL before execution.'
metrics('PAT-COMPARE-DATA-003','Check variability calculations in Compare','Compare',7,ADV,'Population SD is the supplied oracle; a different required SD formula needs an approved matching oracle before pass/fail.')
metrics('PAT-COMPARE-DATA-005','Check 90-day values in Compare','Compare',90,CORE+BANDS+ADV+['device_usage_percent'])
for cid,page in [('PAT-REPORT-DATA-005','Assessment Report'),('PAT-OVERVIEW-DATA-014','Overview')]:
    put(cid,'Check estimated A1c against the specified formula',BASE+' The run setup must name the expected formula (GMI or ADAG) and its approved label. A formula decision cannot be inferred by choosing whichever number matches. Missing formula means Blocked.',[
        login(page),('Select 7 days.','The 7-day period is selected.'),
        ('Read the A1c label and compare it with the formula specified for this run.','The label identifies the specified formula.'),
        ('Compare the value with the matching formula column in Test Assets.',vals(7,['gmi_percent','adag_estimated_a1c_percent'])+' Only the preselected formula is judged. '+VALUE_RULE)],
        ['Formula/setup reference.','A1c label and number with the selected period.','Expected/actual value and rounding.'],True)
metrics('PAT-REPORT-DATA-006','Check Assessment Report advanced calculations','Assessment Report',7,['average_mg_dl']+ADV+['device_usage_percent'])
U['PAT-REPORT-DATA-006']['pre']+=' The supplied oracle uses population SD. The estimated A1c formula and label must be supplied before that additional metric can be judged.'
U['PAT-REPORT-DATA-006']['proc']+='\n'+str(len(U['PAT-REPORT-DATA-006']['proc'].splitlines())+1)+'. Compare the estimated A1c label and number with the formula specified for this run.'
U['PAT-REPORT-DATA-006']['exp']+='\n'+str(len(U['PAT-REPORT-DATA-006']['exp'].splitlines())+1)+'. '+vals(7,['gmi_percent','adag_estimated_a1c_percent'])+' The specified formula label and its rounded value match; missing formula approval leaves this part Blocked.'
for cid,a,b in [('PAT-COMPARE-DATA-001',7,15),('PAT-COMPARE-DATA-002',15,30)]:
    put(cid,f'Compare the {a}-day and {b}-day populations separately',BASE,[login('Compare'),
        (f'Set Range A to {a} days.',f'Range A shows {a} days.'),(f'Set Range B to {b} days.',f'Range B shows {b} days.'),
        ('Compare the latest, average, lowest and highest values in Range A with its Test Assets row.',vals(a,CORE)+' '+VALUE_RULE),
        ('Compare the same four values in Range B with its Test Assets row.',vals(b,CORE)+' '+VALUE_RULE),
        ('Compare any remaining required shared metrics using the approved field list for this build and the corresponding reference rows.','Each required metric uses its own panel’s population; a missing field list is identified as a coverage gap, not silently ignored.')],
        ['Both panels with account and selected ranges.','Separate expected/actual tables for A and B; include the required field list.'],True)

# Historical examples use explicit dates, not unexplained D0 offsets.
put('PAT-HISTORY-DATA-001','Check five History readings and a calibration',BASE+f' The retained fixture date is {day(3)}. Historical access to this day is required.',[
    login('History'),(f'Select a custom date range with start and end both {day(3)}.',f'Only {day(3)} is selected in Europe/London time.'),
    ('Read the values at 00:00, 00:03, 00:09, 00:51 and 00:59.','Values are 50, 63, 156, 240 and 240 mg/dL respectively.'),
    ('Find the calibration at 09:30.','One calibration has a reference value of 156 mg/dL.')],
    ['Custom date and Patient identity.','All five timestamp/value pairs and the calibration details.'])
put('PAT-HISTORY-CAL-001','Check calibration details and date filtering',BASE+f' The retained calibration is {day(3)} at 09:30 Europe/London, 156 mg/dL. No calibration exists on {day(0)} in this fixture.',[
    login('History'),(f'Select the custom date {day(3)}.',f'The selected date contains the controlled calibration.'),
    ('Open the 09:30 calibration details.','The Patient, timestamp and 156 mg/dL reference match Test Assets; the calibration appears once.'),
    (f'Select the custom date {day(0)}.',f'The {day(3)} calibration is not shown for {day(0)}.')],['Calibration details and first selected date.','Second selected date with the calibration absent.'])
put('PAT-HISTORY-005','Read all History data without page or sort controls',BASE+' At least two screens of historical data are available in a selectable 90-day range.',[
    login('History'),('Select 90 days.','The range is selected and historical data is available.'),
    ('Inspect the controls above and below the data.','No page-number, next-page, previous-page or sort controls are shown.'),
    ('Scroll through the available History data to its end.','Data remains usable through the implemented view; no undocumented paging action is required.')],['Controls at top and bottom of History.','A short screen capture or screenshots demonstrating scrolling to the last available data.'])
put('PAT-HISTORY-004','Check History preset ranges and a custom date',BASE,[login('History'),
    ('Select 24 hours and note the current Europe/London date/time.','The selected range is rolling 24 hours; readings older than its boundary are not shown.'),
    ('Select 7 days.',f'For the verified fixture, populated days run from {day(6)} through {day(1)}; {day(7)} is excluded.'),
    ('Select 15 days.',f'The high marker {day(10)} 03:00 and low marker {day(12)} 15:00 are included.'),
    ('Select 30 days.','Both controlled markers remain within the selected range.'),
    ('Select 90 days.','Both controlled markers remain within the selected range.'),
    (f'Select a custom range containing only {day(3)}.',f'Only that day is shown, including the 09:30 calibration of 156 mg/dL.')],
    ['One screenshot per selected range, showing its dates and first/last visible readings.','Both marker readings and the custom-day calibration.','The exact execution time and rolling-24-hour boundary.'],True)
put('PAT-HISTORY-DATA-003','Check daily first last lowest and highest readings',BASE,[login('History'),
    ('Select 7 days.','The verified 7-day fixture is selected.'),
    ('For each of the six populated days, write its first time, last time, lowest and highest value.',f'Days {day(6)} through {day(1)} each start at 00:00, end at 23:59, have lowest 50 and highest 240 mg/dL. No extra day is included.')],['Selected range and the six-day expected/actual table.','Screenshots supporting each day’s first/last and min/max values.'],True)
for cid,page in [('PAT-COMPARE-DATA-008','Compare'),('PAT-OVERLAY-DATA-001','Overlays')]:
    pairs=[login(page),('Select 7 days.',f'Only populated dates {day(6)} through {day(1)} appear.')]
    if page=='Compare':pairs += [('Switch from Overlay mode to History mode.','Both modes use the same selected period.'),('Compare the dates and each day’s first/last and minimum/maximum.',f'The same six dates appear; each runs from 00:00 to 23:59 with a 50–240 mg/dL range.')]
    else:pairs += [('Select 15 days.',f'Dates {day(14)} through {day(8)} are added; {day(7)} remains empty.'),('Find the controlled high marker.',f'The marker is 300 mg/dL on {day(10)} from 03:00 to 03:59. No date older than {day(14)} appears.')]
    put(cid,'Check the dates included in '+page,BASE,pairs,['Both views/ranges with date labels.','Daily values or high-marker timestamp/value, as required by the steps.'],True)
put('PAT-DIDO-005','Check the rolling last 24 hours in History',BASE+' A freshly verified fixture must contain readings yesterday and none today. The tester must use Europe/London time for the range calculation.',[
    login('History'),('Write the current Europe/London date and time, then subtract exactly 24 hours.','Both the execution time and lower boundary are written in the note.'),
    ('Select 24 hours.','The Portal applies the rolling period.'),
    ('Inspect the earliest and latest readings against the written boundary.','No reading older than the lower boundary is included and no readings are invented for the empty part of today.')],['Execution time and calculated boundary.','Selected 24-hour period with earliest/latest readings and its empty portion.'],True)

for cid,page in [('PAT-EXPORT-DATA-001','Assessment Report'),('PAT-EXPORT-DATA-002','Assessment Report')]:
    put(cid,'Compare a downloaded report with its source values',BASE+' Browser downloads are allowed and a PDF reader is available.',[
        login(page),('Select 7 days.','The 7-day period is visible.'),
        ('Download the report PDF once.','One new PDF is saved without an error.'),
        ('Open the downloaded PDF.','The file opens and identifies the correct Patient, period and mg/dL unit.'),
        ('Compare the PDF’s latest, average, minimum and maximum with Test Assets.',vals(7,CORE)+' '+VALUE_RULE),
        ('Compare the PDF’s range percentages with Test Assets.',vals(7,BANDS)+' '+VALUE_RULE),
        (f'Check plotted points on {day(3)} at 00:00, 00:09 and 00:51 where the PDF exposes a numeric value.','Values are 50, 156 and 240 mg/dL. If exact chart values cannot be read, document that limitation and obtain an approved numerical check; do not estimate from pixels.')],
        ['The actual downloaded PDF, named with the case ID and test date.','Portal selected range before download.','Expected/actual comparison, page numbers and exact numerical chart evidence or limitation.'],True)

events=[(day(3)+' 07:00','sickness','sickness note'),(day(2)+' 18:00','activity','30-minute moderate walking'),(day(1)+' 08:00','carbohydrate','40 g'),(day(1)+' 08:05','insulin','2.0-unit bolus')]
for cid,page in [('PAT-EVENT-DATA-001','History'),('PAT-OVERVIEW-DATA-016','Overview')]:
    pairs=[login(page),('Select '+('15' if page=='History' else '7')+' days.','The period contains the four controlled events.')]
    if page=='Overview':pairs.append(('Open Events & Notes.','The event area is visible for the selected Patient and period.'))
    for when,kind,value in events:pairs.append((f'Find the {kind} event at {when} Europe/London.',f'It appears once with {value}; no timestamp or Patient mismatch.'))
    pairs.append(('Compare event order with their timestamps.','Events are in a consistent time order and none of the four is duplicated.'))
    if page=='History':pairs.append(('Compare session count, boundaries and status with the session setup sheet supplied for this run.','Every required session matches the sheet. If session source data is missing, this part is Blocked; checking four events alone does not complete the original session coverage.'))
    put(cid,'Check event details'+(' and session data' if page=='History' else ' on Overview'),BASE+(' A verified session sheet with session count, start/end and expected status is required.' if page=='History' else ''),pairs,
        ['Each event’s date/time, type and details.','Selected range and event ordering.' ]+(['Session source sheet and expected/actual session comparison.'] if page=='History' else []),True)
put('PAT-OVERVIEW-DATA-015','Check reading count dates and data-sufficiency text',BASE+' Expected cadence/completeness wording must be supplied with the approved build criteria; without it the wording check remains Blocked.',[
    login(),('Select 7 days.','The 7-day period is selected.'),
    ('Read the count and populated dates.','There are 8640 readings across six populated days; the empty anchor day is not described as populated.'),
    ('Copy the exact cadence/completeness message into the execution note.','The message agrees with the supplied acceptance wording and the actual count/date span; missing criteria are identified as Blocked.')],['Count, dates and sufficiency wording in one screenshot where possible.','The approved wording reference and expected/actual comparison.'],True)
put('PAT-OVERVIEW-DATA-018','Check high and low marker positions in Daily Patterns',BASE,[login(),('Select 15 days.','The 15-day period is selected.'),
    ('Open Daily Patterns.','The pattern view belongs to the selected period.'),
    (f'Find {day(10)} at 03:00–03:59.', 'The high marker is 300 mg/dL at that local hour.'),
    (f'Find {day(12)} at 15:00–15:59.', 'The low marker is 45 mg/dL at that local hour.')],['Selected range and both markers, with date/time and numeric value visible.'],True)
put('PAT-OVERVIEW-DATA-019','Check daily time-in-range percentages',BASE,[login(),('Select 7 days.','The verified 7-day period is selected.'),
    ('Open Time in Range by Day.','The six populated days are identifiable.'),
    ('Compare below, in and above range for each day.','Each populated day shows 15%, 70%, 15% respectively after rounding; the empty anchor day is not presented as populated.')],['All six daily bars/rows with numeric percentages.','Six-row expected/actual table.'],True)
put('PAT-OVERVIEW-DATA-020','Check insufficient data and populated AGP states','QA-PORTAL-SPARSE-01 and QA-PORTAL-HISTORY-01 are available. Both fixtures must have the same current test-date anchor. The approved sufficiency rule is required; the sparse dataset has one reading and the History dataset supplies 15 days of minute data.',[
    ('Check both fixture anchors against the test date in console Test Assets.','Both dates match. Otherwise this case stops as Blocked for fixture refresh.'),
    ('Sign in as QA-PORTAL-SPARSE-01.','The sparse Patient is selected.'),
    ('Open Overview and select 7 days.','A clear insufficient-data indication appears; a single reading is not shown as a reliable AGP.'),
    ('Log out using the Portal logout control and its confirmation.','The sign-in page appears.'),
    ('Sign in as QA-PORTAL-HISTORY-01.','The History Patient is selected.'),
    ('Open Overview and select 15 days.','The populated AGP state follows the approved sufficiency rule; neither sparse Patient data nor its message is reused.')],['Both fixture anchors.','Sparse and populated AGP states with Patient identity, ranges and sufficiency messages.'])

# Sharing, time zones and domain inspection.
put('PAT-SHARE-007','Check own-email and duplicate follower invitations',BASE+' QA-PORTAL-SECONDARY-01 must already be an active follower. The approved expected own-email behavior must be supplied; without that decision the own-email part remains Blocked.',[
    login('Share Management'),('Open Followers.','QA-PORTAL-SECONDARY-01 appears once as an existing follower.'),
    ('Open Invite and enter QA-PORTAL-HISTORY-01’s own email from the credential source.','The entered address is the signed-in Patient’s address.'),
    ('Select Send Invite once.','The response and any created row match the supplied own-email acceptance rule. No rule means this part cannot be given Pass.'),
    ('Open Invite and enter the existing QA-PORTAL-SECONDARY-01 follower email.','The address matches the existing follower.'),
    ('Select Send Invite once.','No second follower relationship is created; the existing one remains usable.')],['Follower list before and after each attempt.','The exact message after each Send Invite and the own-email acceptance reference.'])
tz=FIX['QA-PORTAL-TIMEZONE-01']['controlled_readings']
put('PAT-TIMEZONE-001','Check the same readings in UTC London and Karachi','QA-PORTAL-TIMEZONE-01 is available. The ten timestamp samples are listed in console Test Assets. Historical access to every listed date and permission to change the test computer’s time zone are required.',[
    ('Write the test computer’s original time zone in the execution note.','The original zone is available for cleanup.'),
    ('Set the computer time zone to UTC.','The test computer uses UTC.'),
    ('Sign in as QA-PORTAL-TIMEZONE-01 and open History.','The correct Patient is selected.'),
    ('Open a custom date range containing each of the ten supplied timestamps and copy the displayed date/time to a table.','Each value matches the UTC timestamp in Test Assets.'),
    ('Set the computer time zone to Europe/London, then reload History.','The page has refreshed in the London zone.'),
    ('Repeat the timestamp comparison.','Winter values have UTC offset zero, summer values offset +01:00. Clock-change samples keep their source order without missing or duplicate readings.'),
    ('Set the computer time zone to Asia/Karachi, then reload History.','The page has refreshed in the Karachi zone.'),
    ('Repeat the timestamp comparison.','Each timestamp is UTC plus five hours, with the correct next-day date where midnight is crossed. Source order and count remain unchanged.'),
    ('Restore the computer’s original time zone from step 1.','The original zone is restored.')],['A ten-row table with source UTC, expected/actual London and expected/actual Karachi values.','Screenshots of winter, summer, midnight and clock-change samples.','Original and restored computer time zone.'])
put('PAT-DIDO-020','Check Patient data destinations and browser addresses',BASE+' Browser Developer Tools are available. The environment owner must confirm the service-domain list for this build: frontend.grxdiscovery.link, modapi.grxdiscovery.link, keycloak.dev.platform.glucorx.co.uk. Without that confirmation the external-destination check is Blocked.',[
    login(),('Open browser Developer Tools, select Network, and clear the request list.','A new request list is ready for this case.'),
    ('Visit Overview, History, Assessment Report, Share Management, Profile and Export one at a time.','The named pages can be inspected for the signed-in Patient.'),
    ('Check the address bar and browser history entries for those visits.','Patient identity, clinical values and access/refresh tokens are not present in page URLs/history.'),
    ('Inspect the destination domain of requests that carry Patient identity or clinical data.','Those requests use only the confirmed domain list; no unrelated external destination receives the data.'),
    ('Trigger a required-field validation error on a reversible form without completing a valid save.','A normal validation error is shown and no change is saved.'),
    ('Inspect destinations again for that error.','The error does not send protected information to an unapproved service.')],['Confirmed domain-list reference and visited page list.','Sanitized URL/domain comparison. Mask token, cookie and unnecessary personal values before attaching screenshots.','Validation message and its destination check.'])

# Performance measurements use visible completion, not an unrelated Network Load event.
put('PAT-PERF-001','Measure Overview loading with and without browser cache',BASE+' A supported desktop browser, stable agreed network, browser Network panel with Disable cache control and a timestamped screen capture are available. The build’s agreed timing limits are 2.5 seconds uncached and 1.5 seconds cached at p90. Timing starts at reload and ends when Overview’s required widgets finish drawing and the loading indicator clears. The run owner must confirm this completion definition before formal pass/fail.',[
    login(),('Write the browser/version, build, network conditions and required widget list in the evidence note.','The same conditions and completion definition will apply to all runs.'),
    ('In browser Developer Tools > Network, enable Disable cache.','Browser caching is disabled while the tools remain open.'),
    ('Capture ten Overview reloads, waiting for completion after each; write each elapsed time from the stated start to the stated end.','Ten uncached durations are available, in seconds.'),
    ('Turn Disable cache off and load Overview once to populate the cache.','The warm-up load is excluded from the timed sample.'),
    ('Capture ten normal reloads using the same completion rule.','Ten cached durations are available.'),
    ('Sort each group from fastest to slowest and select its ninth value.','That nearest-rank p90 is at most 2.5 seconds uncached and at most 1.5 seconds cached; results above a limit fail the agreed criterion.'),
    ('Return the browser cache option to its original state.','The browser is left with its original setting.')],['Timestamped captures supporting all twenty measured durations.','Two ten-row timing tables, sorted values and the selected p90s.','Environment details and approved completion/threshold reference.'])
put('PAT-PERF-003','Measure 15-day and 90-day Assessment Report rendering',BASE+' Timestamped screen capture or a browser performance tool is available. Timing starts at the range selection and ends when the Assessment Report chart and statistics finish drawing and its loading indicator clears. The agreed p90 limits are 3 seconds for 15 days and 5 seconds for 90 days. The run owner must confirm this completion definition and the timing tool before formal pass/fail.',[
    login('Assessment Report'),('Write the browser/version, build, network conditions and report completion definition.','All measurements use the same documented conditions.'),
    ('Select a different range, then capture selection of 15 days until completion. Repeat ten times, returning to the other range before each measured selection.','Ten independent 15-day render times are available.'),
    ('Repeat the same procedure for 90 days ten times.','Ten independent 90-day render times are available.'),
    ('Sort each ten-value group from fastest to slowest and take the ninth value.','15-day p90 is at most 3 seconds; 90-day p90 is at most 5 seconds. A value above its agreed limit fails.')],['Capture supporting the start/end of each sample.','Two timing tables, sorted times and p90 calculations.','Selected range, refreshed fixture date and environment/criterion reference.'],True)

# HCP profile tests: reset between invalid attempts, no unintended valid saves.
HCP='QA-PORTAL-HCP-01 is available through the controlled credential source. The HCP Portal Profile form is available. The field rules below are the current supporting test criteria; requirement-gap approval is separate. '
def hcp_start():return [('Sign in as QA-PORTAL-HCP-01 and open Profile.','The profile belongs to the HCP.'),('Open Edit Profile.','The edit form is visible.')]
def invalid_field(cid,title,field,samples,valid,expected):
    pairs=hcp_start()+[('Open browser Developer Tools, select Network and clear the request list.','The request list is ready to check whether an invalid submission sends an update.'),('Write the original values before changing the form.','Original values are available for cleanup.'),
        (f'Test these invalid inputs in {field}: {samples}. For each input, start with the original form, change only the field under test, clear the Network list and select Save. Keep other required fields valid.',f'Each input has its own validation message and no profile-update request. Test First Name and Last Name independently where both are named. If an invalid input saves, mark Fail and restore the original value before continuing.'),
        (f'Discard the invalid input and reopen the form. Test these valid inputs in {field}: {valid}. Move focus away after each input; do not select Save.',expected+'. This checks field acceptance only, not persistence.'),
        ('Close the form without saving.','No test value is intentionally saved.'),
        ('Reopen Profile.','The original profile is unchanged; any unexpected save is reported and restored using the original values.')]
    put(cid,title,HCP+' Other required fields must have valid values. Browser Network inspection must be available to confirm that rejected values send no profile update. Missing valid baseline means Blocked.',pairs,
        ['Original profile and each invalid input with its validation message.','Sanitized Network list showing no update for rejected inputs.','Valid field acceptance without Save and unchanged reopened profile.'])
invalid_field('HCP-PROFILE-UPDATE-003','Check HCP name length punctuation and blank values','First Name and Last Name separately','empty; Ab; three spaces; 51 uppercase A characters',"Anne-Marie and O'Neil, one field at a time",'Names from 3 through 50 characters with normal name punctuation are accepted by field validation')
invalid_field('HCP-PROFILE-UPDATE-005','Check HCP phone characters and length','Phone Number','abc; 1234#56789; 12345678; 1234567890123456; 123+456789','123456789, +123456789 and 123456789012345 in turn','9–15 digits are accepted with or without one leading +; + is not accepted elsewhere')
put('HCP-PROFILE-UPDATE-006','Check HCP gender options and birth-date limits',HCP+' Other required fields have valid values. Browser Network inspection is available. All changes in this case are discarded.',hcp_start()+[
    ('Write the original Gender and Date of Birth.','The baseline values are available.'),
    ('Open Gender and read every option.','Options are Male, Female, Other and Prefer Not To Share, plus the unselected prompt Select a gender.'),
    ('Leave Gender unselected and try Save.','Gender is rejected as required; no profile update is sent.'),
    ('Select each offered gender in turn without saving.','Each offered option can be selected.'),
    ('Set Gender to a valid option and enter tomorrow’s date as Date of Birth, then try Save.','A future birth date is rejected; no update is sent.'),
    ('Enter 1985-04-12 as Date of Birth and leave the field without saving.','The past date is accepted by field validation.'),
    ('Close without saving, then reopen Profile.','The original values remain unchanged.')],['Gender options and required-field message.','Future-date input/error with test date and no update request.','Past-date acceptance and unchanged profile after closing.'])
put('HCP-PROFILE-UPDATE-008','Keep an HCP profile change after refresh and sign-in',HCP+' The original First Name is a valid restorable name and other required fields are valid. Temporary First Name value: ManualQaTest. This case previously could not complete because Save called the Patient bootstrap; that product defect must be retested, not assumed fixed.',hcp_start()+[
    ('Write the original First Name.','The exact value is available for restoration.'),
    ('Replace First Name with ManualQaTest.','Only First Name changes in the form.'),
    ('Select Save.','Save succeeds and the form closes only after success. If Save fails, capture the error and mark this step Fail; the dependent persistence checks cannot complete.'),
    ('Refresh the Portal and reopen Profile.','First Name is ManualQaTest.'),
    ('Log out using the Portal logout control and confirmation.','The signed-in session ends.'),
    ('Sign in again as the same HCP and reopen Profile.','First Name is still ManualQaTest.'),
    ('Restore the original First Name using Edit Profile and Save.','The original value is saved.'),
    ('Reopen Profile.','The original value is visible.')],['Original value, save result and any product error.','Value after refresh and after a new sign-in.','Restored original value after reopening.'])
put('HCP-PROFILE-UPDATE-009','Discard an unsaved HCP name change',HCP,hcp_start()+[
    ('Write the original First Name.','The original value is available for comparison.'),
    ('Enter UnsavedTest in First Name.','The temporary value is shown only in the form.'),
    ('Close Profile without selecting Save.','The form closes without claiming to save the change.'),
    ('Reopen Profile.','The original First Name is shown; UnsavedTest is absent.')],['Original name, unsaved form value, and reopened original value.'])
FAULTS['HCP-PROFILE-UPDATE-010']={'rule_names':['HCP-PROFILE-UPDATE-010-1'],'request_names':['actual HCP profile update URL confirmed during setup'],'mode':'synthetic 500 before server mutation','provisioned':False}
put('HCP-PROFILE-UPDATE-010','Keep HCP edits available after Save fails',HCP+' A valid original First Name and valid other fields are required. Disabled local rule HCP-PROFILE-UPDATE-010-1 must intercept the actual HCP update before it reaches the server and return HTTP 500. The setup owner must demonstrate the exact request and rule. A Patient-bootstrap error before the update request is a separate product failure; it does not prove this fault was exercised.',hcp_start()+[
    ('Write the original First Name.','The restoration value is available.'),
    ('Enter ManualQaTest in First Name.','The valid test value appears in the form.'),
    ('Enable HCP-PROFILE-UPDATE-010-1.','Only the intended HCP update is intercepted.'),
    ('Select Save.','The intended update receives HTTP 500 without a server mutation. The form shows a clear error, retains the entered value and does not claim success. An earlier unrelated error is reported separately.'),
    ('Disable HCP-PROFILE-UPDATE-010-1.','The rule is off.'),
    ('Close without saving, then reopen Profile.','The original name remains stored.'),
    ('Edit First Name to ManualQaTest and select Save with the rule off.','The normal update succeeds; otherwise recovery fails.'),
    ('Reopen Profile.','ManualQaTest persists after the normal update.'),
    ('Restore the original First Name and save.','The original value is restored.')],['Rule scope and sanitized HTTP 500 evidence proving the intended update was reached.','Error with retained edits and original stored value after failed Save.','Normal retry, persisted test value, restored original and disabled rule.'])

def simplify_preconditions():
    """Keep prerequisites specific; put inputs and test actions in the steps."""
    for cid,c in U.items():
        c['pre']=c['pre'].replace(BASE,'Patient test account: QA-PORTAL-HISTORY-01.')
        c['pre']=c['pre'].replace(DATE_GATE,'The reference dataset and expected values match the test date.')
        c['pre']=c['pre'].replace(HCP,'HCP test account: QA-PORTAL-HCP-01. ')
        if cid in FAULTS:
            role='HCP' if cid.startswith('HCP-') else 'Patient'
            account='QA-PORTAL-HCP-01' if role=='HCP' else 'QA-PORTAL-HISTORY-01'
            c['pre']=f'{role} test account: {account}. The page loads normally. Prepared local failure rule: '+', '.join(FAULTS[cid]['rule_names'])+' (setup details in the QA guide).'
    short={
      'PAT-AUTH-002':'A Patient test account and a browser with site-data controls for individual websites.',
      'PAT-HOME-009':'A Patient test account with access to Profile and Edit Profile.',
      'PAT-HISTORY-005':'A Patient account with enough readings to scroll through History.',
      'PAT-HISTORY-DATA-001':f'QA-PORTAL-HISTORY-01 has the sample readings and calibration for {day(3)}. Display time zone: Europe/London.',
      'PAT-HISTORY-CAL-001':f'QA-PORTAL-HISTORY-01 has a calibration on {day(3)} and none on {day(0)}. Display time zone: Europe/London.',
      'PAT-SHARE-007':'QA-PORTAL-HISTORY-01 has QA-PORTAL-SECONDARY-01 as an existing follower. The expected rule for inviting your own email is available.',
      'PAT-TIMEZONE-001':'QA-PORTAL-TIMEZONE-01 has the ten sample readings in Test Assets. The test computer allows time-zone changes.',
      'PAT-DIDO-020':'A Patient test account, browser Network tools and the allowed service-domain list for this build.',
      'PAT-PERF-001':'A Patient account with readings, a screen-timing tool and browser cache controls. The required widgets and timing limits are agreed for this run.',
      'PAT-PERF-003':'QA-PORTAL-HISTORY-01 has current 15-day and 90-day data. A screen-timing tool and agreed report timing limits are available.',
      'PAT-OGP-DATA-003':'QA-PORTAL-SPARSE-01 has one reading inside the selected 7-day period.',
      'PAT-OVERVIEW-DATA-020':'QA-PORTAL-SPARSE-01 has one recent reading; QA-PORTAL-HISTORY-01 has current 15-day data. The AGP minimum-data rule is available.',
      'PAT-OVERVIEW-DATA-015':'QA-PORTAL-HISTORY-01 has current reference data. The expected cadence/completeness wording is available.',
      'PAT-DIDO-005':'QA-PORTAL-HISTORY-01 has readings yesterday and none today. Display time zone: Europe/London.',
      'PAT-EVENT-DATA-001':'QA-PORTAL-HISTORY-01 has the four events below in the selected period. Expected session dates and status are available in Test Assets.',
      'PAT-OVERVIEW-DATA-016':'QA-PORTAL-HISTORY-01 has the four events below in the selected period.',
      'PAT-REPORT-DATA-004':'QA-PORTAL-HISTORY-01 has current reference readings and expected range percentages.',
      'PAT-REPORT-DATA-005':'QA-PORTAL-HISTORY-01 has current reference readings. The required A1c formula is specified as GMI or ADAG.',
      'PAT-OVERVIEW-DATA-014':'QA-PORTAL-HISTORY-01 has current reference readings. The required A1c formula is specified as GMI or ADAG.',
      'PAT-REPORT-DATA-006':'QA-PORTAL-HISTORY-01 has current reference readings and matching calculation values. The A1c and SD formulas are specified.',
      'PAT-TIR-002':'QA-PORTAL-HISTORY-01 has current reference readings. Low/high thresholds are 70/180 mg/dL.',
      'HCP-PROFILE-UPDATE-003':'An HCP test account with access to Edit Profile. Other required fields contain valid values.',
      'HCP-PROFILE-UPDATE-005':'An HCP test account with access to Edit Profile. Other required fields contain valid values.',
      'HCP-PROFILE-UPDATE-006':'An HCP test account with access to Edit Profile. Other required fields contain valid values.',
      'HCP-PROFILE-UPDATE-008':'An HCP test account with access to Edit Profile. Other required fields contain valid values.',
      'HCP-PROFILE-UPDATE-009':'An HCP test account with access to Edit Profile.',
    }
    for cid,c in U.items():
        if 'The matching numeric reference table is available.' in c['pre']:
            c['pre']='QA-PORTAL-HISTORY-01 has current reference readings and matching expected values in Test Assets.'
        if cid in ['PAT-OGP-CALC-002','PAT-OGP-DATA-002','PAT-OGP-DATA-004']:
            c['pre']='QA-PORTAL-HISTORY-01 has current reference readings. Numeric chart values and the expected hourly percentile table are available.'
        if cid.startswith('PAT-EXPORT-DATA-'):
            c['pre']='QA-PORTAL-HISTORY-01 has current reference readings. PDF downloads are allowed and a PDF reader is available.'
        if cid in short:c['pre']=short[cid]
    # These are calculation exercises: the inputs belong with the instructions.
    for cid in ['PAT-OGP-CALC-001','PAT-CALC-001','PAT-CALC-002','PAT-TIR-001','PAT-UNIT-001']:
        c=U[cid]
        inputs=c['pre'].replace('No sign-in is required. ','').replace('A calculator and a blank calculation note are available.','').replace('A calculator is available.','').strip()
        p=[re.sub(r'^\d+\.\s*','',x) for x in c['proc'].splitlines()]
        e=[re.sub(r'^\d+\.\s*','',x) for x in c['exp'].splitlines()]
        c['pre']='A calculator and a blank calculation sheet. No Portal account is needed.'
        c['proc']=numbered(['Copy these inputs onto your calculation sheet: '+inputs]+p)
        c['exp']=numbered(['The calculation sheet contains all the supplied inputs.']+e)
    # A save/cancel test needs a reversible edit, not a separately prepared dataset.
    c=U['PAT-HOME-009']
    c['proc']=c['proc'].replace('Sign in as QA-PORTAL-HISTORY-01 and open Overview.','Sign in with the Patient test account and open Overview.')
    c['exp']=c['exp'].replace('Overview belongs to QA-PORTAL-HISTORY-01; no other Patient is selected.','Overview belongs to the signed-in Patient.')
    c['exp']=c['exp'].replace('and matches the profile in Test Assets','')
    c['proc']=c['proc'].replace('Write the supplied field name and its original value in the execution note.','Choose an enabled free-text profile field other than given name, family name or date of birth. Write its label and original value. If no such field is available, note that the edit part cannot run.')
    c['proc']=c['proc'].replace('Enter the supplied valid replacement in that field only.','Append Test to the existing text in the chosen field (or enter Test if empty). Leave all other fields unchanged.')
    c['exp']=c['exp'].replace('Only the intended field changes in the form.','Only the chosen field changes. If the form rejects Test, capture the validation and do not continue to the save check with an invalid input.')
    # Keep measurement definitions in the measurement instructions.
    c=U['PAT-PERF-001']
    c['proc']=c['proc'].replace('Write the browser/version, build, network conditions and required widget list in the evidence note.','Write the browser/version, build, network conditions, original cache setting and required widgets. Confirm timing starts at reload and ends when those widgets finish drawing and the loading indicator clears. Use the agreed limits stated below.')
    c=U['PAT-PERF-003']
    c['proc']=c['proc'].replace('Write the browser/version, build, network conditions and report completion definition.','Write the browser/version, build and network conditions. Confirm timing starts at range selection and ends when the chart and statistics finish drawing and the loading indicator clears. Use the agreed limits stated below.')
    U['PAT-DATA-ERROR-001']['pre']+=' The rule identifies one reading and removes only glucoseCentiMgDl; its timestamp/index remain unchanged.'
    U['HCP-PROFILE-UPDATE-010']['pre']+=' The rule returns HTTP 500 before the update reaches the server.'
    U['HCP-LIST-004']['pre']+=' The HCP has two shared Patients: QA Portal History and QA Portal Secondary.'
    U['HCP-DATA-019']['pre']+=' QA Portal History shares a populated glucose period with this HCP.'
    # Failure recovery needs a populated baseline, not a freshly dated numeric oracle.
    c=U['PAT-HOME-004']
    c['proc']=numbered([re.sub(r'^\d+\.\s*','',x) for x in c['proc'].splitlines()[1:]])
    c['exp']=numbered([re.sub(r'^\d+\.\s*','',x) for x in c['exp'].splitlines()[1:]])
    c['exp']=c['exp'].replace('The 7-day period is selected and Latest, Average, Lowest and Highest values are populated.','Overview opens. A period with populated statistics is available.')
    c['proc']=c['proc'].replace('Take a screenshot of the normal page before enabling a rule.','Select a period with populated statistics and take a screenshot before enabling the rule.')

def apply_verified_labels():
    # Live Patient Portal v6.1.3, 13 October 2026: Profile > Edit Profile?
    # Address and Town are editable; Email remains disabled. No profile was saved.
    for cid,c in U.items():
        c['pre']=c['pre'].replace('A Patient test account','Patient test account QA-PORTAL-HISTORY-01').replace('A Patient account','Patient test account QA-PORTAL-HISTORY-01').replace('An HCP test account','HCP test account QA-PORTAL-HCP-01')
        for field in ('proc','exp'):
            c[field]=c[field].replace('Select Edit Profile.','Select Edit Profile?.').replace('Open Edit Profile.','Select Edit Profile?.')
    put('PAT-HOME-009','Save and restore the Patient Town',
        'Patient test account: QA-PORTAL-HISTORY-01. Other required profile fields contain valid values.',[
        ('Sign in as QA-PORTAL-HISTORY-01.','Overview identifies QA Portal History.'),
        ('Select Profile in the left menu.','The User Profile window opens.'),
        ('Select Edit Profile?.','Town is editable. Email remains read-only.'),
        ('Write the current Town value in the execution note, including whether it is empty.','The original Town value is available for restoration.'),
        ('Replace the Town value with Bristol. Leave the other fields unchanged.','Town displays Bristol without a length-validation error.'),
        ('Select Save.','The save succeeds. If another required field prevents saving, capture its exact label and validation message; do not change unrelated fields to bypass it.'),
        ('Close User Profile with ×, then select Profile again.','Town displays Bristol after reopening.'),
        ('Select Edit Profile? and replace Bristol with the original Town value from step 4.','Town displays the original value.'),
        ('Select Save.','The original Town value is saved.'),
        ('Close User Profile with ×, then select Profile again.','Town matches the original value from step 4.')],
        ['Original Town before editing.','Town showing Bristol after Save and reopening.','Town showing the restored original value after reopening.'])
    c=U['PAT-DIDO-020']
    c['proc']=c['proc'].replace('Trigger a required-field validation error on a reversible form without completing a valid save.','Select Profile, then Edit Profile?. Enter AB in Town and move focus to Address. Do not select Save.')
    c['exp']=c['exp'].replace('A normal validation error is shown and no change is saved.','Town shows its 3–20-character validation message; no profile change is saved.')
    c['proc']+='\n8. Close User Profile with × without selecting Save.'
    c['exp']+='\n8. The unsaved Town change is discarded.'
    for cid,c in U.items():
        for field in ('proc','exp','ev'):
            c[field]=c[field].replace('Range A','the left panel').replace('Range B','the right panel')
            c[field]=c[field].replace('Download the report PDF once.','Select Download PDF on Assessment Report.')
            c[field]=c[field].replace('Open Events & Notes.','Scroll to EVENTS & NOTES.').replace('Open Daily Patterns.','Scroll to DAILY PATTERNS.').replace('Open Time in Range by Day.','Scroll to TIME IN RANGE BY DAY.')
        c['proc']=re.sub(r'Set the (left|right) panel to (\d+) days\.',r'Select \2 days in the \1 panel under the Overlay tab.',c['proc'])
    U['PAT-SHARE-007']['proc']=U['PAT-SHARE-007']['proc'].replace('Open Followers.','Select Patient Management, then Followers.').replace('Open Invite and enter','Select Invite. In Email address, enter')
    U['PAT-PERF-003']['proc']=U['PAT-PERF-003']['proc'].replace('Select a different range, then capture selection of 15 days until completion. Repeat ten times, returning to the other range before each measured selection.','Select 7 days and wait for loading to finish. Start the timed capture when selecting 15 days. Repeat ten times, selecting 7 days between samples.').replace('Repeat the same procedure for 90 days ten times.','Select 7 days between samples and time selection of 90 days ten times.')
    # History has only 7/15/30-day controls in the inspected build.
    c=U['PAT-HISTORY-005']
    for field in ('proc','exp'):c[field]=c[field].replace('90 days','30 days')
    for cid in ['PAT-HISTORY-DATA-001','PAT-HISTORY-CAL-001']:
        c=U[cid]
        lines=c['proc'].splitlines()
        for i,line in enumerate(lines):
            if 'custom' in line:
                date=re.search(r'2026-\d\d-\d\d',line)[0]
                lines[i]=f'{i+1}. Select 30 days. Scroll to the daily chart headed From: {dt.date.fromisoformat(date).strftime("%d-%m-%Y")}. Read that day’s chart and the Glucose history readings table beneath it.'
                ex=c['exp'].splitlines();ex[i]=f'{i+1}. The daily section for {date} is visible; use only that section for the next check.';c['exp']='\n'.join(ex)
        c['proc']='\n'.join(lines)
        c['pre']+=' The sample date is within the last 30 days.'
    # Unsupported controls must be explicit gaps, never invented instructions.
    gaps={
      'PAT-HISTORY-004':'The inspected History page has 7 days, 15 days and 30 days only. Its 24-hour, 90-day and custom-range checks cannot be executed on this build.',
      'PAT-DIDO-005':'The inspected History page has no 24 hours control. This History-specific rolling-24-hour check cannot be executed on this build.',
      'PAT-TIMEZONE-001':'History has no custom-date control and only offers the last 7, 15 or 30 days. The ten winter/summer samples cannot all be reached through this screen.',
    }
    for cid,reason in gaps.items():
        c=U[cid]
        c['pre']+=' Current UI gap: '+reason
        c['proc']=numbered(['Sign in as '+('QA-PORTAL-TIMEZONE-01' if cid=='PAT-TIMEZONE-001' else 'QA-PORTAL-HISTORY-01')+' and select History.','Inspect the date controls above the daily charts.','Capture the available date controls and attach the UI gap to this case. Do not substitute Overview or mark the original coverage complete.'])
        c['exp']=numbered(['History opens for the specified account.','The required controls must be available to execute the original coverage. '+reason,'The original coverage remains incomplete; the missing controls are identified in the execution note.'])
    report={'date':'2026-10-13','source':'Live Patient Portal v6.1.3, authenticated UI inspection; no profile saved and no invitation sent.',
      'verified_labels':['Profile','Edit Profile?','Town','Address','Save','Patient Management','Followers','Invite','Email address','Send Invite','Download PDF','Overlay','History'],
      'ui_gaps':gaps,'account_references':'Preserved in all account-based cases.'}
    (ROOT/'output/manual-qa-live-label-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

def main():
    simplify_preconditions()
    apply_verified_labels()
    target=set()
    for f in ['rewrite_portal_blocked_batch1.py','rewrite_portal_blocked_batch2.py','rewrite_portal_blocked_batch3.py']:
        target.update(runpy.run_path(str(ROOT/'scripts'/f))['UPDATES'])
    target.update(['HCP-LIST-004','HCP-DATA-019','HCP-PROFILE-UPDATE-003','HCP-PROFILE-UPDATE-005','HCP-PROFILE-UPDATE-006','HCP-PROFILE-UPDATE-008','HCP-PROFILE-UPDATE-009','HCP-PROFILE-UPDATE-010'])
    assert len(target)==71
    assert set(U)==target,(sorted(target-set(U)),sorted(set(U)-target))
    cases=json.loads(PATH.read_text(encoding='utf-8'))
    backup=ROOT/'output/console-update/before-manual-71-2026-10-13.json'
    if not backup.exists():backup.write_text(json.dumps([c for c in cases if c['id'] in target],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for c in cases:
        if c['id'] in U:
            c.update(U[c['id']])
            assert len(c['proc'].splitlines())==len(c['exp'].splitlines()),c['id']
            assert not re.search(r'\brecorded\b|\bChrome\b', ' '.join(c.values()) if all(isinstance(v,str) for v in c.values()) else ' '.join(str(v) for v in c.values()),re.I),c['id']
    PATH.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'date':'2026-10-13','updated_count':71,'fixture_anchor':H['anchor'],'case_ids':sorted(target),'fault_setup_cards':FAULTS,
            'scope':'Definitions and evidence instructions only; no new live execution and no fixture reseed.'}
    (ROOT/'output/manual-qa-71-update.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated 71 cases; IDs and execution results preserved. Fault setup cards:',len(FAULTS))

if __name__=='__main__':main()
