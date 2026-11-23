# Any2Any — Anytype → Anytwo migrator (v0.9.3)

**[Français](NOTES-TECHNIQUES.fr.md) · [English](NOTES-TECHNIQUES.en.md)**

The common version starts with Any2Any.exe in the standalone Windows archive, or demarrer.bat in the source version, and offers Anytype or Notion before the access checks. This document mainly details the Anytype source; the Notion journey is described in [NOTION-IMPORT.en.md](NOTION-IMPORT.en.md).

**Project version: 0.9.3.** The change sections below trace previous versions. Current improvements are detailed in [the bilingual changelog](../CHANGELOG.md) and [import fidelity](IMPORT-FIDELITE.en.md).

Python application + local web interface for importing Anytype spaces, collections, types and objects into Anytwo. **The simple import really creates data in Anytwo.** The Anytype source is always queried read-only. The “With synchronization” option is **not operational yet** and does not allow a real import.

> **Read before a first attempt**: automated tests with simulated local HTTP APIs are complemented by targeted checks of the APIs and the installed client code, as well as manual tests by the project owner. This is not exhaustive validation of every content type. The Anytype v2 API is an evolving preview. Start with 1 or 2 pages and a **test Anytwo space**, back up your data and compare the result. There is **no automatic rollback**. A second simple import creates new copies.

## Starting on Windows

1. Install Python **3.10 or newer** if needed.
2. Extract the whole archive.
3. Open **Anytype** and **Anytwo** and let the spaces load.
4. Double-click **`demarrer.bat`**, or run `python app/server.py`.
5. In the local browser, authorise Anytype (four-digit code in its window), then select the source and destination.
6. Run **Test** for a scope simulation, then **Import** for the real writes (additional confirmation).

To explore the interface without the applications open: `demo.bat` or `python app/server.py --demo`. The import button **stays disabled in demonstration mode**.

No additional Python dependency is mandatory. The web application is limited to `127.0.0.1`, on a port starting from `8766`. Leave the console window open while using it.

**Connection**: Anytype normally listens on `31009` with an API key obtained by pairing. Anytwo is detected automatically (`31310`, `7001`, `2657`, `5344`, then listening ports of `any.exe` on Windows), or through the “API” status button. Ports are remembered in `%APPDATA%\anytype-anytwo-importer\settings.json`. The Anytype key is protected by Windows DPAPI (user file permissions on macOS/Linux).

## What the import does

