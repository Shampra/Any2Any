"""Staged regression suite, copied to the actual project by the update script."""
import json
import unittest
from unittest.mock import patch

from api_clients import APIError, Anytype, anytype_property_definitions
from migration import Engine, render_blocks, declared_column_shape, declared_properties, slug
from view_conversion import (ViewConverter, UnsupportedView, enrich_descriptor,
                             create_saved_views, modify_records)


class FidelityTests(unittest.TestCase):
    def setUp(self):
        self.form=declared_column_shape({'format':'select','options':[{'name':'À faire','color':'ice'},'Fini']})[1]
        self.converter=ViewConverter({
            'score':[('books.score',{'format':'number'},{'type':'number'})],
            'status':[('books.status',{'format':'select'},self.form)],
            'related':[('books.related',{'format':'objects'},{'type':'relation'})],
            'date':[('books.date',{'format':'date'},{'type':'date'})]},
            {'a':'new-a','b':'new-b'},{'book':'books'}, {})

    def test_unused_options_colors_strings_and_order(self):
        self.assertEqual([v['name'] for v in self.form['options'].values()],['À faire','Fini'])
        self.assertEqual(self.form['options'][slug('À faire','À faire')]['color'],'ice')
        self.assertLess(*[v['pos'] for v in self.form['options'].values()])

    def test_property_settings_are_not_discarded_or_claimed_enforced(self):
        spec={'name':'Lien','format':'objects','max_count':1,'readonly':True,'default_value':[],'description':'Explication'}
        issues=set(); form=enrich_descriptor(spec,{'type':'relation','config':{'multiple':True}},issues)
        self.assertFalse(form['config']['multiple'])
        self.assertTrue(json.loads(form['any2any']['sourceSettings'])['readonly'])
        self.assertTrue(any('readonly' in x and 'non appliqué' in x for x in issues))

    def test_type_definition_preserves_settings(self):
        result=declared_properties({'property_definitions':[{'property':'Date','format':'date','include_time':True,'description':'When'}]}, {})
        self.assertTrue(result[0]['include_time'])
        self.assertEqual(result[0]['description'],'When')

    def test_date_time_setting(self):
        self.assertEqual(enrich_descriptor({'format':'date','include_time':True},{'type':'date'})['type'],'datetime')

    def test_nested_filter_false_zero_and_or(self):
        rule=self.converter.predicate({'operator':'or','filters':[
            {'property':'Score','condition':'equal','value':0},
            {'property':'Score','condition':'greater','value':5}]})
        self.assertEqual(rule['$or'][0]['$and'][1],{'books.score':{'$eq':0}})
        self.assertEqual(self.converter.predicate({'operator':'or','filters':[]}),{'$or':[]})
        self.assertEqual(self.converter.predicate({'operator':'and','filters':[]}),{'$and':[]})

    def test_select_filter_rewrites_option_names(self):
        rule=self.converter.predicate({'property':'Status','condition':'in','value':['À faire']})
        self.assertEqual(rule['$and'][1]['books.status']['$in'],[slug('À faire','À faire')])

    def test_unknown_filter_refuses_entire_view(self):
        for bad in ({'property':'Unknown','condition':'equal','value':1},
                    {'property':'Date','condition':'equal','date_preset':'today'},
                    {'property':'Status','condition':'empty'},
                    {'property':'Related','condition':'in','value':['missing']}):
            with self.subTest(bad=bad),self.assertRaises(UnsupportedView):
                self.converter.convert({'filters':[bad]}, {'id':{'$in':['new-a']}})

    def test_collection_source_never_widens_to_all_objects(self):
        result=self.converter.query({'is_collection':True},{'collection_items':['a','excluded']},[])
        self.assertEqual(result,{'id':{'$in':['new-a']}})
        self.assertEqual(self.converter.query({'is_collection':True},{},[]),{'id':{'$in':[]}})

    def test_empty_query_source_is_not_collection_fallback(self):
        result=self.converter.query({}, {'query_source':{},'collection_items':['a']},['a'])
        self.assertEqual(result,{'id':{'$in':[]}})

    def test_type_source_remaps_collection(self):
        self.assertEqual(self.converter.query({}, {'query_source':{'types':['type-book']}},[]),{'any.collections':'books'})

    def test_sort_and_group_remap_property_ids(self):
        layout,query,settings=self.converter.convert({'type':'kanban','group_by':'Status',
            'sorts':[{'property':'Score','direction':'desc'}],'columns':[{'property':'Score','width':180}]}, {'any.collections':'books'})
        self.assertEqual(layout,'board'); self.assertEqual(query['sort'],['-books.score','id'])
        self.assertEqual(query['groupBy'],'books.status')
        self.assertEqual(json.loads(settings['any2any']['sourceView'])['columns'][0]['width'],180)

    def test_multiple_property_owners_cannot_match_negation_through_absence(self):
        self.converter.bindings['score'].append(('other.p',{'format':'number'},{}))
        rule=self.converter.predicate({'property':'Score','condition':'not_equal','value':0})
        self.assertEqual(rule['$or'][1]['$and'][0],{'any.collections':'other'})
        with self.assertRaises(UnsupportedView):self.converter.convert({'sorts':[{'property':'Score'}]}, {})

    def test_partial_modify_response_is_a_failure(self):
        with patch('view_conversion.target_write',return_value={'rejections':[{'reason':'bad field'}]}):
            with self.assertRaises(APIError):modify_records(None,'s','o','views',[{'id':'v','name':'N'}])

    def test_saved_view_uses_native_api_and_complete_source_scope(self):
        issues=set(); calls=[]
        def write(api,path,body):
            calls.append((path,body));return {'objectId':'view-root'} if path.endswith('/objects') else {'recordIds':['row']}
        with patch('view_conversion.target_write',side_effect=write):
            root,failed=create_saved_views(None,'dest','page',{'is_collection':True,'views':[{'filters':[{'property':'Score','condition':'greater','value':0}]}]}, {'collection_items':['a']},[],self.converter,issues)
        self.assertEqual(root,'view-root'); self.assertFalse(failed)
        self.assertEqual(calls[0][1]['initialProperties']['dataview']['host'],'page')
        fields={op['path']:op['value'] for op in calls[2][1]['records'][0]['ops']}
        self.assertEqual(fields['query']['filter']['$and'][0],{'id':{'$in':['new-a']}})
        self.assertTrue(any('rendu' in x for x in issues))

    def test_reuses_root_without_overwriting_other_tables(self):
        with patch('view_conversion.target_write',return_value={}) as write:
            create_saved_views(None,'s','page',{'is_collection':True,'views':[{}]}, {},[],self.converter,set(),root_id='root',table_key='second')
        self.assertEqual(write.call_count,2)
        self.assertEqual(write.call_args.args[2]['records'][0]['id'],'second-view-0')

    def test_unconvertible_view_makes_no_writes(self):
        with patch('view_conversion.target_write') as write:
            with self.assertRaises(UnsupportedView):create_saved_views(None,'s','p',{'views':[{'filters':[{'property':'bad','condition':'equal','value':1}]}]}, {'query_source':{}},[],self.converter,set())
            write.assert_not_called()

    def test_columns_keep_nested_media_links_code_and_unknown_blocks(self):
        blocks=[{'type':'row'},{'type':'column','indent':1,'fields':{'width':.4}},
            {'type':'image','indent':2,'object_id':'img','name':'photo.png'},
            {'type':'code','indent':2,'text':'<keep>\n  indented','language':'python'},
            {'type':'column','indent':1,'fields':{'width':.6}},
            {'type':'paragraph','indent':2,'text':'[Link](anytype://object?objectId=a)'},
            {'type':'unknown','indent':2,'payload':{'important':'yes'}},
            {'type':'paragraph','text':'AFTER'}]
        issues=set(); imports=[]
        def load(*args):imports.append(args);return 'any://f/s/image'
        result=render_blocks({'blocks':blocks},{'a':'new-a'},'s',{},True,load,issues)
        self.assertEqual(len(imports),1);self.assertIn('any://f/s/image',result)
        self.assertIn('<keep>',result); self.assertIn('any://o/s/new-a',result)
        self.assertIn('important',result);self.assertIn('AFTER',result)
        self.assertEqual(result.count('<!-- any:columns '),1)

    def test_nested_columns_do_not_duplicate_inner_column(self):
        blocks=[{'type':'row'}, {'type':'column','indent':1}, {'type':'row','indent':2},
            {'type':'column','indent':3},{'type':'paragraph','indent':4,'text':'UNIQUE'},
            {'type':'column','indent':3},{'type':'paragraph','indent':4,'text':'INNER RIGHT'},
            {'type':'column','indent':1},{'type':'paragraph','indent':2,'text':'RIGHT'}]
        result=render_blocks({'blocks':blocks},{},'s',{},False,None,set())
        self.assertEqual(result.count('UNIQUE'),1);self.assertEqual(result.count('<!-- any:columns '),2)

    def test_table_cell_links_are_rewritten_inside_columns(self):
        doc={'blocks':[{'type':'row'},{'type':'column','indent':1},
            {'type':'table','indent':2,'rows':[{'cells':[{'blocks':[{'type':'paragraph','text':'[A](anytype://object?objectId=a)'}]}]}]}]}
        result=render_blocks(doc,{'a':'new-a'},'s',{},False,None,set())
        self.assertIn('any://o/s/new-a',result);self.assertNotIn('anytype://',result)

    def test_simple_table_fallback_keeps_compound_cells_and_false_values(self):
        doc={'blocks':[{'type':'table','rows':[{'cells':[
            {'blocks':[{'type':'paragraph','text':'[A](anytype://object?objectId=a)'}]},
            {'value':False}, {'value':0}]}]}]}
        result=render_blocks(doc,{'a':'new-a'},'s',{},False,None,set(),rich_mode=False)
        self.assertIn('any://o/s/new-a',result)
        self.assertIn('False',result)
        self.assertIn('0',result)

    def test_date_less_filter_is_refused_when_empty_semantics_differ(self):
        with self.assertRaises(UnsupportedView):
            self.converter.predicate({'property':'Date','condition':'less','value':'2026-10-29'})

    def test_option_vocabulary_loaded_with_colors(self):
        with patch('api_clients.paginated',side_effect=[
                [{'id':'status','key':'state','name':'État','format':'select'}],
                [{'id':'tag','name':'Ready','color':'teal'}]]):
            result=anytype_property_definitions(Anytype(1,'key'),'s')
        self.assertEqual(result['state']['options'][0]['color'],'teal')


if __name__=='__main__':unittest.main()
