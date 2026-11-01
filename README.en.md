# Any2Any — Anytype / Notion → Anytwo

**[Français](README.md) · [English](README.en.md)**

**Any2Any** is a tool for importing **Anytype** or **Notion** into **Anytwo**. Its local web interface lets you choose the source, check access, select content and configure the destination. Both sources reuse the same Anytwo backend. Anytype and Anytwo use local APIs; Notion uses its Internet API.

> [!WARNING]
> **Experimental tool — Anytwo alpha builds**
>
> Any2Any was developed and used to **test alpha versions of Anytwo**, not as a stable or officially supported migration solution. It works in certain scenarios, but **there is no guarantee of compatibility with future Anytwo versions, successful migration, or the accuracy, completeness, or quality of imported items**. APIs and data formats may change without notice.
>
> **Do not migrate the only copy of important data.** Back up your data, begin with a few objects in a **test Anytwo space**, and check the results manually. There is no automatic rollback or guarantee against duplicate imports.

## Features

- **Anytype selection**: spaces, collections, types and objects, with optional linked objects.
- **Notion selection**: a tree with three selectable levels; selected branches include their deeper descendants. Linked objects outside the tree are optional.
- **Notion views and properties**: compatible inline and collection views, filters, sorts, grouping, gallery settings, two-way relations and rollups.
- **Anytwo destination**: choose an existing space or create one. Anytype can also use an existing collection where that mode is offered. Each imported Notion data source creates its own collection/supertag and properties; its schema is not merged into an existing collection.
- **Content migration**: pages, properties and relations, formatted text, links, images, and other files, subject to the current converter’s capabilities.
- **Optional Anytype chat archives**: disabled by default; one archive page per source-space chat, with authors, dates, replies, reactions and attachments according to the files option. Chats remain outside ordinary page/type imports.
- **Read-only sources**: neither Anytype nor Notion is modified. Notion files are downloaded over the Internet without sending the API token to their hosts.
- **Pre-import simulation**: use **Test** to inspect the planned scope without writing to Anytwo.
- **Migration report**: imported objects, why they were included, adaptations, unsupported features, and errors, with JSON export.
- **Multilingual interface**: French, English, and German; your selection is saved in the browser.

## Getting started

**Requirements:** a running **Anytwo** client. The **standalone Windows** archive bundles Python; the **source** archive requires Python **3.10+**. For Anytype imports, also open its desktop client and authorize its API. For Notion, provide a connection token with read access to the selected pages; the Notion desktop client is not required. No additional Python libraries are needed.

1. Open the [GitHub releases](https://github.com/Shampra/Any2Any/releases) and download the **application archive** attached to the desired release. Extract it into a dedicated folder and open that folder. The attached SHA-256 file can be used to verify the download.
2. Open Anytwo and, for an Anytype import, Anytype.
3. In the **standalone Windows** archive, run **`Any2Any.exe`** at the top level. With the **source** archive, run `demarrer.bat` or `python app/server.py` from the project directory.
4. Choose **Anytype** or **Notion** in the welcome dialog, then complete the access checks. Saved Notion tokens are checked automatically.
5. Select your content and destination. Run **Test**, then **Import**.

### Folder layout

The Windows archive has `Any2Any.exe` at the top level, dependencies under `_internal/` and documentation under `documentation/`. Keep these folders alongside the executable.

The repository and source archive keep launchers at the top level and runtime files under `app/`. The repository’s `dev/` folder groups tests and development tools and is excluded from the application archive.

### Connect your source

- **Anytype**: keep Anytype and Anytwo running. Choose **Authorize in Anytype**, then complete the pairing request. Source reads use the local API.
- **Notion**: create an internal connection with read access and share the pages/databases you want to import with it. Enter the token only in the tool’s local form. Sharing a page containing a linked view may not grant access to its original database. On Windows, the token can be remembered and later forgotten in settings. Internet access is required; the Notion desktop app can remain closed. See the [Notion connection guide (French)](docs/NOTION-API.fr.md).

The API status button at the top right reopens connection settings. **Retrieve files** and **Import linked items** options adapt to the source and selected scope.

Use `demo.bat`, `Any2Any.exe --demo` or `python app/server.py --demo` to explore sample content without real writes. The source selector at the top lets you switch applications later.

The interface listens on `127.0.0.1`, starting at port `8766`. On Windows, settings are stored in `%APPDATA%/any2any`; remembered credentials use Windows DPAPI. The first launch can reuse saved development credentials without changing the old profiles. Typical destination/source API ports are `31310` for Anytwo and `31009` for Anytype.

## Known limitations

The applications have different data models. Notion formulas become static results. Buttons, text/background colors, reminders, history and some view or block formats may be adapted or omitted. Notion charts are not imported; grouped inline views may become lists. Compatible collection views preserve grouping, filters and sorting. Galleries preserve **Fit image** and pages use **side peek** unless the source explicitly supplies full-page opening. The app shows source-specific limitations and each report lists detected changes. See [Notion import details (French)](docs/NOTION-IMPORT.fr.md).

Simple imports create new copies on every run, so restarting may create duplicates. Interrupted Notion reads can be reused in memory for 30 minutes; this does not automatically resume writes or synchronize data. There is no global rollback.

## About the project

This is an independent project and **is not officially affiliated with Anytype, Notion or Anytwo**. Any2Any is distributed under the [GNU GPLv3 license](LICENSE). Copyright (c) 2026 Shampra.

Detailed documentation: [Anytype import](docs/NOTES-TECHNIQUES.fr.md), [Notion import](docs/NOTION-IMPORT.fr.md) and [Notion connection/API](docs/NOTION-API.fr.md) (French). See the [changelog](CHANGELOG.md) for the release history.
