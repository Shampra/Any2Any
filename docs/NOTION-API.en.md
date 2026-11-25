# Notion → Anytwo: API, connection and conversion strategy

**[Français](NOTION-API.fr.md) · [English](NOTION-API.en.md)**

Analysis of 30 October 2026, selected API version: `2026-03-11`.

## What works in this branch

The local journey offers the Anytype / Notion choice. For Notion: connection validation, inventory, adding by link, scope selection, tree with branch selection and exclusion, schema and view reading, exportable analysis. The journey can now launch a real import into Anytwo, with optional file downloads, out-of-tree links, progress, cancellation and an exportable report. The Notion reader remains read-only. A real fixture was imported and read back in a dedicated Anytwo test space; the remaining limits are in NOTION-IMPORT.en.md.

The reader is `notion_source.py`, the local routes are `notion_routes.py`, the interface is `static/notion.js`. The destination engine remains `anytwo_backend.py`, shared by Anytype and Notion; no second Anytwo write client is created.

## Model and scopes

A Notion space is not an object exportable in one call. The connection sees the content it is allowed to access. A database is a container with one or more **data sources**, each carrying its schema and pages (rows). Pages contain blocks, sometimes nested. Linked databases reuse their original source: sharing only the page that displays them is not necessarily enough; also share the original database. [Database model](https://developers.notion.com/guides/data-apis/working-with-databases).

The interface presents the space associated with the connection, then a tree: pages, databases, data sources and pages of these sources. An internal connection concerns a single workspace; multiple spaces will require distinct connections. The API does not provide reliable details of explicit versus inherited permissions. The displayed roots are therefore the items for which no parent is known in the accessible inventory; a missing parent is never invented.

The journey starts with a Notion and Anytwo connection popup. An available token is checked automatically; without a token, the form is displayed. The popup then shows first-level retrieval. The list stays on “Choose a space…” without preselecting; explicitly choosing the space displays the already prepared data. “Refresh” restarts the search with an indicator, without prematurely showing an empty state. “Refresh” re-reads this inventory. Expanding an item loads its children on demand, without traversing all its content in advance. Checking a branch includes all its descendants; unchecking a sub-branch excludes them, even if it is not fully expanded. A deeper selection can be re-included. “Select everything in this space” takes the accessible roots and their descendants, not unauthorized private content. The analysis materializes this selection and counts the resulting pages.

Search is not a guaranteed exhaustive inventory: its index may lag. Manually adding a URL or identifier can find a known item. The tool therefore does not promise a complete workspace export. [Search limits](https://developers.notion.com/reference/search-optimizations-and-limitations).

## Connection: what to prepare

1. In the Notion developer portal, create an **internal connection** for the relevant space. Its creation requires workspace owner rights. Give it the **Read content** capability, without creating or modifying content. Comment reading will be a separate capability if their archiving is developed.
2. Authorize pages and databases through **Content access**, or add the connection from the Notion page menu. Access to children is inherited; also authorize the original databases of linked views.
3. Launch `Any2Any.exe` (Windows archive) or `demarrer.bat` (source archive), then choose **Notion** in the welcome window (local interface from port 8766). Enter the secret token in the local field and click **Validate connection**. Do not send the token in a conversation, a screenshot or a Git repository.
4. Explicitly choose a space, wait for the roots to load, then check the whole space or expand branches to choose items and launch their analysis. A known page or database can also be added by its link. A test page with properties, relations, files and views will help verify the real differences.

The connection calls `/users/me` then content search. No token is returned to the browser by API responses. When a token is available, a message replaces the input field; “Forget token” clears the session and the remembered copy, then shows the field again. By default it stays in process memory; optional persistence uses Windows DPAPI protection in the Notion profile configuration. Revocation in Notion remains possible independently.

A personal access token also exists, but a read-only internal connection explicitly limits the scope. OAuth will be relevant for later multi-user distribution; it is not necessary for this first personal use. [Internal connection](https://developers.notion.com/guides/get-started/internal-connections), [capabilities](https://developers.notion.com/reference/capabilities), [connection types](https://developers.notion.com/guides/get-started/quick-start).

## Calls used and next reads

| Need | API |
|---|---|
| Identity | `GET /users/me` |
| Search | `POST /search` — read despite POST |
| Container and schema | `GET /databases/{id}`, `GET /data_sources/{id}` |
| Rows of a source | `POST /data_sources/{id}/query` — read |
| Metadata and content | `GET /pages/{id}`, `GET /blocks/{id}/children`, recursively |
| Views | `GET /views?database_id=…`, then `GET /views/{id}` |
| Complete properties, importer | `GET /pages/{id}/properties/{property_id}`, with pagination |

Lists are paginated, including block children. A limit or a stuck cursor produces an explicit error rather than an inventory presented as complete. The prototype caps a selection at 2,000 pages and a traversal at 5,000 blocks. Notion quotas now depend on the plan and workspace; the reader spaces requests and handles 429 responses. Long waits require a retry. [Data source query](https://developers.notion.com/reference/query-a-data-source), [quotas](https://developers.notion.com/reference/request-limits).

## Planned Anytype mappings

| Notion | Proposal for Anytwo / point to verify |
|---|---|
| Page, title, icon, cover | Page and metadata; retrieve the relevant files |
| Data source | Supertag owning its schema; each row receives this supertag |
| Text, lists, boxes, headings, toggles | Native blocks through the common engine; verify annotations |
| Columns, tables, callouts | Adapt to the native structure, check rendering |
| Select / multiselect | Preserve vocabulary and colours, with palette matching |
| Status | Simple choice; keep the Notion workflow groups archived |
| Number | Unchanged value, currency format with currency, percentage and native separators; unknown formats archived |
| Date | Respect time, time zone and range; do not silently reduce to a day |
| Relation | Remap pages, restrict to the target supertag handle; dependency schemas without their members outside the selection |
| Formula | Frozen result; archived expression, without claiming to recreate the active calculation |
| Rollup | Native definition to adapt: remapped relation and target property, compatible operator; archive the result if the calculation cannot be translated |
| People, authors, unique identifier | Archived values; do not invent Anytwo accounts or authors |
| Image, file, audio, video | Download then use Anytwo blocks and attachments, preserve available names and dimensions |
| Embed / bookmark / mention | Rewrite internal links, use an embed if compatible, otherwise report the adaptation |
| Synced block | Original and references synchronized in Anytwo; no live link with Notion |
| Buttons, automations, forms, permissions, history | No active recreation planned; reporting and metadata when accessible |
| Unknown / unsupported blocks | Explicit warning, never an invented replacement |

These choices are conversion decisions. The exact accessible types are described in [Notion blocks](https://developers.notion.com/reference/block) and [page properties](https://developers.notion.com/reference/page-property-values). The destination is constrained by [the Anytwo editor](https://docs.any.org/types/editor.html) and [its types and properties](https://docs.any.org/database/types-and-properties.html). Underline and text/background colours notably require checking the capabilities of the target Markdown bridge; a literal HTML representation would be incorrect.

### Views and displayed properties

The current Notion API has a views API: reading their configuration allows studying the type, filters, sorts, visible properties and their order. A view is not a new supertag; it must target its source supertag. Linked views and their placement in the page will require specific verification of the content returned by the API. A condition that cannot be translated must make the entire view conversion refused, so its result is not silently widened. [Views guide](https://developers.notion.com/guides/data-apis/working-with-views), [retrieve a view](https://developers.notion.com/reference/retrieve-a-view), [list views](https://developers.notion.com/reference/list-views).

### Exhaustiveness and files

A simple page read may truncate some properties: relations and people, mentions in titles/texts, calculations. The import reads property items with pagination before writing and reports formula/rollup limits; a simple analysis may remain partial on these values. [Property values](https://developers.notion.com/reference/page-property-values).

Files hosted by Notion use temporary URLs (about one hour). They must be re-read at transfer time, downloaded then uploaded into Anytwo, and their URL must not be kept as a definitive attachment. No Notion authorization header must be sent to an external file host. [Notion files](https://developers.notion.com/reference/file-object).

## Validation before a real import

The `--demo` mode verifies the journey without calling Notion or Anytwo. Tests cover pagination, read-only route permissions, errors without secrets, selection invalidation and analysis. The real connection and converter were verified on the fixture requested by the user, in a dedicated Anytwo space; visual validation of the renderings remains to be done in the client.

Validation uses a search limited to one item, independently of the complete inventory. The inventory is loaded after explicitly choosing the space, then can be re-read with Refresh. Operations display a wait counter; connection and inventory have respective budgets of 5 and 90 seconds; the browser limits its wait to 7 seconds for the connection and 120 seconds for other calls.


## Intermediate parents and long analysis

Block-type parents (toggle, column, etc.) are fetched through `GET /blocks/{id}` to find the ancestor page or database, even if the block is not a search item. Readable ancestors absent from the index are retrieved. An inaccessible parent or a cyclic chain remains reported after a small grey heading “Other accessible items that are not top-level pages”. This separation is always visible and does not collapse during a selection. These items participate in the same preloading and on-demand reading as the other branches. [Notion parents](https://developers.notion.com/reference/parent-object), [retrieve a block](https://developers.notion.com/reference/retrieve-a-block).

Analysis is background work, kept only in server memory. The interface queries its state separately and shows the step, elapsed time and request count next to the button; an error remains visible there. Cancellation interrupts the traversal after the current network request (maximum network delay of 25 seconds). The total budget is 900 seconds; an overrun produces an explicit error result, without presenting a partial analysis as complete. Blocks read to establish the selection are reused during analysis, in a cache bounded to that operation. Property reading uses the same selection snapshot; exhaustiveness limitations remain reported.


## Connection responsiveness and preloading

The connection uses `https://api.notion.com`, without detecting the installed Notion client. Token validation has a budget of 5 seconds; the browser abandons its wait after 7 seconds. Inventory loading is separate and continues with an indicator, without locking the whole interface. A busy server returns an explicit response rather than letting a new validation wait for its network lock. [Cloud authentication](https://developers.notion.com/reference/authentication).

Branches are then preloaded in the background, starting with the upper levels. This anticipation is bounded to 60 branches or two minutes, with a single request in flight; it stops in favour of user actions. Ready branches expand immediately without a new network call. A branch still being read is reused rather than downloaded twice. Results remain in the session and are invalidated by “Refresh”. Non-preloaded or errored branches remain viewable on demand. This cache concerns navigation; analysis re-reads the selected data.

“Test” produces a read-only report; it does not write into Anytwo. The destination is loaded after choosing the workspace if Anytwo is available and can be refreshed. “Import” creates a real copy in Anytwo, without modifying Notion. An interruption keeps the objects already created; a new ordinary run creates another copy.


## Parallelization and recovery of large analyses

The journey reads up to four pages simultaneously. A single regulator spaces starts by about 0.35 seconds, including retries: four tasks therefore do not allow four times more traffic. `Retry-After` pauses on 429 or 529 are common to all readers; waits remain cancellable. Current limits are 180 requests/minute (600 on Business/Enterprise), with a separate limit for source queries. Conservative mode is used without assuming the plan. [Notion quotas](https://developers.notion.com/reference/request-limits).

A shared read cache avoids identical requests within an analysis, including those started simultaneously. After an error, overrun or cancellation, it remains reusable for the same selection for five minutes. Recovery is reported in the report: it uses the recent snapshot, not a complete re-read of every object. “Refresh”, manual addition of an item, reconnection or a selection change invalidate recovery. A successful analysis clears this recovery point. The cache remains in memory and is bounded to 32 MiB; excess responses remain readable but are not kept. No key is stored in this cache, no recovery file is created.

The fifteen-minute delay is a safety bound, not a duration estimate. A large selection may require more than three minutes at the allowed rate. Concurrency hides part of the network latency; it does not remove quotas. No precise gain is promised on the real account before measurement.

The API status at the top right reopens the popup at any time. It allows changing the Notion token, forgetting its persistence and setting/testing the Anytwo port. The space remains explicitly chosen by the user. The main screen has “01 · Choose items to import” and “02 · Import configuration”. The second pane offers the destination, the file and out-of-tree link options, then Test (without writing) and Import (real copy to Anytwo).

The validated connection is explicitly displayed in green and its button can no longer be re-enabled. Initial loading uses a dedicated closable popup; closing the popup lets the search continue in the background. API settings can be reopened during this loading without being automatically closed when it completes. See also ANYTWO-RELATIONS-ROLLUPS.en.md and SOURCE-FIXTURES.en.md.
