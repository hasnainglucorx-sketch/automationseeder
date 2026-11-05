"""Persistent, account-bound QA seed run using the deployed message fields."""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import uuid

from src.auth import access_token
from src.seeder import generate, rpc

RUN = Path(__file__).resolve().parents[1] / 'output/qa-run.json'


def save(data):
    RUN.parent.mkdir(parents=True, exist_ok=True)
    temp = RUN.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    temp.replace(RUN)


def stamp(value):
    return value.astimezone(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def identity(email):
    token = access_token()
    claims = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '==='))
    if claims.get('email', '').casefold() != email.casefold():
        raise RuntimeError('Authenticated email does not match the requested QA account')
    user = rpc('GetUser', {'name': 'users/me'}, token)
    if user['subject'] != claims['sub']:
        raise RuntimeError('API identity does not match the login identity')
    return user


def prepare(email):
    if RUN.exists():
        raise RuntimeError('A run already exists; use resume commands')
    user = identity(email)
    patient = user.get('selfPatient')
    if not patient:
        raise RuntimeError('Account has no self patient; explicit patient creation is needed')
    existing = rpc('ListSessions', {'parent': patient}, access_token())
    if existing.get('sessions'):
        raise RuntimeError('Patient already has sessions; use a reviewed plan for existing data')
    run_id = str(uuid.uuid4())
    end = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0) - dt.timedelta(minutes=10)
    data = generate(end)
    start = dt.datetime.fromisoformat(data['readings'][0]['measure_time'].replace('Z', '+00:00'))
    session_id = str(uuid.uuid5(uuid.UUID(run_id), 'session'))
    session_name = patient + '/sessions/' + session_id
    actions = []

    def action(key, method, body, group):
        actions.append({'key': key, 'method': method, 'body': body, 'group': group, 'status': 'pending'})

    action('profile', 'UpdatePatient', {'patient': {'name': patient, 'display_name': 'QA Synthetic Patient 01',
           'time_zone': 'Asia/Karachi', 'date_of_birth': {'year': 1985, 'month': 6, 'day': 15},
           'diabetes_type': 'TYPE_2', 'country': 'PK'},
           'update_mask': 'displayName,timeZone,dateOfBirth,diabetesType,country'}, 'profile')
    action('settings', 'UpdatePatientSettings', {'patient_settings': {'name': patient + '/settings',
           'urgent_low_centi_mg_dl': 5400, 'low_centi_mg_dl': 7000, 'high_centi_mg_dl': 18000,
           'urgent_high_centi_mg_dl': 25000},
           'update_mask': 'urgentLowCentiMgDl,lowCentiMgDl,highCentiMgDl,urgentHighCentiMgDl'}, 'profile')
    action('session', 'CreateSession', {'parent': patient, 'session_id': session_id,
           'session': {'transmitter': 'transmitters/QASEED' + run_id.replace('-', '')[:8].upper(),
                       'session_index': '1', 'start_time': stamp(start),
                       'firmware_version': {'major': 3, 'minor': 1, 'patch': 0,
                           'image_sha256': hashlib.sha256(b'QA synthetic firmware fixture v1').hexdigest()},
                       'app_build': {'platform': 'IOS', 'version': '1.0.4'}}}, 'session')
    # Use reproducible per-resource identifiers and request IDs for safe resume.
    for day in range(14):
        day_start = start + dt.timedelta(days=day)
        for hour, detail in [(1, {'carbohydrate': {'grams': 40}}),
                             (6, {'carbohydrate': {'grams': 60}}),
                             (12, {'carbohydrate': {'grams': 50}}),
                             (13, {'insulin': {'units': 2.0, 'kind': 'BOLUS', 'product': 'QA synthetic fixture'}}),
                             (14, {'activity': {'activity_type': 'QA walking', 'duration_minutes': 30, 'intensity': 'MODERATE'}}),
                             (15, {'note': {'text': 'Synthetic QA scenario; not real patient activity.', 'category': 'GENERAL'}})]:
            key = f'event-{day}-{hour}'
            action(key, 'CreateEvent', {'parent': patient,
                   'request_id': str(uuid.uuid5(uuid.UUID(run_id), key)),
                   'event': {'event_time': stamp(day_start + dt.timedelta(hours=hour)), **detail}}, 'events')
        key = f'calibration-{day}'
        action(key, 'CreateCalibration', {'parent': session_name,
               'calibration_id': str(uuid.uuid5(uuid.UUID(run_id), key)),
               'calibration': {'reference_glucose_centi_mg_dl': 10500,
                               'measure_time': stamp(day_start + dt.timedelta(hours=16))}}, 'calibrations')
    for key, when, severity, detail in [
        ('alarm-low', start + dt.timedelta(days=6), 'CRITICAL',
         {'glucose': {'threshold': 'URGENT_LOW', 'glucose_centi_mg_dl': 5200}}),
        ('alarm-gap', start + dt.timedelta(days=2, minutes=30), 'INFORMATIONAL',
         {'no_data': {'since_last_reading': '1800s'}})]:
        action(key, 'CreateAlarm', {'parent': patient,
               'request_id': str(uuid.uuid5(uuid.UUID(run_id), key)),
               'alarm': {'session': session_name, 'raise_time': stamp(when), 'severity': severity, **detail}}, 'alarms')
    state = {'run_id': run_id, 'email': email, 'user': user['name'], 'patient': patient,
             'session': session_name, 'data': data, 'actions': actions, 'batches': [],
             'created_at': stamp(dt.datetime.now(dt.timezone.utc))}
    save(state)
    print(f'Prepared {len(data["readings"])} readings, 84 events, 14 calibrations, 2 alarms.')


