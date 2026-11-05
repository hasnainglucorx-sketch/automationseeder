"""
Create a new 'Pending Implementation' batch from 4 cases confirmed as not yet implemented.
Removes each case from its current batch and adds it to the new batch with a new ID.

Mapping:
  VP-APP-ABOUT-009    -> VP-APP-PENDING-001
  VP-APP-TX-PAIR-026  -> VP-APP-PENDING-002
  VP-APP-SENSOR-ID-007-> VP-APP-PENDING-003
  VP-APP-MYCGM-009    -> VP-APP-PENDING-004
"""
import json, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent.parent
COMPACT = ROOT / 'output/console-update/PRT-0701-cases.json'
RO      = ROOT / 'output/console-update/PRT-0701-run_order.json'

OLD_TO_NEW = {
    'VP-APP-ABOUT-009':     'VP-APP-PENDING-001',
    'VP-APP-TX-PAIR-026':   'VP-APP-PENDING-002',
    'VP-APP-SENSOR-ID-007': 'VP-APP-PENDING-003',
    'VP-APP-MYCGM-009':     'VP-APP-PENDING-004',
}

BATCH_SEC = 'Batch PENDING - Pending Implementation'
METHOD    = 'Manual - Real Device'

# ── corrected compact case content (verified from screenshots + developer responses) ──

PENDING_COMPACT = [
    {
        'id':  'VP-APP-PENDING-001',
        'sec': BATCH_SEC,
        't':   'Recall-status staleness warning appears after more than 24 hours offline',
        'method': METHOD,
        'req': 'DI-84 / DO-722',
        'pre': 'The app is signed in and internet is available. The recall status has been refreshed online.',
        'proc': (
            '1. Confirm the app is online and no recall-staleness warning is shown.\n'
            '2. Disable Wi-Fi and mobile data and confirm the device is fully offline.\n'
            '3. Leave the device offline for more than 24 hours without restoring internet.\n'
            '4. Open the app and observe the Home screen and any notifications for a recall-staleness warning.\n'
            '5. Restore internet and observe whether the warning clears automatically.'
        ),
        'exp': (
            '1. No recall-staleness warning is visible while the app is online and recall data is current.\n'
            '2. The device is offline and no internet connection is active.\n'
            '3. More than 24 hours pass with no recall-status refresh from the server.\n'
            '4. A warning is displayed — as a dashboard card, push notification or both — informing the user that recall information has not been refreshed for more than 24 hours, per DI-84/DO-722.\n'
            '5. When internet is restored and the recall status refreshes successfully, the warning clears without requiring further user action.'
        ),
        'ev': (
            'Screenshot confirming no warning while online; '
            'screenshot of the recall-staleness warning after 24 hours offline (dashboard card and/or notification with exact text recorded); '
            'screenshot confirming the warning has cleared after internet is restored; '
            'execution record with offline start time and warning appearance time.'
        ),
    },
    {
        'id':  'VP-APP-PENDING-002',
        'sec': BATCH_SEC,
        't':   'Trusted-time manual confirmation is shown when trusted-time cache is unavailable for offline session start',
        'method': METHOD,
        'req': 'DI-837 / DO-903; DO-732; DI-375 / DO-719; DI-322 / DO-692',
        'pre': (
            'The trusted-time cache is either absent or older than 15 days. '
            'Internet connectivity can be disabled using normal device controls without changing the device clock.'
        ),
        'proc': (
            '1. Confirm the trusted-time cache is absent or expired: either use a freshly installed build or allow more than 15 days to elapse since the last online trusted-time sync.\n'
            '2. Disable Wi-Fi and mobile data using the normal device controls.\n'
            '3. Open the app and navigate to the sensor or transmitter setup screen.\n'
            '4. Attempt to start or resume a CGM session.\n'
            '5. Restore Wi-Fi and mobile data after the observation and record all screens encountered.'
        ),
        'exp': (
            '1. The trusted-time cache is confirmed absent or older than 15 days; the device is not connected to the internet.\n'
            '2. The phone is offline; no internet connection is active.\n'
            '3. The sensor or transmitter setup screen is displayed.\n'
            '4. A manual time and timezone confirmation screen is displayed before the session proceeds, per DI-322/DO-692 and DO-732, requiring the user to confirm the device date and time is correct.\n'
            '5. Internet is restored; the app continues normally; all screens encountered during the offline flow are recorded.'
        ),
        'ev': (
            'Offline state screenshot; trusted-time cache state or install date; '
            'session start attempt screenshots; '
            'manual time/timezone confirmation screen screenshot showing the confirmation prompt and controls; '
            'execution record.'
        ),
    },
    {
        'id':  'VP-APP-PENDING-003',
        'sec': BATCH_SEC,
        't':   'Manual Sensor ID entry and expiry confirmation while internet is unavailable',
        'method': METHOD,
        'req': 'DI-716 / DO-819; DI-820 / DO-882',
        'pre': (
            'An approved Sensor Test ID and sensor packaging are available. '
            'The user is in new-sensor setup and internet connectivity can be disabled using normal device controls.'
        ),
        'proc': (
            '1. Disable Wi-Fi and mobile data using the normal device controls and confirm the phone is offline.\n'
            '2. On the Scan your sensor screen, tap Type manually.\n'
            '3. Enter the approved Sensor Test ID into the Sensor ID field and tap Continue.\n'
            '4. On the Confirm Sensor ID screen, verify the Sensor ID matches the entered value and tap Continue.\n'
            '5. Observe and record all screens displayed before physical sensor-application guidance begins.'
        ),
        'exp': (
            '1. The phone is confirmed offline; no internet connection is active.\n'
            '2. The manual entry section expands showing the Sensor ID field and the static expiry guidance '
            '"Before applying the sensor, check the expiry date on the packaging and make sure the sensor has not expired."\n'
            '3. The Confirm Sensor ID screen displays the body "Sensor ID: [entered ID] — Please check that this ID '
            'exactly matches the Sensor ID printed on your sensor packaging. An accurate Sensor ID is required for '
            'correct sensor identification and recall handling." Edit Sensor ID and Continue controls are present.\n'
            '4. An explicit expiry-confirmation step is presented — a screen or control requiring the user to actively '
            'confirm the sensor has not expired — before physical sensor-application guidance begins, per DI-820/DO-882.\n'
            '5. Physical sensor-application guidance is displayed only after the expiry confirmation is completed; '
            'all screens are recorded in the execution record.'
        ),
        'ev': (
            'Offline state screenshot; Scan your sensor screen showing expanded manual entry and static expiry guidance; '
            'Confirm Sensor ID screen screenshot showing entered ID and body text; '
            'expiry-confirmation step screenshot showing the confirmation control; '
            'physical application guidance screen; execution record.'
        ),
    },
    {
        'id':  'VP-APP-PENDING-004',
        'sec': BATCH_SEC,
        't':   'Sensor-expiry advance reminders and final expiry notification',
        'method': METHOD,
        'req': 'DI-845 / DO-943',
        'pre': (
            'The approved sensor-expiry reminder schedule is defined in Protocol Test Data '
            '(Quality/RA/Product sign-off required before execution). Notification permission is enabled.'
        ),
        'proc': (
            '1. Record the current sensor remaining time from My CGM or Home.\n'
            '2. At each approved advance-reminder point defined in Protocol Test Data, observe the notification or in-app reminder shown.\n'
            '3. Record the notification priority, title and body text at each reminder point.\n'
            '4. Continue to the final sensor expiry condition.\n'
            '5. Observe and record the final expiry notification priority, title and body text, and the session state shown on My CGM and Home.'
        ),
        'exp': (
            '1. The sensor remaining time is recorded before the first reminder point.\n'
            '2. At each advance-reminder point in Protocol Test Data, a reminder notification or in-app indicator is shown.\n'
            '3. Each advance reminder uses the approved priority and wording defined in Protocol Test Data.\n'
            '4. The final expiry condition is reached and confirmed.\n'
            '5. A higher-priority expiry notification is shown indicating the CGM sensor has expired and no longer produces session data, per DI-845/DO-943.'
        ),
        'ev': (
            'Screenshots of each advance reminder notification and in-app indicator; '
            'screenshot of the final expiry notification showing priority, title and body text; '
            'My CGM and Home screenshots showing post-expiry session state; execution record.'
        ),
    },
]

