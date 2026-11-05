"""Update PRT-0701 for the observed iOS 22-step setup and warm-up flow."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/console-update"


def numbered(items):
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


def case(title, requirement, precondition, actions, results, evidence):
    assert len(actions) == len(results)
    return {
        "t": title,
        "req": requirement,
        "pre": precondition,
        "proc": numbered(actions),
        "exp": numbered(results),
        "ev": evidence,
    }


UPDATES = {
    "VP-APP-VIDEO-004": case(
        "Back and forward navigation within the 22-step setup guide",
        "DI-716 / DO-819",
        "A screen within the 22-step sensor setup guide is displayed before session start.",
        [
            "Record the current step number and visible selections, then select Back.",
            "Select the visible forward action to return to the recorded step.",
            "Inspect the step number, selections and sensor-session state.",
        ],
        [
            "The preceding setup screen is displayed without exiting the guide or starting a sensor session.",
            "The recorded setup screen is displayed again without a blank screen, crash or duplicate transition.",
            "The step sequence remains coherent, applicable selections are retained, and no sensor session was started by navigation alone.",
        ],
        "Before/after screenshots or screen recording showing step numbers, selections and session state; execution record.",
    ),
    "VP-APP-PREP-001": case(
        "Step 17 sensor removal guidance",
        "DI-716 / DO-819",
        "Step 17 of 22 - Take out your sensor is displayed.",
        [
            "Inspect the complete Step 17 screen without selecting its action.",
            "Read the package, expiry, damage and cannula guidance.",
        ],
        [
            "Step 17 shows Take out your sensor, relevant visual guidance, Back, the voice control and I have my applicator; all content is readable.",
            "The screen tells the user to check the package and expiry and not to use a damaged product or exposed cannula.",
        ],
        "Step 17 screenshot showing the full content and controls; execution record.",
    ),
    "VP-APP-PREP-002": case(
        "Continue from sensor removal to cap removal",
        "DI-716 / DO-819",
        "Step 17 of 22 - Take out your sensor is displayed.",
        ["Select I have my applicator once."],
        ["Step 18 of 22 - Remove the cap is displayed once and the setup guide remains active."],
        "Step 17 and Step 18 screenshots or transition recording; execution record.",
    ),
    "VP-APP-PREP-003": case(
        "Back from sensor removal returns to skin preparation",
        "DI-716 / DO-819",
        "Step 17 of 22 - Take out your sensor is displayed.",
        [
            "Select Back once.",
            "Select My skin is clean and dry once.",
        ],
        [
            "Step 16 of 22 - Clean and dry your skin is displayed without exiting setup.",
            "Step 17 of 22 - Take out your sensor is displayed again.",
        ],
        "Step 17 > 16 > 17 screenshots or screen recording; execution record.",
    ),
    "VP-APP-SITE-001": case(
        "Step 4 application-site guidance and choices",
        "DI-716 / DO-819",
        "Step 4 of 22 - Choose the application site is displayed.",
        ["Inspect the complete screen, placement guidance and both site choices."],
        ["Back of the upper arm and Abdomen are readable selectable choices, with placement guidance, Back, voice control, Skip and Continue visible and usable."],
        "Step 4 screenshot showing the complete content and controls; execution record.",
    ),
    "VP-APP-SITE-002": case(
        "Select and change the application site",
        "DI-716 / DO-819",
        "Step 4 of 22 - Choose the application site is displayed.",
        [
            "Select Back of the upper arm and record its selection indicator.",
            "Select Abdomen and record its selection indicator.",
            "Select Back of the upper arm again.",
        ],
        [
            "Back of the upper arm alone has the selected blue outline.",
            "Abdomen alone has the selected blue outline and the previous choice is cleared.",
            "Back of the upper arm alone is selected again; switching choices does not advance the guide.",
        ],
        "Screenshots of both selected states; execution record.",
    ),
    "VP-APP-SITE-003": case(
        "Continue after choosing an application site",
        "DI-716 / DO-819",
        "Step 4 of 22 is displayed with one application site selected.",
        ["Select Continue once."],
        ["Step 5 of 22 - A few permissions to keep you safe is displayed once and the selected site remains available for later setup guidance."],
        "Selected Step 4 and Step 5 screenshots or transition recording; execution record.",
    ),
    "VP-APP-SITE-004": case(
        "Back from application site returns to saved profile review",
        "DI-716 / DO-819",
        "Step 4 of 22 - Choose the application site is displayed.",
        [
            "Select Back once.",
            "Select Continue on the saved-profile review screen.",
        ],
        [
            "Step 3 of 22 - Tell us about you is displayed without exiting onboarding.",
            "Step 4 of 22 - Choose the application site is displayed again.",
        ],
        "Step 4 > 3 > 4 screenshots or screen recording; execution record.",
    ),
    "VP-APP-CAP-001": case(
        "Step 18 applicator-cap guidance",
        "DI-716 / DO-819",
        "Step 18 of 22 - Remove the cap is displayed.",
        ["Inspect the complete instruction, warning, illustration and controls without selecting the action."],
        ["Step 18 clearly instructs the user to remove the cap, warns not to put it back on before use, and shows Back, voice control, Skip and Cap removed without clipped content."],
        "Step 18 screenshot showing the complete content and controls; execution record.",
    ),
    "VP-APP-CAP-002": case(
        "Continue from cap removal to applicator placement",
        "DI-716 / DO-819",
        "Step 18 of 22 - Remove the cap is displayed.",
        ["Select Cap removed once."],
        ["Step 19 of 22 - Place the applicator is displayed once and the setup guide remains active."],
        "Step 18 and Step 19 screenshots or transition recording; execution record.",
    ),
    "VP-APP-CAP-003": case(
        "Back from cap removal returns to sensor removal",
        "DI-716 / DO-819",
        "Step 18 of 22 - Remove the cap is displayed.",
        [
            "Select Back once.",
            "Select I have my applicator once.",
        ],
        [
            "Step 17 of 22 - Take out your sensor is displayed without exiting setup.",
            "Step 18 of 22 - Remove the cap is displayed again.",
        ],
        "Step 18 > 17 > 18 screenshots or screen recording; execution record.",
    ),
    "VP-APP-WARMUP-003": case(
        "Leave warm-up for Home without ending the session",
        "DI-860 / DO-905 and DI-862 / DO-918",
        "The full-screen warm-up UI is displayed for an established sensor session that is still warming up.",
        [
            "Inspect and record the available navigation or dismissal controls.",
            "Use the applicable visible control or standard iOS navigation route once to leave the full-screen warm-up UI.",
            "Observe the destination and current sensor-session state.",
        ],
        [
            "A user-accessible route to dismiss the full-screen warm-up UI is available.",
            "Home is displayed without cancelling, restarting or completing the sensor session.",
            "Home shows the same sensor session warming up with its estimated remaining time; inability to reach Home is recorded as a failure against DO-905.",
        ],
        "Screen recording from established warm-up through the navigation attempt; warm-up and Home screenshots; app/iOS version and execution record.",
    ),
    "VP-APP-WARMUP-004": case(
        "Home shows the ongoing warm-up after dismissal",
        "DI-717 / DO-820 and DI-860 / DO-905",
        "An established sensor session is warming up and the full-screen warm-up UI has been dismissed successfully.",
        [
            "Inspect the CGM area on Home.",
            "Wait for an observable countdown or status update without ending the session, then inspect Home again.",
        ],
        [
            "Home shows warm-up in progress instead of a glucose value and displays the estimated remaining time.",
            "Home continues to represent the same warm-up session and does not falsely display LIVE CGM; if dismissal is blocked, record this case as dependent on WARMUP-003 rather than Passed.",
        ],
        "Home screenshots at two times with device clock/status visible; session identifier where available; execution record.",
    ),
    "VP-APP-WARMUP-006": case(
        "Non-real-time functions remain available during warm-up",
        "DI-860 / DO-905",
        "An established sensor session is warming up and Home is accessible.",
        [
            "Open available historical glucose or report content from Home.",
            "Open the manual-entry function and return without saving patient data.",
            "Return to Home and inspect the warm-up status.",
        ],
        [
            "Historical non-real-time content remains accessible during warm-up.",
            "Manual entry remains accessible during warm-up; no entry is required for this navigation check.",
            "The same sensor session remains in warm-up; blocked Home access is recorded as the upstream WARMUP-003 failure and prevents these dependent checks.",
        ],
        "Screen recording of the accessible routes and return to Home; app/iOS version and execution record.",
    ),
    "VP-APP-WARMUP-007": case(
        "Bluetooth interruption preserves warm-up and navigation",
        "DI-717 / DO-820 and DI-860 / DO-905",
        "An established sensor session is warming up, Home is accessible and Bluetooth is on.",
        [
            "Record the warm-up status and remaining-time estimate, then turn Bluetooth off briefly.",
            "Turn Bluetooth on and allow the same transmitter to reconnect.",
            "Leave the full-screen status if it reappears and inspect Home.",
        ],
        [
            "The interruption is represented without falsely completing or restarting warm-up.",
            "The same session reconnects and warm-up continues from transmitter-reported state.",
            "Home remains reachable and shows the continuing warm-up; a renewed navigation trap is recorded as a failure against DO-905.",
        ],
        "Timed screen recording before, during and after interruption; reconnection and Home screenshots; execution record.",
    ),
    "VP-APP-WARMUP-008": case(
        "Transmitter power cycle does not restart warm-up or block Home",
        "DI-717 / DO-820 and DI-860 / DO-905",
        "An established sensor session is warming up and the approved transmitter power-cycle procedure is available.",
        [
            "Record warm-up status and remaining-time estimate, then perform the approved transmitter power cycle.",
            "Allow the app to reconnect to the same transmitter and inspect the reported session state.",
            "Leave the full-screen status if it appears and inspect Home.",
        ],
        [
            "The app does not falsely complete the session or create a second session during the interruption.",
            "The app resumes the transmitter-reported warm-up state rather than restarting a new 60-minute warm-up solely because of the power cycle.",
            "Home remains reachable and shows the continuing session; a navigation trap is recorded as a failure against DO-905.",
        ],
        "Timed recording of warm-up, power cycle, reconnection and Home; execution record.",
    ),
    "VP-APP-WARMUP-009": case(
        "Warm-up completion transitions to live CGM",
        "DI-345 / DO-709, DI-717 / DO-820 and DI-862 / DO-918",
        "A valid test sensor session is in established warm-up and can provide its first valid glucose-containing measurement.",
        [
            "Observe the warm-up state until the first valid glucose-containing measurement is received.",
            "Inspect the CGM state and navigation after the transition.",
        ],
        [
            "Warm-up ends in response to the qualifying transmitter measurement and does not complete merely because the displayed estimate reaches zero.",
            "The app presents the live CGM state for the same session, shows the applicable current reading/status and permits normal navigation.",
        ],
        "Timestamped warm-up and first-live-reading screenshots or recording; transmitter/session evidence and execution record.",
    ),
}


NEW_CASES = [
    ("VP-APP-SETUP-001", "Setup Guide", case(
        "Your setup overview and four stages", "DI-716 / DO-819",
        "Step 1 of 22 - Your setup is displayed.",
        ["Scroll through the complete screen and inspect the four stages.", "Select Continue once."],
        ["Prepare your app, Pair your sensor, Apply your sensor and Start warm-up are readable, with the progress, Back, voice, Skip and Continue controls accessible.", "Step 2 of 22 - Before you begin is displayed once."],
        "Step 1 full-page screenshots and Step 2 destination screenshot; execution record.")),
    ("VP-APP-SETUP-002", "Setup Guide", case(
        "Before-you-begin checklist and route", "DI-716 / DO-819",
        "Step 2 of 22 - Before you begin is displayed.",
        ["Inspect the complete checklist and controls.", "Select I'm ready once."],
        ["The internet, phone date/time and sensor-box/applicator checklist items are readable with progress, Back, voice and Skip available.", "Step 3 of 22 - Tell us about you is displayed once; static checkmarks alone are not recorded as proof of live connectivity or clock validation."],
        "Step 2 and Step 3 screenshots or transition recording; execution record.")),
    ("VP-APP-SETUP-003", "Setup Guide", case(
        "Permission overview content and progression", "DI-716 / DO-819 and DI-719 / DO-822",
        "Step 5 of 22 - A few permissions to keep you safe is displayed.",
        ["Scroll through the full permission overview.", "Select Continue once."],
        ["Apple Health, Bluetooth, Notifications and Critical alerts guidance is readable and the action remains accessible without permanently hidden content.", "Step 6 of 22 - Connect Apple Health is displayed once."],
        "Full Step 5 screenshots and Step 6 destination screenshot; execution record.")),
    ("VP-APP-SETUP-004", "Setup Guide", case(
        "Skip does not start or complete a sensor session", "DI-714 / DO-818 and DI-716 / DO-819",
        "A skippable screen in the sensor-installation setup guide is displayed before sensor session start.",
        ["Record the current guide step and sensor-session state, then select Skip once.", "Start new-sensor setup again from the available app route."],
        ["The guide exits through the approved non-clinical destination without starting a sensor session or representing incomplete onboarding as complete.", "The complete sensor/transmitter guide is presented again from its defined first step for the new setup."],
        "Before/after screenshots or recording showing step, destination and session state; reopened-guide screenshot; execution record.")),
    ("VP-APP-VOICE-001", "Application Guidance", case(
        "Voice guidance follows the speaker control", "DI-716 / DO-819",
        "A narrated sensor-application step with the speaker control is displayed and device audio can be heard safely.",
        ["With the speaker shown as enabled, replay or reopen the step and listen to its guidance.", "Select the speaker control to mute it, then replay or reopen the same step.", "Navigate to the next narrated step."],
        ["The visible step guidance is narrated once and the enabled icon matches the audible state.", "The control shows muted and the same guidance does not play while muted.", "No stale or overlapping narration from the previous step continues after navigation."],
        "Screen recording with device audio and visible speaker states; execution record.")),
    ("VP-APP-VOICE-002", "Application Guidance", case(
        "Voice setting does not control the application timer", "DI-716 / DO-819",
        "Step 20 of 22 - Press and hold is displayed and the timer has not started.",
        ["Mute the voice control and select Start 10-second timer once.", "Observe the timer until its completed state."],
        ["The voice is muted and the application timer starts normally without duplicate starts.", "Ten seconds complete is displayed once even though narration was muted."],
        "Screen recording with muted icon and timer start/completion; execution record.")),
    ("VP-APP-APPLY-001", "Application Guidance", case(
        "Step 16 clean-and-dry guidance", "DI-716 / DO-819 and DI-866",
        "Step 16 of 22 - Clean and dry your skin is displayed.",
        ["Inspect the complete instruction and controls.", "Select My skin is clean and dry once."],
        ["The screen presents cleaning and drying guidance with relevant visual content and accessible navigation/action controls.", "Step 17 of 22 - Take out your sensor is displayed once."],
        "Step 16 and Step 17 screenshots or transition recording; execution record.")),
    ("VP-APP-APPLY-002", "Application Guidance", case(
        "Step 19 applicator placement guidance", "DI-716 / DO-819",
        "Step 19 of 22 - Place the applicator is displayed.",
        ["Inspect the complete instruction and controls.", "Select I'm ready to apply once."],
        ["The placement guidance and image are readable with Back, voice, Skip and the action accessible.", "Step 20 of 22 - Press and hold is displayed once."],
        "Step 19 and Step 20 screenshots or transition recording; execution record.")),
    ("VP-APP-APPLY-003", "Application Guidance", case(
        "Ten-second press-and-hold timer", "DI-716 / DO-819",
        "Step 20 of 22 - Press and hold is displayed and the timer has not started.",
        ["Start a device screen recording with a visible time reference, then select Start 10-second timer once.", "Keep the app foregrounded and observe the timer until completion."],
        ["A single running timer starts and the screen does not show completion immediately.", "Ten seconds complete is shown once after approximately ten seconds, without an early or duplicate completion."],
        "Timed screen recording from tap through completion; app/iOS version and execution record.")),
    ("VP-APP-APPLY-004", "Application Guidance", case(
        "Application timer resists duplicate and interrupted actions", "DI-716 / DO-819",
        "Step 20 of 22 - Press and hold is displayed and the timer has not started.",
        ["Select Start 10-second timer twice in quick succession.", "During a fresh timer run, background and foreground the app once.", "Inspect the timer state and complete or restart it using the visible controls."],
        ["Only one timer is active and no duplicate completion states are created.", "Returning to the app produces one coherent timer state without overlapping timers or stale narration.", "The flow provides a clear single path to the completed state and does not advance to Step 21 before completion."],
        "Screen recordings of duplicate tap and background/foreground scenarios; execution record.")),
    ("VP-APP-APPLY-005", "Application Guidance", case(
        "Step 21 removal and used-applicator disposal guidance", "DI-716 / DO-819",
        "Step 21 of 22 - Remove the applicator is displayed.",
        ["Inspect the complete removal, post-use cap and disposal guidance.", "Select Applicator removed once."],
        ["The screen tells the user to remove the applicator and presents the post-use cap/disposal guidance with readable controls.", "Step 22 of 22 - Make sure your sensor is secure is displayed once."],
        "Step 21 and Step 22 screenshots or transition recording; execution record.")),
    ("VP-APP-APPLY-006", "Application Guidance", case(
        "Step 22 sensor-secure check and transmitter-setup handoff", "DI-716 / DO-819 and DI-720",
        "Step 22 of 22 - Make sure your sensor is secure is displayed and no transmitter session has started.",
        ["Inspect the complete security-check guidance and controls.", "Select Sensor is secure once.", "Inspect the next screen and session state."],
        ["The final sensor-security guidance is readable and does not represent the transmitter as connected.", "The app transitions once to transmitter setup without falsely starting a live or warm-up session.", "Transmitter Setup is displayed at its scan-or-pair stage and requires a separate transmitter connection action."],
        "Step 22 and Transmitter Setup screenshots or transition recording; session-state evidence and execution record.")),
]


def main():
    compact_path = OUT / "PRT-0701-cases.json"
    full_path = OUT / "PRT-0701-run_order.json"
    compact = json.loads(compact_path.read_text(encoding="utf-8-sig"))
    full = json.loads(full_path.read_text(encoding="utf-8-sig"))
    before_compact_ids = [row["id"] for row in compact]
    before_full_ids = [row["id"] for row in full]
    update_ids = set(UPDATES)
    assert all(sum(row["id"] == cid for row in compact) == 1 for cid in update_ids)
    assert all(sum(row["id"] == cid for row in full) == 1 for cid in update_ids)
    new_ids = [cid for cid, _, _ in NEW_CASES]
    all_existing_ids = set(before_compact_ids) | set(before_full_ids)
    assert not (all_existing_ids & set(new_ids)), all_existing_ids & set(new_ids)

    mapping = {"t": "title", "req": "requirement", "pre": "preconditions", "proc": "procedure", "exp": "expected", "ev": "evidence"}
    for cid, values in UPDATES.items():
        c = next(row for row in compact if row["id"] == cid)
        f = next(row for row in full if row["id"] == cid)
        c.update(values)
        f.update({mapping[key]: value for key, value in values.items()})

    next_r = max(row["r"] for row in compact) + 1
    next_run = max(row["run"] for row in full) + 1
    for offset, (cid, section, values) in enumerate(NEW_CASES):
        compact.append({
            "r": next_r + offset,
            "sec": f"iOS 22-step setup - {section}",
            "id": cid,
            "t": values["t"],
            "method": "Manual - Real Device",
            "req": values["req"],
            "pre": values["pre"],
            "proc": values["proc"],
            "exp": values["exp"],
            "ev": values["ev"],
        })
        full.append({
            "run": next_run + offset,
            "day": "Day 4",
            "phase": "Phase 3",
            "id": cid,
            "recovery": "R3",
            "est": "6",
            "section": section,
            "title": values["t"],
            "requirement": values["req"],
            "preconditions": values["pre"],
            "procedure": values["proc"],
            "expected": values["exp"],
            "evidence": values["ev"],
        })

    assert [row["id"] for row in compact[:len(before_compact_ids)]] == before_compact_ids
    assert [row["id"] for row in full[:len(before_full_ids)]] == before_full_ids
    assert len(compact) == len(before_compact_ids) + len(NEW_CASES)
    assert len(full) == len(before_full_ids) + len(NEW_CASES)

    html_path = OUT / "PRT-0701-Console-source.html"
    html = html_path.read_text(encoding="utf-8-sig")
    embedded = json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html, count = re.subn(
        r"(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)",
        lambda match: match[1] + embedded + match[2],
        html,
        count=1,
        flags=re.S,
    )
    assert count == 1
    compact_path.write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    full_path.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    shutil.copy2(html_path, ROOT / "PRT-0701-Console-source.updated.html")
    print("Updated existing:", ", ".join(UPDATES))
    print("Added:", ", ".join(new_ids))
    print("Counts:", len(compact), len(full))


if __name__ == "__main__":
    main()
