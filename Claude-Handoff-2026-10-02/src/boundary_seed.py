"""Add or refresh an isolated 89/90/91-day fixture on the bound QA account."""
import argparse
import datetime as dt
import json
from pathlib import Path
import uuid

from src.auth import access_token
from src.qa_run import RUN, load_bound, matches_payload, paged, stamp
from src.seeder import rpc

FILE = RUN.with_name('boundary-90-days.json')


def save(state):
    tmp = FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2), encoding='utf-8')
    tmp.replace(FILE)


def archive_existing():
    """Keep prior verification evidence while allowing a fresh time boundary."""
    if not FILE.exists():
        return None
    state = json.loads(FILE.read_text(encoding='utf-8'))
    reference = state.get('reference_time', 'unknown').replace(':', '').replace('-', '')
    archive = FILE.with_name(f'boundary-90-days-{reference}.json')
    if not archive.exists():
        archive.write_text(FILE.read_text(encoding='utf-8'), encoding='utf-8')
    FILE.unlink()
    return archive


def main():
    global FILE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true',
                        help='Create a new isolated boundary session using the current time')
    parser.add_argument('--file', type=Path, default=FILE,
                        help='Checkpoint/report path (defaults to output/boundary-90-days.json)')
    args = parser.parse_args()
    FILE = args.file.resolve()
    if args.refresh:
        archived = archive_existing()
        if archived:
            print(f'Archived prior boundary evidence to {archived}', flush=True)
    original = load_bound()
    if FILE.exists():
        state = json.loads(FILE.read_text(encoding='utf-8'))
        if state['patient'] != original['patient'] or state['user'] != original['user']:
            raise RuntimeError('Boundary run belongs to a different account')
    else:
        fixture = json.loads(json.dumps(next(a['body']['session'] for a in original['actions'] if a['key'] == 'session')))
        # Refresh/authenticate before choosing the boundary reference time.
        access_token()
        anchor = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        rows = [{'index': i, 'measure_time': stamp(anchor - dt.timedelta(days=days)),
                 'glucose_centi_mg_dl': glucose}
                for i, days, glucose in [(1, 91, 9800), (2, 90, 10000), (3, 89, 10200)]]
        fixture.update(transmitter='transmitters/QABOUND' + uuid.uuid4().hex[:8].upper(),
                       session_index='1', start_time=rows[0]['measure_time'])
        state = {'user': original['user'], 'patient': original['patient'],
                 'reference_time': stamp(anchor), 'readings': rows,
                 'session_request': {'parent': original['patient'], 'session_id': str(uuid.uuid4()), 'session': fixture}}
        save(state)
    if not state.get('session'):
        sessions = paged('ListSessions', {'parent': state['patient']}, 'sessions')
        matches = [s for s in sessions if s.get('transmitter') == state['session_request']['session']['transmitter']]
        if len(matches) > 1:
            raise RuntimeError('Ambiguous boundary session')
        result = matches[0] if matches else rpc('CreateSession', state['session_request'], access_token())
        if not result.get('name', '').startswith(state['patient'] + '/sessions/'):
            raise RuntimeError('Unexpected session owner')
        state['session'] = result['name']
        state['session_response'] = result
        save(state)
    if not state.get('written'):
        response = rpc('WriteReadings', {'parent': state['session'], 'partial_success': False,
                                        'readings': state['readings']}, access_token())
        if response.get('failedReadings') or response.get('failed_readings'):
            raise RuntimeError('Some boundary readings were rejected')
        state['written'] = True
        save(state)
    rows = paged('QueryReadings', {'parent': state['session']}, 'readings')
    actual = {r['index']: r for r in rows}
    if len(rows) != 3 or not all(matches_payload(r, actual.get(r['index'])) for r in state['readings']):
        raise RuntimeError('Boundary readings did not match read-back')
    state['verification'] = {'passed': True, 'count': len(rows), 'readings': rows,
                             'verified_at': stamp(dt.datetime.now(dt.timezone.utc))}
    save(state)
    # This is historical data; close its fixture session so it does not become
    # a second active source in CurrentGlucose alongside the main seed session.
    current = rpc('GetSession', {'name': state['session']}, access_token())
    if current.get('state') == 'ACTIVE':
        current = rpc('StopSession', {'name': state['session']}, access_token())
    state['session_response'] = current
    save(state)
    print(json.dumps({'reference_time': state['reference_time'], 'readings': state['readings'],
                      'verified': True, 'session_state': current.get('state')}, indent=2))


if __name__ == '__main__':
    main()
