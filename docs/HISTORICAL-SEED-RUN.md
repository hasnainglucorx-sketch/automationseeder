# Historical seeder notes (before the 14 October 2026 refactor)

This is the previous README, preserved as historical evidence. Its counts and deployment observations are dated; use the root README.md and PROJECT_STATE.md for current instructions and status.

# Modus QA automation seeder

Working QA seeder with OAuth PKCE login, automatic token refresh, persistent run
checkpoints, account identity checks, deterministic readings, and paginated read-back
verification. Uses Python standard library and system curl. No Postman dependency.

## Completed QA run

The designated test patient's data has been seeded and read back successfully:

- One active synthetic session.
- 20,115 readings, September 15–29, 2026, at one-minute intervals with a 45-minute gap.
- 84 events: 42 carbohydrate, 14 insulin, 14 activity, 14 notes.
- 14 calibrations.
- Synthetic profile in Asia/Karachi, with the existing matching alert thresholds.

Alarm writes cannot complete on the current deployment: CreateAlarm and ListAlarms
return HTTP 404. They remain in the run plan and are not reported as seeded.

The data is synthetic QA fixture data. The firmware hash and transmitter identifier
describe fixtures, not physical hardware. No actual device pairing was performed.

## Use

From this directory in PowerShell:

```powershell
.\seeder.ps1 verify
.\seeder.ps1 run       # Resume this run; completed writes are skipped.
```

If the refresh token expires, sign in again:

```powershell
.\seeder.ps1 login
```

The login command prompts for email and password with hidden password input. The
password is not saved. Tokens are stored in the ignored `.secrets` directory.
Do not share that directory. The account email, API user ID, and self-patient ID
must match the saved run before reads or writes proceed.

For another account that already has a self patient and no sessions:

```powershell
.\seeder.ps1 login
.\seeder.ps1 prepare -Email 'new-test-account@example.com' -RunFile 'output/another-run.json'
.\seeder.ps1 run -RunFile 'output/another-run.json'
```

The prepare step creates a local plan. The run step applies it. A different dataset
requires a new reviewed plan; changing an existing run's data after upload is not
supported. New patient creation when selfPatient is absent is not automated yet.

Individual phases are also available: profile, session, smoke, readings, events,
calibrations, alarms, verify. `inventory` lists RPCs from the supplied contract.

## Files and verification

- `output/qa-run.json`: exact input data, request bodies, resource IDs, responses,
  batch progress, and errors. Required for resuming; do not delete it.
- `output/qa-run-verification.json`: read-back results, missing/mismatched indices,
  duplicates, event/calibration comparisons, statistics, and current glucose.
- `schemas/deployed-messages.json`: 24 message descriptor files extracted from the
  public QA portal bundle. Extraction preserves field types, enums, oneofs, and
  field behavior flags. This is message metadata, not a complete protobuf compiler.
- `docs/portal.js` and `docs/portal.html`: public source evidence used for extraction.

All readings are compared by index, timestamp, and glucose value. Events and
calibrations are checked against planned fields and returned resource identities.
Statistics for rolling windows can exclude the earliest samples as time advances;
the session read-back is the exact total check.

Transport errors or server errors during resource creation leave an uncertain
request in flight. It must be reconciled before replay; the tool does not blindly
retry non-idempotent creates. Session reconciliation handles the deployed server
assigning its own session ID despite the requested session_id. Reading replay uses
the contract's session/index idempotency. Only one process should run a given
checkpoint at a time.

## Observed deployment differences

Verified September 29, 2026:

- Direct Connect JSON API calls work with the system HTTP client.
- PKCE login and token refresh work for the designated account.
- CreateSession accepts a synthetic transmitter and an omitted optional sensor.
- ListDevices returns 501: device pairing/binding is not implemented.
- GetServiceInfo, ListTermsAcceptances, CreateAlarm, and ListAlarms return 404.
- Session and patient operations did not require a terms acceptance in this run.
- UpdatePatientSettings rejected an advertised threshold field in update_mask.
  Existing settings already matched the plan, so they were reused and verified.
- FirmwareVersion uses numeric major/minor/patch and an image hash. The previous
  PDF's image_sha256 value of "3.1.0" was not used.

Sharing invitations, co-administrator invitations, account deletion, exports,
firmware releases, and recalls are not part of the synthetic patient-data run.

## Tests

```powershell
python -m unittest discover -s tests
```

Eight tests pass, covering deterministic generation, the intentional gap/low period,
account switch rejection, server-assigned session IDs, pagination, rejected-batch
checkpoint behavior, and field-level read-back comparison.

