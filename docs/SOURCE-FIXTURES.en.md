# Source demonstration pages

**[Français](SOURCE-FIXTURES.fr.md) · [English](SOURCE-FIXTURES.en.md)**

The JSON examples are in `examples/notion-test-page.json` and `examples/anytype-test-page.json`. They describe the basic blocks, without private identifiers or keys.

`tools/create_test_pages.py` is an explicit fixture-creation tool, independent from the read-only importer. Without arguments, it only generates the JSON examples. `--apply` enables the requested writes; for Notion, the expected workspace must also be named:

```powershell
python -B tools/create_test_pages.py --apply --source notion --notion-workspace "Your workspace"
python -B tools/create_test_pages.py --apply --source anytype
```

The default Notion parent page is “Test pour Anytwo”; `--notion-parent` lets you specify its title. It must be unique, at the root, and shared with the connection. The program checks the workspace name before any creation. It creates a sub-page, not a replacement of the parent page.

For Anytype, the program tries the new space “Test pour Anytwo” and uses Cobaye1 only if space creation is refused. The key must have write access: the fallback does not bypass that permission. Application settings are read to authenticate, without modifying or copying keys. The program never widens permissions.

## Content

- Headings, text, bold, italic, underline, strikethrough, code, colours, empty paragraphs.
- Nested lists, checkboxes, toggles and collapsible headings, quotes, callouts, dividers.
- Columns, tables, equation and table of contents.
- PNG image, synthetic WAV sound, text file, CSV, the same image referenced in several places, YouTube video and bookmark.
- Notion: sub-page and mentions, a synced block and its reference; two inline databases, two projects and three tasks, coloured choices, dates, relations, formulas, rollups (sum and original values) and a filtered/sorted view with hidden properties.
- Anytype: demonstration type with properties, two linked objects, coloured options, collection and query, filtered/sorted inline view and hidden properties. The table contains a real cell checkbox.

This is not a reproduction of every interface control: buttons, forms, automations, some visual settings or specific media remain limited by the API. No chat/message is sent.

## Checks and rerun

The local log `reports/source-fixtures.json` keeps the created resources and completed steps. It is ignored by Git, may contain temporary file URLs and contains no API key. After an unknown network result, check the resources before rerunning: Notion does not provide a general idempotency guarantee here.

The fixtures created during this session were read back through their APIs: 40 top-level blocks, two projects and three tasks in Notion; 43 blocks, four files and one inline view in Anytype. The Notion sums were verified at 100, 180 and 0; the view has its filter and sort. Both Anytype image blocks reference the same file object.
