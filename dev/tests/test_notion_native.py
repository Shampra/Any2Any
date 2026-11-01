import json
import unittest
from unittest.mock import Mock,patch
from notion_content import Content,mark
from notion_native import caption_image,caption_text,envelope,prepare_synced,synced_block,finalise,patch_block


class NativeTests(unittest.TestCase):
    def engine(self):
        e=Mock();e.pages={'page':{},'other':{}};e.blocks={};e.mapping={'page':'target','other':'other-target'};e.sid='space';e.content_plans={}
        e.results={'page':{'issues':set(),'errors':[]},'other':{'issues':set(),'errors':[]}}
        e.report={}
        e.issues=lambda page:e.results[page]['issues'];e.names={};e.databases={};e.collections={};e.synced_sources={}
        return e
    def test_annotations_put_spaces_outside_markdown_markers(self):
        e=self.engine();c=Content(e,'page')
        result=c.rich([{'type':'text','text':{'content':'Gras '},'annotations':{'bold':True}},
                       {'type':'text','text':{'content':' Italique '},'annotations':{'italic':True}},
                       {'type':'text','text':{'content':'Barré '},'annotations':{'strikethrough':True}}])
        self.assertEqual(result,'**Gras**  *Italique* ~~Barré~~ ')
        self.assertEqual(mark('   ','**'),'   ')
    def test_callout_is_native_and_keeps_child_blocks(self):
        e=self.engine();e.blocks={'callout':[{'id':'child','type':'paragraph','paragraph':{'rich_text':[{'text':{'content':'Enfant'}}]}}]}
        result=Content(e,'page').render([{'id':'callout','type':'callout','has_children':True,'callout':{'icon':{'emoji':'💡'},'rich_text':[{'text':{'content':'Encadré'}}]}}])
        self.assertIn('<!-- any:callout {"icon":"💡"} -->',result);self.assertIn('Enfant',result);self.assertNotIn('> Encadré',result)
    def test_caption_belongs_to_image_extension_not_next_paragraph(self):
        encoded=caption_image('![Photo](any://f/space/file)','# Légende & lien https://example.com','target','image')
        self.assertIn('"kind":"image-caption"',encoded);self.assertIn('![Photo]',encoded)
        self.assertIn(r'\# Légende &amp; lien https'+'\u200c'+'://example.com',encoded)
        self.assertEqual(caption_text('un\n\n  deux  '),'un\n&#32;&#32;deux&#32;&#32;')
    def test_synced_original_and_reference_share_source_identity(self):
        e=self.engine();original={'id':'original','type':'synced_block','synced_block':{},'has_children':True}
        reference={'id':'reference','type':'synced_block','synced_block':{'synced_from':{'block_id':'original'}}}
        e.blocks={'page':[original],'other':[reference]};prepare_synced(e)
        plan={'synced':[]};first=synced_block(e,'page',original,'Corps',plan);second=synced_block(e,'other',reference,'Corps',plan)
        self.assertIn('"role":"source"',first);self.assertIn('"role":"reference"',second)
        self.assertEqual(plan['synced'][0]['original'],plan['synced'][1]['original'])
    def test_reference_without_selected_original_becomes_first_local_original(self):
        e=self.engine();block={'id':'copy','type':'synced_block','synced_block':{'synced_from':{'block_id':'outside'}}}
        e.blocks={'page':[block]};prepare_synced(e);plan={'synced':[]}
        self.assertIn('"role":"source"',synced_block(e,'page',block,'Texte',plan));self.assertTrue(e.issues('page'))
    def test_batch_block_id_colon_is_kept_in_the_native_patch_route(self):
        e=self.engine()
        with patch('notion_native.backend.target_write') as write:patch_block(e,'page','change:42',{'text':'Sommaire'})
        self.assertTrue(write.call_args.args[1].endswith('/blocks/change:42'))
    def test_finalise_uses_real_block_ids_for_toc_and_cross_page_sync(self):
        e=self.engine();e.content_plans={'page':{'headings':[{'source_id':'h','text':'Titre','label':'Titre','level':1}],
            'tocs':['TOC_TOKEN'],'synced':[{'original':'s','instance':'source-instance','role':'source'}]},
            'other':{'headings':[],'tocs':[],'synced':[{'original':'s','instance':'ref-instance','role':'reference'}]}}
        source=json.loads(envelope('synced-block','source-instance',{'role':'source'},'Texte').split('\n')[0][15:-4])
        ref={'v':1,'kind':'synced-block','schema':1,'instance':'ref-instance','data':{'role':'reference','ref':'pending'}}
        rows={'page':[{'id':'heading-id','type':'heading','text':'Titre','style':{'level':1}}, {'id':'toc-id','type':'paragraph','text':'TOC_TOKEN'},
             {'id':'original-id','type':'html','text':'<!-- any:block '+json.dumps(source,separators=(',',':'))+' -->'}],
             'other':[{'id':'reference-id','type':'html','text':'<!-- any:block '+json.dumps(ref,separators=(',',':'))+' -->'}]}
        with patch('notion_native.records',side_effect=lambda eng,page:rows[page]),patch('notion_native.patch_block') as write:
            finalise(e)
        toc=next(c.args[3]['text'] for c in write.call_args_list if c.args[2]=='toc-id')
        sync=next(c.args[3]['text'] for c in write.call_args_list if c.args[2]=='reference-id')
        self.assertIn('any://o/space/target/editor_blocks/heading-id',toc)
        self.assertIn('any://o/space/target/editor_blocks/original-id',sync)
        self.assertEqual(e.report['synced_blocks']['s']['block'],'original-id')


if __name__=='__main__':unittest.main()
