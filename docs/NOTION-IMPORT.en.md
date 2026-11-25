# Notion to Anytwo conversion contract

**[Français](NOTION-IMPORT.fr.md) · [English](NOTION-IMPORT.en.md)**

## Selection and reading

The navigation offers three levels: root (0), level 1, level 2. Databases and data sources count as structural levels. Deeper items are neither displayed nor preloaded by navigation, even if the initial search has already listed them. The root of an item whose parent is inaccessible is still shown in the separation of other accessible items.

Selecting a branch includes all its accessible descendants, without a selection depth limit. Compatibility analysis continues to read these descendants: the navigation limit speeds up the preparation of the choice, not a complete content analysis. Volume limits and cancellation remain applicable. The initial inventory always uses Notion search and parent reconstruction; this limit does not remove these requests.

## Destination

After Verify Anytwo, the space bearing exactly the Notion workspace name is proposed if it is unique. Otherwise, creating a space with that name is proposed; the name is editable. Several same-named spaces require an explicit choice. The user can choose another existing space. No space is created during this configuration.

An ordinary page becomes a page, without a generic “Page” supertag carrying the properties of unrelated databases. Each data source becomes a collection with its supertag, its properties and its options/colours; the definition is also created for an empty database. All its members receive this supertag. A Notion database with several sources produces several collections to respect the distinct schemas. For a single source, reuse the database name; for several, distinguish the collections by the source names, keeping the source identifiers to avoid collisions.

Even for a single selected database, create a collection and its supertag: do not offer to merge the members into an existing collection whose schema could be incompatible. A new import must not reuse a collection based only on its name; a future recovery will require a source/target identifier match.

A database embedded in a page provides its collections and members, then an inline view at the source block location. Filters, sorts and visible properties are remapped. A view does not create a new collection at every occurrence. A condition that cannot be translated must be reported, without discreetly replacing the view with an unfiltered view.

## Converter operation order

1. Resolve or create the space and record identifier mappings.
2. Create the collections/supertags and the simple properties/options, including for empty sources.
3. Create the pages and members with their membership; import simple values and files deduplicated by identity/content, not by name alone.
4. Remap relation properties and their values; create rollups with the target identifiers and verify compatible aggregations.
5. Convert blocks, internal links and inline views after the identifiers are available. Keep empty blocks and embedded media.
6. Produce a report of adaptations, losses, out-of-scope references and archived settings.

Writes go through anytwo_backend.py, the common engine; no Anytwo HTTP writes in the Notion reader. The Import button launches the converter as a background task, with the same destination lock as Anytype imports. Demo mode refuses any real write.

## Compatibility

The visible frame before analysis presents the general limits. The detailed report counts separately the blocks, properties and views actually detected. Table, list, grouped table and gallery are adaptation candidates, not a guarantee of validated conversion. Calendar still has to be verified. Charts/statistics, cards, timeline/chronology, forms and dashboards are not visually reproduced at this stage; keep their data and archive their definitions. A journal built with pages and dates remains importable as such; do not confuse this data with a chronological layout.

The Notion “Known migration limits” window presents the following adaptations:

- Views: chart, feed, card and timeline formats not reproduced; calendar to study. Conditional colours, sub-items and automations not reproduced.
- Properties: frozen formulas without recalculation; buttons not reproduced; rich text adapted to plain text; files and media kept as links to the retrieved attachments.
- Pages: visual link previews, buttons, breadcrumbs and tabs not reproduced; block columns beyond four to adapt; reminder dates not kept; cover adapted to an image in the content; text/background colours and underline not kept.
- History not imported. Imports to study: wikis and calendars.

Relations, compatible rollups and native Anytwo synced blocks are supported and no longer appear as general limitations. Each import report keeps precise warnings when a particular configuration cannot be reproduced.

References: https://developers.notion.com/reference/create-view and docs/ANYTWO-RELATIONS-ROLLUPS.en.md.

## First operational version

