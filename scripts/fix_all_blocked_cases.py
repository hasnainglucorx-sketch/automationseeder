"""
Fix all 43 blocked cases across five categories:

  A) TD- row cases  → replace with QA-MAIN-01 / Nobe references (8 cases)
  B) QA-HISTORY-01  → add fixture re-seed verification step + fix 1:1 (16 cases)
  C) QA-NODATA-01   → add fixture verification step + fix 1:1 (3 cases)
  D) Fixable false-positives → fix preconditions and/or 1:1 (7 cases)
  E) Hardware-blocked → fix proc/exp 1:1 only, preserve intent (9 cases)
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "output/console-update"
COMPACT_PATH = OUT / "PRT-0701-cases.json"
FULL_PATH    = OUT / "PRT-0701-run_order.json"
HTML_PATH    = OUT / "PRT-0701-Console-source.html"
ROOT_HTML    = ROOT / "PRT-0701-Console-source.updated.html"

def n(*items):
    return "\n".join(f"{i}. {s}" for i, s in enumerate(items, 1))

RESEED_STEP = (
    "Confirm QA-HISTORY-01 fixture data is current; "
    "if stale, request a backend re-seed and do not proceed until confirmed. "
    "Sign in with QA-HISTORY-01 and allow account data to synchronize."
)
RESEED_EXP = (
    "QA-HISTORY-01 fixture is confirmed current. Sign-in succeeds and account "
    "data synchronizes without crash or data from another account."
)
NODATA_STEP = (
    "Confirm QA-NODATA-01 fixture is current: 24 Hours should contain no "
    "readings and 3 Days should contain populated varied readings. If stale, "
    "request a backend verification and do not proceed until confirmed. "
    "Sign in with QA-NODATA-01."
)
NODATA_EXP = (
    "QA-NODATA-01 fixture is confirmed: 24 Hours is empty and 3 Days is "
    "populated. Sign-in succeeds."
)

def prepend_step(proc, exp, step_text, exp_text):
    """Add step 1 / exp 1 and shift existing numbered items."""
    def shift(text):
        # shift numbered list items up by 1
        def inc(m):
            return f"{int(m.group(1))+1}."
        return re.sub(r"^(\d+)\.", inc, text, flags=re.MULTILINE)
    return f"1. {step_text}\n{shift(proc)}", f"1. {exp_text}\n{shift(exp)}"


UPDATES = {}

# ── A: TD- row cases ────────────────────────────────────────────────────────

UPDATES["VP-APP-HOME-001"] = dict(
    t="Home screen live glucose display and automatic update",
    pre=(
        "QA-MAIN-01 is signed in on an approved device. An active CGM session "
        "is running with the Nobe simulator set to Normal (In Range) output. "
        "Bluetooth is ON and fresh glucose readings are arriving."
    ),
    proc=n(
        "Open Home and record the session status, live/freshness indicator, "
        "glucose value, unit, trend text/icon and last-update time.",
        "Keep Home open and observe three consecutive CGM measurement arrivals, "
        "recording the glucose value and update time after each arrival.",
        "Confirm the newest Home value corresponds to the latest Nobe reading received.",
    ),
    exp=n(
        "Home displays an active live session, the current glucose value in the "
        "configured unit, trend information when valid, and recency information.",
        "Each newly received valid glucose measurement updates Home automatically "
        "without a manual refresh; three consecutive updates are observed and recorded.",
        "The most recently displayed glucose value matches the latest Nobe "
        "simulator reading received.",
    ),
    ev=(
        "Three consecutive Home screenshots each showing an updated glucose value "
        "and timestamp; execution record."
    ),
)

UPDATES["VP-APP-HOME-002"] = dict(
    t="Bluetooth loss, STALE state, automatic reconnection and LIVE recovery",
    pre=(
        "QA-MAIN-01 is signed in with an active CGM session producing Normal "
        "readings. Bluetooth is ON and the current reading is fresh."
    ),
    proc=n(
        "Record the current LIVE status and the latest reading time.",
        "Turn Bluetooth OFF using the normal phone Bluetooth control.",
        "Remain on Home until the app shows its connection-loss or stale state; "
        "record the exact user-facing status and recovery instruction displayed.",
        "Turn Bluetooth ON using the normal phone Bluetooth control.",
        "Keep Home open and observe the connection status during automatic recovery.",
        "Wait for the next new sensor reading and record the final status, "
        "glucose value and update time.",
    ),
    exp=n(
        "The LIVE status and latest reading time are recorded.",
        "Turning Bluetooth off does not crash or navigate away from Home.",
        "While Bluetooth is OFF, the retained reading is not presented as "
        "fresh/LIVE and the app displays understandable recovery guidance; "
        "the exact status and instruction are recorded.",
        "Restoring Bluetooth does not crash or produce an error screen.",
        "The app attempts automatic reconnection without requiring manual intervention.",
        "After fresh sensor data is received the app returns to LIVE; the final "
        "status, glucose value and update time are recorded.",
    ),
    ev=(
        "LIVE-state screenshot, stale-state screenshot showing recovery guidance, "
        "and restored LIVE screenshot; execution record."
    ),
)

UPDATES["VP-APP-HOME-003"] = dict(
    t="All real-time trend states and invalid-trend suppression",
    pre=(
        "QA-MAIN-01 is signed in with an active CGM session. The Nobe simulator "
        "is available to produce stable and directional glucose trends by adjusting "
        "the SW1/SW2 potentiometer between measurement cycles."
    ),
    proc=n(
        "Set the Nobe to a stable output and wait for a Steady trend to establish; "
        "record the Home trend text and directional icon.",
        "Gradually increase the Nobe output over successive measurement cycles; "
        "record the Home trend text and icon for the Slowly Rising state, then "
        "increase further and record for Rising.",
        "Increase the Nobe output more rapidly over successive cycles; record "
        "the Home trend text and icon for the Rapidly Rising state.",
        "Gradually decrease the Nobe output; record trend text and icon for "
        "Slowly Falling, Falling and Rapidly Falling states.",
        "From a valid displayed trend, use the Nobe Off control to interrupt "
        "incoming measurements until the trend window becomes incomplete; record "
        "the Home trend area, then restore Normal output and wait for a valid "
        "trend to re-establish.",
    ),
    exp=n(
        "Home displays a Steady trend text and a non-directional icon during "
        "stable Nobe output.",
        "Home displays Slowly Rising and Rising trend text and the corresponding "
        "upward directional icons as Nobe output increases.",
        "Home displays Rapidly Rising trend text and the corresponding rapidly-upward "
        "directional icon during fast Nobe output increase.",
        "Home displays Slowly Falling, Falling and Rapidly Falling trend text and "
        "corresponding downward directional icons as Nobe output decreases.",
        "During the measurement interruption Home does not show a misleading "
        "directional trend; a valid trend returns after sufficient fresh data resumes.",
    ),
    ev=(
        "Screenshots of each trend state on Home; screenshot of the no-valid-trend "
        "state; execution record."
    ),
)

UPDATES["VP-APP-HOME-004"] = dict(
    t="Remaining sensor life for confirmed and unconfirmed session state",
    pre=(
        "QA-MAIN-01 is signed in with an active confirmed sensor session. "
        "The approximate session start time is noted."
    ),
    proc=n(
        "Open Home and record the remaining sensor-life value displayed.",
        "Turn Bluetooth OFF using the phone Bluetooth control and wait for "
        "the app to recognize the connection loss.",
        "Restore Bluetooth, wait for session recovery and record the "
        "remaining sensor-life value again.",
    ),
    exp=n(
        "When the session timing is confirmed, Home shows a remaining-life "
        "value for the active sensor session.",
        "When the app cannot confirm current session timing due to Bluetooth "
        "loss, it does not continue showing a misleading confirmed remaining-life "
        "value; the state change is observable.",
        "After Bluetooth is restored and the session recovers, remaining-life "
        "presentation returns to the confirmed state.",
    ),
    ev=(
        "Screenshot of remaining sensor life in confirmed state, screenshot "
        "of unconfirmed/disconnected state, and screenshot of recovered state; "
        "execution record."
    ),
)

UPDATES["VP-APP-HOME-005"] = dict(
    t="Home glucose state presentation: In Range, Critical Low and High",
    pre=(
        "QA-MAIN-01 is signed in with an active CGM session. The Nobe simulator "
        "is available to produce Normal (In Range), Critical Low and High glucose "
        "readings by adjusting SW1/SW2. Alarm behavior is covered in the dedicated "
        "alarm batches and is not assessed here."
    ),
    proc=n(
        "Set the Nobe to Normal output and record the Home glucose value, "
        "unit and state presentation.",
        "Set the Nobe to Critical Low output and record the Home glucose "
        "value, unit and state presentation.",
        "Set the Nobe to High output and record the Home glucose value, "
        "unit and state presentation.",
    ),
    exp=n(
        "The Normal (In Range) glucose value is displayed with the correct "
        "unit and an understandable In Range state indication.",
        "The Critical Low glucose value is displayed with the correct unit "
        "and an understandable Critical or Severe Low state indication.",
        "The High glucose value is displayed with the correct unit and an "
        "understandable High state indication.",
    ),
    ev=(
        "Screenshot of Home for each glucose state (In Range, Critical Low, High); "
        "Nobe potentiometer setting notes; execution record."
    ),
)

UPDATES["VP-APP-HOME-010"] = dict(
    t="Home contextual cards show applicable data and open their destinations",
    pre=(
        "QA-MAIN-01 is signed in. At least one Meal, one Insulin and one Activity "
        "log entry have been recorded in Journal during this or a prior test session "
        "so that the Meals, Insulin and Activity contextual cards are populated."
    ),
    proc=n(
        "On Home, locate the Meals card, record its visible information, tap it "
        "and verify Carbohydrates opens; return to Home.",
        "Locate the Insulin card, record its visible information, tap it and "
        "verify Insulin detail opens; return to Home.",
        "Locate the Activity card, record its visible information, tap it and "
        "verify Activities opens; return to Home.",
        "Inspect the Active Energy card and verify the displayed data or a "
        "legitimate no-data state; if actionable, open its destination and return.",
        "If an Upcoming Sensor card is displayed, record the replacement "
        "information, tap View Details and verify My CGM opens.",
    ),
    exp=n(
        "The Meals card reflects the logged Meal data and routes to Carbohydrates.",
        "The Insulin card reflects the logged Insulin data and routes to Insulin detail.",
        "The Activity card reflects the logged Activity data and routes to Activities.",
        "The Active Energy card shows the applicable data or a legitimate "
        "no-data state and opens its destination when actionable.",
        "If present, the Upcoming Sensor View Details action opens My CGM; "
        "if absent, step 5 is recorded as not applicable.",
    ),
    ev=(
        "Screenshots of each contextual card and its opened destination; "
        "execution record noting any card not present."
    ),
)

UPDATES["VP-APP-HOSTED-SIGNIN-010"] = dict(
    pre=(
        "QA-MAIN-01 exists. The user is unauthenticated, internet is available "
        "and Hosted Sign In is displayed."
    ),
    proc=n(
        "Enter the QA-MAIN-01 email in the Email field.",
        "Enter the QA-MAIN-01 password from the controlled credential source.",
        "Select Sign in twice rapidly in quick succession.",
    ),
    exp=n(
        "The QA-MAIN-01 email is displayed in the Email field.",
        "The password is masked and not shown in plain text.",
        "One sign-in completes and the app shows one destination screen; no "
        "duplicate browser page, stacked app screen, error or corrupted "
        "authentication state appears.",
    ),
    ev="Screenshot of the single destination screen after rapid double-tap; execution record.",
)

UPDATES["VP-APP-HOSTED-SIGNIN-015"] = dict(
    pre=(
        "A fresh QA account that has never completed onboarding is available "
        "for this test. The user is unauthenticated, internet is available "
        "and Hosted Sign In is displayed."
    ),
    proc=n(
        "Select the fresh unused QA account, record its alias, and sign in "
        "using its credentials from the controlled credential source.",
        "Complete the first onboarding screen and select Continue.",
        "On the next onboarding screen, remove CGMx 1 using the approved "
        "app-reset method, reinstall it and launch it.",
        "Open the hosted sign-in flow and sign in again with the same account.",
    ),
    exp=n(
        "The fresh account alias is recorded, sign-in succeeds and the first "
        "onboarding screen is shown; its title is recorded.",
        "The next onboarding screen is shown.",
        "CGMx 1 opens on the Welcome screen in an unauthenticated state.",
        "Sign-in succeeds and onboarding starts again from the first screen "
        "recorded in Step 1; Home is not shown until onboarding is completed.",
    ),
    ev=(
        "Screenshot of first onboarding screen, screenshot after reinstall "
        "showing Welcome, screenshot confirming onboarding restarts; "
        "execution record with account alias."
    ),
)

# ── B: QA-HISTORY-01 cases — add re-seed step + fix 1:1 ────────────────────

def history_pre_strip_signin(pre):
    """Remove 'Sign in with...' from precondition so it moves to procedure."""
    return re.sub(r'\s*Sign in with the controlled historical account QA-HISTORY-01[^.]*\.', '', pre).strip()

# HOME-006
_h006_proc = n(
    "Confirm QA-HISTORY-01 fixture data is current for 1 October 2026; "
    "if stale request a backend re-seed and do not proceed until confirmed. "
    "Sign in with QA-HISTORY-01 and open Home.",
    "Record the selected range, chart time span and visible Low/High threshold markers.",
    "Select a different approved Home range and record the updated time span "
    "and whether the threshold markers are unchanged.",
    "Select the range containing the documented gap (07:23–08:07 PKT on "
    "1 October 2026) and locate the gap on the graph.",
)
_h006_exp = n(
    "QA-HISTORY-01 fixture is confirmed current; sign-in succeeds and Home loads.",
    "The chart represents the selected data window; Low (70 mg/dL) and High "
    "(180 mg/dL) threshold markers are visible.",
    "The chart updates to the newly selected range; threshold markers remain "
    "correct for the configured thresholds.",
    "A genuine missing-data interval (07:23–08:07 PKT) is identifiable as a gap "
    "and is not fabricated as a continuous glucose trace.",
)
UPDATES["VP-APP-HOME-006"] = dict(proc=_h006_proc, exp=_h006_exp,
    ev="Screenshots of at least two range selections and the documented gap; execution record.")

# HOME-007
_h007_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a backend "
    "re-seed and do not proceed. Sign in with QA-HISTORY-01 and open Home.",
    "Select a Home range that contains the known plotted point (1 Oct 2026 "
    "07:22 PKT, ~125 mg/dL).",
    "Tap the plotted point and record the displayed glucose value and timestamp.",
    "Drag horizontally across the graph to pan and verify the time axis moves "
    "with the viewed data.",
    "Use a two-finger pinch gesture to zoom in and then back out; inspect "
    "axis labels for clipping or ambiguity.",
    "Return the graph to its normal viewport and confirm the selected Home "
    "range has not changed.",
)
_h007_exp = n(
    "QA-HISTORY-01 fixture is confirmed current; sign-in succeeds and Home loads.",
    "The range is selected and the known data point is visible on the graph.",
    "Tapping the point reports its value and timestamp; the displayed glucose "
    "value matches the fixture reference (subject to the app's display rounding).",
    "The graph pans smoothly; the time axis moves with the dragged direction.",
    "Pinch zoom works without crash; axis labels remain readable and unclipped "
    "at all zoom levels used.",
    "The graph returns to a normal viewport; the selected Home range is unchanged.",
)
UPDATES["VP-APP-HOME-007"] = dict(proc=_h007_proc, exp=_h007_exp,
    ev="Screenshots of the tapped data point, panned state, zoomed state and restored state; execution record.")

# HOME-008
_h008_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Home.",
    "Record the selected range and the Time in Range, Daily Average, GMI "
    "and Severe Events values.",
    "Select a different approved Home range and record all four tile values again.",
    "Tap Time in Range and verify the Time in Range detail screen opens; return.",
    "Tap Daily Average, verify Average Glucose opens; return. "
    "Tap GMI, verify GMI (est. A1C) opens; return. "
    "Tap Severe Events, verify Severe Events opens; return.",
)
_h008_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Home loads.",
    "All four tile values for the initial range are recorded.",
    "All four tile values update to reflect the newly selected range; no stale "
    "values from the previous range remain.",
    "Tapping Time in Range opens the Time in Range detail screen; returning "
    "restores Home.",
    "Each of the remaining three tiles opens its named detail screen; returning "
    "each time restores Home without crash or blank state.",
)
UPDATES["VP-APP-HOME-008"] = dict(proc=_h008_proc, exp=_h008_exp,
    ev="Screenshots of both range tile sets and each opened detail screen; execution record.")

# HOSTED-SIGNIN-012
_h012_proc_existing = n(
    "Check the fixture ages immediately before execution. If necessary, refresh "
    "the three controlled readings so they are 91, exactly 90 and 89 days old, "
    "then record their timestamps and values.",
    "Remove CGMx 1 or clear its local data, reinstall or relaunch it as "
    "applicable, and confirm the user is logged out.",
    "Sign in with QA-HISTORY-01 through the normal hosted sign-in flow.",
    "Complete the normal post-sign-in flow until Home is displayed without "
    "manually re-entering historical readings.",
    "Open the Home or Reports historical view that includes the boundary dates "
    "and check the controlled readings.",
)
_h012_exp_existing = n(
    "The recorded fixture contains one reading more than 90 days old, one "
    "exactly 90 days old and one less than 90 days old at execution time.",
    "CGMx 1 starts in a fresh logged-out state with no locally retained history.",
    "Sign-in succeeds and the account's server-held data is restored without "
    "data from another account.",
    "Home is displayed without the tester manually recreating the historical readings.",
    "The exactly-90-day and less-than-90-day readings are available in the "
    "supported historical view; the more-than-90-day reading is excluded.",
)
UPDATES["VP-APP-HOSTED-SIGNIN-012"] = dict(
    proc=_h012_proc_existing, exp=_h012_exp_existing,
    ev=(
        "Fixture age confirmation record; screenshots of the historical view "
        "showing the boundary readings; execution record."
    ),
)

# REPORT-001
_r001_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and navigate to Reports from the bottom navigation.",
    "Observe the report area and the available top-level report-view controls.",
    "Select each available top-level view one at a time.",
    "After each selection observe the displayed report content and the "
    "active-view indication.",
)
_r001_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Reports is reachable.",
    "Reports opens without crash or blank state; top-level report-view controls are visible.",
    "Each selection responds without crash or unintended navigation.",
    "Each top-level control opens its corresponding report content and the "
    "selected view is visually identifiable; switching views does not leave "
    "stale content from the previously selected view.",
)
UPDATES["VP-APP-REPORT-001"] = dict(proc=_r001_proc, exp=_r001_exp,
    ev="Screenshot of each report view selected; execution record.")

# REPORT-002
_r002_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports.",
    "Record the current report view and active time window.",
    "Open the report time-range control and select another approved available range.",
    "Observe the report content, chart and metrics after the range change.",
    "Select one additional approved range and observe again.",
)
_r002_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Reports opens.",
    "The current report view and active time window are recorded.",
    "The time-range control is accessible and the new selection is accepted.",
    "The report recalculates for the selected range without showing stale values "
    "from the previous range; the selected window is visibly active.",
    "The report recalculates again for the additional range without stale content.",
)
UPDATES["VP-APP-REPORT-002"] = dict(proc=_r002_proc, exp=_r002_exp,
    ev="Screenshots of at least three range selections showing updated content; execution record.")

# REPORT-005
_r005_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 while online.",
    "Open Reports and select the populated 7 Days period; wait for it to load "
    "and record one visible value and date to confirm the local cache is established.",
    "Disable Wi-Fi and mobile data using the normal phone controls.",
    "Return to or open Reports.",
    "Select the same historical period recorded in Step 2 and observe the "
    "report content and any network-status messaging.",
    "Restore connectivity after evidence is captured.",
)
_r005_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds online.",
    "The 7 Days report loads and a reference value and date are recorded; "
    "local cache is established.",
    "Connectivity is disabled without crash.",
    "Reports is accessible offline.",
    "Historical report data already available locally remains viewable; the app "
    "does not fabricate new remote data or fail solely due to network unavailability; "
    "any offline messaging is recorded.",
    "Connectivity is restored without crash.",
)
UPDATES["VP-APP-REPORT-005"] = dict(proc=_r005_proc, exp=_r005_exp,
    ev="Online Reports screenshot, offline Reports screenshot with content visible; execution record.")

# REPORT-016
_r016_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports on the populated 15 Days period.",
    "Scroll to Key Insights and take a screenshot of each insight; then scroll "
    "to the Focus Area card and take a screenshot.",
    "Select 30 Days and repeat: screenshot Key Insights, screenshot Focus Area.",
)
_r016_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Reports "
    "shows the 15 Days period.",
    "Key Insights are readable and refer to values consistent with the displayed "
    "summary cards; Focus Area is readable and refers to the displayed data.",
    "Key Insights and Focus Area update for 30 Days; no 15-day values remain "
    "in either section.",
)
UPDATES["VP-APP-REPORT-016"] = dict(proc=_r016_proc, exp=_r016_exp,
    ev="Screenshots of Key Insights and Focus Area for both 15 Days and 30 Days; execution record.")

# REPORT-DAY-004
_rd004_proc = n(
    "Confirm QA-HISTORY-01 fixture is current and the Quality/Test Engineering "
    "approval for the backend-seeded gap is on record. If stale request a re-seed.",
    "Sign in with QA-HISTORY-01 and allow server data to synchronize.",
    "Open Reports > Day and navigate to 1 October 2026.",
    "Use the 24 Hours view where available and locate 07:22 through 08:08 PKT.",
    "Verify the readings immediately before and after the interval against the "
    "fixture reference (07:22 PKT ~125 mg/dL; 08:08 PKT ~128 mg/dL).",
    "Inspect the glucose line immediately before, across and after the "
    "missing-data interval (07:23–08:07 PKT).",
)
_rd004_exp = n(
    "Fixture is confirmed current and the approval reference is recorded.",
    "Sign-in succeeds and account data synchronizes without data from another account.",
    "Reports > Day opens and 1 October 2026 is reachable.",
    "The 24 Hours view and the 07:22–08:08 PKT window are accessible.",
    "The readings surrounding the gap appear at their recorded times and values "
    "subject only to the app's display rounding.",
    "A visible line break is present across 07:23–08:07 PKT; the graph does not "
    "interpolate or imply a continuous glucose trend across the gap.",
)
UPDATES["VP-APP-REPORT-DAY-004"] = dict(proc=_rd004_proc, exp=_rd004_exp,
    ev="Screenshot of Reports > Day for 1 October 2026 clearly showing the gap; execution record.")

# REPORT-WEEK-002
_rw002_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports > Day.",
    "Record at least three glucose-point timestamps occurring on different "
    "dates (27, 28 and 29 September 2026) to establish their chronological order.",
    "Open Reports > Week and select a period containing those readings.",
    "Compare the relative left-to-right positions of the recorded dates/times "
    "with their expected chronological order.",
)
_rw002_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and Reports > Day opens.",
    "At least three timestamps on different dates are recorded and their "
    "expected chronological order is established.",
    "Reports > Week opens and the selected period contains the recorded readings.",
    "The Week history progresses chronologically from earlier to later dates/times; "
    "recorded readings are not ordered in a way that contradicts their timestamps.",
)
UPDATES["VP-APP-REPORT-WEEK-002"] = dict(proc=_rw002_proc, exp=_rw002_exp,
    ev="Screenshots of Reports > Day timestamps and Reports > Week view for comparison; execution record.")

# TAR-001
_tar1_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports > Time Above Range.",
    "Take a screenshot of the Latest value and the selected period.",
    "Tap 24 Hours, 7 Days, 15 Days, 30 Days and 90 Days in turn (and 3 Days "
    "if shown — record only), taking a screenshot after each selection.",
    "Tap Back.",
)
_tar1_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and the "
    "Time Above Range detail opens.",
    "A Latest value and a highlighted period are shown.",
    "For each period the highlight, chart title/window and values change; "
    "no previous-period values remain.",
    "Reports is displayed after Back is tapped.",
)
UPDATES["VP-APP-TAR-001"] = dict(proc=_tar1_proc, exp=_tar1_exp,
    ev="Screenshot after each period selection; execution record.")

# TAR-002
_tar2_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01, open Time Above Range and select 7 Days; "
    "record the device clock time t (minutes after midnight).",
    "Take screenshots of the tiles: Total readings, Above readings, Above %, "
    "Total, Peak, Tracked and the Tracked date range.",
    "Divide the displayed Above readings by Total readings and multiply by 100.",
    "Scroll to Recent Days and take a screenshot of each date and value.",
)
_tar2_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and 7 Days is selected.",
    "Tiles are labelled and refer to the selected period; values are recorded.",
    "The calculated percentage equals the displayed Above % to the displayed "
    "precision and matches the seeded values (Above 750; Total 10020 − t).",
    "Recent Days entries are listed with dates and values (recorded only).",
)
UPDATES["VP-APP-TAR-002"] = dict(proc=_tar2_proc, exp=_tar2_exp,
    ev="Screenshots of all tiles and Recent Days; calculation record; execution record.")

# TBR-001
_tbr1_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports > Time Below Range.",
    "Take a screenshot of the Latest value and the selected period.",
    "Tap 24 Hours, 7 Days, 15 Days, 30 Days and 90 Days in turn (and 3 Days "
    "if shown — record only), taking a screenshot after each selection.",
    "Tap Back.",
)
_tbr1_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and the "
    "Time Below Range detail opens.",
    "A Latest value and a highlighted period are shown.",
    "For each period the highlight, chart title/window and values change; "
    "no previous-period values remain.",
    "Reports is displayed after Back is tapped.",
)
UPDATES["VP-APP-TBR-001"] = dict(proc=_tbr1_proc, exp=_tbr1_exp,
    ev="Screenshot after each period selection; execution record.")

# TBR-002
_tbr2_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01, open Time Below Range and select 7 Days; "
    "record the device clock time t (minutes after midnight).",
    "Take screenshots of the tiles: Total readings, Below readings, Below %, "
    "Total, Lowest, Tracked and the Tracked date range.",
    "Divide the displayed Below readings by Total readings and multiply by 100.",
    "Scroll to Recent Days and take a screenshot of each date and value.",
)
_tbr2_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and 7 Days is selected.",
    "Tiles are labelled and refer to the selected period; values are recorded.",
    "The calculated percentage equals the displayed Below % to the displayed "
    "precision and matches the seeded values (Below 1500; Total 10020 − t).",
    "Recent Days entries are listed with dates and values (recorded only).",
)
UPDATES["VP-APP-TBR-002"] = dict(proc=_tbr2_proc, exp=_tbr2_exp,
    ev="Screenshots of all tiles and Recent Days; calculation record; execution record.")

# VAR-001
_var1_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01 and open Reports > Variability.",
    "Take a screenshot of the Latest value and the selected period.",
    "Tap 24 Hours, 7 Days, 15 Days, 30 Days and 90 Days in turn, taking a "
    "screenshot after each selection.",
    "Tap Back.",
)
_var1_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and the "
    "Variability detail opens.",
    "A Latest value and a highlighted period are shown.",
    "For each period the highlight, chart title/window and values change; "
    "no previous-period values remain.",
    "Reports is displayed after Back is tapped.",
)
UPDATES["VP-APP-VAR-001"] = dict(proc=_var1_proc, exp=_var1_exp,
    ev="Screenshot after each period selection; execution record.")

# VAR-002
_var2_proc = n(
    "Confirm QA-HISTORY-01 fixture is current; if stale request a re-seed. "
    "Sign in with QA-HISTORY-01, open Variability and select 15 Days.",
    "Take screenshots of Total readings, CV, Peak, Tracked and the Tracked "
    "date range; scroll to Recent Days and take a screenshot of each date and value.",
)
_var2_exp = n(
    "QA-HISTORY-01 fixture confirmed current; sign-in succeeds and 15 Days "
    "is selected in Variability.",
    "Tiles are labelled with % unit for CV and refer to the selected period; "
    "values and Recent Days entries are recorded only.",
)
UPDATES["VP-APP-VAR-002"] = dict(proc=_var2_proc, exp=_var2_exp,
    ev="Screenshots of all tiles and Recent Days; execution record.")

# ── C: QA-NODATA-01 cases ───────────────────────────────────────────────────

UPDATES["VP-APP-TAR-004"] = dict(
    proc=n(
        "Confirm QA-NODATA-01 fixture is current: 24 Hours should be empty and "
        "3 Days should be populated with varied readings including readings above "
        "180 mg/dL. If stale request a backend verification and do not proceed "
        "until confirmed. Sign in with QA-NODATA-01 and open Time Above Range.",
        "Select the no-data period (24 Hours) and observe the state.",
        "Select 3 Days (populated) and observe the state.",
    ),
    exp=n(
        "QA-NODATA-01 fixture confirmed current; sign-in succeeds and "
        "Time Above Range opens.",
        "An empty or no-data state is shown (0% / no chart values); "
        "previous-period values are not shown.",
        "Populated values return for the 3 Days period.",
    ),
    ev="Screenshot of empty 24 Hours state and populated 3 Days state; execution record.",
)

UPDATES["VP-APP-TBR-004"] = dict(
    proc=n(
        "Confirm QA-NODATA-01 fixture is current: 24 Hours should be empty and "
        "3 Days should be populated with varied readings including readings below "
        "70 mg/dL. If stale request a backend verification and do not proceed "
        "until confirmed. Sign in with QA-NODATA-01 and open Time Below Range.",
        "Select the no-data period (24 Hours) and observe the state.",
        "Select 3 Days (populated) and observe the state.",
    ),
    exp=n(
        "QA-NODATA-01 fixture confirmed current; sign-in succeeds and "
        "Time Below Range opens.",
        "An empty or no-data state is shown (0% / no chart values); "
        "previous-period values are not shown.",
        "Populated values return for the 3 Days period.",
    ),
    ev="Screenshot of empty 24 Hours state and populated 3 Days state; execution record.",
)

UPDATES["VP-APP-VAR-004"] = dict(
    proc=n(
        "Confirm QA-NODATA-01 fixture is current: 24 Hours should be empty and "
        "3 Days should be populated with varied readings. If stale request a "
        "backend verification and do not proceed until confirmed. "
        "Sign in with QA-NODATA-01 and open Variability.",
        "Select the no-data period (24 Hours) and observe the state.",
        "Select 3 Days (populated) and observe the state.",
    ),
    exp=n(
        "QA-NODATA-01 fixture confirmed current; sign-in succeeds and "
        "Variability opens.",
        "An empty or no-data state is shown; previous-period values are not shown.",
        "Populated values return for the 3 Days period.",
    ),
    ev="Screenshot of empty 24 Hours state and populated 3 Days state; execution record.",
)

# ── D: Fixable false positives ──────────────────────────────────────────────

UPDATES["VP-APP-HIGH-008"] = dict(
    pre="The High threshold configuration screen is displayed in the threshold setup flow.",
    proc=n(
        "Enter 7.7 mmol/L and attempt to continue or save.",
        "Record the validation response shown.",
        "Enter 14.0 mmol/L and attempt to continue or save.",
        "Record the validation response shown.",
        "Enter an in-range value (for example 10.0 mmol/L) and attempt to continue or save.",
    ),
    exp=n(
        "7.7 mmol/L is rejected as below the permitted minimum; the value cannot "
        "become the saved High threshold.",
        "The validation message or blocking state for the below-minimum value is recorded.",
        "14.0 mmol/L is rejected as above the permitted maximum; the value cannot "
        "become the saved High threshold.",
        "The validation message or blocking state for the above-maximum value is recorded.",
        "An in-range value (7.8–13.9 mmol/L) is accepted and the validation "
        "state clears.",
    ),
    ev="Screenshots of each rejected entry with its validation state and the accepted in-range entry; execution record.",
)

UPDATES["VP-APP-LOW-008"] = dict(
    pre="The Low threshold configuration screen is displayed in the threshold setup flow.",
    proc=n(
        "Enter 3.8 mmol/L and attempt to continue or save.",
        "Record the validation response shown.",
        "Enter 5.7 mmol/L and attempt to continue or save.",
        "Record the validation response shown.",
        "Enter an in-range value (for example 4.5 mmol/L) and attempt to continue or save.",
    ),
    exp=n(
        "3.8 mmol/L is rejected as below the permitted minimum; the value cannot "
        "become the saved Low threshold.",
        "The validation message or blocking state for the below-minimum value is recorded.",
        "5.7 mmol/L is rejected as above the permitted maximum; the value cannot "
        "become the saved Low threshold.",
        "The validation message or blocking state for the above-maximum value is recorded.",
        "An in-range value (3.9–5.6 mmol/L) is accepted and the validation "
        "state clears.",
    ),
    ev="Screenshots of each rejected entry with its validation state and the accepted in-range entry; execution record.",
)

UPDATES["VP-APP-INSULIN-003"] = dict(
    pre="The Insulin entry form is open.",
    proc=n(
        "Enter 0.5 units with otherwise valid fields and confirm it can be saved.",
        "Enter 30 units and confirm it can be saved.",
        "Enter 2.5 units, save and verify the saved value remains 2.5.",
        "Attempt to enter 0, a negative value, 30.5, 2.3 and a non-numeric "
        "value where the UI permits, and observe the field or save behavior for each.",
        "Record any validation message or blocking state shown for rejected values.",
    ),
    exp=n(
        "0.5 units is accepted as the minimum valid dose.",
        "30 units is accepted as the maximum valid dose.",
        "2.5 units is saved exactly; no rounding to an unsupported increment occurs.",
        "Out-of-range values (0, negative, above 30) and unsupported-precision "
        "values (2.3, 30.5) and non-numeric input are each rejected before save.",
        "A validation message or blocking state is shown for each rejected value; "
        "the form returns to a valid state after correction.",
    ),
    ev="Screenshots of accepted boundary values, rejected values with validation messages; execution record.",
)

UPDATES["VP-APP-SCAN-010"] = dict(
    pre=(
        "The expired-sensor QR code test asset (Sensor ID SN0009999, expiry "
        "31 Dec 2022) is available from the console Test Assets panel."
    ),
    proc=n(
        "Open the Scan the sensor QR code camera scanner.",
        "Present the expired-sensor QR code from the Test Assets panel within "
        "the viewfinder.",
        "Continue until the application performs sensor validity or expiry evaluation.",
        "Observe whether session setup can proceed past the expiry check.",
    ),
    exp=n(
        "The scanner opens without crash and the camera feed is active.",
        "The expired-sensor barcode is read by the scanner.",
        "The app evaluates the sensor expiry date extracted from the GS1 barcode.",
        "The expired sensor is rejected with a user-facing message and progression "
        "to session start is blocked.",
    ),
    ev=(
        "Screenshot of the scanner reading the expired QR code and screenshot "
        "of the rejection message; execution record."
    ),
)

UPDATES["VP-APP-SENSOR-ID-006"] = dict(
    pre=(
        "Step 14 of 22 — Scan your sensor is displayed with the inline Sensor ID "
        "entry expanded. An approved Sensor Test ID from physical or test packaging "
        "is available."
    ),
    proc=n(
        "Enter the approved Sensor Test ID and select Continue to reach the "
        "Confirm Sensor ID modal; select Continue on the modal.",
        "Continue through any recall or trusted-time validation steps until "
        "the manual expiry-check prompt is reached.",
        "Read and record the exact expiry-check instruction displayed.",
        "Follow the user confirmation path and attempt to continue.",
    ),
    exp=n(
        "The Confirm Sensor ID modal is displayed and confirmed; the flow "
        "advances to the recall or expiry-check stage.",
        "The manual-ID path presents a prompt asking the user to verify the "
        "sensor expiry date from its physical packaging before proceeding.",
        "The prompt does not claim that expiry was obtained from a scanned "
        "GS1 code; the instruction is recorded.",
        "The flow allows continuation only after the user confirms the expiry "
        "check; no crash or unintended navigation occurs.",
    ),
    ev="Screenshots of the expiry-check prompt and the post-confirmation screen; execution record.",
)

UPDATES["VP-APP-SICK-005"] = dict(
    pre="The Add Note (sickness) screen is open.",
    proc=n(
        "Enter a 2-character note and tap Save.",
        "Enter exactly 3 characters with a valid date/time and tap Save.",
        "Open Add Note again, enter exactly 256 characters and tap Save.",
        "Enter 257 characters and observe the field or Save behavior.",
        "Record any validation message or counter shown for the rejected lengths.",
    ),
    exp=n(
        "The 2-character note is not accepted; Save is blocked or a validation "
        "message is shown.",
        "The 3-character note is accepted and saved without error.",
        "The 256-character note is accepted and saved without error.",
        "257 characters is not saved; the field blocks additional input, truncates "
        "to 256, or a validation message is shown.",
        "Validation messages or character-count feedback for rejected lengths "
        "are recorded.",
    ),
    ev="Screenshots of the rejected 2-char and 257-char states and the accepted 3-char and 256-char saves; execution record.",
)

UPDATES["VP-APP-WARMUP-007"] = dict(
    pre=(
        "QA-MAIN-01 has an active sensor session currently in the warm-up phase. "
        "The warm-up debug bypass must NOT be used for this case. "
        "Home is accessible and Bluetooth is ON."
    ),
    proc=n(
        "Record the warm-up status and remaining-time estimate displayed, "
        "then turn Bluetooth OFF briefly using the phone Bluetooth control.",
        "Turn Bluetooth ON and allow the same transmitter to reconnect.",
        "Dismiss any full-screen warm-up status if it reappears and inspect Home.",
    ),
    exp=n(
        "The Bluetooth interruption is represented on screen without falsely "
        "completing or restarting the warm-up.",
        "The same session reconnects; warm-up continues from the "
        "transmitter-reported remaining time.",
        "Home remains reachable and shows the continuing warm-up; a renewed "
        "navigation trap is recorded as a failure against DO-905.",
    ),
    ev="Screenshots of warm-up state before interruption, during interruption, and after reconnection; execution record.",
)

# ── E: Hardware/infrastructure blocked — fix proc/exp 1:1 only ─────────────

UPDATES["VP-APP-HIGH-015"] = dict(
    proc=n(
        "Record the configured High threshold and the last live reading index "
        "before the controlled interruption.",
        "Create a sustained Bluetooth disconnection using the approved real-device "
        "method so measurements become missing during the gap.",
        "Allow the transmitter to record at least one historical High reading "
        "during the interruption.",
        "Restore Bluetooth and allow the missing readings to backfill via RACP.",
        "Verify the historical High reading appears in history or Journal.",
        "Observe the system notification surface during and after backfill.",
    ),
    exp=n(
        "The High threshold and last live reading index are recorded.",
        "Bluetooth is disconnected and measurements become missing for the gap period.",
        "At least one High-threshold-breach reading is recorded by the transmitter "
        "during the gap.",
        "Bluetooth is restored and missing readings backfill through RACP without crash.",
        "The historical High reading appears at its correct position in history or Journal.",
        "No new High system notification is generated solely because a historical "
        "High reading arrived during RACP backfill; new notifications remain "
        "limited to eligible live measurements.",
    ),
    ev="History or Journal screenshot showing backfilled High reading; notification surface screenshot during backfill; execution record.",
)

UPDATES["VP-APP-HOME-014"] = dict(
    proc=n(
        "Record the last Home reading, its timestamp and measurement index before "
        "performing the power-cycle.",
        "Perform the approved transmitter or CGM power-cycle using the test-kit procedure.",
        "Allow normal reconnection and data replay or recovery.",
        "Review Home and the historical graph across the interruption and compare "
        "with the pre-interruption record.",
    ),
    exp=n(
        "The last reading, timestamp and measurement index are recorded.",
        "The power-cycle completes using the approved procedure without unintended "
        "app crash or navigation.",
        "The app reconnects and replays or recovers data without crash.",
        "The expected session resumes without an incorrect new session; "
        "repeated or backfilled readings are handled without duplicate or "
        "corrupted historical data.",
    ),
    ev="Screenshots before and after power-cycle showing session continuity; history screenshot confirming no duplicates; execution record.",
)

UPDATES["VP-APP-HOME-015"] = dict(
    proc=n(
        "Record the final reading, timestamp and measurement index before disconnecting.",
        "Turn Bluetooth OFF and maintain the approved disconnection duration "
        "long enough to miss multiple measurements.",
        "Turn Bluetooth ON and allow automatic reconnection.",
        "Keep the app open while missing measurements are retrieved.",
        "Review Home and history across the interruption and compare the "
        "recovered chronology with the recorded gap.",
    ),
    exp=n(
        "The final reading, timestamp and measurement index before the gap are recorded.",
        "Bluetooth is disabled and held for the required duration without app crash.",
        "Bluetooth is restored and automatic reconnection begins without crash.",
        "Missing measurements are retrieved without crash or unintended navigation.",
        "Available missed readings are backfilled into their correct chronological "
        "positions without duplicate entries or a false new session.",
    ),
    ev="Screenshots before and after reconnection; history view showing backfilled readings in chronological order; execution record.",
)

UPDATES["VP-APP-LOW-015"] = dict(
    proc=n(
        "Record the configured Low threshold and the last live reading index "
        "before the controlled interruption.",
        "Create a sustained Bluetooth disconnection using the approved real-device "
        "method so measurements become missing during the gap.",
        "Allow the transmitter to record at least one historical Low reading "
        "during the interruption.",
        "Restore Bluetooth and allow the missing readings to backfill via RACP.",
        "Verify the historical Low reading appears in history or Journal.",
        "Observe the system notification surface during and after backfill.",
    ),
    exp=n(
        "The Low threshold and last live reading index are recorded.",
        "Bluetooth is disconnected and measurements become missing for the gap period.",
        "At least one Low-threshold-breach reading is recorded by the transmitter "
        "during the gap.",
        "Bluetooth is restored and missing readings backfill through RACP without crash.",
        "The historical Low reading appears at its correct position in history or Journal.",
        "No new Low system notification is generated solely because a historical "
        "Low reading arrived during RACP backfill; new notifications remain "
        "limited to eligible live measurements.",
    ),
    ev="History or Journal screenshot showing backfilled Low reading; notification surface screenshot during backfill; execution record.",
)

UPDATES["VP-APP-MEDIUM-002"] = dict(
    proc=n(
        "Confirm current measurements are being received and record the last "
        "reading time and index.",
        "Create an approved controlled interruption without ending the CGM session.",
        "Observe and record the first no-data or disconnection alarm stage "
        "before any critical escalation.",
        "With Do Not Disturb or Focus enabled, verify whether the medium-stage "
        "alert is presented and audible.",
        "Restore the normal measurement path after evidence is captured.",
    ),
    exp=n(
        "Current measurements are being received and the last reading is recorded.",
        "The controlled interruption is created without crash or unintended session end.",
        "Loss of recent measurements initiates the defined medium-priority "
        "no-data or disconnection alert before any critical escalation; the "
        "alert repeats as defined while unresolved.",
        "The medium alert is presented and audible under Do Not Disturb or Focus "
        "where the OS permits; DND-bypass behavior is recorded.",
        "Normal measurement path is restored without crash.",
    ),
    ev="Screenshot of medium-priority alert; audio evidence or notes; DND state screenshot; execution record.",
)

UPDATES["VP-APP-REPORT-DAY-005"] = dict(
    proc=n(
        "Wait for a normal reading and record its value, timestamp and session "
        "identifier before the interruption.",
        "Move the phone outside reliable Bluetooth range using the approved "
        "normal-device method and maintain the interruption for at least five "
        "expected reading intervals.",
        "Restore communication and wait for the first valid reading after reconnection; "
        "record its value, timestamp and session identifier.",
        "Confirm whether expected measurement indexes remain missing or were "
        "backfilled; if backfilled, repeat with an interruption exceeding 30 minutes.",
        "Open Reports > Day, navigate to the documented date and locate the interruption.",
        "Inspect the glucose line immediately before, across and after the interval.",
    ),
    exp=n(
        "A valid reading before the interruption is recorded with its timestamp "
        "and session identifier.",
        "Communication is interrupted for the required duration without app crash.",
        "The first valid reading after reconnection is recorded; the gap boundaries "
        "are established.",
        "Either at least five consecutive measurement indexes remain missing, or "
        "the timestamps surrounding the gap are more than 30 minutes apart; "
        "if backfilled with no qualifying gap, the attempt is recorded as unsuitable.",
        "Reports > Day opens and the documented date and interruption area are reachable.",
        "A visible line break is present across the documented discontinuity; "
        "the graph does not interpolate or imply a continuous glucose trend "
        "across the interval; normal graphing resumes when valid readings resume.",
    ),
    ev="Pre-gap and post-gap reading records; Reports > Day screenshot showing the line break; execution record.",
)

UPDATES["VP-APP-TX-PAIR-017"] = dict(
    proc=n(
        "Start the transmitter pairing or direct-connection flow.",
        "Power off the transmitter during direct connection or device-info loading.",
        "Wait for at least the required retry interval (5 seconds) and observe "
        "whether one automatic direct-connection retry occurs.",
        "If the retry fails, observe whether the app returns to transmitter selection.",
    ),
    exp=n(
        "The transmitter pairing or direct-connection flow starts without crash.",
        "The disconnection is detected during direct connection or device-info "
        "loading without app crash.",
        "Under DO-824, one automatic direct-connection retry fires after "
        "5 seconds; the retry attempt is observable.",
        "Only after the single retry fails does the app return to transmitter "
        "selection; no second automatic retry or indefinite wait occurs.",
    ),
    ev="Screen recordings or timed screenshots showing the disconnect event, the single retry and the return to transmitter selection; execution record.",
)

UPDATES["VP-APP-TX-PAIR-024"] = dict(
    proc=n(
        "Use the recalled test data item in the specified normal start or upload flow "
        "and record the recall response shown by the app.",
        "Close and relaunch the app, or background and resume it as specified in "
        "the test data.",
        "Return to the affected CGM flow and attempt normal use of the same "
        "recalled item.",
        "Record the state shown and whether normal CGM use is permitted.",
    ),
    exp=n(
        "The app presents the applicable recall or safe-action state when the "
        "recalled item is used; the response is recorded.",
        "The app relaunches or resumes without crash.",
        "Returning to the CGM flow with the same recalled item does not bypass "
        "the recall state.",
        "Normal CGM use with the recalled item remains blocked; the recall or "
        "safe-action state is presented rather than silently accepted.",
    ),
    ev="Screenshots of the initial recall response, post-relaunch state and the re-attempted blocked state; execution record.",
)

UPDATES["VP-APP-WARMUP-008"] = dict(
    pre=(
        "QA-MAIN-01 has an active sensor session currently in the warm-up phase. "
        "The warm-up debug bypass must NOT be used for this case. "
        "The approved transmitter power-cycle procedure is available."
    ),
    proc=n(
        "Record the warm-up status and remaining-time estimate, then perform "
        "the approved transmitter power-cycle.",
        "Allow the app to reconnect to the same transmitter and inspect the "
        "reported session state.",
        "Dismiss any full-screen warm-up status if it appears and inspect Home.",
    ),
    exp=n(
        "The power-cycle completes using the approved procedure without the app "
        "falsely completing the session or creating a second session.",
        "The app resumes the transmitter-reported warm-up state rather than "
        "restarting a new 60-minute warm-up solely because of the power-cycle.",
        "Home remains reachable and shows the continuing warm-up session; a "
        "navigation trap is recorded as a failure against DO-905.",
    ),
    ev="Screenshots of warm-up state before and after power-cycle showing session continuity; execution record.",
)

# ── Apply + write ────────────────────────────────────────────────────────────
FULL_MAP = {"t":"title","req":"requirement","pre":"preconditions",
            "proc":"procedure","exp":"expected","ev":"evidence"}

compact = json.loads(COMPACT_PATH.read_text(encoding="utf-8-sig"))
full    = json.loads(FULL_PATH.read_text(encoding="utf-8-sig"))

before_c_ids = [r["id"] for r in compact]
before_f_ids = [r["id"] for r in full]

for cid, fields in UPDATES.items():
    cc = sum(1 for r in compact if r["id"] == cid)
    fc = sum(1 for r in full    if r["id"] == cid)
    assert cc == 1, f"Compact: expected 1 of {cid}, found {cc}"
    assert fc == 1, f"Full: expected 1 of {cid}, found {fc}"

for cid, fields in UPDATES.items():
    c = next(r for r in compact if r["id"] == cid)
    f = next(r for r in full    if r["id"] == cid)
    c.update(fields)
    f.update({FULL_MAP[k]: v for k, v in fields.items() if k in FULL_MAP})

assert [r["id"] for r in compact] == before_c_ids
assert [r["id"] for r in full]    == before_f_ids

# Re-embed compact into HTML
html = HTML_PATH.read_text(encoding="utf-8-sig")
embedded = json.dumps(compact, ensure_ascii=False, separators=(",",":")).replace("<","\\u003c")
html, count = re.subn(
    r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
    lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
assert count == 1, "EMBEDDED_CASES replacement failed"

COMPACT_PATH.write_text(json.dumps(compact, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
FULL_PATH.write_text(json.dumps(full, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
HTML_PATH.write_text(html, encoding="utf-8")
shutil.copy2(HTML_PATH, ROOT_HTML)

print(f"Updated: {len(UPDATES)} cases")
print(f"Compact: {len(compact)}  Run-order: {len(full)}")
