# Common fixes log

**[Français](COMMON-FIXES.md) · [English](COMMON-FIXES.en.md)**

Backport base: main / 0.9.3 / 684c8867ac67b6f4752743d23c88040103b19a98.

| Fix | Main commit | Backported to Notion | Validation |
|---|---|---|---|
| Published 0.9.3 state (Anytype properties, views, files and archives) | 684c886 | Yes, worktree base | 137 reference tests |

For every future fix, record the original commit, any adaptations and the tests performed. An uncommitted change or a message in another conversation does not mean it is integrated here. Avoid duplicating the same fix with diverging histories; prefer an independent common commit, then the main backport.

## Current preparation

- Profiles and launchers: specific to develop/notion; no backport planned into the stable version before the common application.
- anytwo_backend.py boundary: compatible refactoring, isolated in a separate commit for a possible main backport. Not yet integrated into main.
- Preparation validation: 140 tests passed, JavaScript syntax checks and two simultaneous demonstration servers with an unchanged stable reference configuration. No real import performed.

## Notion reader and analysis

- Notion connection, inventory and analysis: specific to develop/notion; no active Notion migration writes. Documentation: NOTION-API.en.md.
- Common fix `192d0be`: server UTF-8 output on Windows, especially with redirection; candidate for an independent backport, not integrated into main.
- Validation: 157 tests passed, syntax checks of the three JavaScript scripts, demonstration browser journey (connection, database, selection, analysis and return to Anytype). No real Notion call and no real import.

## Notion tree selection

- Notion-specific journey: available token masked, single space of the connection, roots loaded after connection, children on demand, selection/exclusions by branch. No change to the stable version or the destination engine.
- Inventory roots are not presented as an exact list of explicit permissions. Search limits and parents outside access remain reported.

- Next fix: reconstruction of block-type ancestors, distinct group for unresolved parents, asynchronous analysis with progress and cancellation. Block cache limited to one analysis, no modification of the Anytwo engine.

- Validation of this fix: 174 tests passed, including block-type parents, parents absent from search, asynchronous HTTP analysis, tracking during the network lock, cancellation and errors without leaking details. Browser journey checked with slowed fake responses.

- Responsiveness: cloud token validation limited to 5 seconds, bounded lock wait, inventory without blocking the whole interface, sequential branch preloading and navigation cache reuse. No need for the Notion client; the Anytwo client remains required for the local destination.
- Validation: 177 tests passed; branch preloaded then read back over HTTP in demo mode, without calling the real Notion account. JavaScript syntax checks and diff without errors.

- Large Notion analyses: four concurrent reads with a conservative global rate, shared cache and request deduplication, reuse of the same selection after interruption for five minutes, cancellable fifteen-minute budget. Notion-specific functions; no backport needed in Anytype.
- Validation: 185 tests passed. Concurrent reads verified, global cap tested, 529 delay and cancellation tested, reuse without re-reading successful blocks, cache invalidated by refresh. Fake network measurement (41 pages, 82 requests): 2.11 s serial, 1.33 s concurrent; this figure does not predict the real account throughput.

- Notion journey: connection popup with automatic check of the available token and first-level preparation; access to Notion/Anytwo settings through the API status; two selection/configuration panes. Explicit search indicator and permanent separation of non-first-level items, preloaded like other branches. Frontend scenario tests: tests/test_notion_ui.cjs.

- Validation of the new journey: 185 Python tests and 5 JavaScript scenarios passed; balanced HTML structure and unique identifiers. The Windows visual verification module does not start in this environment. No real Notion account test and no import performed.

- Notion connection state confirmed in green, button disabled after validation, separate loading popup closable without cancellation. Six interface scenarios verified. Rollup report fixed after reading the real descriptors of the Anytwo client (sum/original).
- Requested fixtures created then read back in Notion (parent page Test pour Anytwo) and in a new Anytype space Test pour Anytwo. The user personally granted Anytype write access; no stable setting was modified by the agent. Creation isolated in tools/create_test_pages.py, never used by the importer. Private log in reports/source-fixtures.json, excluded from Git.

- Final verification: 185 Python tests, six frontend scenarios, balanced HTML tags and unique identifiers. The source fixtures were read back through the API; no Anytwo object was modified to test rollups.

- Notion selection limited to root + two levels, without deeper preloading; selected branches are still fully traversed for analysis/import. Destination space configuration by workspace name, systematic collection creation policy and report by view type. Contract: NOTION-IMPORT.en.md. Validation: 188 Python tests and seven frontend scenarios. Notion → Anytwo writes still inactive; no change to the stable version.