- Traverses the source space, its collection or the chosen types/objects. With “Also import linked items”, adds the referenced objects found in that space and records the **reason for their inclusion**.
- Recreates the chosen Anytype collections; an additional collection per **type** is created when there are properties to preserve (including type columns without a value). Mappings to existing Anytwo collections are respected according to the interface choices.
- Creates pages **before** rebuilding links, so references can be rewritten to their new Anytwo identifiers.
- Attempts to transfer properties (`text`, `number`, `boolean`, `dates`, `select`, `multi-select`, `relations`) and options. Fields without a certain mapping are converted to text **with a warning**.
- Transcribes AnyBlock v2 blocks into Anytwo Markdown: headings, paragraphs, emphasis, lists, checked boxes, quotes, simplified callouts, code, links, files and media. Columns, rich tables, image dimensions and YouTube videos: attempted rendering through HTML embedded in Markdown, with a fallback to simplified content if rejected (Anytwo rendering must be checked). Unknown blocks include their original JSON to avoid silent disappearance.
- Transfers binary files through the APIs if the option is checked; a cover image may be added at the start of the page, but is **not** reproduced as the original banner. Emoji icons are attempted as object metadata (field under validation): they are no longer added to the page body.
- Inserts a **warning into the Anytwo page** when major blocks/content cannot be mapped: embedded collection or view, unknown block, missing file, unrebuilt link, etc. Purely cosmetic presentation losses remain in the report.
- Displays a report with each object, the reasons (manual selection, collection membership, linked object), adaptations and errors; groups incompatibility categories. Allows **JSON export**.
- Saves reports in `%APPDATA%\anytype-anytwo-importer\reports\` (Windows), even after an interruption when the operation could be tracked.

## v0.6 changes

- The “API” button is the single access to settings: gear removed.
- Objects identified as **chats or discussions** are excluded from selection and migration (including through links). Messages/discussions are not imported.
- Internal Anytype fields such as `resolved_layout`, `Origin`, `created_in_context` and `created_in_context_ref` are filtered before creating columns and writing values. Do not arbitrarily reject all properties with an unknown format: they may be custom.
- Complete bookmarks are turned into a **clickable link carrying their title**; their enriched metadata is no longer reproduced. Bookmark blocks inside pages follow the same rule.
- Columns, tables and image widths have a structured HTML path (less destructive than the previous flattening); cell colours are not reproduced. This path is **not yet a guarantee of native Anytwo block creation**.
- Valid YouTube videos are represented by an HTML embed rather than a simple link, subject to Anytwo rendering. The source emoji is sent at object creation and never artificially inserted into the content.
- If rich Markdown is refused, a simpler fallback is attempted; the report signals the presentation loss. The import remains non-destructive on the Anytype side.

## v0.7 changes — after the first real test

- **List refresh**: “↻ Refresh” button near the source space. Reloads Anytype/Anytwo spaces, Anytype objects and types and the destination space collections. The selection and destinations are preserved when the objects still exist.
- **After each import**: automatic list reload. The import records the ID of the created space and collections in the report, so the target configuration reuses the **right identifiers**, not just identical names.
- **Tables inside columns**: fixed an omission in the nested traversal; the HTML column structure now contains the real `<table>` elements of nested cells, with their data. Final rendering still depends on the Anytwo parser/editor, to be checked on a test page.
- **Embedded bookmarks**: lookup of the label in the block, then in the name of the referenced bookmark object, reading its metadata through the local Anytype API as a last resort. The link carries that title when the source provides it.
- **YouTube**: Anytwo Markdown rendered the `<iframe>` code as text. The converter now separates it from Markdown and attempts a native editor **`html` block** at the right location, before continuing the page. If the API refuses this block, it inserts a clickable link. The client may nevertheless display the HTML differently: **embedded video playback is not yet validated on the real client**.
- No change to import modes: the simple import creates new copies. Test writes nothing into Anytwo.

## v0.8 changes — CSV file recognition

- **CSV**: the import now explicitly sends `Content-Type: text/csv` for a file whose name ends with `.csv`, even if Anytype announced `application/octet-stream`, `text/plain` or `application/vnd.ms-excel`.
- **Original name preserved**: attachments from an Anytype property could be sent under an artificial name (for example `Documents-<id>`), which prevented Anytwo from identifying their extension. The importer now tries to find the real name in the inventory or in the Anytype file object metadata.
- **Other formats preserved**: for `.bat`, `.xls`, `.ics`, `.log` and other extensions, a specific MIME provided by Anytype is kept. The script only completes generic types when it has a reliable extension.
- **CSV check after upload**: when the installed Anytwo version API allows it, the script reads back the imported CSV file record (`GET /v1/spaces/:spaceId/files/:fileId`). If the recorded MIME differs from `text/csv`, the problem appears in the object report. If this route is absent, the transfer is not marked as an error.
- **Limit**: these fixes apply to new imports. They do not modify previously imported files. Rendering and preview in the Anytwo client still have to be confirmed by a real test. The simple import creates new objects; do not rerun an import into the same space without accounting for duplicates.

## Limits and precautions

- **No synchronization, automatic resume, duplicate resolution or rollback.** Simple import = a new copy on every run.
- Imports are limited to **500 objects** and **100 MiB per file** to prevent scope errors and excessive transfers (limits configurable in the code). The preparation reads documents before the first creation but cannot anticipate every write error.
- Anytype collections and types are not equivalent to Anytwo ones: types are **converted to collections** when needed, dynamic view settings and filters remain unreproduced.
- There are significant gaps for background colours, templates, global/local properties, table of contents, enriched bookmarks, queries/views, advanced filters, embedded collections, properties embedded in pages and discussions. The list shown by **See more** is not exhaustive.
- Blocks are mapped as best as possible, but **the exact layout and media rendering are not guaranteed** (columns / tables / media with HTML to check, non-collapsible toggles). Some relation attributes and system metadata cannot be retrieved.
- Original files must be available through the local Anytype API; the presence of a reference does not guarantee their download.
- An unreadable source object, a refused property or an interrupted API may create a **partial import**. Check the report **before any new import** to avoid duplicates.
- The import mode does not modify the source, but Anytype API keys grant access to approved spaces: keep your user account configuration files safe.

## Tests performed

- `python -m unittest discover -s tests -v`: **45 tests** (including an HTTP integration test against **two simulated local servers** with block, property and binary transfer writes; nine tests specific to file and CSV metadata).
- `node --check static/app.js`, `node --check static/i18n.js` and `node --check static/pair.js`: JavaScript syntax validation.
- Automated Chromium interface test: check of the dialog, selections, destinations and simulation mode.

**What remains to validate with your two applications**: HTML rendering of rich columns and tables (no guarantee of conversion to native blocks), icon emoji (`iconEmoji` is attempted but not confirmed by the documentation), YouTube iframe rendering through a native HTML block, image dimensions, and real column schemas, type and collection loading, space and collection creation, image rendering through `any://f` URIs, `any://o` link rendering, and migration of large collections. Some endpoints may have changed since the documentation.

