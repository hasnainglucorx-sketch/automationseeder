# Portal account fixtures

Portal test cases use the aliases below. Email addresses and passwords are kept
outside the protocol so an account can be replaced without rewriting cases.

| Alias | Account state | Covers |
|---|---|---|
| `QA-PORTAL-HISTORY-01` | Patient with verified minute readings across the last 90 days, deliberate empty days and one two-hour gap; profile, thresholds, calibration and events are populated | Overview, History, OGP, Compare, Assessment Report, export, time-in-range, high/low and performance cases |
| `QA-PORTAL-SPARSE-01` | Patient with one reading exactly three days before the fixture anchor | Sparse OGP, insufficient-data and empty-state cases |
| `QA-PORTAL-MMOL-01` | Patient configured for a mmol/L region with known high and low readings | Unit conversion and mmol/L display cases |
| `QA-PORTAL-SECONDARY-01` | Separate Patient identity with a small known dataset | Sharing, follower, cross-account isolation and authorization cases |
| `QA-PORTAL-TIMEZONE-01` | Patient with fixed winter, summer and UK daylight-saving-boundary timestamps | Browser time-zone and ordering cases |
| `QA-PORTAL-QUALITY-01` | Patient containing backend-approved reduced-quality readings | Quality-marker cases only; this fixture cannot be produced by the supplied AppService contract because `Reading` exposes no quality flag |
| `QA-PORTAL-HCP-01` | Provisioned HCP with active shares to `QA-PORTAL-HISTORY-01` and `QA-PORTAL-SECONDARY-01`; the live Connect Code page currently reports that this account is not linked to a practice | Patient List, shared Patient clinical view, search, profile and date-range cases |
| `QA-PORTAL-HCP-EMPTY-01` | HCP with no current Patient shares | Patient List empty-state case; still requires administrative provisioning |
| `QA-PORTAL-HCP-CLINIC-01` | HCP linked to the controlled clinic with a working Connect Code | Connect Code, QR download, printable poster and Patient consent cases; still requires administrative provisioning |
| `QA-PORTAL-CLINIC-ADMIN-01` | Clinic Administrator for the controlled clinic | Clinic management cases; requires administrative provisioning |
| `QA-PORTAL-ADMIN-01` | Modus Administrator with the permissions required by the case | Admin portal cases; requires administrative provisioning |
| `QA-PORTAL-SUPER-ADMIN-01` | High-access administrator with authenticator configured | Super Admin cases; requires administrative provisioning |

The direct API seeder is `python -m src.portal_fixture_seed`. It writes a
machine-generated verification manifest for the exact fixture dates and
expected values. Test cases reference the account alias and visible fixture
state; they do not contain an email address, password or workbook row.

## Current QA status

The five self-registerable Patient accounts are created, email-verified and
API-verified in QA. Their current seeded totals are:

| Alias | Verified readings |
|---|---:|
| `QA-PORTAL-HISTORY-01` | 123,720 |
| `QA-PORTAL-SPARSE-01` | 1 |
| `QA-PORTAL-MMOL-01` | 120 |
| `QA-PORTAL-SECONDARY-01` | 60 |
| `QA-PORTAL-TIMEZONE-01` | 10 |

Their replaceable email addresses are shown in the console under **Portal Test
Assets**. Passwords remain only in `.secrets/portal-test-accounts.json`.
`QA-PORTAL-QUALITY-01` still requires a backend-supported quality flag, and
the HCP and administrator accounts still require administrative provisioning.

## Account storage

Actual account details belong in `.secrets/portal-test-accounts.json`, which is
ignored by source control. Each Patient entry uses this shape:

```json
[
  {
    "alias": "QA-PORTAL-HISTORY-01",
    "email": "replaceable-test-email@example.com",
    "password": "stored-locally-only"
  }
]
```

Do not put credentials into the protocol JSON, generated HTML, fixture
manifest, screenshots or execution evidence.

## Execution rules

1. Refresh time-relative fixtures immediately before a formal run.
2. Run the seeder verification command and retain its non-secret manifest.
3. Sign in using the alias named in the case precondition.
4. Keep failure-injection cases separate from seeded-data cases. A seeded
   account cannot create an HTTP 500, timeout, aborted request or invalid API
   response.
5. Provision HCP and administrator permissions through the approved QA admin
   path. Patient self-registration cannot create those roles.