- Notion screen aligned with “Import your data”: compatibility banner and common window adapted to the source, configuration with empty/summary/destination state, file and out-of-tree link options, Test/Import actions. The chats option remains specific to Anytype. Destination loaded automatically when choosing the workspace if Anytwo is available. Notion writing remains unavailable and the Import button reports it; these options trigger no write.

- Operational Notion import: notion_migration.py, notion_content.py, notion_views.py and notion_files.py reuse the common Anytwo boundary. Background task with shared lock, progress, cancellation, private checkpoints and report; Import button and options integration, with a Test preview of the same linked scope. Empty sources, exclusions, null sorts, paginated properties, frozen formulas, relations and rollup configurations are handled. No change to main or publication. Validation: 207 Python tests, eight frontend scenarios, authorized real import of the fixture (7 pages, 2 collections, 4 distinct files), API read-back of dates, relations, properties, colours and views. Rollup recalculation and final visual rendering still to verify in the client.

- Common fix `3e2fa1d` for views: dataview technical objects are created without any.name, like the native client. Naming them “Vues Anytype” made them appear in navigation as stray documents. Identifiers and view sets preserved. Fix isolated on develop/notion, candidate for an independent main backport; stable unchanged. View creation regression completed and Anytype suite verified.

- Notion formats fixed after inspecting the installed client: annotation spaces outside bold/italic/strikethrough markers; native callout, image-caption and synced-block envelopes; synchronization references and tables of contents finalized toward the real block identifiers after the PUT. Underline still unavailable in the bridge and explicitly reported. The existing fixture page was fixed with a prior backup, without creating new pages or modifying Notion. Validation: 214 Python tests, eight frontend scenarios, then conversion of the Markdown actually read back with the client libraries in an isolated DOM (network disabled): formats 1/2/4, callout, two canonical captions, synchronized original/reference and table-of-contents links confirmed. The three technical supports lost only their artificial name, keeping their data.

- Notion properties: collections created before properties, relation restriction by target xKey, rollup title through target collection / any.name, decoded source identities taking priority over names; native currencies, percentages and numeric separators. No artificial parent link. In-place fix of the fixture reimported by the user in Sri, with backup, unchanged values and one-time removal of the two generated links (no document PUT). Verification with the client functions: Projet/Name/Budget selectors, rollup results 100/180/0 and project names, currency/EUR format. Tests: 221 Python and eight frontend scenarios. Stable Anytype unchanged; Notion-specific fix.


- Notion read optimization: already complete properties not re-read, exclusion traversal avoided, shared cache and reuse of interrupted reads in memory, metrics by category, delays distinguished from network errors. No change to main. Addition to the Anytwo boundary of a set_space_icon helper: file attached to the index object and native URI in iconCid; independent candidate for backport if needed. Space image retrieval remains unavailable in the documented metadata of the Notion internal token; no bot avatar substituted.

- Validation of this optimization: 233 Python tests and eight frontend scenarios passed, including twelve regressions on unnecessary reads, exclusions/reinclusions, shared cache, reuse after delay and native icon. No real import triggered for these tests; performance on the user scope still to measure. Stable Anytype version clean and unchanged.


- Notion linked views: sources resolved through views when data_sources is empty, full-page database / inline view distinction, quick filters and removed columns, reported adaptation of groupings; callouts without artificial initial paragraphs and native icons. Minimal common change: inline_records and create_saved_views pass the optional icon field of converted views, without changing views without an icon. Candidate for an independent main backport, not applied to the stable version. Private audit data and replays under reports only, not versioned.

- Linked view validation: full suite of 245 Python tests and eight frontend scenarios passed, then 13 targeted view/icon tests and 25 engine tests after the last adjustments. Private replay of the five source pages: expected view counts confirmed, seven Base recettes views and quick filters present. Conversion by the client's real libraries in an isolated DOM: callouts without initial empty paragraph, Cave as an internal object link inside the callout, composed emoji recognized. No real import or write into Sri.


- Notion groups/relations/rollups: preservation of collection groupings and Kanban columns, text contains filter (LPB), default labels, paired dual_property two-way relations and native average. NotionViewConverter keeps these Notion-specific adaptations; native selection by collection avoids long identifier filters. The common collection_presentation engine accepts an optional group_settings field and translates the native UI schema, without changing other views; ui_clause accepts both notion_-prefixed text conditions. To isolate for a possible backport of the grouping schema into main; stable unchanged. Validation: 252 Python tests + eight frontend scenarios, client parser on 12 views, LPB query six objects on both sides, bidirectional pair recognized and 53 matching averages. No real import or write on Sri.


