"""QA seeder foundation. Python standard library plus the system curl client."""
import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess

BASE = 'https://modapi.grxdiscovery.link'
SERVICE = '/glucorx.modus.v1alpha2.AppService/'
ROOT = Path(__file__).resolve().parents[1]


def methods():
    return re.findall(r'\brpc\s+(\w+)\s*\(', (ROOT / 'schemas/app_service.proto').read_text())


def rpc(method, body, token=None):
    if method not in methods():
        raise ValueError('Method is not in the supplied AppService contract')
    # Credentials go through stdin, never command-line arguments or stored logs.
    headers = ['Content-Type: application/json', 'Connect-Protocol-Version: 1']
    if token:
        if any(c in token for c in '\r\n'):
            raise ValueError('Invalid token')
        headers.append('Authorization: Bearer ' + token)
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'
    config = '\n'.join(['url = ' + quote(BASE + SERVICE + method),
                         'request = "POST"', 'silent', 'show-error',
                         'connect-timeout = 10', 'max-time = 60',
                         'write-out = "\\n%{http_code}"'] +
                        ['header = ' + quote(h) for h in headers] +
                        ['data = ' + quote(json.dumps(body))])
    result = subprocess.run(['curl.exe' if os.name == 'nt' else 'curl', '--config', '-'],
                            input=config, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('Transport failed; request outcome may be unknown. No automatic retry.')
    text, status = result.stdout.rsplit('\n', 1)
    if not 200 <= int(status) < 300:
        raise RuntimeError(f'{method}: HTTP {status}: {text[:1500]}')
    return json.loads(text) if text else {}


def generate(end, days=14, seed=20260929):
    if end.tzinfo is None or not 1 <= days <= 90:
        raise ValueError('Use an explicit timezone and 1–90 days')
    end = end.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)
    start = end - dt.timedelta(minutes=days * 1440 - 1)
    rng = random.Random(seed)
    result = []
    for i in range(days * 1440):
        when = start + dt.timedelta(minutes=i)
        local = when + dt.timedelta(hours=5)
        minute = local.hour * 60 + local.minute
        # Scenarios use elapsed offsets so they always occur, regardless of start hour.
        if 2 * 1440 <= i < 2 * 1440 + 45:
            continue
        glucose = 100 + 8 * math.sin(minute / 1440 * 2 * math.pi) + rng.uniform(-2, 2)
        for meal in (480, 780, 1140):
            elapsed = minute - meal
            if 0 <= elapsed < 180:
                glucose += 65 * math.exp(-((elapsed - 60) / 45) ** 2)
        if 6 * 1440 <= i < 6 * 1440 + 60:
            glucose = 52 + rng.uniform(-2, 2)
        result.append({'index': i + 1, 'measure_time': when.isoformat().replace('+00:00', 'Z'),
                       'glucose_centi_mg_dl': round(glucose * 100)})
    return {'scenario': 'baseline-meals-low-gap', 'seed': seed, 'days': days,
            'end': end.isoformat(), 'time_zone': 'Asia/Karachi',
            'count': len(result), 'readings': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('inventory')
    sub.add_parser('probe')
    read = sub.add_parser('read', help='Authenticated read-only unary RPC')
    read.add_argument('method')
    read.add_argument('body', type=Path)
    gen = sub.add_parser('generate', help='Generate local data; does not call the API')
    gen.add_argument('--end', required=True, help='Fixed ISO timestamp including timezone')
    gen.add_argument('--days', type=int, default=14)
    gen.add_argument('--seed', type=int, default=20260929)
    gen.add_argument('--output', type=Path, default=Path('output/readings.json'))
    args = parser.parse_args()
    if args.command == 'inventory':
        print('\n'.join(methods()))
    elif args.command == 'generate':
        data = generate(dt.datetime.fromisoformat(args.end.replace('Z', '+00:00')), args.days, args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f'Generated {data["count"]} readings in {args.output}')
    elif args.command == 'probe':
        for method, body in [('GetUser', {'name': 'users/me'}),
                             ('GetServiceInfo', {'name': 'serviceInfo'})]:
            try:
                print(method, rpc(method, body))
            except RuntimeError as error:
                print(error)
    else:
        if not args.method.startswith(('Get', 'List', 'Query')):
            parser.error('This command permits read-only methods only')
        token = os.environ.get('MODUS_ACCESS_TOKEN')
        if not token:
            parser.error('Set MODUS_ACCESS_TOKEN locally first')
        print(json.dumps(rpc(args.method, json.loads(args.body.read_text(encoding='utf-8')), token), indent=2))


if __name__ == '__main__':
    main()
