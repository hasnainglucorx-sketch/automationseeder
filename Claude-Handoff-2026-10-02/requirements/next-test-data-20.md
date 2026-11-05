# Next 20 blocked cases - required test data and setup

Checked against the PRT-0701 iOS run report and the applicable DI/DO material on 1 October 2026.

## Decision

- These 20 cases are not ordinary historical-data seeding cases.
- Two controlled account profiles are sufficient: `QA-ALARM-LIVE-01` and `QA-SENSOR-SETUP-01`.
- `VP-APP-HOSTED-REG-005` uses a fresh temporary mailbox and controlled input values; it does not require a pre-created account.
- The alarm cases require live packets from a real transmitter or an approved transmitter simulator. Historical readings written through the patient API cannot prove real-time alarms.
- The scan and Sensor ID cases require controlled GS1/QR/manual-ID assets and known backend product states.

## Account profiles

| Reference | Required state | Cases |
|---|---|---|
| `QA-ALARM-LIVE-01` | Verified account, onboarding complete, notification permission enabled, active expected CGM session, real transmitter or approved simulator delivering one-minute live measurements | NOTIFY-015, NOTIFY-020, MEDIUM-002/003, CRITICAL-013/014/015/018/019 |
| `QA-SENSOR-SETUP-01` | Verified account with onboarding/session setup available and no active sensor session; camera permission can be reset; internet can be enabled/disabled | SCAN-003/008/009/010/011 and SENSOR-ID-003/004/005/006/007 |
| Temporary registration data | New unregistered mailbox, valid names/region, approved compliant and non-compliant passwords | HOSTED-REG-005 |

## Required resources

| Resource reference | Required controlled item |
|---|---|
| `KIT-LIVE-01` | Real transmitter or approved simulator capable of an active session, stopping live delivery, omitting selected indexes while continuing the latest packet, entering phone sleep/doze, and sending permitted future-drift packets |
| `BUILD-UPDATE-01` | Installed older approved build plus a newer optional/encouraged build exposed through the normal controlled update channel |
| `SENSOR-VALID-01` | Valid, unused, unexpired and non-recalled sensor package with recorded GS1/QR data and manual Sensor ID |
| `BARCODE-WRONGTYPE-01` | Valid transmitter/product barcode that is intentionally the wrong product type at the sensor prompt |
| `SENSOR-EXPIRED-01` | Sensor identifier whose controlled expiry state is already expired at execution time |
| `SENSOR-RECALLED-01` | Quality-controlled sensor identifier already marked recalled; testers must not change recall state during execution |
| `SENSOR-INVALID-01` | Structurally invalid or known-nonexistent Sensor ID approved for negative testing |

## Case requirements

