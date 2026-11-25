# Anytype import fidelity

**[Français](IMPORT-FIDELITE.fr.md) · [English](IMPORT-FIDELITE.en.md)**

This document describes the current behaviour of the converter. The [Anytype usage guide](NOTES-TECHNIQUES.en.md) covers selection and access. The [changelog](../CHANGELOG.md) keeps the history of changes.

## Properties and collections

Members of a source collection receive the target collection's supertag. Properties are written into that collection. A type supertag is a fallback for objects outside a collection when their properties need one. A source-global property can be carried by several target collections without becoming several source identities.

Columns declared without values are created. Choice options use the source vocabulary's labels and colours. `lime` is normalised to `green` and `gray` to `grey`. When a target column already exists, differences in settings or colours are reported. Missing options can be added.

Compatible settings, notably time presence and choice options, are transferred. Settings that cannot be applied are archived in `xFormat.any2any.sourceSettings` with a warning. Relation restrictions are applied only when their target types are resolved.

A date with time is stored in a datetime descriptor even when the source declares a plain date. This choice is made before values are written and preserves sorting. Source system dates needed by views are kept in columns separate from the destination's new creation dates.

File/image properties never become text columns. When retrieval is enabled, their content is added at the top of the page under the property label. Images use their inline rendering and other files an attachment link. This adaptation appears in the report.

Anytype's internal bookkeeping (`source_object`, `template_name_prefill_type` and the other system fields of the internal list) is never imported as a column. These keys are matched by identifier, never by label or prefix: a user property named `template_notes` whose key is a generated identifier is still imported. A template setting that cannot be translated is reported.

## Links and files

Collection links target the Anytwo collections directly. Collections are not duplicated as navigation pages. Mentions become inline links to the imported objects. Internal link rewriting removes the parameters and escapes of the original Anytype address.

Files linked as source objects are recognised, including PDFs. The name and extension are looked up in the metadata before transfer. The technical import prefix is removed when it is identifiable and followed by a readable name. Names made only of a hash are kept. The CSV MIME type is explicitly sent as `text/csv`.

The target file library is read once per import. Reusing an existing file checks the normalised name, the size and the SHA-256 of the bytes. Variants and thumbnails are excluded. One source file referenced by several pages reuses the same transfer in that space. The report details transfers and reuse.

Images use native Markdown and their pixel widths use the `any:image-width` marker. Relative widths are approximated against a 720 px reference, with the native 96 px minimum and a warning. The result is not proportional to every window width.

## Views

Selected collections and those referenced by views are resolved before pages are created. An archived source collection referenced by a view can receive its own compatible views. Collection configurations are stored in the native `dataviews` and `views` datasets, with the `default` table and its ordered views.

Nested AND/OR filters, simple comparisons, single-select comparisons, compatible empty conditions, `in`/`not_in`/`all_in` lists, presence and compatible text comparisons are remapped. Options and references are replaced by their target identifiers. Ascending/descending sorts, groups, visible properties and column order are kept when their configuration is transferable.

Unknown conditions, relative dates, contextual filters, custom sorts or incompatible empty rules cause an explicit refusal of the affected view. The active view is never silently replaced by a less filtered one. Definitions and errors remain in the JSON report.

Inline views use the `any:block` envelope of type `inline-view`. Their main configuration is stored under `<instance>.list`, with the source, filters and sort in `query.anyUi`. They reuse their source collection or the collection representing their source type. A source made of several collections is refused.

Compatible Anytwo versions accept inline table and kanban layouts. Older clients can use a replacement list. Groups and secondary views keep their client-specific limits. A pre-existing target collection containing out-of-scope objects is never used to silently widen the results of an imported view.

Width, manual order and presentation settings that are not applied are archived in `layoutSettings.any2any.sourceView`. The collection's views, properties and values stay distinct from the list of columns visible in a particular display.

## Templates and tables of contents

Templates of the concerned types and those explicitly referenced by collection views are read from the source API. They become native Anytwo templates with their content, icon, properties and collections. An empty collection can also receive its template.

The active view's default takes priority over the type default. Anytwo keeps one default per collection. Conflicting defaults or defaults that differ between views are reported. A default already present in an existing target collection is kept when it differs.

On compatible versions, top-level tables of contents become native dynamic `table-of-contents` blocks. Nested tables of contents are adapted into static links to the real heading identifiers. The report notes the absence of automatic updates in that case.

## Blocks, formatting and media

Toggles and collapsible headings use the native `any:collapsible` markers. Columns use `any:columns` and `any:column`, with their nested content. A malformed layout keeps its content in sequence with a warning. Tables keep their cells and checkboxes. Empty paragraphs use a zero-width character so Markdown does not merge them.

YouTube videos use a native `embed` envelope. Audio files use the file links recognised by the client player. Icons use the universal `any.icon` property, with an emoji or a file reference. Enriched bookmarks become titled links.

The current Anytwo client interprets these native markers even when the server stores them as `html` blocks. They are sent without global stripping: removing them would lose column structure, inline views, embedded properties, captions and block synchronization. Unsupported source elements still receive individual, reported adaptations.

Underlining depends on the Markdown support of the Anytwo version. Text, background, block, cell and callout colours, alignment and advanced layouts with views inside callouts or columns remain limitations. Code tags are kept literally, including inside code blocks.

## Widgets and chats

Widgets based on an imported page or collection are added to the shared Overview in source order. Link stays Link and the other modes become Views. System sections and entries, including Recently edited, are ignored. Target duplicates between shared and personal widgets are avoided.

Chats and discussions are excluded from ordinary imports. The archive option reads the chats exposed by the space API and produces one page per chat, with authors, dates, replies, edits, reactions and files according to the options. Messages become archive content. Reading uses cursor pagination and an incomplete history stops before destination writes.

## References and validation

The test suite uses simulated sources and destinations. API re-reads, conversion replays and targeted checks of the client parser complete this validation. Rendering must be verified for the formats and versions in use.

- [Anytype v2 API](https://developers.anytype.io/docs/reference/v2/)
- [AnyBlock v2 format](https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md)
- [Anytwo HTTP API](https://docs.any.org/reference/http-api.html)
- [Anytwo reading and filters](https://docs.any.org/database/reading-data.html)
- [Anytwo editor](https://docs.any.org/types/editor.html)
