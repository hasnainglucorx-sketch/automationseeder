"""Compare the docx-extracted cases against the current run-order JSON.

Normalizes whitespace/smart-quotes before comparing so formatting-only
differences don't show up as noise. Reports, per case id present in both:
  - which fields differ
  - a short diff preview

Cases only in the docx or only in run-order are reported separately.
"""
import json
import re

RUN_ORDER = r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update\PRT-0701-run_order.json"
EXTRACT = r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update\PRT-0392-docx-extract.json"

FIELDS = ["title", "requirement", "preconditions", "procedure", "expected"]

SMART_QUOTES = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\xa0": " ", "\ufffd": "'",
}


def norm(s):
    if not s:
        return ""
    for k, v in SMART_QUOTES.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    run_order = {c["id"]: c for c in load(RUN_ORDER)}
    extract = {c["id"]: c for c in load(EXTRACT)}

    only_docx = sorted(set(extract) - set(run_order))
    only_run = sorted(set(run_order) - set(extract))
    common = sorted(set(extract) & set(run_order))

    diffs = {}
    for cid in common:
        d = extract[cid]
        r = run_order[cid]
        field_diffs = {}
        for field in FIELDS:
            dv = norm(d.get(field, ""))
            rv = norm(r.get(field, ""))
            if field == "title" and not d.get("title"):
                continue  # title not captured from heading, skip
            if dv != rv:
                field_diffs[field] = {"docx": d.get(field, ""), "run_order": r.get(field, "")}
        if field_diffs:
            diffs[cid] = field_diffs

    print(f"common ids: {len(common)}")
    print(f"only in docx (not in run_order): {len(only_docx)} -> {only_docx}")
    print(f"only in run_order (not in docx): {len(only_run)}")
    print(f"ids with field differences: {len(diffs)}")
    print()
    for cid, fd in diffs.items():
        print(f"=== {cid} ===  fields: {list(fd.keys())}")

    out = {
        "only_docx": only_docx,
        "only_run_order": only_run,
        "diffs": diffs,
    }
    with open(
        r"C:\Users\Hasnain\Downloads\Automation seeder\output\console-update\PRT-0392-docx-diff-report.json",
        "w", encoding="utf-8"
    ) as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