## Sources

- Anytype v2 API: https://developers.anytype.io/docs/reference/v2/anytype-api/
- AnyBlock JSON 2.0: https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md
- Anytwo / any v1 API: https://docs.any.org/reference/http-api.html
- Anytwo Markdown: https://docs.any.org/database/markdown-import-export.html

## Organization

- `server.py`: local web server and configuration, simulation, import, report saving.
- `api_clients.py`: API clients, port detection, HTTP read/write, binary transfers.
- `logic.py`: inventory, groups and simulation.
- `migration.py`: reference discovery, mappings, conversion and report.
- `static/`: web interface without a JavaScript framework.
- `tests/`: processing and simulated HTTP call tests.

## v0.9 changes — identity and languages

- Project renamed **Any2Any**. The sources and destinations remain Anytype and Anytwo.
- Public documentation in French and English; strengthened warning about the experimental nature of alpha versions.
- FR / EN / DE language selector for interface labels and the pairing window, with local persistence. User data and technical API messages are not translated.
- No change to the import engine since v0.8.

**v0.9 translation check:** the FR / EN / DE displays of both pages were tested with Chromium offline; the environment's network restrictions prevented a complete browser scenario against the local server.

## v0.9.1 changes — preview without APIs

- The connection screen becomes **closable with an X as soon as the checks are finished**, even when Anytype or Anytwo is unavailable. It remains closed until the user clicks the API status indicator.
- On failure, the top-right indicator is **red with a warning symbol** and the page shows a banner explaining the view-only mode. The FR/EN/DE selector and compatibility information remain available.
- No data test or import can be triggered when both APIs are not accessible; workspace controls become inactive.
- When the APIs become accessible again through “Save and check”, the interface loads the data and re-enables migration functions.
- The migration engine is not modified. The client HTTP identifier was updated from `Anytype-Anytwo-Importer/0.8` to `Any2Any/0.9.1`.


## Conversion fidelity after the first publication

The pass on views, filters, properties, columns and media is described in [Import fidelity](IMPORT-FIDELITE.en.md). It details the effective conversions, the settings that are only archived and the rendering still to be verified. These changes are not part of the first published release.
