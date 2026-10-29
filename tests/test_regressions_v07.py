import unittest
from unittest.mock import patch

from api_clients import APIError
from migration import (bookmark_block_title, bookmark_block_url, render_blocks,
                       write_markdown_with_embeds)


class RegressionV07(unittest.TestCase):
    def test_table_inside_two_columns_is_no_longer_lost(self):
        blocks = [
            {'type': 'row', 'indent': 0},
            {'type': 'column', 'indent': 1},
            {'type': 'paragraph', 'indent': 2, 'text': 'Colonne 1'},
            {'type': 'column', 'indent': 1},
            {'type': 'paragraph', 'indent': 2, 'text': 'Table dans colonne 2'},
            {'type': 'table', 'indent': 2, 'rows': [
                {'cells': [{'text':'a'}, {'text':'b'}, {'text':'c'}]},
                {'cells': [{'text':'2'}, {'text':''}, {'text':''}]},
            ]},
        ]
        issues=set()
        out=render_blocks({'blocks':blocks},{},'space',{},False,lambda *_:None,issues)
        self.assertIn('Table dans colonne 2',out)
        self.assertIn('<td>a</td>',out)
        self.assertIn('<td>b</td>',out)
        self.assertIn('<td>2</td>',out)
        self.assertEqual(out.count('<table'),1)
        self.assertNotIn('Tableau dans une colonne non reconstructible',issues)

    def test_bookmark_title_is_resolved_from_linked_object(self):
        block={'type':'bookmark','object_id':'bookmark-object','url':'https://say.any.org/?board=improvements'}
        self.assertEqual(bookmark_block_url(block),'https://say.any.org/?board=improvements')
        self.assertEqual(bookmark_block_title(block,{'bookmark-object':'Feedback - Any'},block['url']), 'Feedback - Any')
        result=render_blocks({'blocks':[block]}, {}, 'sid', {'bookmark-object':'Feedback - Any'},False,lambda *_:None,set())
        self.assertIn('[Feedback - Any](https://say.any.org/?board=improvements)',result)
        self.assertNotIn('[https://say.any.org',result)

    def test_youtube_uses_native_envelope_in_document_order(self):
        issues=set(); native=[]
        md=render_blocks({'blocks':[
            {'type':'paragraph','text':'Avant'},
            {'type':'embed','processor':'youtube','url':'https://youtu.be/AbCdEfGhI01'},
            {'type':'paragraph','text':'Après'},
        ]},{},'s',{},False,None,issues,native_embeds=native)
        self.assertEqual(native,[])
        self.assertNotIn('<iframe',md)
        self.assertIn('"kind":"embed"',md)
        self.assertLess(md.index('Avant'),md.index('<!-- any:block '))
        self.assertLess(md.index('<!-- /any:block '),md.index('Après'))
        with patch('migration.set_markdown') as put, patch('migration.create_editor_block') as block:
            write_markdown_with_embeds(None,'s','o',md,native,issues)
        put.assert_called_once_with(None,'s','o',md)
        block.assert_not_called()

    def test_legacy_embed_marker_is_upgraded_without_html_block(self):
        with patch('migration.set_markdown') as put, patch('migration.create_editor_block') as block:
            write_markdown_with_embeds(None,'s','o','ANYTWO_NATIVE_EMBED_0000_PLACEHOLDER',
                [{'html':'<iframe></iframe>','url':'https://youtu.be/AbCdEfGhI01'}],set())
        content=put.call_args.args[-1]
        self.assertIn('"provider":"youtube"',content)
        self.assertNotIn('<iframe',content)
        self.assertNotIn('PLACEHOLDER',content)
        block.assert_not_called()


if __name__=='__main__': unittest.main()

class BookmarkHydrationTests(unittest.TestCase):
    def test_local_bookmark_object_metadata_is_used(self):
        from migration import hydrate_bookmark_blocks
        class Source:
            def object_detail(self,sid,oid):
                self.calls+=1
                return {'properties':{'name':'Feedback - Any','url':'https://say.any.org/?board=improvements'}}
        src=Source();src.calls=0
        doc={'blocks':[{'type':'bookmark','object_id':'unknown'}]}
        names={}
        converted=hydrate_bookmark_blocks(doc,src,'space',names)
        self.assertEqual(converted['blocks'][0]['title'],'Feedback - Any')
        self.assertEqual(converted['blocks'][0]['url'],'https://say.any.org/?board=improvements')
        self.assertEqual(names['unknown'],'Feedback - Any')
        self.assertEqual(src.calls,1)
