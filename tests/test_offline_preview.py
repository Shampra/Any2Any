"""Static regressions for the offline inspection state (browser flow tested separately)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OfflinePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
        cls.script = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')
        cls.styles = (ROOT / 'static' / 'style.css').read_text(encoding='utf-8')
        cls.language = (ROOT / 'static' / 'i18n.js').read_text(encoding='utf-8')

    def test_dialog_close_is_present_and_always_allowed_after_checks(self):
        self.assertIn('id="close-settings"', self.page)
        self.assertIn('if(S.connecting)return;', self.script)
        self.assertIn("S.settingsOpen=false;\n  hidden('connection-overlay',true);", self.script)
        self.assertIn("hidden('close-settings',false);", self.script)

    def test_offline_state_blocks_actions_and_highlights_status(self):
        self.assertIn('id="mini-warning"', self.page)
        self.assertIn('id="offline-notice"', self.page)
        self.assertIn('chip.classList.toggle(\'api-failed\'', self.script)
        self.assertIn('workspace.inert=!ready;', self.script)
        self.assertIn('!apiReady() || !S.selection.kind', self.script)
        self.assertIn("if(!apiReady())return toast('API indisponibles : import désactivé.');", self.script)
        self.assertIn('.status-chip.api-failed', self.styles)

    def test_offline_warning_translated_and_version_consistent(self):
        self.assertIn('Bêta 0.9.1', self.page)
        self.assertIn('APIs unavailable: preview only.', self.language)
        self.assertIn('APIs nicht verfügbar: nur Vorschau.', self.language)
        for path in ('README.md', 'README.en.md', 'docs/NOTES-TECHNIQUES.fr.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertIn('0.9.1-beta', text)
        self.assertIn("server_version = 'Any2AnyUI/0.9.1'", (ROOT / 'server.py').read_text(encoding='utf-8'))
        self.assertNotIn('Anytype-Anytwo-Importer/0.8', (ROOT / 'api_clients.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
