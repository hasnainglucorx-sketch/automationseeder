# Deep cleanup — 14 October 2026

The workspace now has one execution console: `CGMX1-Console.html`.
Its canonical inputs remain in `output/console-update/PRT-0701-cases.json`,
`PRT-0701-run_order.json`, `PRT-0702-cases.json`, and `PRT-0701-appendixC.json`.

Retired from the active workspace:

- two byte-identical console copies;
- the old standalone Test Runner and Case Review pages;
- separate Portal review/manual-guide HTML pages.
- their dedicated HTML generators and legacy localStorage replay helpers.
- five historical JSON snapshots that were mixed into the canonical source folder.

The retired material is recoverable from `archive/retired-ui-2026-10-14/` with
its original relative paths. Dated reports, execution evidence, checkpoints,
general case-maintenance scripts, temporary document work, `.secrets`, and current
source JSON were not moved.

The active workspace contains one root HTML file, no HTML under `output/`, and
exactly four files under `output/console-update/`: the three canonical case sources
and Appendix C. Historical copies keep their original paths inside the archive.

To restore a retired page, copy it from the archive to its recorded relative path.
The generator no longer recreates console duplicates or links to the separate
Portal manual guide.