The reader finishes reading paginated properties (titles, texts, people, relations, formulas and rollups) before creating the destination. Conversion preserves numeric types, booleans, dates, choices and colours, internal references and collection membership. Media is downloaded without transmitting the token to its host, with a 100 MB per-file cap; private network addresses and redirects to these addresses are refused. Files are reused by name and content, not by name alone. Images, audio players and YouTube videos use the native dialect already used by the Anytype importer. Image captions use the image-caption extension and remain attached to the image; the target caption text is plain text.

Empty blocks, lists, boxes, headings, toggles, columns, tables, code and equations are converted. Callouts use the native any:callout envelope, with their frame, icon and nested content. Underline and text/background colours remain reported as lost. The table of contents is rebuilt as a list of links to the real identifiers of heading blocks; it remains static. Synced blocks become native Anytwo originals and references, shared between imported occurrences; they do not remain synchronized with Notion. If the Notion original is outside the selection, its first selected occurrence becomes the Anytwo original. Links to child pages are kept at their source location. No artificial link to the parent page is added; Notion favourites and sidebar are not rebuilt.

Collection views are saved with their compatible filters, sorts and visible properties. The target client currently limits inline layouts: table and table are adapted to a list with a warning, gallery kept. A filter that cannot be translated prevents the creation of this view; a link to the collection is presented in its place. Original settings are kept in the report. Links between databases are remapped to the collection if the source is unique; an ambiguous reference to a multi-source database remains reported.

Formulas are typed frozen results, with archived expression. Sum and original-value rollups are configured natively if their relation and target property are available; otherwise result and definition are archived in frozen form. Configuration persistence is verified by API, but visual recalculation in the client is not automatically validated. Currency formats (including EUR), percentages and numeric separators are translated into native descriptors without changing values. Date ranges and time zones, status groups and rich property texts still require a reported adaptation. File properties become links to the retrieved attachments.

Each creation is followed by a checkpoint in the active profile, under reports/notion-<id>.json (APPDATA/any2any for the common version); the report contains the source/target identifiers, property/view definitions and reported losses, without an API token. Do not distribute these reports without checking the personal data they contain. Cancellation keeps the objects already created and makes the report available. The Import button launches a new import, without update or automatic recovery; rerunning creates additional copies. Repeated POSTs with the same request_id do not launch a second job in the same session.

## Real verification

The “Modèle de test — Any2Any” fixture from Sri / Test pour Anytwo was imported into the space “Test import Notion — Any2Any 2026-10-31 19-49-19”: 7 pages, 2 collections and 4 distinct files. Read-back of bodies (toggles, media and inline views), properties, dates, numeric/boolean values and relations succeeded. No source content was modified. The first attempt revealed null view sorts; after the fix, the same space was resumed without recreating pages or properties, and files were reused. The expected adaptations are listed in the private report.

The tools/import_notion_fixture.py utility is limited to this fixture and requires --apply to write. Without this flag it only performs the pre-read; --resume reuses the local report of this technical test. This explicit resume is not yet offered by the general import interface.

## Client format verification

After user feedback on the imported fixture, the real converter of the installed desktop client was executed in an isolated DOM, without network and without launching the application. The libraries were read from the installed executable (Brotli assets LexicalMarkdownEditor-hfMXhO7O.js, useSpellingHighlights-PDgIE7KF.js and format-z9cldY3U.js); no modification to the installation. Analysis copies and results remain in reports/client-inspection, outside Git.

The bold/italic/strikethrough defect came from spaces included in source annotations: **Bold ** is not a valid marker for this client. Spaces are now moved outside the delimiters. The real read-back of the fixed fixture confirms the bold/italic/strikethrough format bits, a callout node, two canonical image-caption extensions, the synchronized original and its reference to the real API block, as well as the table-of-contents links.

Underline remains unavailable through the current Markdown bridge: the test also shows that an HTML paragraph with a u tag is kept as literal text, without underline. Do not work around this with fake Unicode text or an artificial table. This loss remains reported. View support objects are unnamed, like native supports; their data remains present, but they are no longer presented as “Vues Anytype” pages.