def load_bound():
    state = json.loads(RUN.read_text(encoding='utf-8'))
    user = identity(state['email'])
    if user['name'] != state['user'] or user.get('selfPatient') != state['patient']:
        raise RuntimeError('Run is bound to a different account or patient')
    return state


def execute(group):
    state = load_bound()
    for action in state['actions']:
        if action['group'] != group or action['status'] == 'done':
            continue
        if group in ('calibrations', 'alarms'):
            if not any(a['key'] == 'session' and a['status'] == 'done' for a in state['actions']):
                raise RuntimeError('Session setup has not completed')
        if action['key'] == 'settings':
            current = rpc('GetPatientSettings', {'name': state['patient'] + '/settings'}, access_token())
            desired = action['body']['patient_settings']
            def camel(name):
                first, *rest = name.split('_')
                return first + ''.join(x.title() for x in rest)
            if all(current.get(camel(k)) == v for k, v in desired.items()):
                action.update(status='done', result=current, reused_existing=True)
                action.pop('error', None)
                save(state)
                print('settings already match', flush=True)
                continue
        if action['key'] == 'session':
            sessions = paged('ListSessions', {'parent': state['patient']}, 'sessions')
            fixture = action['body']['session']
            matches = [s for s in sessions if s.get('transmitter') == fixture['transmitter']
                       and str(s.get('sessionIndex')) == fixture['session_index']
                       and s.get('startTime') == fixture['start_time']]
            if len(matches) > 1:
                raise RuntimeError('Multiple sessions match this run; refusing ambiguous resume')
            if matches:
                bind_session(state, matches[0])
                action.update(status='done', result=matches[0], reused_existing=True)
                save(state)
                print('session reconciled', flush=True)
                continue
        if action['status'] == 'in_flight':
            raise RuntimeError('Prior request outcome unknown; reconcile before replaying')
        action['status'] = 'in_flight'
        save(state)
        try:
            result = rpc(action['method'], action['body'], access_token())
        except RuntimeError as error:
            # 4xx responses are definite rejections; transport/5xx outcomes may
            # have committed and must be reconciled before replaying creates.
            action['status'] = 'failed' if ': HTTP 4' in str(error) or ': HTTP 501:' in str(error) else 'in_flight'
            action['error'] = str(error)
            save(state)
            raise
        if action['key'] == 'session':
            bind_session(state, result)
        action.update(status='done', result=result)
        action.pop('error', None)
        save(state)
        print(action['key'], 'OK', flush=True)


def bind_session(state, result):
    name = result.get('name', '')
    if not name.startswith(state['patient'] + '/sessions/'):
        raise RuntimeError('Session belongs to an unexpected patient')
    old = state['session']
    state['session'] = name
    for action in state['actions']:
        if action['body'].get('parent') == old:
            action['body']['parent'] = name
        if action['body'].get('alarm', {}).get('session') == old:
            action['body']['alarm']['session'] = name


def write_readings(smoke=False):
    state = load_bound()
    if not any(a['key'] == 'session' and a['status'] == 'done' for a in state['actions']):
        raise RuntimeError('Session setup has not completed')
    rows = state['data']['readings']
    chunks = [(0, rows[:5])] if smoke else [(0, rows[:5])] + [(i, rows[i:i+200]) for i in range(5, len(rows), 200)]
    for offset, batch in chunks:
        key = f'{offset}:{len(batch)}'
        if key in state['batches']:
            continue
        result = rpc('WriteReadings', {'parent': state['session'], 'partial_success': False, 'readings': batch}, access_token())
        if result.get('failedReadings') or result.get('failed_readings'):
            raise RuntimeError('Backend reported rejected readings; batch was not marked complete')
        state['batches'].append(key)
        save(state)
        print(f'Readings {offset + len(batch)}/{len(rows)} accepted', flush=True)


def paged(method, body, key):
    result, seen = [], set()
    body = dict(body, page_size=1000)
    while True:
        response = rpc(method, body, access_token())
        result.extend(response.get(key, []))
        token = response.get('nextPageToken')
        if not token:
            return result
        if token in seen:
            raise RuntimeError('Repeated pagination cursor')
        seen.add(token)
        body['page_token'] = token


