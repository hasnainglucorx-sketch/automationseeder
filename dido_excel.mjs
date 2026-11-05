import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from 'file:///C:/Users/Hasnain/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const source = await fs.readFile('output/PRT-0702-dido-flat.csv', 'utf8');
const rows = source.replace(/^\uFEFF/, '').trimEnd().split(/\r?\n/).map(line => {
  const comma = line.indexOf(',');
  return [line.slice(0, comma), line.slice(comma + 1)];
});
const workbook = Workbook.create();
const sheet = workbook.worksheets.add('DIDO');
sheet.getRange(`A1:B${rows.length}`).values = rows;
sheet.getRange(`A1:B${rows.length}`).format.font = { name: 'Arial', size: 10 };
sheet.getRange('A1:B1').format = { fill: '#17365D', font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' } };
sheet.getRange(`A:A`).format.columnWidth = 135;
sheet.getRange(`B:B`).format.columnWidth = 160;
workbook.recalculate();
await fs.mkdir('outputs/dido-excel', { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save('outputs/dido-excel/PRT-0702-dido.xlsx');
console.log(`Wrote ${rows.length - 1} records`);
