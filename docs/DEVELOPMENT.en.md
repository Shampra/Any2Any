# Isolated Anytype / Notion development

**[Français](DEVELOPMENT.fr.md) · [English](DEVELOPMENT.en.md)**

## Starting state

- Common base: main, commit `684c8867ac67b6f4752743d23c88040103b19a98`, release 0.9.3.
- Stable Anytype: `F:/Documents/ChatGPT/Any2Any`, main branch, unchanged files.
- Prototype: `F:/Documents/ChatGPT/Anytwo/Any2Any`, develop/notion branch.
- Git worktree created separately. The Codex application refused to attach it as a managed worktree because the stable repository is outside the chat's declared roots. Explicitly use the prototype folder in commands; this is not a Git isolation failure.

## Launch

| Version | Launcher | Default port | Settings and reports |
|---|---|---|---|
| Stable Anytype | stable folder, demarrer.bat | 8765 | APPDATA/anytype-anytwo-importer |
| Common application | demarrer.bat | 8766 | APPDATA/any2any |
| Notion prototype | dev/tools/development/demarrer-notion.bat | 8876 | APPDATA/any2any-dev/notion-dev |
| Anytype engine check in development | dev/tools/development/demarrer-anytype-dev.bat | 8877 | APPDATA/any2any-dev/anytype-dev |

In this worktree, server.py and demarrer.bat now use the unified profile and an Anytype/Notion selection window before any check. The specialized launchers moved into tools/development force their former profiles. The first unified launch reuses the protected secrets of both development profiles without modifying those files; the stable configuration is never read or written.

The notion-dev profile opens the Notion journey: internal connection, inventory, selection by database/source/page and read-only compatibility analysis. The Anytype choice remains available for regressions. The Notion converter is active through notion_migration.py; writes use anytwo_backend.py and the lock shared with Anytype. See NOTION-IMPORT.en.md for limits and the authorized real test. See [API analysis and connection](NOTION-API.en.md).

## Shared code and backports

`anytwo_backend.py` is the destination entry point, used by migration.py, view_conversion.py and file_transfer.py. It re-exports the single existing implementation from api_clients.py to keep compatibility and tests during a progressive extraction. Anytype reading functions and its document conversion remain Anytype-specific. The Notion reader uses this destination API and its native formats, without copying its HTTP writes.

A fix from main is brought here by merging main after a commit or shelving current work. Common changes found during Notion work must be isolated from Notion functions: prepare a main-compatible commit, validate it on the Anytype side, then merge main into develop/notion. If a fix depends on still-experimental refactoring, note the adaptation to make in COMMON-FIXES.md rather than claiming it is already backported. Resolve conflicts and rerun the tests; backports are not automatic.

Keep two durable branches. Temporary fix branches may start from main. Do not change main from this conversation or publish without a request. The future Notion merge will be an explicit step, after validating both sources.

## Verify

From this folder: `python -B dev/run_tests.py`, then `node dev/tests/test_notion_ui.cjs`, `node --check app/static/app.js`, `node --check app/static/i18n.js` and `node --check app/static/notion.js`. For a demonstration without APIs: `demarrer-notion.bat --demo`. Always check the profile shown by /api/config and the console before a real test.

The Notion journey uses its own connection and settings popup for both APIs; the Anytype form remains independent. In this folder, demarrer.bat forces the unified profile; the two launchers under tools/development force their respective profile and port.


## Preparing the common version

Local release/unified branch derived from develop/notion, same physical worktree. The stable folder and main remain unchanged. The Anytype and Notion sources use the common Anytwo boundary; tests for both remain mandatory. No publication is done by the preparation.

Build: python -B dev/tools/build_release.py. The dev/dist/Any2Any-<version>.zip archive contains only the application modules, static, READMEs/licence/changelog, user guides and the two main/demo launchers. BUILD.json carries the public file checksums and the ZIP has its separate SHA-256. An explicit allow-list excludes reports, secrets, Git metadata, tests and diagnostic tools. The build is reproducible and does not depend on the reports files.

Private reports/audits remain in reports, ignored by Git and excluded from the distribution. Do not delete user backups to clean the repository. __pycache__ caches for code and tests may be removed; other projects in the parent folder are not affected.


## Active folder and Windows build

The active worktree is F:/Documents/ChatGPT/Anytwo/Any2Any. The historical Any2Any-Notion folder is emptied; no report was deleted. Private data is in dev/reports and dev/.local, always ignored by Git. Active code is in app, tests and builders in dev. The historical Anytype folder is no longer the reference launcher and its files are not modified.

Run demarrer.bat or python app/server.py. Test: python -B dev/run_tests.py, node dev/tests/test_notion_ui.cjs and node dev/tests/test_startup_ui.cjs. Source archive: python -B dev/tools/build_release.py. Windows build on Windows: install the pyinstaller==6.22.3 development dependency, then python -B dev/tools/build_windows.py. The builder extracts its ZIP and starts the EXE in demo mode with temporary settings; both sources are checked without accessing user accounts.

GitHub Actions verifies Linux and Windows, builds the Windows x64 binary, then publishes both ZIPs and their SHA-256 in a new prerelease. Release 0.10.0 remains intact. Compiled files are under dev/build and are not versioned.