def matches_payload(expected, actual):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            first, *rest = key.split('_')
            camel = first + ''.join(x.title() for x in rest)
            if not matches_payload(value, actual.get(camel)):
                return False
        return True
    return expected == actual


def assess_resources(state, report):
    for group, field in [('events', 'event'), ('calibrations', 'calibration'), ('alarms', 'alarm')]:
        result = report[group]
        if 'error' in result:
            continue
        expected = [a for a in state['actions'] if a['group'] == group]
        by_name = {r['name']: r for r in result['items']}
        result['expected_count'] = len(expected)
        result['mismatched_actions'] = [a['key'] for a in expected if
            not matches_payload(a['body'][field], by_name.get(a.get('result', {}).get('name')))]
        result['passed'] = len(by_name) == len(result['items']) and not result['mismatched_actions']
    report['readings_passed'] = (report['actual_readings'] == report['expected_readings'] and
        not report['missing_indices'] and not report['mismatched_indices'] and not report['duplicate_readings'])
    report['supported_categories_passed'] = report['readings_passed'] and all(
        report[g].get('passed', False) for g in ('events', 'calibrations'))
    return report


def verify():
    state = load_bound()
    rows = paged('QueryReadings', {'parent': state['session']}, 'readings')
    expected = {r['index']: r for r in state['data']['readings']}
    actual = {r['index']: r for r in rows}
    mismatches = [i for i, r in actual.items() if i not in expected or
                  r.get('glucoseCentiMgDl') != expected[i]['glucose_centi_mg_dl'] or
                  dt.datetime.fromisoformat(r['measureTime'].replace('Z', '+00:00')) !=
                  dt.datetime.fromisoformat(expected[i]['measure_time'].replace('Z', '+00:00'))]
    report = {'expected_readings': len(expected), 'actual_readings': len(rows),
              'missing_indices': sorted(set(expected) - set(actual)), 'mismatched_indices': mismatches,
              'duplicate_readings': len(rows) - len(actual)}
    for label, method, body, key in [
        ('events', 'ListEvents', {'parent': state['patient']}, 'events'),
        ('calibrations', 'ListCalibrations', {'parent': state['session']}, 'calibrations'),
        ('alarms', 'ListAlarms', {'parent': state['patient']}, 'alarms')]:
        try:
            items = paged(method, body, key)
            report[label] = {'count': len(items), 'items': items}
        except RuntimeError as error:
            report[label] = {'error': str(error)}
    for label, method, name in [('statistics', 'GetGlucoseStatistics', state['patient'] + '/glucoseStatistics'),
                               ('current', 'GetCurrentGlucose', state['patient'] + '/currentGlucose'),
                               ('patient', 'GetPatient', state['patient']),
                               ('settings', 'GetPatientSettings', state['patient'] + '/settings')]:
        try:
            report[label] = rpc(method, {'name': name}, access_token())
        except RuntimeError as error:
            report[label] = {'error': str(error)}
    state['verification'] = report
    assess_resources(state, report)
    save(state)
    RUN.with_name(RUN.stem + '-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('events','calibrations','alarms')}, indent=2))
    for label in ('events','calibrations','alarms'):
        print(label, {k:v for k,v in report[label].items() if k != 'items'})
    if not report['supported_categories_passed']:
        raise RuntimeError('Read-back verification failed; inspect the saved report')


def run_all():
    unavailable = []
    for group in ('profile', 'session'):
        execute(group)
    write_readings(smoke=True)
    state = load_bound()
    actual = {r['index']: r for r in paged('QueryReadings', {'parent': state['session']}, 'readings')}
    if not all(matches_payload(row, actual.get(row['index'])) for row in state['data']['readings'][:5]):
        raise RuntimeError('Smoke readings did not match; full upload stopped')
    write_readings()
    for group in ('events', 'calibrations', 'alarms'):
        try:
            execute(group)
        except RuntimeError as error:
            if ': HTTP 404:' not in str(error) and ': HTTP 501:' not in str(error):
                raise
            unavailable.append(str(error))
            print('Unavailable:', error, flush=True)
    verify()
    if unavailable:
        print('Completed supported data categories. Some endpoints are unavailable.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'profile', 'session', 'events', 'calibrations', 'alarms', 'smoke', 'readings', 'verify', 'run'])
    parser.add_argument('--email')
    parser.add_argument('--run-file', type=Path, help='Separate checkpoint file for a different seed run')
    args = parser.parse_args()
    if args.run_file:
        RUN = args.run_file.resolve()
    if args.command == 'prepare':
        if not args.email:
            parser.error('--email is required')
        prepare(args.email)
    elif args.command in ('profile', 'session', 'events', 'calibrations', 'alarms'):
        execute(args.command)
    elif args.command in ('smoke', 'readings'):
        write_readings(args.command == 'smoke')
    elif args.command == 'run':
        run_all()
    else:
        verify()
