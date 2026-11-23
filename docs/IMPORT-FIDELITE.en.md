# Import fidelity — 29 October 2026

**[Français](IMPORT-FIDELITE.fr.md) · [English](IMPORT-FIDELITE.en.md)**

This pass improves Anytype → Anytwo import fidelity. The READMEs do not contain a version number.

## Properties

- Preservation of unused options, names, colours and their declared order; additional reading of the Anytype tag list when the vocabulary is not included in the v2 metadata.
- Property resolution by identifier, name and `property_internal_keys` caption; type schema preserved even for columns without a value.
- Property description sent as the native description. Date with time and simple relation cardinality mapped when declared. Relation restrictions remapped to the collections matching the imported types when all are available.
- Settings without a safe equivalent (read-only, default value, numeric cardinality limit) kept in `xFormat.any2any.sourceSettings` metadata and reported as not applied. Archiving them does not recreate their behaviour.
- An existing property is not silently reconfigured: parameter or colour differences are reported. Missing options are added with their colours when available.
- Relation properties use the API form `any://<objectId>`, while page content keeps its navigation links with space.

## Views

Properties and their values are transferred before view conversion. Views of selected collections and page `dataview` blocks are examined. A native `dataview` object is attached to the target page or collection and receives `dataviews` and `views` records through `/modify`. Partial rejections are treated as failures.

Collection sources are limited to the identifiers actually imported, without widening to other destination data. Type sources use the type collections; property sources keep a presence condition. An explicitly empty source stays empty. Views sharing a page use the same host object with distinct table and view identifiers.

Supported filters: nested AND/OR groups, simple scalar comparisons, `in`/`not_in`/`all_in` lists, presence. Property, option and relation identifiers are remapped. Ascending/descending sorts and grouping are mapped when the property has a single destination. An unknown filter, a relative date, a comparison whose empty rules differ, or a custom or ambiguous sort makes the entire view refused: no filter is simply removed.

Source definitions of all views are kept in the JSON report (`views`). Property visibility and order are applied to native collection views through `layoutSettings.visible`, `hidden` and `order`. Widths, cards, aggregations and manual document order remain archived in `layoutSettings.any2any.sourceView` when their application is not verified. Table/list/board/gallery layouts are sent as hints to the client, with no rendering guarantee.

**Since 0.9.3:** view blocks inside pages now use the native `any:block` envelope, `kind: inline-view`. Its `instance` matches the `dataviews` table, and its main configuration is stored under `<instance>.list`, with `query.anyUi.source`, `filters` and `sort`. The client rebuilds its query from these settings: saving only `query.filter` is not enough.

Inline views now reuse their real source collection or the collection representing their source type. They no longer create a technical “Vue · …” supertag per block. Several views of the same collection share the same source but keep their distinct view, filter and sort records. If the properties already belong to this source, they are reused; otherwise the necessary fields are copied into it. These copies are not synchronized with a same-named property in another collection.

The current client offers only one type/collection source per Inline view block. A composed source that cannot be expressed by this model is explicitly refused, without inventing a technical collection. A pre-existing target collection containing documents outside the source scope is also refused for this view, so its results are not silently widened. Technical supertags from previous attempts are not removed automatically.

The linked-items option also explores inline view documents, respecting evaluable filters, recursively and without duplicates. It can follow a query by type, notably a query on collections: the displayed collections are then represented by pages containing their own views. Unchecked, the option adds no view documents; the view remains limited to the chosen scope, with a warning if necessary. The simulation shows the same widening.

Client inline views display the list and gallery layouts. A source table is adapted to a list with a warning; a grouping or filter that cannot be converted is explicitly refused. The active view (or the first view when unspecified) is never silently replaced by a less-filtered view. Secondary views are kept as saved views, without claiming the block offers their selector.

The demonstration page provided by the owner confirmed the native format. The installed client's parser and query builder recognized the emitted block, numeric filter and sort, as well as date, boolean, select and relation filters. ANY/ALL relation logic is translated explicitly to avoid unintentional restriction or widening. Empty filters that the client would ignore are refused. The full suite of 99 automated tests passes. A test on the actually reported source, with all target writes simulated in memory, converted the two failed page views. No new Anytwo user object was created during these checks.

