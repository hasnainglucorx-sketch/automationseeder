"""Make language display/initial-selection cases executable using the phone and app."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/console-update'


def numbered(items):
    return '\n'.join(f'{i}. {text}' for i, text in enumerate(items, 1))


UPDATES = {
    'VP-APP-LANGUAGE-001': {
        't': 'Display available languages and current selection',
        'pre': 'The user is signed in to CGMx 1 on the test phone.',
        'proc': numbered([
            'Open Settings > Language.',
            'Inspect and record the language options displayed in the app.',
            'Inspect the current-language selection indicator.',
        ]),
        'exp': numbered([
            'The Language screen opens without a blank screen or crash.',
            'The available language names are readable and distinguishable, with no blank or duplicate options.',
            'Exactly one language is indicated as the current selection.',
        ]),
        'ev': 'Language-list and current-selection screenshots; app build, platform and execution record.',
    },
    'VP-APP-LANGUAGE-005': {
        't': 'Initial language selection and fallback',
        'pre': 'CGMx 1 is installed on the test phone. A working test-account login is available. The phone supports changing its system language and resetting the app to a fresh installation of the same build.',
        'proc': numbered([
            'Sign in to the test account. Open Settings > User Profile and record the displayed account region, then open Settings > Language and record its available languages. Record the phone language and app build.',
            'In the phone settings, choose a system language that appears in the recorded app language list.',
            'Reset CGMx 1 to fresh local state: clear app storage on Android, or delete and reinstall the same build on iOS; do not use Offload App. Launch CGMx 1 and sign in to the same account without manually selecting an app language.',
            'Open Settings > Language, record the selected language, then inspect Settings and Home.',
            'Close and reopen CGMx 1, then check Settings > Language again.',
            'In the phone settings, choose a system language that does not appear in the recorded app language list.',
            'Reset CGMx 1 to fresh local state using the same method as step 3. Launch it and sign in to the same account without manually selecting an app language.',
            'Open Settings > Language and record the language selected automatically. Inspect Settings and Home for readable translated content.',
            'Close and reopen CGMx 1, then check Settings > Language again.',
            'Restore the original phone language and the desired app language through their settings.',
        ]),
        'exp': numbered([
            'The account region and available app languages are visible and recorded for this execution.',
            'The phone uses the chosen language that is present in the app language list.',
            'CGMx 1 completes fresh setup and sign-in without a prior local manual-language selection.',
            'The app selects the language matching the phone setting; Settings and Home use that language.',
            'The same automatically selected language remains active after reopening.',
            'The phone uses a language absent from the recorded app language list.',
            'CGMx 1 completes fresh setup and sign-in despite the unsupported phone language.',
            'The app automatically selects a fallback from its available language list. Settings and Home remain readable, with no blank labels or untranslated resource keys. The observed fallback is recorded.',
            'The same fallback remains active after reopening; it is not replaced by the unsupported phone language.',
            'The phone and app use the restored language settings and remain usable.',
        ]),
        'ev': 'App region/language-list screenshots; phone language settings for both scenarios; initial and reopened app selection screenshots; Settings and Home screenshots; app build, reset method, observed fallback and execution record. Exclude login credentials.',
    },
}


def main():
    paths = [OUT / 'PRT-0701-cases.json', OUT / 'PRT-0701-run_order.json']
    rows = [json.loads(p.read_text(encoding='utf-8-sig')) for p in paths]
    before = [[r['id'] for r in collection] for collection in rows]
    mapping = {'t': 'title', 'pre': 'preconditions', 'proc': 'procedure', 'exp': 'expected', 'ev': 'evidence'}
    for case_id, update in UPDATES.items():
        matches = [[r for r in collection if r['id'] == case_id] for collection in rows]
        assert all(len(m) == 1 for m in matches), case_id
        compact, full = [m[0] for m in matches]
        compact.update(update)
        full.update({mapping[k]: v for k, v in update.items()})
        compact['req'] = full['requirement']
    assert before == [[r['id'] for r in collection] for collection in rows]
    html_path = OUT / 'PRT-0701-Console-source.html'
    html = html_path.read_text(encoding='utf-8-sig')
    embedded = json.dumps(rows[0], ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    html, count = re.subn(r'(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)',
        lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
    assert count == 1
    for path, collection in zip(paths, rows):
        path.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    html_path.write_text(html, encoding='utf-8')
    shutil.copy2(html_path, ROOT / 'PRT-0701-Console-source.updated.html')
    print('Updated:', ', '.join(UPDATES))
    print('Ordered case IDs and counts unchanged:', list(map(len, rows)))


if __name__ == '__main__':
    main()
