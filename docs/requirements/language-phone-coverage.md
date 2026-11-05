# Phone-based language checks — 5 October 2026

`VP-APP-LANGUAGE-001` and `VP-APP-LANGUAGE-005` now use the test phone, installed CGMx 1 build and a working test-account login. No separate Test Data table, seeded glucose dataset, Keycloak administrator access or external language matrix is an execution prerequisite.

- LANGUAGE-001 checks the visible language list and current selection.
- LANGUAGE-005 obtains the region and language list from the app, selects phone languages inside/outside that list, resets local app state between scenarios, checks automatic selection and fallback, and checks persistence after reopening. Reset/reinstallation of the same build is part of the procedure because an existing saved language would mask initial selection.
- Existing requirement links are preserved. LANGUAGE-002 through LANGUAGE-004 are unchanged.

## Requirement coverage limit

The app's own language list and selected fallback are observations, not independent proof of the intended regional configuration. These cases verify observable phone/app behavior. Passing them alone does not prove that the available list or exact fallback language matches the intended regional configuration in DI-823 / DO-879 and DI-279 / DO-667. That configuration-conformance comparison remains unverified; it is not silently treated as Pass or imposed as a prerequisite to executing the observable checks.

No formal execution result was changed. The older report is retained as the original execution record.