Synchronization and table-of-contents references are finalized after body creation, through PATCH of the blocks; do not perform a global PUT afterwards, at the risk of changing the targeted identifiers. Identifiers of blocks created in bulk contain “:”; this version of the PATCH route requires this legal segment character to remain unencoded, otherwise it responds blocks.not_found.

The fixture page of the provided test space was fixed in place, with a prior backup of the Markdown and technical supports in reports/before-notion-native-repair-*.json. No additional page, collection or attachment created, no Notion content modified. tools/repair_notion_fixture.py limits this operation to the fixture and this precise space, with an explicit --apply.

## Relations, rollups and numbers

Collections are all created before their properties. A relation to a Notion source is restricted to the target supertag through xFormat.relation.targetTypes: this list contains the xKey handle of the collection, not its identifier or name. Identifiers remain used for the property owner and for value references. If only the collection carrying the relation is selected, the accessible target schemas are read and created without retrieving their members; the links option still controls adding pages outside the selection. An inaccessible or ambiguous target gives a text property with archived references and a warning, rather than a falsely unrestricted relation.

Rollup selectors only offer relations with resolved targets. The target title is identified by ownerId = target collection identifier and propertyId = any.name. This pair must also be used for the choice displayed in the editor; any / name does not match the native choice. Notion property identifiers are compared after decoding their URL escaping, with identity taking priority over an old name.

Numeric properties keep the number kind. The descriptor becomes currency with config.currency = EUR for euro, percent for percent, or number with config.separators = true for number_with_commas. Other known currencies are translated to their ISO code; unknown formats remain archived and reported. Values are neither converted into another currency nor multiplied for a percentage. Filters and sorts of these properties remain numeric.

On 1 November 2026, the new import of the fixture into Sri was fixed in place: restriction of Projet toward Projets de test, EUR formats of Budget and Prix, configurations of Noms liés and Budget lié, and removal of the two parent links generated in the fixture and its sub-page. Properties manually added by the user remained intact. Private backup before modification and verification that the values of all imported properties are unchanged. No global page rewrite: only the artificial link blocks were removed, preserving the identifiers used by tables of contents and synced blocks.

The installed client's choice and calculation functions were executed in the isolated DOM on the definitions actually read back after the fix: Projet is offered with a single target supertag, the Name and Budget properties are recognized, project names are calculated and the sums are 100, 180 and 0; numeric display is currency / EUR. Results remain in reports/client-inspection/property-check-results.json. The tools/repair_notion_properties.py utility requires --space-id and --apply to write; it is limited to the fixture import identified by its report, backs up definitions and removes only recognizable parent links generated by the importer.


## Read reduction and recovery (1 November 2026)

Short titles/texts, small people lists, explicitly complete relations and numeric/date results already provided by Notion are no longer systematically re-read property by property. Potentially truncated lists, relations without proof of completeness and complex calculations are still re-read with pagination. Additional property reads use four workers, under the existing global rate cap.

Unchecked branches are discarded before their traversal, without querying their databases or reading their pages to remove them afterwards. An explicit inclusion under an excluded branch keeps its priority. Target schema metadata needed for relations is still retrieved without their members.

Navigation, analysis and import share an in-memory cache of at most 32 MB, renewed at the latest after 30 minutes. “Refresh” and a new connection invalidate reads. After an interruption during reading, relaunching the same selection with the same options and destination within 30 minutes reuses its cache, without closing the application. This mechanism reuses reads kept in memory; it is not an automatic write recovery or synchronization. If objects have already been created, the message reports it and asks to check the report before rerunning to avoid duplicates.

Tracking shows the phase, pages/blocks found, requests by category and reused reads. Network attempts, including retries after throttling, are counted. Metrics accompany the saved import reports. Budget or request expiry is no longer presented as a lack of Internet connection. The global read limit remains fifteen minutes per run; the intended gain is fewer calls, not a blind increase in throughput.

### Space image

The Anytwo client accepts a space image: public upload without token, attachment to the index object of the created space, then PATCH iconCid with the any://f URI of this file, like its native selector. The space is saved before this optional operation; an image failure does not block the pages. An existing space keeps its icon.

