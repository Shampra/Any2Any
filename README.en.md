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
- **Flexible destinations**: use existing Anytwo spaces and collections or create new ones.
- **Content migration**: pages, properties and relations, formatted text, links, images, and other files, subject to the current converter’s capabilities.
- **Read-only sources**: neither Anytype nor Notion is modified. Notion files are downloaded over the Internet without sending the API token to their hosts.
- **Pre-import simulation**: use **Test** to inspect the planned scope without writing to Anytwo.
- **Migration report**: imported objects, why they were included, adaptations, unsupported features, and errors, with JSON export.
- **Multilingual interface**: French, English, and German; your selection is saved in the browser.

## Getting started

**Requirements:** Python **3.10+** and a running **Anytwo** client. For Anytype imports, also open its desktop client and authorize its API. For Notion, provide a connection token with read access to the selected pages; the Notion desktop client is not required. No additional Python libraries are needed.

1. Download and extract the project.
2. Open Anytwo and, for an Anytype import, Anytype.
3. Run `demarrer.bat` on Windows, or `python server.py` from the project directory.
4. Choose **Anytype** or **Notion** in the welcome dialog, then complete the access checks. Saved Notion tokens are checked automatically.
5. Select your content and destination. Run **Test**, then **Import**.

Use `demo.bat` or `python server.py --demo` to explore sample content without real writes. The source selector at the top lets you switch applications later.

The interface listens on `127.0.0.1`, starting at port `8766`. On Windows, settings are stored in `%APPDATA%/any2any`; remembered credentials use Windows DPAPI. The first launch can reuse saved development credentials without changing the old profiles. Typical destination/source API ports are `31310` for Anytwo and `31009` for Anytype.

## Known limitations

The applications have different data models. Formula snapshots, buttons, text/background colors, reminders, history and some view or block formats may require adaptation or may be omitted. The app shows source-specific limitations and each report lists detected changes. See [Notion import details (French)](docs/NOTION-IMPORT.fr.md).

Simple imports create new copies on every run, so restarting may create duplicates. Interrupted Notion reads can be reused in memory for 30 minutes; this does not automatically resume writes or synchronize data. There is no global rollback.

## About the project

This is an independent community project and **is not officially affiliated with Anytype or Anytwo**. Any2Any is distributed under the [GNU GPLv3 license](LICENSE). Copyright (c) 2026 Shampra.

For implementation details and the current release history, see the [French technical notes](docs/NOTES-TECHNIQUES.fr.md).


Chat archives are optional and disabled by default: one page per chat in the source space, with authors, dates, replies, reactions and optional attachments. Chats remain excluded from ordinary page and type imports.
