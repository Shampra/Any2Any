"""Current-client block contracts at the shared Markdown write boundary."""
import unittest
from unittest.mock import patch

from inline_views import inline_markdown
from migration import render_blocks, write_markdown_with_embeds
from notion_native import caption_image, envelope
from rich_content import image_markdown, youtube_markdown


def samples():
    """Small synthetic documents also usable by the optional desktop-parser check."""
    return {
        'toggle': render_blocks({'blocks': [
            {'type': 'toggle_heading_2', 'text': 'Toggle title'},
            {'type': 'paragraph', 'indent': 1, 'text': 'Hidden body'}
        ]}, {}, 'space', {}, False, None, set()),
        'columns': render_blocks({'blocks': [
            {'type': 'row'}, {'type': 'column', 'indent': 1, 'width': 1},
            {'type': 'paragraph', 'indent': 2, 'text': 'Left'},
            {'type': 'column', 'indent': 1, 'width': 2},
            {'type': 'paragraph', 'indent': 2, 'text': 'Right'}
        ]}, {}, 'space', {}, False, None, set()),
        'inline-view': inline_markdown('space', 'page', 'view-instance', 'Collection', 'collection'),
        'collection-view': envelope('collection-view', 'collection-instance', {
            'space': 'space', 'collection': 'collection', 'view': 'default', 'layout': 'table'
        }, '[Collection](any://o/space/collection)'),
        'property': envelope('property', 'property-instance', {
            'space': 'space', 'object': 'page', 'owner': 'any', 'property': 'author'
        }, 'Created by'),
        'synced-source': envelope('synced-block', 'source-instance', {'role': 'source'}, 'Shared text'),
        'synced-reference': envelope('synced-block', 'reference-instance', {
            'role': 'reference', 'ref': 'any://o/space/page/editor_blocks/source-block',
            'sourceInstance': 'source-instance'
        }, 'Shared text'),
        'table-of-contents': envelope('table-of-contents', 'toc-instance', {}, ''),
        'embed': youtube_markdown('https://youtu.be/LMXMbeKyneQ', 'video'),
        'image-caption': caption_image(image_markdown('any://f/space/image', 'Photo', 320),
                                       'Image caption', 'page', 'image'),
        'callout': '<!-- any:callout {"icon":"💡"} -->\n\nCallout body\n\n<!-- /any:callout -->',
        'code': '```html\n<!-- any:block {"kind":"example"} -->\n```',
        'spacing': '\n\nFirst\n\n\nSecond\n\n',
    }


class NativeWriteTests(unittest.TestCase):
    def test_native_blocks_and_literal_source_reach_the_api_unchanged(self):
        for kind, markdown in samples().items():
            with self.subTest(kind=kind), patch('migration.set_markdown') as write:
                issues = set()
                write_markdown_with_embeds('api', 'space', 'page', markdown, [], issues)
                write.assert_called_once_with('api', 'space', 'page', markdown)
                self.assertEqual(issues, set())

    def test_embed_placeholder_becomes_a_native_embed_without_iframe_source(self):
        with patch('migration.set_markdown') as write:
            issues = set()
            write_markdown_with_embeds('api', 's', 'p', 'ANYTWO_NATIVE_EMBED_0000_PLACEHOLDER',
                                       [{'url': 'https://youtu.be/LMXMbeKyneQ'}], issues)
        content = write.call_args.args[-1]
        self.assertIn('"kind":"embed"', content)
        self.assertNotIn('PLACEHOLDER', content)
        self.assertNotIn('<iframe', content)
        self.assertFalse(issues)

    def test_unsupported_embed_keeps_its_url_and_reports_the_adaptation(self):
        with patch('migration.set_markdown') as write:
            issues = set()
            write_markdown_with_embeds('api', 's', 'p', 'ANYTWO_NATIVE_EMBED_0000_PLACEHOLDER',
                                       [{'url': 'https://example.org/video'}], issues)
        self.assertIn('https://example.org/video', write.call_args.args[-1])
        self.assertNotIn('any:block', write.call_args.args[-1])
        self.assertTrue(issues)

    def test_write_failure_is_not_hidden_by_a_successful_plain_text_retry(self):
        from api_clients import APIError
        with patch('migration.set_markdown', side_effect=APIError('rejected')) as write:
            with self.assertRaises(APIError):
                write_markdown_with_embeds('api', 's', 'p', samples()['inline-view'], [], set())
        self.assertEqual(write.call_count, 1)