The current connection uses a Notion internal token. GET /users/me exposes the space name, but its documentation does not provide its image. avatar_url designates the integration, not the space: it is never reused in its place. The importer can transmit workspace_icon if the connection metadata provides it; otherwise it explicitly reports unavailability and keeps the default icon. Automatic image retrieval with the current token therefore remains unavailable, and is not presented as validated.


## Linked views, callouts and icons (1 November 2026)

A child_database is not always an owning database: the inspected linked views have an empty data_sources, but each view provides its data_source_id. The importer resolves this schema and uses the views specific to the location, without creating a supertag for the view container. If the database is outside the tree, its members are only added with the linked-items option; its schema remains necessary for the view. Databases with is_inline=false become links to their collection; they are no longer replaced by a view that the client moves outside the callout.

Properties removed from the schema but still referenced in a view presentation are ignored with a warning. A filter or sort targeting a missing property remains blocking for this view. Non-empty quick_filters are combined with the main filter; multiple selections remain flat lists. A grouped view can be adapted to a list, with a warning, while keeping its filter and sort. A non-convertible collection view no longer makes the other compatible views disappear.

Callouts without their own text start directly with their child blocks, without generated empty paragraphs. Empty paragraphs actually present in the source remain preserved. Page and collection icons use the native icon:v2 format; composed emoji (for example the cook) remain a single grapheme. Collection images are transferred when files are enabled. Known named Notion icons have a deterministic mapping table to emoji; no image recognition or AI call. Property and view icons are transmitted when their metadata is provided by the API; the current API may omit this information.

Read-only verification on the reported Gastronomie pages, then offline replay with all writes simulated: a Cave link in the callout, an inline view in Recettes and Idées repas, three in the cellar dashboard and Le bar, seven saved views for Base recettes with their quick filters. The installed client's converter confirms three callouts without an initial empty paragraph, the Cave object link in its callout and the cook as a single native grapheme. This does not replace visual verification of the next import. No new import and no in-place fix of Sri were launched.


## Collection groupings, two-way relations and averages (1 November 2026)

Collection groupings are no longer flattened like inline view ones. Table/list/gallery views use query.groupBy = {propId: …} and query.anyUi.group; Kanban uses layoutSettings.boardColumns. Property identifiers are remapped, with group order and hideEmpty. Inline views keep their reported adaptation to a list when the client does not offer this presentation.

Notion text filters “contains / does not contain” are converted to case-insensitive literal regular expressions and native client conditions. This conversion is Notion-specific; the collation reservations of the Anytype import are unchanged. Newly created Notion collections are targeted by their native membership, without injecting a list of hundreds of identifiers into the displayed filter. A Notion view without a meaningful name receives a label from its format: notably Tableau Kanban instead of Untitled. Non-importable formats, including chart, remain excluded and reported.

dual_property relations are paired after creating all properties, with xFormat.anyui.inverseOwner and inverseProperty on each side. Escaped Notion identifiers are decoded to find the inverse property. No duplicate inverse property is invented; a missing or inconsistent reference is reported. These settings enable Two-way mode in the client, independently of the imported relation values.

Rollups now support average, as well as min/max/median/range and compatible counts, in addition to sum and original. An average is a native object/rollup property with its remapped relation and target property identifiers; the source JSON result is not written as a text value. References specific to each object limit the calculation to the objects actually linked.

Validation on the user report: 12 Cave views kept out of 13, chart excluded; LPB and Kanban present, group settings recognized by the client parser. LPB query executed read-only: six results in Notion and six in Anytwo. The client's real functions recognize both paired directions and reproduce 53 numeric averages from the source report, including 11.5. Suite: 252 Python tests and eight frontend scenarios. No real import or modification of the existing space.


## Gallery presentation and page opening

The cover_aspect=contain setting becomes layoutSettings.galleryFitImage=true; cover becomes false. This setting is kept in collection and inline views. The target mode is side-peek by default, including when the Notion API omits its opening mode; only explicit full-page metadata gives full-screen. No alternative central mode is created. The applied settings remain those stored by the Anytwo client (openMode and galleryFitImage).