- Authorized common preparation: independent unified profile, source choice before access checks, one main launcher, local reuse of protected development secrets and reproducible public archive. Optional presentation settings openMode / galleryFitImage carried by the shared converter, without changing views that do not specify them. The profile and files of the stable Anytype version remain unchanged; no push or release.

- Common fix isolated in local commit 21592f3 (on release/unified): optional view presentation, native group_settings, view icons and space icon helper. Not integrated into main; depends on the anytwo_backend boundary already present in this branch. Final validation: 258 Python tests, four startup scenarios and eight Notion scenarios passed; Fit image/openMode recognized by the client's real parser. Archive extracted then started in demo mode: two sources accessible, writes disabled. No real import, no publication.


- 0.10.1 organization: active folder F:/Documents/ChatGPT/Anytwo/Any2Any, modules and static moved under app, tests/tools/examples/private reports grouped under dev. Launchers and test imports adapted; user profiles unchanged. Clean source archive and standalone Windows x64 distribution (Any2Any.exe, _internal, documentation); EXE checked after extraction before publication, without a real import. Reorganization authorized for the local folder, GitHub and a new release, without rewriting 0.10.0.

- Common fix `03e08b2` for Anytype mentions: `<mention object_id="…">Name</mention>` becomes a native object link `any://o/…` in text, columns, tables, compound cells and the description. Link discovery recognizes mention targets; they join the scope when the linked-items option is enabled, otherwise the label stays plain text with a warning. No backfill of already imported pages. Validation: 278 Python tests passed, including paragraph, table, compound cell, out-of-scope target, empty label and simulation with or without link following.

- Common fix for Anytype bookkeeping properties (23 November 2026): `source_object`, `template_name_prefill_type` and the other internal bookkeeping keys (`template_*`, `unique_key`, `cover_*`, `set_of`…) no longer become Anytwo columns. Matching is by key, never by label, across values, type schemas and inline views. Safety net: columns bearing those names in the collections created by the import are removed through `DELETE /collections/:id/properties/:propId` and listed in `removed_properties`; reused collections are never cleaned. Validation: 283 Python tests passed, including filtering, schema, artifacts and simulated deletion.

- Bilingual interface (23 November 2026): every static label of the Anytype and Notion pages is now translated FR/EN/DE, including `title`, `placeholder` and `aria-label` attributes. Dynamic log and report lines are translated through patterns (`Bilan : …`, `<name> — partiel · 1 adaptation(s)`, the “Contenu non reproduit :”, “Erreur :”, “ID Anytwo :” prefixes, selection reasons, API messages); source data (object names, identifiers, raw API text) stays untouched. The import window now fits the browser viewport (`max-height` with internal scrolling), with no zooming out. Tests: 286 Python, including two i18n checks (dictionary and markup coverage).
- Property values (23 November 2026): an empty value is no longer written for the url/email/phone/number/date formats, which removed the Anytwo `property.format_violation` error on the “source” property. A non-absolute address stays as text. Regression test added.

- Interface and error follow-up (23 November 2026): engine messages (issues, API errors, progress, analysis) are translated through a catalog of 144 templates, with names and identifiers reinserted. Relation columns always receive an array of `any://` URIs, removing the `property.format_violation` error on collections. The server must be restarted after a module update. Validation: 287 Python tests, a real read-only simulation fully in English, a simulated import without errors (0 of 237 objects).

- Relation normalization (23 November 2026): a relation value stored as a JSON list or a raw identifier is converted to `any://` URIs before writing; an unimported reference is skipped with a warning. Removes the `link "[...]" must be a plain any://<objectId> URI` error reported on the Regular collection. Validation: 288 Python tests and a simulated import of the real source with no property error.

- Layout markers and duplicate columns (23 November 2026): server any v0.5.0 stores any HTML comment as an `html` block, so the `any:collapsible`, `any:columns` and `any:block` envelopes were displayed as text. The migrator reads the server version (`envelopes_supported`) and, from 0.5.0 on, rewrites those blocks as plain Markdown (`legacy_markup`: bold title or heading, sequential columns, embed link, omitted image width) for both the Anytype and Notion engines. A partially imported relation no longer creates an `X (Anytype)` text column: the declared relation column is reused and only the missing references are dropped; a relation with no imported target writes nothing. Validation: 295 Python tests, 25 to 31 envelopes reduced to 0 on three real source pages, a real write into a test space with no `html` block, test spaces deleted afterwards.
