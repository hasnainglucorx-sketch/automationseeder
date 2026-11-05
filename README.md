# Modus QA automation and protocol workspace

This project supports **PRT-0392: Modus App UIRS Test Cases** and **PRT-0396: Modus Portal UIRS Test Cases**. It combines a Python API fixture seeder, controlled test-case sources, a generated browser console, and saved verification/readiness reports.

Read [PROJECT_STATE.md](PROJECT_STATE.md) for the verified state on **14 October 2026**, refactoring changes, and remaining work. Read [CLAUDE.md](CLAUDE.md) before editing protocol content. Older counts in handoffs and working instructions are historical; use fresh audit results.

## Capabilities

- Deterministic synthetic glucose readings, gaps, low periods, events, calibrations, and history/timezone fixtures.
- OAuth PKCE login, token refresh, account binding, resumable checkpoints, and paginated field-level read-back verification.
- A unified HTML console for browsing both protocols, recording results and evidence, and viewing test assets.
- Case consistency checks and reports about account, fixture, hardware, and acceptance-criteria dependencies.

The console is a QA aid, not the official controlled protocol record. Execution data lives in browser localStorage. Export records before clearing browser data or switching profiles/origins; files on disk do not automatically contain all browser execution history.

## Setup

Use Python **3.10 or newer** (validated with 3.12.10), PowerShell for the wrapper, and system `curl.exe` on Windows (`curl` elsewhere). The Python code uses the standard library. Portal fixtures need IANA timezone data for `Europe/London`; install `tzdata` only if the timezone check fails.

```powershell
python --version
curl.exe --version
python -c "from zoneinfo import ZoneInfo; print(ZoneInfo('Europe/London'))"
# Only if timezone data is missing:
python -m pip install tzdata
```

Run commands from the project root. There is no root dependency manifest or installable Python package. `docs/requirements/requirements.txt` contains product requirements, not pip dependencies. The PowerShell wrapper prefers the Codex bundled Python in the user's cache, then falls back to `python`; direct Python commands use your selected interpreter.

## Offline validation

```powershell
python -m unittest discover -s tests
python -m compileall -q src tests
python scripts/check_case_rules.py
python scripts/check_portal_case_rules.py
```

The iOS checker prints findings but currently returns zero even when violations exist: inspect the summary. The Portal checker returns nonzero for findings. Neither proves application behavior or passing execution.

