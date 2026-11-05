# Project state — 14 October 2026

This snapshot distinguishes fresh local checks from dated saved reports. No live API seeding, account login, hardware testing, or browser execution was performed during this refactor. Structurally valid cases are not necessarily passed application tests.

## Fresh local verification

| Check | Result |
| --- | --- |
| Python runtime | 3.12.10 |
| Offline tests | 21 passed: 14 existing and 7 added |
| Python compilation | `src/` and `tests/` pass |
| Main and Portal CLI help | Both load successfully |
| PRT-0392 Modus App sources | 497 cases each; unique IDs and identical ordered ID lists |
| PRT-0396 Modus Portal source | 574 cases; unique IDs |
| Generated console | One canonical `CGMX1-Console.html` |
| PRT-0392 structural audit | 1,387 findings across 282 cases |
| PRT-0396 structural audit | 574 checked, zero findings |

The iOS findings comprise 1,112 mapped-field differences, 274 numbering findings, and one actionable precondition in `VP-APP-PROFILE-008`. These are existing content issues; case definitions were not modified during this refactor. Fresh post-cleanup logs: [iOS audit](output/refactor-validation/app-audit-after-cleanup.txt), [Portal audit](output/refactor-validation/portal-audit-after-cleanup.txt).

Tests used workspace `tmp/` for TEMP/TMP because the sandbox's system temporary directory denied filesystem operations. This changes test scratch placement, not production checkpoints.

## Completed code refactor

- Added `src/storage.py` and consolidated checkpoint writes from `qa_run`, `boundary_seed`, `no_data_profile_seed`, and `portal_fixture_seed`. Serialization happens before touching temporary files; replacement follows a successful write. Missing parent directories are created.
- Added `src/api_helpers.py` for protobuf JSON field-name conversion, recursive planned-field comparison, and cursor pagination.
- Preserved `qa_run.paged`, `qa_run.matches_payload`, and existing save entry points for callers. Authentication is still obtained for each page.
- Preserved CLI commands, saved JSON formats, account binding, session reconciliation, rejected-reading handling, and uncertain-request safeguards.
- Added regression tests for checkpoint replacement and failure preservation, caller-input isolation, per-page authentication, empty pages, propagated transport errors, and nested response comparison.
- Expanded `README.md` into a project guide and preserved its former content as `docs/HISTORICAL-SEED-RUN.md`.
- Consolidated three identical generated consoles into one canonical HTML file and removed the separate Case Review, Test Runner, and Portal review-guide surfaces.

Temporary checkpoint names now consistently append `.tmp` to the full filename (for example `run.json.tmp`). Final filenames are unchanged. Existing temporary files are not treated as completed checkpoints. The helper does not add process locking or guarantee durability after power loss. Authentication's token cache retains its separate implementation.

This is a focused runtime refactor. The console generator and historical migration scripts remain in place; controlled protocol content has not been bulk-rewritten.

## Saved execution/readiness evidence

The following comes from existing reports, not fresh live verification.

### iOS blocked cohort — report dated 14 October 2026

The formal blocked cohort has 75 unique original cases, appearing twice in 150 extracted rows.

| Source-review category | Cases |
| --- | ---: |
| Corrected; live execution/setup confirmation required | 32 |
| Corrected; fixture revalidation required | 19 |
| Definition repair required | 8 |
| Dependency or acceptance criteria open | 12 |
| Pending implementation/validation | 4 |

The report identifies 63 non-pending definitions passing its structural review, including 12 with special unresolved prerequisites. This does not establish 63 passing reruns. The eight definition repairs concern HOSTED-SIGNIN-014, NOTIFY-015, NOTIFY-020, HOME-016, REPORT-008, REPORT-013, REPORT-DAY-001, and ABOUT-008 (all prefixed `VP-APP-`). Pending cases are `VP-APP-PENDING-001` through `004`.

The detailed dated review files are retained in the cleanup archive named below.

### Web Portal readiness — reports dated 12 October 2026

| Saved classification | Cases |
| --- | ---: |
| Blocked by account | 104 |
| Blocked by account and test asset | 176 |
| Blocked by test asset | 75 |
| Ready | 175 |
| Ready with manual setup | 44 |

The archived missing-account report records 14 missing login aliases affecting 280 cases. Availability has not been rechecked against live provisioning.

### Historical seeding and deployment

The prior README records a successful 29 September 2026 run with 20,115 readings, 84 events, and 14 calibrations. It records alarm endpoints returning 404 and device listing returning 501. These are historical observations, not current endpoint-health guarantees. Saved read-back evidence remains under `output/`. Time-relative fixtures may no longer match their intended rolling windows; reverify before execution. See [historical notes](docs/HISTORICAL-SEED-RUN.md).

## Remaining work

1. Review the 282 affected iOS cases in controlled batches using actual UI and requirement evidence. Prioritize the eight definition repairs in the blocked cohort. Audit findings alone do not establish expected behavior.
2. Confirm pending behavior, hardware/build fixtures, and open acceptance criteria. Obtain execution evidence before changing blocked/pending outcomes.
3. Provision or confirm missing Portal accounts and test assets; rerun readiness review and application tests.
4. Revalidate rolling-date fixtures and current API support before live seeding.
5. Separate canonical case inputs from generated output before Git tracking; the existing ignore rule would omit authoritative sources.
6. In a later code refactor, separate the monolithic console generator into template, rendering, and entry-point modules, with isolated generation tests. It currently executes at import; that behavior was not changed here.
7. Normalize checker exit codes and introduce automated validation with an explicit policy for existing iOS findings. This workspace currently has no CI setup, and unit tests do not cover browser rendering or live services.

## Refreshing this document

Run the offline commands in [README.md](README.md), save fresh audit outputs, and update counts with a review date. Preserve dated reports as historical evidence. Do not replace execution statuses with structural-audit results or copy credentials into documentation.

Obsolete and duplicated HTML consoles/review portals, their dedicated generators,
and legacy localStorage replay helpers were retired on 14 October 2026. Reports,
evidence, general maintenance scripts, handoff material, and temporary renders
remain unchanged. See [CLEANUP.md](CLEANUP.md) and
`archive/retired-ui-2026-10-14/` for recovery details.
