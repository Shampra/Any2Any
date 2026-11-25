"""Staged regression suite, copied to the actual project by the update script."""
import json
import unittest
from unittest.mock import patch

from api_clients import APIError, Anytype, anytype_property_definitions
from migration import (Engine, render_blocks, declared_column_shape, declared_properties, slug,
                       custom_properties, import_artifacts, internal_record_property, mapped_relation,
                       relation_references, write_markdown_with_embeds)
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
                    {'property':'Status','condition':'unknown'},
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
        # A technical dataview host has no name in the native client. Naming it
        # makes it appear as an unrelated document in the content browser.
        self.assertNotIn('any',calls[0][1]['initialProperties'])
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

    def test_mention_tags_become_native_object_links(self):
        issues=set()
        doc={'blocks':[{'type':'paragraph',
            'text':'The <mention object_id="a">Magic 8 ball</mention> of it all, '
                   "then <mention objectId='b'>Tom &amp; Jerry</mention>."}]}
        result=render_blocks(doc,{'a':'new-a','b':'new-b'},'s',{'a':'Magic 8 ball','b':'Tom & Jerry'},
                             False,None,issues)
        self.assertIn('[Magic 8 ball](any://o/s/new-a)',result)
        self.assertIn('[Tom & Jerry](any://o/s/new-b)',result)
        self.assertNotIn('<mention',result)
        self.assertFalse(issues)

    def test_mentions_in_table_cells_and_compound_checkboxes(self):
        doc={'blocks':[{'type':'table','rows':[{'cells':[
            {'blocks':[{'type':'paragraph','text':'See <mention object_id="a">Alpha</mention>'}]},
            {'type':'checkbox','checked':True,'text':'Check <mention object_id="a">Alpha</mention>'}]}]}]}
        result=render_blocks(doc,{'a':'new-a'},'s',{'a':'Alpha'},False,None,set())
        self.assertEqual(result.count('<a href="any://o/s/new-a">Alpha</a>'),2)
        self.assertNotIn('<mention',result)

    def test_unmapped_and_empty_label_mentions(self):
        issues=set()
        result=render_blocks({'blocks':[{'type':'paragraph',
            'text':'Ask <mention object_id="gone">Former name</mention>.'}]},
            {},'s',{'gone':'Current name'},False,None,issues)
        self.assertEqual(result,'Ask Former name.')
        self.assertIn('Mention vers un objet non importé',issues)
        result=render_blocks({'blocks':[{'type':'paragraph',
            'text':'See <mention object_id="x"></mention>.'}]},
            {'x':'new-x'},'s',{'x':'Known name'},False,None,set())
        self.assertIn('[Known name](any://o/s/new-x)',result)

    def test_date_less_filter_is_refused_when_empty_semantics_differ(self):
        with self.assertRaises(UnsupportedView):
            self.converter.predicate({'property':'Date','condition':'less','value':'2026-10-29'})

    def test_option_vocabulary_loaded_with_colors(self):
        with patch('api_clients.paginated',side_effect=[
                [{'id':'status','key':'state','name':'État','format':'select'}],
                [{'id':'tag','name':'Ready','color':'teal'}]]):
            result=anytype_property_definitions(Anytype(1,'key'),'s')
        self.assertEqual(result['state']['options'][0]['color'],'teal')


