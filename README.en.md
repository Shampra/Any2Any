# Any2Any — Anytype → Anytwo Migrator

**[Français](README.md) · [English](README.en.md)**

**Any2Any** is a community-developed migration tool for transferring data from **Anytype** to **Anytwo** through both applications’ local APIs.

It provides a **local web interface** to browse Anytype spaces, select an entire space, a collection, multiple types, or individual objects, and choose where to import them in Anytwo.

> [!WARNING]
> **Experimental tool — Anytwo alpha builds**
>
> Any2Any was developed and used to **test alpha versions of Anytwo**, not as a stable or officially supported migration solution. It works in certain scenarios, but **there is no guarantee of compatibility with future Anytwo versions, successful migration, or the accuracy, completeness, or quality of imported items**. APIs and data formats may change without notice.
>
> **Do not migrate the only copy of important data.** Back up your data, begin with a few objects in a **test Anytwo space**, and check the results manually. There is no automatic rollback or guarantee against duplicate imports.

## Features

- **Selective import**: Anytype spaces, collections, types, and objects; optional inclusion of linked objects.
- **Flexible destinations**: use existing Anytwo spaces and collections or create new ones.
- **Content migration**: pages, properties and relations, formatted text, links, images, and other files, subject to the current converter’s capabilities.
- **Local processing**: the tool communicates with the APIs exposed by the two applications on your machine; Anytype is accessed read-only.
- **Pre-import simulation**: use **Test** to inspect the planned scope without writing to Anytwo.
- **Migration report**: imported objects, why they were included, adaptations, unsupported features, and errors, with JSON export.
- **Multilingual interface**: French, English, and German; your selection is saved in the browser.

## Getting started

**Requirements:** Python **3.10+**, the **Anytype** and **Anytwo** desktop clients running on the same computer, and authorization to access Anytype’s API.

1. Download and extract the project.
2. Open Anytype and Anytwo.
3. On Windows, run `demarrer.bat`; on other systems, run `python server.py` from the project directory.
4. The interface opens in your browser. Check API connectivity and authorize Anytype when prompted.
5. Select the source data and the Anytwo destination.
6. Run **Test**, review the destination, then choose **Import**.

To preview the interface without opening the applications, start the app normally, let the API checks finish, and close the connection dialog with the × button. The API status stays red and imports are disabled, while the FR/EN/DE language switcher remains available. To explore sample data, run `demo.bat` or `python server.py --demo` (real imports are disabled in demo mode).

The web interface listens on `127.0.0.1` only (using a local port starting at `8765`). API ports and authorization are saved on your computer. The usual Anytwo port is `31310`; the usual Anytype port is `31009`.

## Known limitations

The applications do not always use the same data models. Some information may be simplified, transformed, or lost: **types, templates, global or local properties, dynamic views and queries, advanced filters, embedded collection views, tables of contents, discussions, rich bookmarks, and presentation settings**. This is not an exhaustive list.

Embeds, complex layouts, and some file formats may not be reconstructed as native Anytwo blocks, even where the Anytwo application supports them through its interface. Migration reports describe detected adaptations, but **cannot by themselves guarantee that every item was transferred faithfully**.

**Simple import** creates new objects on every run. **Synchronization**, automatic resume, deduplication, and rollback are **not available yet**.

## About the project

This is an independent community project and **is not officially affiliated with Anytype or Anytwo**. Any2Any is distributed under the [GNU GPLv3 license](LICENSE). Copyright (c) 2026 Shampra.

For implementation details and the current release history, see the [French technical notes](docs/NOTES-TECHNIQUES.fr.md).


Chat archives are optional and disabled by default: one page per chat in the source space, with authors, dates, replies, reactions and optional attachments. Chats remain excluded from ordinary page and type imports.
