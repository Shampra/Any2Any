"""Page content must follow the language chosen in the interface."""
import re
import unittest
from unittest.mock import patch

from migration import Engine, render_blocks
from page_text import TEXTS, activate, language, notice, page_text


def fields(template):
    return {name: 'X' for name in re.findall(r'\{(\w+)\}', template)}


VIEWS = {'properties': {'name': 'Views'},
         'blocks': [{'type': 'dataview', 'id': 'v1'}, {'type': 'paragraph', 'text': 'Body'}]}


class PageTextTests(unittest.TestCase):
    def tearDown(self):
        activate('fr')

    def test_every_message_exists_in_every_interface_language(self):
        for key, entries in TEXTS.items():
            with self.subTest(key=key):
                self.assertEqual(len(entries), 3)
                self.assertTrue(all(value.strip() for value in entries))
                self.assertEqual(len(set(entries)), 3, 'untranslated entry')

    def test_language_codes_are_normalized(self):
        self.assertEqual(language('EN'), 'en')
        self.assertEqual(language('de-DE'), 'de')
        self.assertEqual(language('es'), 'fr')
        self.assertEqual(language(None), 'fr')

    def test_notices_carry_no_inline_markup(self):
        # Anytwo shows quote text verbatim, so "**" would appear on the page.
        for key, entries in TEXTS.items():
            if not key.startswith('notice.'):
                continue
            for code, template in zip(('fr', 'en', 'de'), entries):
                with self.subTest(key=key, language=code):
                    self.assertNotIn('**', notice(key, code, **fields(template)))

    def test_render_blocks_follows_the_active_language(self):
        self.assertIn('> Attention : collection ou vue intégrée non importée.',
                      render_blocks(VIEWS, {}, 'sid', {}, False, None, set()))
        activate('en')
        markdown = render_blocks(VIEWS, {}, 'sid', {}, False, None, set())
        self.assertIn('> Warning: inline collection or view not imported.', markdown)
        self.assertNotIn('Attention', markdown)
        self.assertIn('Body', markdown)


class EnginePageTextTests(unittest.TestCase):
    def tearDown(self):
        activate('fr')

    def test_engine_writes_the_page_in_the_interface_language(self):
        class Source:
            def object_detail(self, sid, oid):
                return VIEWS

        page = {'id': 'v', 'name': 'Views', 'type': 'character'}
        inventory = {'all': [page], 'objects': [page], 'collections': [], 'members': {}, 'standalone': [],
                     'types': [{'id': 'type-character', 'key': 'character', 'name': 'Characters', 'items': [page]}],
                     'stats': {}}
        plan = {'source_space': {'id': 'src', 'name': 'Source'}, 'selection': {'kind': 'space'},
                'target': {'space_mode': 'create', 'space_name': 'Dest', 'collection_mode': 'none',
                           'type_mappings': []},
                'mode': 'simple', 'follow_links': False, 'files': False, 'language': 'en'}
        written = []
        with patch('migration.create_space', return_value='dest'), \
             patch('migration.create_object', return_value='new-v'), \
             patch('migration.anytype_property_definitions', return_value={}), \
             patch('migration.list_columns', return_value=[]), \
             patch('migration.add_column', return_value='prop'), \
             patch('migration.set_markdown', side_effect=lambda *a: written.append(a[-1])), \
             patch('anytwo_backend.server_version', return_value=(0, 5, 0)):
            list(Engine(Source(), object(), inventory, plan).run())
        self.assertTrue(written)
        self.assertIn('> Warning: inline collection or view not imported.', written[0])
        self.assertNotIn('Attention', written[0])

    def test_french_stays_the_default(self):
        self.assertEqual(page_text('notice.collection_view'),
                         'Attention : collection ou vue intégrée non importée.')


if __name__ == '__main__':
    unittest.main()