| # | Test case | Required test data/setup | Preparation method |
|---:|---|---|---|
| 1 | `VP-APP-HOSTED-REG-005` | Fresh temporary mailbox; valid registration names/region; one password violating one documented Keycloak rule; one password satisfying all documented rules. Record the exact rule and values outside evidence containing secrets. | Manual input. Obtain the approved password policy before execution. |
| 2 | `VP-APP-NOTIFY-015` | `QA-ALARM-LIVE-01` synchronized normally, followed by a controlled silent new-data-check failure. DI-754/DO-869 specifies repeating notification after each 24 hours of connectivity errors. | Controlled network/service condition. Patient-data seeding alone is insufficient. |
| 3 | `VP-APP-NOTIFY-020` | `QA-ALARM-LIVE-01` in an active session on `BUILD-UPDATE-01`, with a newer optional build discoverable through the normal update mechanism. | Release/distribution environment plus real device. |
| 4 | `VP-APP-MEDIUM-002` | Normal live measurements, notifications enabled, DND/Focus configured, then live delivery interrupted while the expected session remains active. | `KIT-LIVE-01`; physical range/Bluetooth interruption or approved simulator control. |
| 5 | `VP-APP-MEDIUM-003` | Latest real-time measurement remains available, but at least one of the preceding 14 measurements used for the 15-measurement trend window is missing. | Approved simulator/packet-control sequence. Do not use ordinary historical API writes. |
| 6 | `VP-APP-CRITICAL-013` | Active expected session, a recorded last valid glucose value, then no live measurements through the medium-to-critical escalation point defined by DO-821. | `KIT-LIVE-01`; record actual medium and critical timestamps. Escalation is glucose-dependent, not a universal 45-minute value. |
| 7 | `VP-APP-CRITICAL-014` | Same no-data condition as CRITICAL-013 while the phone enters normal supported sleep/doze. | Real Android/iOS device plus `KIT-LIVE-01`; capture notification history after wake. |
| 8 | `VP-APP-CRITICAL-015` | Active session with normal live data, then internet disabled and phone time deliberately changed under the approved device-time procedure while delivery is interrupted. DO-951 invalidates the last live value after 90 seconds using a monotonic clock. | Real device and `KIT-LIVE-01`; restore time/network after evidence. |
| 9 | `VP-APP-CRITICAL-018` | Approved live packet sequence whose trusted measurement timestamps are a permitted few minutes ahead, with known packet indexes and arrival order. | Transmitter simulator/test firmware. Backend timestamp edits are not valid evidence. |
| 10 | `VP-APP-CRITICAL-019` | A repeatable medium-priority condition, notification permission enabled, audible volume, vibration, and DND/Focus configured with no app allow-list exception. | Use MEDIUM-002 or MEDIUM-003 setup and record first/repeat behavior. |
| 11 | `VP-APP-SCAN-003` | `QA-SENSOR-SETUP-01`, camera permission available, and `SENSOR-VALID-01` packaging at the sensor scan step. | Physical/printed controlled package used through the normal camera flow. |
| 12 | `VP-APP-SCAN-008` | Full recorded GS1/QR content for `SENSOR-VALID-01`, including product type and Sensor ID expected by the app/backend. | Normal camera scan while online. |
| 13 | `VP-APP-SCAN-009` | `BARCODE-WRONGTYPE-01`, preferably the matching controlled transmitter barcode, presented at the sensor prompt. | Normal camera scan; record that no sensor state is created. |
| 14 | `VP-APP-SCAN-010` | `SENSOR-EXPIRED-01` with recorded expiry date earlier than validated execution time. | Normal camera scan while trusted time is available; do not alter phone time to manufacture expiry. |
| 15 | `VP-APP-SCAN-011` | `SENSOR-RECALLED-01` whose recall state was supplied and approved by Quality before execution. | Normal scan/recall-check flow; tester must not create or change recall records. |
| 16 | `VP-APP-SENSOR-ID-003` | Manual Sensor ID printed on `SENSOR-VALID-01`, recorded exactly before execution. | Enter through the supported manual path while online. |
| 17 | `VP-APP-SENSOR-ID-004` | `SENSOR-INVALID-01` and the reason it is invalid, such as prohibited format/check digit or known-nonexistent ID. | Manual negative input; use an approved value, not an invented production-like identifier. |
| 18 | `VP-APP-SENSOR-ID-005` | `SENSOR-VALID-01` package and its exact printed Sensor ID for the confirmation comparison. | Manual entry followed by packaging confirmation. |
| 19 | `VP-APP-SENSOR-ID-006` | `SENSOR-EXPIRED-01`, its printed manual ID and expiry date, with trusted time available. | Manual path; verify expiry guidance/check occurs before physical application guidance. |
| 20 | `VP-APP-SENSOR-ID-007` | `SENSOR-VALID-01` manual ID, trusted-time state established online first, then Wi-Fi/mobile data disabled. | Manual ID offline flow; record whether cached trusted time or manual time/timezone confirmation is used. |

## What can be automated

- The seeder can provision the two patient/account profiles after their Keycloak users exist.
- It can record account/patient IDs, thresholds, and non-clinical fixture metadata.
- It cannot create valid physical GS1 packaging, camera evidence, real-time Bluetooth packet loss, OS sleep/doze, an app-store update, or approved recall/expiry states unless dedicated test-environment APIs exist for those systems.
- The current patient API must not be used to imitate real-time alarm packet arrival or to change recall state during a formal manual run.

## Inputs needed before execution

1. Two Keycloak test users for `QA-ALARM-LIVE-01` and `QA-SENSOR-SETUP-01`, unless Quality approves reuse of existing resettable accounts.
2. One live transmitter or approved simulator with packet-sequence control.
3. The five sensor/barcode assets listed above.
4. The approved Keycloak password policy.
5. Access to the controlled optional-update channel and the older/newer build pair.
6. Quality-approved instructions for service outage, device-time change, DND/Focus and sleep/doze execution.
