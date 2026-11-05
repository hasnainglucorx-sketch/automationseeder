# Coverage check for the 20 data-dependent cases

Checked: 2026-10-01

## Result

- Fully covered now: **19 of 20**
- Conditionally covered with verified data: **1 of 20**
- Not covered: **0 of 20**

## Historical, Home and Reports account

Account: `rekod43112@maxtanie.com`

Verified state: the original 20,115-reading 14-day fixture is preserved, the recent 1,395-reading fixture contains the documented 45-minute gap, 168 events and 14 calibrations are present, thresholds are 70/180 mg/dL, and a refreshed isolated 89/90/91-day boundary fixture is verified.

| Test case | Status | Evidence or remaining execution step |
|---|---|---|
| VP-APP-HOME-006 | Covered | Multiple ranges, thresholds and known gap exist. |
| VP-APP-HOME-007 | Covered | Deterministic readings provide a known timestamp/value point. |
| VP-APP-HOME-008 | Covered | More than two Home ranges contain readings. |
| VP-APP-REPORT-001 | Covered | Historical glucose is available. |
| VP-APP-REPORT-002 | Covered | Multiple selectable report windows contain data. |
| VP-APP-REPORT-005 | Covered with device pre-step | Open the populated report online before disabling connectivity. |
| VP-APP-REPORT-016 | Covered | Populated report windows exist for Key Insights/Focus Area. |
| VP-APP-REPORT-DAY-004 | Conditional; data ready | A recent controlled fixture was verified on 1 October 2026 with no readings from 07:23 through 08:07 PKT. In Reports select Day > 24 Hours and verify the line breaks between the 07:22 and 08:08 readings. The protocol prohibits backend-created discontinuities, so Quality must accept this synthetic fixture or QA must document a natural gap/session boundary. |
| VP-APP-REPORT-WEEK-002 | Covered | Readings exist on more than three different days. |
| VP-APP-TAR-001 | Covered | Populated historical windows exist. |
| VP-APP-TAR-002 | Covered | High readings produce checkable non-zero supporting statistics. |
| VP-APP-TAR-004 | Covered by no-data account | `similoh324@caps7.com` has 217 varied readings in the 3-day window, including 72 high readings, while its latest 24-hour window is empty. |
| VP-APP-TBR-001 | Covered | Populated historical windows exist. |
| VP-APP-TBR-002 | Covered | Low readings produce checkable non-zero supporting statistics. |
| VP-APP-TBR-004 | Covered by no-data account | `similoh324@caps7.com` has 217 varied readings in the 3-day window, including 37 low readings, while its latest 24-hour window is empty. |
| VP-APP-VAR-001 | Covered | Populated historical windows exist. |
| VP-APP-VAR-002 | Covered | Varied readings produce checkable variability statistics. |
| VP-APP-VAR-004 | Covered by no-data account | `similoh324@caps7.com` has varied readings in the populated 3-day window while its latest 24-hour window is empty. |
| VP-APP-HOSTED-SIGNIN-012 | Covered with device pre-step | The account contains verified server-held readings, events, sessions and refreshed historical boundary data. Relative to 1 October 2026 13:48:37 PKT: 2 July 13:48:37 is 91 days old (98 mg/dL), 3 July 13:48:37 is exactly 90 days old (100 mg/dL), and 4 July 13:48:37 is 89 days old (102 mg/dL). Clear/reinstall the app before login, then verify restoration. Run `python -m src.boundary_seed --refresh` immediately before a later exact-boundary execution. |

## Separate server-restoration account

Account role: `server-restoration`

| Test case | Status | Missing state |
|---|---|---|
| VP-APP-HOSTED-SIGNIN-012 | Optional isolation account | This account is not required for restoration coverage because `rekod43112@maxtanie.com` contains the boundary fixture. It now also serves as the controlled no-data account for TAR-004, TBR-004 and VAR-004. |

## Regional-configuration account

Account role: `regional-configuration`

| Test case | Status | Evidence and missing state |
|---|---|---|
| VP-APP-HOSTED-SIGNIN-014 | Covered with device verification | `362qq@aristocrtic.live` is active and backend-verified with registered region/country US, time zone America/New_York, mg/dL expectation, 70/180 mg/dL thresholds and English fallback expectation. During execution, capture User Profile Country, a glucose-unit screen, and Settings > Language to prove the visible values. |

## Actions needed for complete coverage

1. For VP-APP-HOSTED-SIGNIN-012, clear/reinstall the app before signing in to `rekod43112@maxtanie.com`, and record the server item timestamps/values used for verification.
2. The boundary is current relative to 1 October 2026 13:48:37 PKT. For a later exact-boundary execution, run `python -m src.boundary_seed --refresh` because timestamp ages continuously change.
3. For VP-APP-HOSTED-SIGNIN-014, sign in to the regional account and capture the visible US country, mg/dL unit and English language/fallback screens.
4. For TAR-004, TBR-004 and VAR-004, use `similoh324@caps7.com`; select 24 Hours for the empty state and 3 Days to confirm valid content returns.
5. Obtain Quality/Test Engineering acceptance for the synthetic gap in VP-APP-REPORT-DAY-004, or use a naturally occurring gap/session boundary.