If a restricted Windows sandbox denies access to the system temporary directory, use workspace scratch files for that shell session:

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp'
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
$env:TMP = $env:TEMP
python -m unittest discover -s tests
```

Local generation and contract inventory require no login or API access:

```powershell
python -m src.seeder generate --end 2026-10-14T00:00:00Z --output output/example-readings.json
python -m src.seeder inventory
```

## Main seeder workflow

For an authorized QA account with a self patient and no sessions:

```powershell
.\seeder.ps1 login
.\seeder.ps1 prepare -Email 'qa-account@example.com' -RunFile 'output/new-run.json'
.\seeder.ps1 run -RunFile 'output/new-run.json'
.\seeder.ps1 verify -RunFile 'output/new-run.json'
```

Login prompts for credentials. Main-run `prepare` authenticates and reads remote state, then writes a local plan; it does not create a missing patient. `run` writes to the API. `verify` reads the API and updates local reports. Omitting `-RunFile` selects the existing `output/qa-run.json`, so use an explicit file for a new run.

Individual phases are `profile`, `session`, `smoke`, `readings`, `events`, `calibrations`, and `alarms`. Resume using `run`. Completed actions are skipped; readings use session/index idempotency. Uncertain resource-create outcomes stay `in_flight` and require reconciliation. Session reconciliation supports server-assigned IDs. Use one process per checkpoint: no process locking is implemented.

Keep checkpoints: resource identities and progress are needed for safe resume. Do not edit an uploaded dataset's plan. Synthetic transmitters and firmware hashes are fixtures, not proof of device pairing.

The API base URL is in `src/seeder.py`. Authentication defaults are in `src/auth.py`; `MODUS_ISSUER` and `MODUS_REDIRECT` override issuer/callback settings. Changing authentication does not change the API host. Tokens live in `.secrets/tokens.json`; do not share them. The low-level read command accepts `MODUS_ACCESS_TOKEN` from the local environment.

## Portal fixtures

```powershell
python -m src.portal_fixture_seed --help
# Local-only; replaces the public fixture manifest using today's anchor:
python -m src.portal_fixture_seed plan
# Rebuilds the manifest using saved checkpoint anchors where available:
python -m src.portal_fixture_seed manifest
```

Supported aliases: `QA-PORTAL-HISTORY-01`, `QA-PORTAL-SPARSE-01`, `QA-PORTAL-MMOL-01`, `QA-PORTAL-SECONDARY-01`, `QA-PORTAL-TIMEZONE-01`.

API operations require `--alias`. The controlled `.secrets/portal-test-accounts.json` list contains `alias`, `email`, and `password`; optional `user` and `self_patient` bind expected identities. Never copy real credentials into case sources or documentation.

**Portal `prepare` can create a missing patient remotely**, unlike main-run preparation. `run` uploads fixtures; `verify` reads them back. Preparing again can replace a local checkpoint, so preserve existing runs. Rolling-date fixtures require revalidation at execution time.

| Specialized module | Responsibility |
| --- | --- |
| `src/boundary_seed.py` | Isolated 89/90/91-day fixture; refresh archives the previous checkpoint |
| `src/recent_gap_seed.py` | Recent readings with a controlled gap |
| `src/no_data_profile_seed.py` | Older history with an empty latest 24 hours |
| `src/regional_profile_seed.py` | Regional profile/settings fixture |
| `src/account_coverage_verify.py` | Account coverage verification |
| `src/extract_schema.py` | Message descriptors extracted from captured portal source |

These utilities have specific account/checkpoint assumptions; inspect their entry points before invoking them. Several perform writes directly.

## Console maintenance

Canonical inputs under `output/console-update/`:

The JSON filenames retain their earlier PRT-0701/PRT-0702 names for compatibility;
the console and exports use the current PRT-0392/PRT-0396 protocol names.

- `PRT-0701-cases.json`: compact iOS case source.
- `PRT-0701-run_order.json`: full iOS run-order representation.
- `PRT-0702-cases.json`: compact Portal case source.
- `PRT-0701-appendixC.json`: controlled test-data source where applicable.

Edit the appropriate JSON representations first, then regenerate and validate affected IDs:

```powershell
python scripts/generate_unified_console.py
python scripts/check_case_rules.py CHANGED_APP_CASE_ID
python scripts/check_portal_case_rules.py CHANGED_PORTAL_CASE_ID
```

Open `CGMX1-Console.html` in a browser. It is the only generated console; regenerate it from the JSON sources rather than editing it directly.

The generator also reads the Portal fixture manifest, test-asset catalog, and optional alias/email mappings from the secret account list. Generated HTML can include account emails; it is not automatically anonymized. Passwords must remain outside protocols, evidence, and HTML.

Follow `CLAUDE.md`: unique IDs, synchronized representations, state-only preconditions, matching numbered procedure/expected items, embedded-source equality, and visual inspection. Do not bulk-copy one case representation over another merely to clear audit findings. Other scripts include historical migrations and must not be run as one batch pipeline.

## Architecture and files

| Path | Responsibility |
| --- | --- |
| `seeder.ps1` | Main command wrapper |
| `src/auth.py` | PKCE login, refresh, token cache |
| `src/seeder.py` | Contract-checked curl transport and deterministic readings |
| `src/qa_run.py` | Planning, account binding, phase execution, reconciliation, verification |
| `src/api_helpers.py` | Transport-independent pagination and payload comparison |
| `src/storage.py` | Shared JSON checkpoint replacement |
| `tests/` | Offline tests with mocked remote calls |
| `scripts/generate_unified_console.py` | Canonical unified console generator |
| `scripts/check_*.py` | Current case-source and embedded-console validation |
| `schemas/` | Protobuf contract and extracted message metadata |
| `docs/requirements/` | Product requirements evidence, coverage plans, fixture notes |
| `docs/portal.js`, `docs/portal.html` | Captured source evidence, not the editable console frontend |
| `output/` | Canonical case sources, resumable checkpoints, reports, generated artifacts |
| `.secrets/` | Local credentials and tokens |
| `Claude-Handoff-2026-10-02/` and ZIP | Historical snapshot; do not restore over current files |
| `outputs/` | Portal test-asset workbook and rendered reference images |

Do not delete `output/` as a build cleanup: it contains authoritative inputs and resume state. The current `.gitignore` excludes this entire directory, and this workspace has no Git repository. Review the layout before introducing version control so canonical sources are preserved without committing secrets or account-bearing execution data.

Historical references: [previous seeder README](docs/HISTORICAL-SEED-RUN.md), [earlier handoff](CLAUDE-HANDOFF.md). Current findings: [PROJECT_STATE.md](PROJECT_STATE.md).
