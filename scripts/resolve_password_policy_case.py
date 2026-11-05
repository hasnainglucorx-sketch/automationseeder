"""Synchronize REG-005 with the recorded verified password-policy behavior."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/console-update'
CASE_ID = 'VP-APP-HOSTED-REG-005'


def main():
    paths = [OUT / 'PRT-0701-cases.json', OUT / 'PRT-0701-run_order.json']
    collections = [json.loads(p.read_text(encoding='utf-8-sig')) for p in paths]
    original_ids = [[c['id'] for c in rows] for rows in collections]
    selected = []
    for rows in collections:
        matches = [c for c in rows if c['id'] == CASE_ID]
        assert len(matches) == 1, CASE_ID
        selected.append(matches[0])
    procedure = '\n'.join([
        '1. Complete Email, Given name(s) and Region with valid details. Leave both password fields empty.',
        '2. Enter the same password in Password and Confirm password using fewer than 12 characters, including a number, lowercase letter, uppercase letter and special character.',
        '3. Replace both entries with the same password of at least 12 characters containing lowercase, uppercase and special characters but no number.',
        '4. Replace both entries with the same password of at least 12 characters containing a number, uppercase letter and special character but no lowercase letter.',
        '5. Replace both entries with the same password of at least 12 characters containing a number, lowercase letter and special character but no uppercase letter.',
        '6. Replace both entries with the same password of at least 12 characters containing a number, lowercase letter and uppercase letter but no special character.',
        '7. Replace both entries with the same password of at least 12 characters containing a number, lowercase letter, uppercase letter and special character. Observe the validation and Create an account control without submitting the form.',
    ])
    messages = [
        'Invalid password: minimum length 12.',
        'Invalid password: must contain at least 1 numerical digits.',
        'Invalid password: must contain at least 1 lower case characters.',
        'Invalid password: must contain at least 1 upper case characters.',
        'Invalid password: must contain at least 1 special characters.',
    ]
    expected = '\n'.join(
        ['1. Create an account remains disabled while the password fields are empty.']
        + [f'{i}. Keycloak shows "{message}" Create an account remains disabled.'
           for i, message in enumerate(messages, 2)]
        + ['7. No password-format message is shown and Create an account is enabled. The registration form remains open and no account is created.']
    )
    update = {
        't': 'Password format validation',
        'pre': 'Hosted Registration is open. Valid values for every other required field are available.',
        'proc': procedure,
        'exp': expected,
        'ev': 'Screenshots or recording of the empty-password state, each of the five password-format messages with the disabled action, and the valid-password state with the enabled action; execution record. Password values remain masked and are excluded from evidence.',
    }
    mapping = {'t': 'title', 'pre': 'preconditions', 'proc': 'procedure', 'exp': 'expected', 'ev': 'evidence'}
    selected[0].update(update)
    selected[1].update({mapping[k]: v for k, v in update.items()})
    # Preserve the existing full-case traceability in the compact representation.
    selected[0]['req'] = selected[1]['requirement']
    assert original_ids == [[c['id'] for c in rows] for rows in collections]
    html_path = OUT / 'PRT-0701-Console-source.html'
    html = html_path.read_text(encoding='utf-8-sig')
    embedded = json.dumps(collections[0], ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    pattern = r'(var EMBEDDED_CASES = )\[.*?\](;\n\n  function startWithCases)'
    html, count = re.subn(pattern, lambda m: m[1] + embedded + m[2], html, count=1, flags=re.S)
    assert count == 1
    for path, rows in zip(paths, collections):
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    html_path.write_text(html, encoding='utf-8')
    shutil.copy2(html_path, ROOT / 'PRT-0701-Console-source.updated.html')
    assert html_path.read_bytes() == (ROOT / 'PRT-0701-Console-source.updated.html').read_bytes()
    print(f'{CASE_ID}: updated; ordered IDs and counts unchanged: {list(map(len, collections))}')


if __name__ == '__main__':
    main()