## Columns and tables

- Recursive traversal of nested rows and columns, without duplicating inner columns.
- Images and attachments inside columns transferred by the same mechanism as main block files; explicit failures.
- Code preserved without interpreting it as formatting; object links rewritten inside cells, including cells composed of several blocks.
- Unknown blocks preserved with their JSON instead of being removed when they have no text.

The layout now uses the native `any:columns` / `any:column` markers, with source widths and nested content. The installed client's parser rebuilds them as real columns. A malformed layout keeps its content in sequence with a warning.

## Verified references

- https://docs.any.org/types/index.html — view objects, datasets, host.
- https://docs.any.org/types/editor.html — blocks, parents, styles; boundary between storage and rendering.
- https://docs.any.org/database/reading-data.html — target filters and sorts.
- https://github.com/anyproto/any/blob/main/docs/27-descriptors.md — property settings and extension namespaces.
- https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md — Anytype filters, sources, properties and columns.
- https://developers.anytype.io/docs/reference/2025-11-08/list-tags — reading the choice vocabulary.

The view and write schemas were also read on the installed API (any v0.3.4). No user data was imported or modified during the research. Automated checks use simulated APIs.


## Formatting, media and icons

Isolated verification with the installed client's real parser (build `7a477ecc`, server any v0.3.4), without accessing its data or remote media:

- Toggles: `any:collapsible` markers, with titles and nested content. The parser produces `collapsible-container`, `collapsible-title` and `collapsible-content`.
- YouTube: native `any:block` envelope, `embed` type, provider `youtube`. The parser produces `extension-block`, without displaying iframe code.
- Audio: native file link `any://f/…` with the real name and extension. The parser produces `file-link`; the client selects its audio player by extension.
- Tables: HTML lists of the checklist type, recognized as checkable boxes with their state. HTML underline is kept inside cells, whose import uses the DOM.
- Files: name and extension looked up in the source metadata, then reused in the upload and the document.
- Icons: universal `any.icon` property for emoji; uploaded file and same property for image icons.

**Underline limit outside tables:** this client's Markdown parser has no transformer for `<u>`, even though the text engine can represent the style. The migrator keeps the text without the visible tags and reports the loss. Superscripts and subscripts follow the same rule. Tags inside code remain literal. Text and background colours remain limited by Anytwo.

Automated tests cover the emitted formats and simulated transfers. The project owner then verified the reported fixes in Anytwo. The limits described here, notably underline outside tables and view rendering, still apply.

The reference page created by the user, “Demo pour import” in “Test space”, was then consulted read-only. Its Markdown confirms the toggle markers, native audio links and YouTube envelope used here, as well as both checklist states in the tables.


## Files and images — fix of 30 October 2026

- Original names are resolved before transfer, even when the block already provides an extension. The technical pattern of 32 hexadecimal characters followed by a readable name is removed from metadata originating from an import/clipboard. Names consisting only of a hash are kept. The declared extension is still appended to names already containing dots, notably timestamped audio/video records.
- Regular images use native Markdown `![name](any://f/space/file)`, with the same escaping as the client. Pixel widths use the native `any:image-width` comment. Anytype width percentages have no exact native equivalent: they are approximated in pixels on a 720 px reference block, with a warning in the report.
- The target space library is read once per import. An existing file is reused only if the normalized name, size and SHA-256 of the bytes match; the name alone is not enough. Variants/thumbnails are excluded. If the content cannot be verified, a normal transfer is used.
- The same Anytype file referenced from several pages uses the same Anytwo file, while remaining an embedded image at each location. Caches are separated by target space. Transfers and reuses appear in the report's `file_transfers`.
- The two images reported in “Cobaye1” were found by content with their existing identifiers, without uploading or modifying a page. The client's real code recognized names with spaces, underscores, brackets and ampersands as native images.

