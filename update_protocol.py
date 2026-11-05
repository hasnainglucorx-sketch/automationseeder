from pathlib import Path
from docx import Document
from docx.shared import Pt

source = Path(r"C:\Users\Hasnain\Downloads\PRT-0392 Modus Mobile Apps UI Test Cases ver-0 1 (1).docx")
output = Path(r"C:\Users\Hasnain\Downloads\Automation seeder\output\PRT-0392-Modus-Mobile-App-UI-Test-Protocol-Updated.docx")
doc = Document(str(source))

# The supplied file has one case table per unique test case ID.
case_ids = set()
for table in doc.tables:
    sample = " ".join(cell.text for row in table.rows[:2] for cell in row.cells)
    import re
    match = re.search(r"VP-APP-[A-Z0-9-]+", sample)
    if match:
        case_ids.add(match.group(0))
assert len(case_ids) == 451, f"Unexpected case count: {len(case_ids)}"

# Replace existing visible text in-place to preserve the document's styles and layout.
def replace_paragraph(paragraph, value):
    if paragraph.runs:
        paragraph.runs[0].text = value
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(value)

for p in doc.paragraphs:
    text = p.text.strip()
    if text == "PURPOSE":
        continue
    if text.startswith("This protocol defines the controlled verification activities"):
        replace_paragraph(
            p,
            "This protocol defines controlled verification activities for the Modus App mobile application. It contains 451 unique test cases covering the current documented application scope, with prerequisites, procedures, expected results, requirement traceability, and evidence requirements. Case definitions do not represent execution results; execution status and evidence must be recorded by an authorized tester.",
        )
    elif text == "RELATED ITEMS":
        replace_paragraph(p, "RELATED DOCUMENTS AND RECORDS")
    elif text == "ENVIRONMENT HEALTH AND SAFETY":
        replace_paragraph(p, "ENVIRONMENTAL HEALTH AND SAFETY")
    elif text == "An approved iOS and Android mobile phone loaded with the correct version of the Modus App is required to execute this protocol. Refer to section 9.3 Test Data for reference IDs.":
        replace_paragraph(
            p,
            "Use an approved iOS or Android phone, as applicable to the test case, with the approved Modus App build installed. Record the device model, operating system version, application build, and relevant equipment identifiers in the execution record. Refer to section 9.3 Test Data for controlled reference IDs.",
        )
    elif text == "Appendix A is the test case register contained in the Process section. Execution exports, screenshots, recordings, defect records, and signed approvals are retained in the controlled quality system and referenced from the execution record.":
        replace_paragraph(
            p,
            "Appendix A is the test case register contained in the Process section. Execution results and supporting evidence, including screenshots, recordings, defect records, and approvals, are recorded by the authorized tester in the controlled quality system and referenced from the execution record. Do not infer a pass from the presence of a test case definition.",
        )
    elif text == "<Add execution evidence for each test case with its ID here>":
        replace_paragraph(
            p,
            "Execution evidence is maintained in the controlled quality system and linked to each test case ID in the execution record. No execution evidence is asserted by this protocol document.",
        )

doc.core_properties.title = "PRT-0392 Modus Mobile App UI Test Protocol"
doc.core_properties.subject = "Controlled verification protocol containing 451 unique Modus App UI test cases"
output.parent.mkdir(parents=True, exist_ok=True)
doc.save(str(output))
print(output)
