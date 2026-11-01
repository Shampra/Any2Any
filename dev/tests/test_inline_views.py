import json
import unittest
from collections import Counter
from unittest.mock import patch

from api_clients import APIError
from migration import discover_documents,render_blocks,Engine
from source_views import SourceViews
from inline_views import instance_id,inline_markdown,inline_records
from view_conversion import ViewConverter,UnsupportedView
from logic import simulate


class Source:
    def __init__(self):self.reads=Counter()
    def object_detail(self,sid,oid):
        self.reads[oid]+=1
        return {
            'a':{'blocks':[{'id':'inline','type':'dataview','object_id':'col',
                'views':[{'filters':[{'property':'Score','condition':'greater','value':4}]}]}]},
            'col':{'type':'collection','collection_items':['b','c'],'blocks':[
                {'id':'main','type':'dataview','is_collection':True,'views':[{}]}]},
            'b':{'properties':{'name':'B','Score':8},'blocks':[{'type':'link','object_id':'a'}]},
            'c':{'properties':{'name':'C','Score':1},'blocks':[]},
            'type-col':{'kind':'object_type','internal_key':'collection'},
            'type-book':{'kind':'object_type','internal_key':'book'},
        }[oid]


class InlineViewTests(unittest.TestCase):
    def setUp(self):
        self.a={'id':'a','name':'A','type':'page'}
        self.b={'id':'b','name':'B','type':'book'}
        self.c={'id':'c','name':'C','type':'book'}
        self.col={'id':'col','name':'Library','type':'collection'}
        self.inv={'all':[self.a,self.b,self.c,self.col], 'objects':[self.a,self.b,self.c],
            'collections':[self.col],'members':{'col':[self.b,self.c]},
            'types':[{'id':'book-type','key':'book','name':'Books','items':[self.b,self.c]}]}
        self.source=Source()
        self.converter=ViewConverter({'score':[('scope.p',{'format':'number'}, {'type':'number'})]},
            {'a':'new-a','b':'new-b'}, {},{})

    def test_follow_imports_only_matching_inline_documents_and_handles_cycles(self):
        reasons={'a':['Selected']}
        entries,docs,problems=discover_documents(self.source,'src',self.inv,[self.a],reasons,True)
        self.assertEqual(set(entries),{'a','b'})
        self.assertEqual(self.source.reads['b'],1)
        self.assertFalse(problems)
        self.assertIn('vue intégrée',reasons['b'][0])

    def test_unchecked_follow_does_not_import_inline_documents(self):
        entries,_,problems=discover_documents(self.source,'src',self.inv,[self.a],{},False)
        self.assertEqual(set(entries),{'a'})
        self.assertFalse(problems)
        self.assertEqual(self.source.reads['b'],0)

    def test_type_collection_query_resolves_collections_then_their_documents(self):
        resolver=SourceViews(self.source,'src',self.inv)
        doc={'blocks':[{'type':'dataview','object_id':'type-col'}]}
        resolver.docs['a']=doc
        entries,_,problems=discover_documents(self.source,'src',self.inv,[self.a],{},True,resolver)
        self.assertEqual(set(entries),{'a','col','b','c'})
        self.assertFalse(problems)

    def test_reference_target_kind_overrides_inline_collection_flag(self):
        resolver=SourceViews(self.source,'src',self.inv)
        _,ids,_=resolver.resolve({'type':'collection','collection_items':['a']},
            {'type':'dataview','object_id':'type-book','is_collection':True})
        self.assertEqual(ids,['b','c'])

    def test_empty_query_source_does_not_use_collection_items(self):
        resolver=SourceViews(self.source,'src',self.inv)
        _,ids,_=resolver.resolve({'query_source':{},'collection_items':['b']},{'type':'dataview'})
        self.assertEqual(ids,[])

    def test_unknown_filter_fails_discovery_expansion_explicitly(self):
        resolver=SourceViews(self.source,'src',self.inv)
        resolver.docs['a']={'blocks':[{'type':'dataview','object_id':'col','views':[
            {'filters':[{'property':'Score','condition':'unknown','value':4}]}]}]}
        entries,_,problems=discover_documents(self.source,'src',self.inv,[self.a],{},True,resolver)
        self.assertEqual(set(entries),{'a'})
        self.assertIn('non résolus',problems[0][1])

    def test_native_envelope_uses_page_host_and_matching_dataview_instance(self):
        instance=instance_id('new-page','block')
        markdown=inline_markdown('dest','new-page',instance,'View','scope')
        envelope=json.loads(markdown.split('-->')[0].removeprefix('<!-- any:block '))
        self.assertEqual(envelope['kind'],'inline-view')
        self.assertEqual(envelope['data'],{'space':'dest','host':'new-page','dataview':instance})
        self.assertEqual(envelope['instance'],instance)
        text=render_blocks({'blocks':[{'type':'paragraph','text':'BEFORE'},
            {'type':'any2any_inline_view','markdown':markdown},{'type':'paragraph','text':'AFTER'}]},
            {},'dest',{},False,None,set())
        self.assertLess(text.index('BEFORE'),text.index('<!-- any:block '))
        self.assertLess(text.index('<!-- /any:block '),text.index('AFTER'))

    def test_inline_schema_has_list_id_and_preserves_filters_and_sorts(self):
        records,failed=inline_records(self.converter,{'views':[{'type':'table',
            'filters':[{'operator':'or','filters':[
                {'property':'Score','condition':'greater','value':4},
                {'property':'name','condition':'equal','value':'Dune'}]}],
            'sorts':[{'property':'Score','direction':'desc'}]}]},'scope','instance',set())
        record=records[0];ui=record['query']['anyUi']
        self.assertEqual(record['id'],'instance.list')
        self.assertEqual(ui['source'],{'kind':'collection','id':'scope'})
        self.assertEqual(ui['filters'][0]['conjunction'],'or')
        self.assertEqual(ui['filters'][0]['children'][0]['condition'],{'kind':'number','operator':'gt','value':'4'})
        self.assertEqual(ui['sort'][0]['propertyId'],'p')
        self.assertEqual(ui['sort'][0]['dir'],'desc')
        self.assertFalse(failed)

    def test_invalid_active_view_never_falls_back_to_unfiltered_view(self):
        with self.assertRaises(UnsupportedView):inline_records(self.converter,{'views':[
            {'filters':[{'property':'Score','condition':'unknown','value':4}]},{}]},'scope','instance',set())

    def test_multiple_inline_blocks_have_distinct_instances(self):
        self.assertNotEqual(instance_id('page','block-1'),instance_id('page','block-2'))
        self.assertNotEqual(instance_id('page','block-1'),instance_id('another-page','block-1'))

    def test_empty_scope_retains_filter_schema_without_adding_unfollowed_documents(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={'a':'new-a'}
        block={'id':'inline','object_id':'col','properties':[{'property':'Score','format':'number'}],
            'views':[{'filters':[{'property':'Score','condition':'greater','value':4}]}]}
        converter=ViewConverter({},engine.mapping,{}, {})
        with patch.object(engine,'col',return_value='bounded'), patch.object(engine,'property',return_value=('score',{'type':'number'})), patch('migration.add_membership') as membership:
            scope,scoped=engine.inline_scope('a',block,['b','c'],converter,set())
        membership.assert_not_called()
        records,_=inline_records(scoped,block,scope,'instance',set())
        self.assertEqual(records[0]['query']['anyUi']['source']['id'],'bounded')
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['propertyId'],'score')

    def test_scope_mirrors_values_into_its_own_property_descriptors(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={'b':'new-b'}
        engine.written_properties={'b':{'scope.p':{'value':8}}}
        block={'id':'inline','object_id':'col','views':[{'filters':[{'property':'Score','condition':'greater','value':4}]}]}
        with patch.object(engine,'col',return_value='bounded'), patch.object(engine,'property',return_value=('score',{'type':'number'})), patch('migration.add_membership') as membership, patch('migration.set_column_value') as value:
            scope,scoped=engine.inline_scope('a',block,['b','c'],self.converter,set())
        membership.assert_called_once_with(engine.target,'dest','new-b','bounded')
        value.assert_called_once_with(engine.target,'dest','new-b','bounded','score',8)
        self.assertEqual(scoped.fields('Score')[0][0],'bounded.score')

    def test_preview_includes_matching_inline_documents_when_checked(self):
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'objects','ids':['a']},
              'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create','collection_name':'Items'},
              'files':False,'follow_links':True}
        output='\n'.join(simulate(self.source,self.inv,plan))
        self.assertIn('Document de vue intégrée « B »',output)
        self.assertIn('BILAN : 2 objet(s)',output)
        self.assertNotIn('OBJET : C',output)

    def test_preview_does_not_expand_inline_documents_when_unchecked(self):
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'objects','ids':['a']},
              'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create','collection_name':'Items'},
              'files':False,'follow_links':False}
        output='\n'.join(simulate(self.source,self.inv,plan))
        self.assertIn('BILAN : 1 objet(s)',output)
        self.assertNotIn('OBJET : B',output)

    def test_client_ignored_empty_filters_are_rejected_instead_of_broadening(self):
        self.converter.bindings['status']=[('scope.status',{'format':'multi_select'},
            {'type':'choice','options':{'ready':{'name':'Ready'}}})]
        for node in ({'property':'name','condition':'equal','value':''},
                     {'property':'Status','condition':'in','value':[]},
                     {'operator':'or','filters':[]}):
            with self.subTest(node=node),self.assertRaises(UnsupportedView):
                inline_records(self.converter,{'views':[{'filters':[node]}]},'scope','instance',set())

    def test_relation_ui_values_are_raw_ids_for_client_uri_encoding(self):
        self.converter.bindings['related']=[('scope.related',{'format':'objects'},
            {'type':'relation','config':{'multiple':True}})]
        records,_=inline_records(self.converter,{'views':[{'filters':[
            {'property':'Related','condition':'in','value':['b']}]}]},'scope','instance',set())
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['condition']['values'],['new-b'])
        self.assertIn('any://new-b',json.dumps(records[0]['query']['filter']))

    def test_unix_date_filter_is_serialized_to_client_calendar_format(self):
        self.converter.bindings['date']=[('scope.date',{'format':'date'},{'type':'date'})]
        records,_=inline_records(self.converter,{'views':[{'filters':[
            {'property':'Date','condition':'equal','value':0}]}]},'scope','instance',set())
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['condition']['value'],'1970-01-01')

    def test_relation_any_of_multiple_values_is_expanded_to_or_singletons(self):
        self.converter.bindings['related']=[('scope.related',{'format':'objects'},
            {'type':'relation','config':{'multiple':True}})]
        records,_=inline_records(self.converter,{'views':[{'filters':[
            {'property':'Related','condition':'in','value':['a','b']}]}]},'scope','instance',set())
        group=records[0]['query']['anyUi']['filters'][0]
        self.assertEqual(group['conjunction'],'or')
        self.assertEqual([c['condition']['values'] for c in group['children']],[['new-a'],['new-b']])

    def test_single_select_all_of_multiple_options_is_expanded_to_and(self):
        self.converter.bindings['status']=[('scope.status',{'format':'select'},
            {'type':'choice','config':{'multiple':False},'options':{'a':{'name':'A'},'b':{'name':'B'}}})]
        records,_=inline_records(self.converter,{'views':[{'filters':[
            {'property':'Status','condition':'all_in','value':['A','B']}]}]},'scope','instance',set())
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['conjunction'],'and')

    def test_two_views_reuse_real_source_collection_without_view_supertags(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={}
        converter=ViewConverter({}, {},{}, {})
        with patch.object(engine,'col',return_value='actual-collection') as col:
            for block_id in ('first','second'):
                engine.inline_scope('a',{'id':block_id,'object_id':'col','views':[{}]},[],converter,set())
        self.assertEqual([c.args[0] for c in col.call_args_list],['collection:col','collection:col'])
        self.assertFalse(any('inline:' in str(c) or 'Vue ·' in str(c) for c in col.call_args_list))

    def test_inline_view_reuses_properties_already_owned_by_its_source(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={'b':'new-b'}
        converter=ViewConverter({'score':[('actual.score',{'format':'number'},{'type':'number'})]},engine.mapping,{}, {})
        with patch.object(engine,'col',return_value='actual'),patch.object(engine,'property') as create,patch('migration.set_column_value') as values,patch('migration.add_membership'):
            _,scoped=engine.inline_scope('a',{'id':'inline','object_id':'col','views':[{'columns':[{'property':'Score'}]}]},['b'],converter,set())
        create.assert_not_called();values.assert_not_called()
        self.assertEqual(scoped.fields('Score')[0][0],'actual.score')

    def test_existing_collection_cannot_silently_include_outside_documents(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={'b':'new-b'}
        engine.target=type('API',(),{'port':123})()
        engine.existing_collections={'existing'}
        with patch.object(engine,'col',return_value='existing'),patch('migration.local_get',return_value={'records':[{'id':'outside'}]}) as query,patch('migration.add_membership') as membership:
            with self.assertRaises(UnsupportedView):engine.inline_scope('a',{'id':'inline','object_id':'col','views':[{}]},['b'],self.converter,set())
        membership.assert_not_called()
        self.assertEqual(query.call_args.kwargs['body']['filter']['$and'][1],{'id':{'$nin':['new-b']}})

    def test_existing_collection_with_exact_scope_is_reused(self):
        engine=Engine(self.source,object(),self.inv,{'source_space':{'id':'src'},'target':{}})
        engine.dest_sid='dest';engine.mapping={'b':'new-b'}
        engine.target=type('API',(),{'port':123})()
        engine.existing_collections={'existing'}
        with patch.object(engine,'col',return_value='existing'),patch('migration.local_get',return_value={'records':[]}),patch('migration.add_membership'):
            scope,_=engine.inline_scope('a',{'id':'inline','object_id':'col','views':[{}]},['b'],self.converter,set())
        self.assertEqual(scope,'existing')


if __name__=='__main__':unittest.main()