These fixes apply to future imports. Reusing an old prefixed file does not rename its library record; the new location uses a cleaned label. Pages and files already created by previous attempts are neither rewritten nor removed automatically.

### Spacing, sizes and collection properties

Empty paragraphs are kept as paragraphs containing a zero-width character, to avoid being merged by Markdown. Anytype relative widths are approximated in pixels on a 720 px reference block width, then limited to the native minimum of 96 px; the report signals this approximation. The rendering will therefore not be proportional to each window width.

Select options and colours are read through `/v2/spaces/:space_id/properties/:key/options`. Document properties are also available in their source collection, including when hidden in the view. Dates with time remain datetime to preserve sorts; visible view properties remain distinct from the columns present in the collection. These fixes concern future imports and do not automatically repair already-created copies.

### Chat archives (option)

Chats remain excluded from ordinary pages and types. The “Import chats as archives” option, disabled by default, archives all chats exposed by `/v2/spaces/:space_id/chats` for the source space, even with a partial page selection. It does not separately discover object discussions absent from that list.

One page per chat, grouped by day, from oldest to newest: quotes with author/date headers (explicit time zone), replies, edits, reactions and separators between messages. Images are embedded and other files linked if file retrieval is enabled. Links to already imported objects are rebuilt; others are reported. No publish call is made into Anytwo chats. Reactions remain archive annotations. No unverified callout frame or colour is invented.

Reading follows `next_before`, without `offset`. Incomplete, inconsistent histories or repeated cursors stop the process before any target write. The simulation announces the additional pages without writing or downloading files. The JSON report contains the source messages and their identifiers, notably those of the authors, to preserve metadata and enable future presentation improvements.

### Property identity, palette and nested collections

A global Anytype property can be written into several target supertags when objects have different types. These locations do not define different source properties: in a collection or inline view, their values are merged into a single column bearing the source name. Select values are translated by label when target keys differ. A contradiction between values or between same-named source identities causes an explicit report; no technical suffix is invented. Property references belonging only to types outside the scope are ignored.

The source green `lime` is translated to `green`, recognized by the Anytwo client; the client's palette includes `green` but not `lime`. The value `gray` is normalized to `grey`.

Importing a space also preserves collections as navigation pages with their inline views. Memberships in parent collections use the source document's `collection_items` identifiers, even if the endpoint listing members omits nested collections. A collection membership does not automatically mean that every page displaying that collection in an inline view belongs to the same parent.

### Properties owned by collections and native view

Members of an imported collection receive its equivalent supertag and their properties are written directly into it. An object member of several collections keeps these memberships; the required properties are available in each. The source type supertag serves as a fallback for objects outside imported collections, or as an explicitly chosen destination for a type import. “Page” is no longer automatically added to collection members. Accounting fields therefore no longer appear in the fallback supertag of pages that only have a Tag.

A collection uses the native `dataviews/default` table and its first `views/default` view (the following ones remain in the same table). Visible and hidden properties and their order are applied; sorts are in `query.sort` and in `query.anyUi.sort`. Source dates are kept in a collection property, distinct from the creation date of the imported copy. The Tag can be defined and filled while being hidden in this view. The existing view host is reused when importing into an existing collection. Widths remain local to the client and are archived with a warning.

## Anytype mentions — fix of 23 November 2026

- Inline `@` mentions exported by Anytype as `<mention object_id="…">Name</mention>` are converted to native object links `[Name](any://o/<space>/<object>)`, like Markdown links `anytype://object?objectId=…`. They are supported in paragraphs, headings, lists, quotes, columns, tables, compound table cells and the description prefix.
- Mention targets are recognized by link discovery: they are imported automatically when the “Also import linked items” option is enabled. With the option disabled, the mention remains the display name as plain text and an explicit warning appears in the report.
- A mention whose object is not in the imported scope keeps its label, without visible tag, and produces the warning “Mention vers un objet non importé”.
- The label uses the mention text, then the known object name, then the identifier. HTML entities in the label are decoded.
- These fixes apply to future imports; already copied pages are not repaired automatically.
