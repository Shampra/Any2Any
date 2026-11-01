from copy import deepcopy
import json
import unittest
from unittest.mock import Mock,patch
from notion_demo import DemoNotion,ROOT,DB,SOURCE,PAGE,SCHEMA,rich
from notion_migration import Engine
from notion_content import Content
from notion_views import normalise,converter
from notion_icons import emoji,content_icon
from inline_views import inline_records
from view_conversion import UnsupportedView,create_saved_views

class LinkedViewTests(unittest.TestCase):
    def engine(self):
        schema=deepcopy(SCHEMA)
        e=Engine(DemoNotion(),Mock(),{'pages':{ROOT:DemoNotion().page(ROOT)},'schemas':{SOURCE:schema}},
                 {'files':False,'links':False,'destination':{'id':'space'}})
        e.sid='space';e.mapping={ROOT:'page'};e.collections={SOURCE:'collection'};e.results={ROOT:{'source_id':ROOT,'status':'pending','issues':set()}}
        e.names={ROOT:'Page'};e.props[(SOURCE,'state')]=('state','array',{'type':'choice','options':{'todo':{'name':'À faire'}}})
        e.databases={DB:{'id':DB,'title':rich('Linked database'),'is_inline':True,'data_sources':[]}}
        e.views={DB:[{'id':'view','name':'Subset','data_source_id':SOURCE,'type':'table','quick_filters':{'state':{'status':{'equals':'À faire'}}},'configuration':{'properties':[{'property_id':'title','visible':True},{'property_id':'deleted','visible':True}]}}]}
        return e

    def test_linked_database_without_owned_sources_uses_its_own_views(self):
        e=self.engine()
        with patch('notion_migration.backend.target_write',return_value={'objectId':'host'}),patch('notion_migration.modify_records') as write:
            content=e.database_content(ROOT,DB)
        self.assertIn('"kind":"inline-view"',content)
        rows=write.call_args_list[-1].args[-1];self.assertEqual(rows[0]['name'],'Subset')
        self.assertTrue(rows[0]['query']['anyUi']['filters']);self.assertIn('todo',str(rows[0]['query']))

    def test_collect_resolves_linked_view_schema_without_importing_external_members(self):
        e=self.engine();e.schemas={}
        original=e.source.database
        e.source.database=lambda did:{**original(did),'data_sources':[]} if did==DB else original(did)
        e.source.views=lambda did:[{'id':'v','type':'table','data_source_id':SOURCE}] if did==DB else []
        e.source.selection=Mock(side_effect=AssertionError('external members must remain outside selection'))
        e.collect()
        self.assertIn(SOURCE,e.schemas);self.assertEqual(set(e.pages),{ROOT})
        e.source.selection.assert_not_called()

    def test_full_page_database_stays_linked_without_creating_view(self):
        e=self.engine();e.databases[DB]['is_inline']=False
        with patch('notion_migration.backend.target_write',side_effect=AssertionError('must stay a link')):
            content=e.database_content(ROOT,DB)
        self.assertIn('(any://o/space/collection)',content);self.assertNotIn('inline-view',content)

    def test_empty_callout_title_does_not_add_an_empty_paragraph(self):
        e=self.engine();e.blocks['callout']=[{'id':'heading','type':'heading_2','heading_2':{'rich_text':rich('Heading')}}]
        md=Content(e,ROOT).render([{'id':'callout','type':'callout','has_children':True,'callout':{'rich_text':[],'icon':{'type':'icon','icon':{'name':'pot'}}}}])
        self.assertIn('-->\n\n## Heading',md);self.assertNotIn('-->\n\n\n',md)
        self.assertIn('🍲',md)

    def test_seven_views_survive_deleted_column_and_preserve_quick_filters(self):
        e=self.engine();e.schemas[SOURCE]['parent']={'database_id':DB}
        e.views[DB]=[{**deepcopy(e.views[DB][0]),'id':str(i),'name':'View '+str(i)} for i in range(7)]
        block=e.view_block(SOURCE,set())
        with patch('view_conversion.modify_records') as write:
            _,failed=create_saved_views(e.target,e.sid,'collection',block,{'type':'collection','collection_items':[]},[],converter(e,SOURCE),set(),root_id='host',table_key='default')
        self.assertFalse(failed);rows=write.call_args_list[-1].args[-1];self.assertEqual(len(rows),7)
        self.assertTrue(all(r['query']['anyUi']['filters'] for r in rows))

    def test_unsupported_first_collection_view_does_not_discard_other_views(self):
        e=self.engine();e.schemas[SOURCE]['parent']={'database_id':DB}
        e.views[DB].insert(0,{'id':'chart','type':'chart','name':'Unsupported chart','data_source_id':SOURCE})
        issues=set();block=e.view_block(SOURCE,issues)
        self.assertEqual(len(block['views']),1);self.assertEqual(block['views'][0]['name'],'Subset');self.assertTrue(issues)

    def test_missing_filter_property_still_fails_closed(self):
        view={'type':'table','quick_filters':{'deleted':{'number':{'equals':1}}}}
        with self.assertRaises(UnsupportedView):normalise(view,SCHEMA,set())

    def test_quick_select_list_is_flat_and_conjoined_with_main_filter(self):
        view={'type':'table','filter':{'property':'title','rich_text':{'equals':'Name'}},'quick_filters':{'state':{'status':{'equals':['À faire','Done']}},'title':{}}}
        result=normalise(view,SCHEMA)
        self.assertEqual(len(result['filters']),2);self.assertEqual(result['filters'][1]['value'],['À faire','Done'])

    def test_grouped_inline_view_is_adapted_without_losing_filter_or_sort(self):
        e=self.engine();view=deepcopy(e.views[DB][0]);view['type']='board';view['configuration']['group_by']={'property_id':'state'}
        view['sorts']=[{'property':'title','direction':'ascending'}];issues=set()
        result=normalise(view,SCHEMA,issues,inline=True);self.assertEqual(result['type'],'list');self.assertTrue(result['filters']);self.assertTrue(result['sorts']);self.assertTrue(issues)
        rows,_=inline_records(converter(e,SOURCE),{'views':[result]},'collection','instance',issues)
        self.assertTrue(rows[0]['query']['anyUi']['filters']);self.assertTrue(rows[0]['query']['anyUi']['sort'])

    def test_named_icons_map_without_guessing_arbitrary_images(self):
        self.assertEqual(emoji({'type':'icon','icon':{'name':'chef-hat'}}),'🧑‍🍳')
        self.assertEqual(emoji({'type':'external','external':{'url':'https://www.notion.so/icons/wine-bottle_red.svg'}}),'🍾')
        self.assertIsNone(emoji({'type':'external','external':{'url':'https://example.org/my-photo.png'}}))
        self.assertIsNone(emoji({'type':'icon','icon':{'name':'unmapped-built-in'}}))
        icon=content_icon({'type':'emoji','emoji':'🧑‍🍳'})
        self.assertEqual(json.loads(icon.removeprefix('icon:v2:'))['assignment']['grapheme'],'🧑‍🍳')

    def test_view_icons_are_written_to_inline_and_saved_views(self):
        e=self.engine();view=e.views[DB][0];view['icon']={'type':'emoji','emoji':'⭐'}
        converted=normalise(view,SCHEMA)
        rows,_=inline_records(converter(e,SOURCE),{'views':[converted]},'collection','instance',set())
        self.assertEqual(rows[0]['icon'],content_icon(view['icon']))
        with patch('view_conversion.modify_records') as write:
            create_saved_views(e.target,e.sid,'collection',{'is_collection':True,'views':[converted]}, {'type':'collection','collection_items':[]},[],converter(e,SOURCE),set(),root_id='host',table_key='default')
        self.assertEqual(write.call_args_list[-1].args[-1][0]['icon'],content_icon(view['icon']))

    def test_property_icon_is_in_the_descriptor(self):
        e=self.engine();prop={'id':'number','type':'number','number':{'format':'euro'},'icon':{'type':'icon','icon':{'name':'euro'}}}
        _,form=e.shape(SOURCE,'Price',prop)
        self.assertEqual(form['icon'],content_icon(prop['icon']))

    def test_collection_icon_and_composite_page_icon_are_native(self):
        e=self.engine();e.collections={};e.databases[DB]['data_sources']=[{'id':SOURCE}];e.databases[DB]['icon']={'type':'emoji','emoji':'🥃'}
        e.schemas[SOURCE]['parent']={'database_id':DB}
        with patch('notion_migration.backend.create_collection',return_value='collection'),patch('notion_migration.backend.add_column',return_value='prop'),patch('notion_migration.backend.target_write') as write:
            e.create_schema()
        self.assertEqual(write.call_args.args[2]['iconCid'],content_icon({'emoji':'🥃'}))

if __name__=='__main__':unittest.main()
