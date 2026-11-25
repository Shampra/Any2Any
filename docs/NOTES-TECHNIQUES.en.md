# Anytype to Anytwo import

**[Français](NOTES-TECHNIQUES.fr.md) · [English](NOTES-TECHNIQUES.en.md)**

Any2Any reads the local Anytype v2 API and writes into Anytwo through the shared destination engine. The common application offers Anytype or Notion at startup. The [Notion guide](NOTION-IMPORT.en.md) describes the other source.

## Connection and launch

The standalone Windows archive launches with `Any2Any.exe`. The source version requires Python 3.10 or later and launches with `demarrer.bat` or `python app/server.py`. The interface listens on `127.0.0.1`, starting at port `8766`.

Anytype and Anytwo must be open. Anytype normally uses port `31009`, with a key obtained by pairing. The API status button lets you check or change the accesses. The Anytwo port is detected automatically when possible, with `31310` as the usual port.

The common profile's settings and reports are kept in `%APPDATA%/any2any` on Windows. Memorised secrets are protected by Windows DPAPI. Development profiles use their own directories. The `--demo` mode explores both sources with fictitious data and disables real imports.

## Selection and destination

The user can choose a space, a collection, types or objects. The linked-items option adds the references reachable in the same space, including inline-view documents whose filters are evaluable. For a whole space, this option is disabled in the interface. The report gives the reason for every inclusion.

The destination is an existing space or a new space. Source collections become Anytwo collections, with their supertags and their properties. A type collection is a fallback for objects that have properties and belong to no imported collection, or when a per-type destination is explicitly chosen.

Pages are created before their links are rebuilt. Links to a collection target the collection directly. Collections referenced by a view can also be taken over when they are archived on the Anytype side. Their views stay limited to the scope of the objects actually imported.

## Content and properties

Formatted text, headings, empty paragraphs, lists, checkboxes, toggles, quotes, callouts, code, equations, tables and columns are converted according to the capabilities of the Anytwo client. Images, files, audio players and YouTube videos use the compatible native formats. Mentions become inline links and internal links are remapped to the new identifiers.

Text, number, boolean, date, select and compatible relation properties are transferred into the target collections. Options and their colours are read from the source vocabulary. A date containing a time stays datetime even when the source metadata declares a plain date. Columns without values declared by the type are also created, except non-portable file/image properties.

File/image properties become content at the top of the page, under their label, when file retrieval is enabled. They do not create replacement text columns. File names are looked up in their metadata. One file is reused between pages, and an existing file is reused only after checking the normalised name, the size and the content.

Templates of the imported types and those referenced by collection views become native Anytwo templates. Their content, icon and properties are taken over. The active view's default takes priority over the type default. Conflicting defaults and differences with an existing target default are reported.

Top-level tables of contents use the native dynamic block when the Anytwo version allows it. Nested tables of contents use static links to the real heading identifiers.

## Views and widgets

Compatible table, list, gallery and kanban layouts are taken over. Nested AND/OR filters, simple comparisons, selections, empty-value conditions and compatible text comparisons are remapped with the properties, options and references. Sorts, groups, visible properties and column order are applied when their configuration is transferable. An incompatible active view is reported.

An inline view must rest on a single Anytwo collection. Several views can reuse that collection with their own configurations. Compatible Anytwo versions accept inline tables and kanbans; older clients may need a list adaptation. An advanced layout, notably a view inside a callout or a column, may lose its location or its presentation.

Anytype widgets based on an imported page or collection are added to the shared Overview, in source order. Link mode stays Link and the other modes use Views. System sections and widgets are ignored. Target duplicates between shared and personal widgets are avoided.

## Chats, limits and report

Chats and discussions are excluded from ordinary imports. The chat archive option creates one page per chat exposed by the space API, with authors, dates, replies, reactions and attachments according to the files option. Object discussions absent from this list are not discovered separately.

Some features are absent from Anytwo or have a different model. This concerns text, background, block, cell and callout colours, types, local/global property scope, file/image properties, enriched bookmarks, discussions, mini-apps and the Graph/Calendar layouts. Alignment and some block compositions are not preserved. Relative dates, custom sorts, out-of-scope relation restrictions and other non-transferable conditions are reported.

A simple import creates new copies on every run. It provides no synchronisation and no global undo. The current limit is 500 objects, templates included, and 100 MiB per file. Simulation examines the scope without writing into Anytwo.

The JSON report contains the source/target mappings, the views, the archived settings, the file transfers, the adaptations and the errors. It may contain source content. It is saved in the active profile.

The [fidelity details](IMPORT-FIDELITE.en.md) specify the conversions and limits. The [bilingual changelog](../CHANGELOG.md) describes the published and upcoming changes.