# ── run-order versions ──

PENDING_RO = [
    {
        'id':           'VP-APP-PENDING-001',
        'title':        PENDING_COMPACT[0]['t'],
        'requirement':  PENDING_COMPACT[0]['req'],
        'preconditions':PENDING_COMPACT[0]['pre'],
        'procedure':    PENDING_COMPACT[0]['proc'],
        'expected':     PENDING_COMPACT[0]['exp'],
        'evidence':     PENDING_COMPACT[0]['ev'],
    },
    {
        'id':           'VP-APP-PENDING-002',
        'title':        PENDING_COMPACT[1]['t'],
        'requirement':  PENDING_COMPACT[1]['req'],
        'preconditions':PENDING_COMPACT[1]['pre'],
        'procedure':    PENDING_COMPACT[1]['proc'],
        'expected':     PENDING_COMPACT[1]['exp'],
        'evidence':     PENDING_COMPACT[1]['ev'],
    },
    {
        'id':           'VP-APP-PENDING-003',
        'title':        PENDING_COMPACT[2]['t'],
        'requirement':  PENDING_COMPACT[2]['req'],
        'preconditions':PENDING_COMPACT[2]['pre'],
        'procedure':    PENDING_COMPACT[2]['proc'],
        'expected':     PENDING_COMPACT[2]['exp'],
        'evidence':     PENDING_COMPACT[2]['ev'],
    },
    {
        'id':           'VP-APP-PENDING-004',
        'title':        PENDING_COMPACT[3]['t'],
        'requirement':  PENDING_COMPACT[3]['req'],
        'preconditions':PENDING_COMPACT[3]['pre'],
        'procedure':    PENDING_COMPACT[3]['proc'],
        'expected':     PENDING_COMPACT[3]['exp'],
        'evidence':     PENDING_COMPACT[3]['ev'],
    },
]


def update_file(path, is_compact):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    before = len(data)
    old_ids = set(OLD_TO_NEW.keys())

    # verify all old IDs exist
    found = {c['id'] for c in data if c['id'] in old_ids}
    missing = old_ids - found
    if missing:
        sys.exit(f'ERROR: IDs not found in {path.name}: {missing}')

    # remove old cases
    data = [c for c in data if c['id'] not in old_ids]

    # add new batch at end
    if is_compact:
        for c in PENDING_COMPACT:
            data.append(c)
    else:
        for c in PENDING_RO:
            data.append(c)

    after = len(data)
    assert after == before, f'Count changed unexpectedly: {before} -> {after}'

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'{path.name}: removed {sorted(old_ids)}, added PENDING-001..004 ({before} -> {after} cases)')


update_file(COMPACT, is_compact=True)
update_file(RO,      is_compact=False)

# regenerate console
result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts/generate_unified_console.py')],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(result.stdout)
if result.returncode != 0:
    print('GENERATOR ERROR:', result.stderr)
    sys.exit(1)

print('Done. New IDs: VP-APP-PENDING-001 through VP-APP-PENDING-004')
