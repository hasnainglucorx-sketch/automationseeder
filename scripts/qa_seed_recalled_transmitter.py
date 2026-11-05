"""
QA helper: seed and lift a recalled transmitter via GlobalService.

Creates a controlled recall entry against a specific QA transmitter so
TX-PAIR-023 and TX-PAIR-024 can be executed. Lifts the recall afterwards
so the same transmitter can be reused.

SETUP
-----
1. Obtain a super-admin JWT for the QA GlobalService environment.
2. Set it as an environment variable:
       set GLOBAL_ADMIN_TOKEN=<your token>       (Windows)
       export GLOBAL_ADMIN_TOKEN=<your token>    (macOS/Linux)

USAGE
-----
  # Create the recall:
  python scripts/qa_seed_recalled_transmitter.py create <transmitter_id>

  # List existing recalls (verify):
  python scripts/qa_seed_recalled_transmitter.py list

  # Rescind (lift) the recall after testing:
  python scripts/qa_seed_recalled_transmitter.py rescind <recall_name>
  # e.g.: python scripts/qa_seed_recalled_transmitter.py rescind recalls/qa-tx-recall-TX00123

NOTE ON FIELD NAMES
-------------------
The exact field names inside the Recall message come from recall.proto,
which is not available here. The fields below (transmitter, reason,
severity) are best-effort based on the GlobalService proto comments.
Verify against recall.proto and adjust if the server returns a 400.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# ---- QA environment base URL -------------------------------------------------
# Change this to your actual QA GlobalService host if different.
QA_HOST = 'https://global-qa.modus.glucorx.co.uk'

# Recall ID prefix used for QA-created recalls so they are easy to identify.
RECALL_ID_PREFIX = 'qa-tx-recall-'


# ---- helpers -----------------------------------------------------------------

def auth_headers():
    tok = os.environ.get('GLOBAL_ADMIN_TOKEN', '')
    if not tok:
        sys.exit(
            'ERROR: GLOBAL_ADMIN_TOKEN is not set.\n'
            'Set it to a valid super-admin JWT for the QA GlobalService.'
        )
    return {
        'Authorization': f'Bearer {tok}',
        'Content-Type': 'application/json',
    }


def http(method, url, body=None):
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=auth_headers(), method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace')
        sys.exit(f'HTTP {e.code} from {url}:\n{msg}')


# ---- sub-commands ------------------------------------------------------------

def cmd_create(transmitter_id, recall_id=None):
    """Issue a recall against a single QA transmitter."""
    recall_id = recall_id or f'{RECALL_ID_PREFIX}{transmitter_id}'

    # TODO: verify field names below against recall.proto before first use.
    # 'transmitter' is the resource name of the device to recall.
    # 'reason'/'severity' names may differ in the actual message definition.
    recall_body = {
        # TODO: confirm field name — may be 'subject', 'transmitter', or a oneof.
        'transmitter': f'transmitters/{transmitter_id}',

        # TODO: confirm allowed severity values from recall.proto enum.
        # Expected values: SAFETY_NOTICE, VOLUNTARY_RECALL, MANDATORY_RECALL, etc.
        'severity': 'SAFETY_NOTICE',

        # Human-readable reason for the recall entry.
        'reason': 'QA controlled recall for TX-PAIR-023 / TX-PAIR-024 test execution. '
                  'Do not use this recall entry in production.',
    }

    url = f'{QA_HOST}/v1alpha2/recalls?recall_id={recall_id}'
    result = http('POST', url, body={'recall': recall_body})

    print('=== Recall created ===')
    print(json.dumps(result, indent=2))
    print()
    recall_name = result.get('name', f'recalls/{recall_id}')
    print(f'Record in Test Data:')
    print(f'  Transmitter ID : transmitters/{transmitter_id}')
    print(f'  Recall name    : {recall_name}')
    print()
    print(f'Rescind after testing:')
    print(f'  python scripts/qa_seed_recalled_transmitter.py rescind {recall_name}')


def cmd_list():
    """List all active recalls in the QA environment."""
    url = f'{QA_HOST}/v1alpha2/recalls'
    result = http('GET', url)
    print('=== Active recalls ===')
    print(json.dumps(result, indent=2))


def cmd_rescind(recall_name):
    """Lift a recall so the transmitter can be reused."""
    # recall_name must be the full resource name, e.g. "recalls/qa-tx-recall-TX00123"
    if not recall_name.startswith('recalls/'):
        sys.exit(
            f'ERROR: recall_name must be the full resource name, e.g. recalls/<id>.\n'
            f'Got: {recall_name!r}'
        )
    url = f'{QA_HOST}/v1alpha2/{recall_name}:rescind'
    result = http('POST', url, body={})
    print('=== Recall rescinded ===')
    print(json.dumps(result, indent=2))


# ---- entry point -------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Seed and lift QA recalled transmitters via GlobalService.'
    )
    sub = parser.add_subparsers(dest='action', required=True)

    p_create = sub.add_parser('create', help='Create a recall against a transmitter.')
    p_create.add_argument('transmitter_id', help='Transmitter serial / ID, e.g. TX00123')
    p_create.add_argument('--recall-id', default=None,
                          help='Optional recall_id (default: qa-tx-recall-<transmitter_id>)')

    sub.add_parser('list', help='List all recalls in the QA environment.')

    p_rescind = sub.add_parser('rescind', help='Lift a recall after testing.')
    p_rescind.add_argument('recall_name',
                           help='Full resource name returned by create, e.g. recalls/qa-tx-recall-TX00123')

    args = parser.parse_args()

    if args.action == 'create':
        cmd_create(args.transmitter_id, getattr(args, 'recall_id', None))
    elif args.action == 'list':
        cmd_list()
    elif args.action == 'rescind':
        cmd_rescind(args.recall_name)


if __name__ == '__main__':
    main()
