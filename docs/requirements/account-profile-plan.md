# Account profiles for the 20 data-dependent blocked cases

## Decision

- Recommended: **3 account profiles / 3 accounts**.
- Minimum possible: **2 accounts** if the restore and regional-configuration profiles are combined.
- Existing account `rekod43112@maxtanie.com` can be used as the historical/report profile after its timing windows are refreshed and documented.

## Profile A — Historical, Home and Reports

**Accounts required:** 1

**Cases covered:** 18

- VP-APP-HOME-006
- VP-APP-HOME-007
- VP-APP-HOME-008
- VP-APP-REPORT-001
- VP-APP-REPORT-002
- VP-APP-REPORT-005
- VP-APP-REPORT-016
- VP-APP-REPORT-DAY-004
- VP-APP-REPORT-WEEK-002
- VP-APP-TAR-001
- VP-APP-TAR-002
- VP-APP-TAR-004
- VP-APP-TBR-001
- VP-APP-TBR-002
- VP-APP-TBR-004
- VP-APP-VAR-001
- VP-APP-VAR-002
- VP-APP-VAR-004

**Required state:**

- Verified account with completed onboarding.
- Approved low/high thresholds recorded in TD-11 and TD-12.
- Historical glucose across 3-day, 7-day, 15-day and 90-day selectors.
- At least three different days containing readings.
- One known graph point with timestamp and expected value for TD-19.
- One documented missing-data interval or genuine sensor-session boundary for TD-20.
- A populated report period and a selectable no-data period for TD-24.
- Above-range, below-range and varied readings so TAR, TBR and Variability calculations are non-zero and checkable.
- Reports opened online before the offline report test so local data is cached.

**Existing account status:**

`rekod43112@maxtanie.com` already has 20,115 readings over 14 days, readings on more than three days, known high/low patterns, a 45-minute gap, events, calibrations and 89/90/91-day boundary data. Exact time-dependent windows must be refreshed immediately before QA execution.

**Restriction:** VP-APP-REPORT-DAY-004 says the discontinuity must not be created by backend manipulation. The synthetic gap can only be used if Quality/Test Engineering formally accepts it as controlled test data. Otherwise, document a naturally occurring gap or physical sensor-session boundary.

## Profile B — Server restoration

**Accounts required:** 1

**Cases covered:** 1

- VP-APP-HOSTED-SIGNIN-012

**Required state:**

- Verified account with known server-held readings/events inside the approved restoration window.
- Exact item type, timestamp/value and destination screen recorded before execution.
- Fresh installation or cleared local app state so the server items are initially absent locally.
- If the optional local-only item is tested, create and record it through the app before login; the seeder cannot prove local retention by itself.
- Include readings less than 90 days old, exactly 90 days old and more than 90 days old, generated relative to the actual execution timestamp.

## Profile C — Regional configuration

**Accounts required:** 1

**Cases covered:** 1

- VP-APP-HOSTED-SIGNIN-014

**Required state:**

- Verified account with completed onboarding.
- Country/region explicitly recorded.
- Expected glucose unit explicitly recorded.
- Expected supported language or fallback language explicitly recorded.
- App logged out before execution and any previously used account configuration documented.

The existing account has country `PK` and time zone `Asia/Karachi`, but completed onboarding, glucose-unit selection and language/fallback still need UI verification.

## Account request

For the recommended three-account setup, retain the existing account for Profile A and provide **two new Keycloak accounts with self-patients**:

1. One account for Profile B — server restoration.
2. One account for Profile C — regional configuration.

If account availability is limited, Profiles B and C can share one new account, giving a minimum total of two accounts. The account must be reset between the two executions and the regional settings must remain controlled.