class ImportArtifactTests(unittest.TestCase):
    """Anytype record bookkeeping must never become an Anytwo column."""

    def test_bookkeeping_keys_are_recognized_by_identifier(self):
        for key in ('source_object','template_name_prefill_type',
                    'import_type','cover_x','set_of'):
            with self.subTest(key=key):
                self.assertTrue(internal_record_property(key))
        # A user property key is an id; a similar label is still user data.
        self.assertFalse(internal_record_property('660578238cec08068e66a674'))
        self.assertFalse(internal_record_property(''))
        # The template_ prefix is never a system signal: a custom property
        # whose key merely starts with template_ is user data.
        self.assertFalse(internal_record_property('template_notes'))
        self.assertFalse(internal_record_property('template_anything'))

    def test_custom_properties_drop_bookkeeping_and_keep_user_values(self):
        doc={'properties':{'name':'Kitty','source_object':['bafy-x'],
                           'template_name_prefill_type':1,'stars':['bafy-y']}}
        self.assertEqual(custom_properties(doc),{'stars':['bafy-y']})

    def test_type_schema_ignores_bookkeeping_definitions(self):
        result=declared_properties({'property_definitions':[
            {'property':'source_object','name':'Source object','format':'objects'},
            {'property':'template_name_prefill_type','name':'template_name_prefill_type','format':'number'},
            {'property':'abc123','name':'Mood','format':'select'}]}, {})
        self.assertEqual([x['name'] for x in result],['Mood'])

    def test_artifact_labels_use_the_source_vocabulary(self):
        doc={'properties':{'source_object':['bafy-x'],'template_name_prefill_type':1,'stars':['bafy-y']},
             'property_internal_keys':{}}
        vocabulary={'source_object':{'name':'Source object','format':'objects'}}
        self.assertEqual(import_artifacts(doc,vocabulary),
                         {'Source object':'source_object',
                          'template_name_prefill_type':'template_name_prefill_type'})

    def test_engine_skips_artifact_columns_and_preserves_homonymous_leftovers(self):
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Kitty','source_object':['bafy-x'],
                                      'template_name_prefill_type':1,'stars':['k']},
                        'blocks':[{'type':'paragraph','text':'Body'}]}
        kitty={'id':'k','name':'Kitty','type':'character'}
        inventory={'all':[kitty],'objects':[kitty],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'type-character','key':'character','name':'Characters','items':[kitty]}],
                   'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        vocabulary={'source_object':{'name':'Source object','format':'objects'},
                    'template_name_prefill_type':{'format':'number'},
                    'stars':{'name':'Player','format':'objects'}}
        created=[]; target=object()
        def add_column(target,sid,cid,name,xkey,kind,fmt):
            created.append(name)
            return 'prop-'+name
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',return_value='new-k'),\
             patch('migration.anytype_property_definitions',return_value=vocabulary),\
             patch('migration.list_columns',return_value=[{'id':'p1','name':'Source object'}]),\
             patch('migration.add_column',side_effect=add_column),\
             patch('migration.set_column_value'),\
             patch('migration.set_markdown'),\
             patch('migration.delete_column') as delete:
            events=list(Engine(Source(),target,inventory,plan).run())
        summary=events[-1]
        self.assertNotIn('Source object',created)
        self.assertNotIn('template_name_prefill_type',created)
        self.assertIn('Player',created)
        # A homonymous leftover column is never deleted by display name.
        delete.assert_not_called()
        self.assertNotIn('removed_properties',summary)

    def test_custom_properties_keep_a_template_prefixed_user_key(self):
        doc={'properties':{'name':'Kitty','template_notes':'A user note',
                           'template_name_prefill_type':1}}
        self.assertEqual(custom_properties(doc, {}),
                         {'template_notes':'A user note'})

    def test_custom_label_with_custom_identity_is_not_a_system_property(self):
        doc={'properties':{'Source object':['bafy-x'],'notes':'A note'},
             'property_internal_keys':{'Source object':'660578238cec08068e66a674'}}
        self.assertEqual(custom_properties(doc, {}),
                         {'Source object':['bafy-x'],'notes':'A note'})

    def test_system_identity_under_a_custom_label_is_excluded(self):
        doc={'properties':{'Prefill':1,'notes':'A note'},
             'property_internal_keys':{'Prefill':'template_name_prefill_type'}}
        self.assertEqual(custom_properties(doc, {}), {'notes':'A note'})
        self.assertEqual(import_artifacts(doc),
                         {'template_name_prefill_type':'template_name_prefill_type'})

    def test_declared_properties_keep_a_custom_identity_with_a_system_like_label(self):
        result=declared_properties({'property_definitions':[
            {'property':'abc123','name':'Source object','format':'text'},
            {'property':'source_object','name':'Source object','format':'objects'}]}, {})
        self.assertEqual([x['key'] for x in result], ['abc123'])

    def test_label_keyed_property_is_kept_when_the_vocabulary_describes_a_custom_entry(self):
        # No alias map: the document keys the property by its label.
        doc={'properties':{'Source object':['bafy-x']}}
        vocabulary={'source object':{'name':'Source object','key':'abc123','format':'objects'}}
        self.assertEqual(custom_properties(doc,vocabulary),{'Source object':['bafy-x']})

    def test_label_keyed_system_property_is_still_dropped(self):
        doc={'properties':{'Source object':['bafy-x']}}
        vocabulary={'source object':{'name':'Source object','key':'source_object','format':'objects',
                                     'hidden':True}}
        self.assertEqual(custom_properties(doc,vocabulary),{})

    def test_cleanup_compares_identities_exactly(self):
        from migration import Engine
        engine=Engine.__new__(Engine)
        engine.target=object(); engine.dest_sid='dest'
        engine.created_columns=[
            {'source_key':'source-object','collection_id':'c1','property_id':'p-dash','label':'Source object'}]
        engine.report={}
        with patch('migration.delete_column') as delete:
            engine.remove_import_artifacts([{'properties':{'source_object':['x']}}], {})
        delete.assert_not_called()

    def test_artifact_cleanup_only_deletes_tracked_system_columns(self):
        # A user column labelled like a system field must survive cleanup.
        from migration import Engine
        engine=Engine.__new__(Engine)
        engine.target=object(); engine.dest_sid='dest'
        engine.created_columns=[
            {'source_key':'abc123','collection_id':'c1','property_id':'p-user','label':'Source object'},
            {'source_key':'source_object','collection_id':'c1','property_id':'p-sys','label':'Source object'}]
        engine.report={}
        docs=[{'properties':{'source_object':['x']}}]
        vocabulary={'source_object':{'name':'Source object','format':'objects'}}
        with patch('migration.delete_column') as delete:
            removed=engine.remove_import_artifacts(docs, vocabulary)
        delete.assert_called_once_with(engine.target,'dest','c1','p-sys')
        self.assertEqual(removed,[{'name':'Source object','collection_id':'c1','property_id':'p-sys'}])

    def test_property_tracks_the_source_identity_end_to_end(self):
        from migration import Engine
        engine=Engine.__new__(Engine)
        engine.target=object(); engine.dest_sid='dest'
        engine.prop_cache={}; engine.col_cache={}; engine.created_columns=[]
        engine.inv={'types':[]}; engine.report={}
        with patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',return_value='p1'),\
             patch('migration.delete_column') as delete:
            pid,_=engine.property('c1','Source object','text','x',set(),{},
                                  source_key='source_object')
            removed=engine.remove_import_artifacts(
                [{'properties':{'source_object':['x']}}],
                {'source_object':{'name':'Source object','format':'objects'}})
        self.assertEqual(pid,'p1')
        self.assertEqual(engine.created_columns[0]['source_key'],'source_object')
        delete.assert_called_once_with(engine.target,'dest','c1','p1')
        self.assertEqual(removed[0]['property_id'],'p1')

    def test_property_without_a_source_identity_is_not_tracked_for_cleanup(self):
        from migration import Engine
        engine=Engine.__new__(Engine)
        engine.target=object(); engine.dest_sid='dest'
        engine.prop_cache={}; engine.col_cache={}; engine.created_columns=[]
        engine.inv={'types':[]}
        with patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',return_value='p1'):
            engine.property('c1','Source object','text','x',set(),{})
        self.assertEqual(engine.created_columns,[])

    def test_engine_call_sites_never_track_a_display_label(self):
        # A user property with no source identity must be created but not
        # tracked under its label; with an identity it must track that identity.
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Kitty','Notes':'A note'},
                        'blocks':[{'type':'paragraph','text':'Body'}]}
        kitty={'id':'k','name':'Kitty','type':'character'}
        inventory={'all':[kitty],'objects':[kitty],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'type-character','key':'character','name':'Characters','items':[kitty]}],
                   'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        created=[]
        def add_column(target,sid,cid,name,xkey,kind,fmt):
            created.append(name);return 'prop-'+name
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',return_value='new-k'),\
             patch('migration.anytype_property_definitions',return_value={'notes':{'name':'Notes','format':'text'}}),\
             patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',side_effect=add_column),\
             patch('migration.set_column_value'),\
             patch('migration.set_markdown'),\
             patch('migration.delete_column') as delete:
            engine=Engine(Source(),object(),inventory,plan)
            list(engine.run())
        self.assertIn('Notes',created)
        # Without a resolved identity the column is created but never tracked,
        # so a label can never become a cleanup identity.
        self.assertEqual(engine.created_columns,[])
        delete.assert_not_called()

    def test_engine_tracks_a_resolved_property_identity(self):
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Kitty','Notes':'A note'},
                        'blocks':[{'type':'paragraph','text':'Body'}]}
        kitty={'id':'k','name':'Kitty','type':'character'}
        inventory={'all':[kitty],'objects':[kitty],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'type-character','key':'character','name':'Characters','items':[kitty]}],
                   'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',return_value='new-k'),\
             patch('migration.anytype_property_definitions',
                   return_value={'notes':{'name':'Notes','key':'abc123','format':'text'}}),\
             patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',return_value='prop-Notes'),\
             patch('migration.set_column_value'),\
             patch('migration.set_markdown'),\
             patch('migration.delete_column') as delete:
            engine=Engine(Source(),object(),inventory,plan)
            list(engine.run())
        self.assertEqual([row['source_key'] for row in engine.created_columns],['abc123'])
        delete.assert_not_called()

    def test_untranslated_template_settings_are_reported(self):
        from migration import Engine
        engine=Engine.__new__(Engine)
        engine.target=object(); engine.dest_sid='dest'
        engine.created_columns=[]; engine.report={}
        engine.remove_import_artifacts(
            [{'properties':{'template_name_prefill_type':1,'default_template_id':'x'}}], {})
        reported=engine.report['template_settings_not_translated']
        self.assertIn('template_name_prefill_type',reported)
        self.assertIn('default_template_id',reported)

    def test_empty_url_and_relative_url_values_do_not_fail_the_page(self):
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Trinket','source':''},
                        'blocks':[{'type':'paragraph','text':'Body'}]}
        trinket={'id':'t','name':'Trinket','type':'character'}
        inventory={'all':[trinket],'objects':[trinket],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'type-character','key':'character','name':'Characters','items':[trinket]}],
                   'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        created=[]
        def add_column(target,sid,cid,name,xkey,kind,fmt):
            created.append(name); return 'prop-'+name
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',return_value='new-t'),\
             patch('migration.anytype_property_definitions',return_value={'source':{'name':'Source','format':'url'}}),\
             patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',side_effect=add_column),\
             patch('migration.set_column_value') as set_value,\
             patch('migration.set_markdown'):
            events=list(Engine(Source(),object(),inventory,plan).run())
        summary=[event for event in events if event['event']=='summary'][-1]
        self.assertNotIn('Source',created)
        set_value.assert_not_called()
        self.assertEqual(summary['objects'][0]['errors'],[])
        self.assertIn('Valeur vide ignorée pour la propriété « Source »',summary['objects'][0]['issues'])


    def test_relation_values_are_native_uri_arrays(self):
        mapping={'a':'target-a','b':'target-b'}
        self.assertEqual(mapped_relation(['a','b'],mapping),['any://target-a','any://target-b'])
        self.assertEqual(mapped_relation('a',mapping),['any://target-a'])
        # A single unmapped reference keeps the page usable: no relation array.
        self.assertIsNone(mapped_relation(['a','gone'],mapping))
        self.assertIsNone(mapped_relation([],mapping))
        self.assertIsNone(mapped_relation('gone',mapping))


    def test_stored_relation_values_are_normalized_before_writing(self):
        mapping={'a':'target-a'}
        self.assertEqual(relation_references('any://target-a',mapping),['any://target-a'])
        self.assertEqual(relation_references('a',mapping),['any://target-a'])
        # A JSON list of raw ids is what an unmapped relation leaves in the report.
        self.assertEqual(relation_references('["a"]',mapping),['any://target-a'])
        self.assertIsNone(relation_references('["gone"]',mapping))
        self.assertIsNone(relation_references([],mapping))
        self.assertIsNone(relation_references(['a',None],mapping))


    def test_engine_preserves_native_toggle_on_current_server(self):
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Toggled'},
                        'blocks':[{'type':'toggle','text':'Secret stash'},
                                  {'type':'paragraph','indent':1,'text':'Hidden note'}]}
        page={'id':'t','name':'Toggled','type':'character'}
        inventory={'all':[page],'objects':[page],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'type-character','key':'character','name':'Characters','items':[page]}],
                   'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        written=[]
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',return_value='new-t'),\
             patch('migration.anytype_property_definitions',return_value={}),\
             patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',return_value='prop'),\
             patch('migration.set_markdown',side_effect=lambda *a: written.append(a[-1])),\
             patch('anytwo_backend.server_version',return_value=(0,5,0)):
            events=list(Engine(Source(),object(),inventory,plan).run())
        self.assertTrue(written)
        self.assertIn('<!-- any:collapsible {"open":false} -->', written[0])
        self.assertIn('<!-- any:collapsible-content -->', written[0])
        self.assertIn('Hidden note', written[0])
        self.assertFalse(any('marqueurs de mise en page' in str(e.get('message','')) for e in events))

    def _relation_columns(self, adventure):
        class Source:
            def object_detail(self, sid, oid):
                return {'properties':{'name':'Sigil','adventure':adventure},
                        'blocks':[{'type':'paragraph','text':'Body'}]}
        item={'id':'i','name':'Sigil','type':'character'}
        other={'id':'0','name':'Other','type':'character'}
        inventory={'all':[item,other],'objects':[item,other],'collections':[],'members':{},'standalone':[],
                   'types':[{'id':'t','key':'character','name':'Characters','items':[item,other]}],'stats':{}}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'space'},
              'target':{'space_mode':'create','space_name':'Dest','collection_mode':'none','type_mappings':[]},
              'mode':'simple','follow_links':False,'files':False}
        created=[]; written=[]; ids=iter(['new-i','new-0'])
        def add_column(target,sid,cid,name,xkey,kind,fmt):
            created.append((name,kind,(fmt or {}).get('type')))
            return 'prop-'+name
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',side_effect=lambda *a, **k: next(ids)),\
             patch('migration.anytype_property_definitions',
                   return_value={'adventure':{'name':'Mystery','format':'objects'}}),\
             patch('migration.list_columns',return_value=[]),\
             patch('migration.add_column',side_effect=add_column),\
             patch('migration.set_column_value',side_effect=lambda *a: written.append(a[-1])),\
             patch('migration.set_markdown'):
            list(Engine(Source(),object(),inventory,plan).run())
        return created,written

    def test_unmapped_relation_does_not_create_a_text_duplicate(self):
        created,written=self._relation_columns(['gone'])
        self.assertFalse(any('(Anytype)' in name for name,_,_ in created))
        # Every target is missing: no column and no value are created at all.
        self.assertEqual(created,[])
        self.assertEqual(written,[])

    def test_partially_mapped_relation_keeps_only_imported_targets(self):
        created,written=self._relation_columns(['0', 'gone'])
        self.assertFalse(any('(Anytype)' in name for name,_,_ in created))
        self.assertIn(('Mystery','array','relation'),created)
        # Only the imported target survives; the unknown reference is dropped.
        self.assertTrue(written)
        self.assertTrue(all(v==['any://new-0'] for v in written), written)



if __name__=='__main__':unittest.main()