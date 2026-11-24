"""Regressions through the normal importer for templates, TOCs and mixed filters."""
import json
import unittest
from unittest.mock import patch, Mock

from api_clients import APIError
from migration import Engine
from anytype_templates import Templates
from view_conversion import ViewConverter
from inline_views import inline_records
from source_views import matches_filter
import anytwo_backend


class Source:
    def templates(self, sid):
        return [{'id':'tpl', 'name':'Violet', 'template_for':'task', 'default':True},
                {'id':'outside', 'template_for':'unselected'}]

    def type_detail(self, sid, key):
        return {'type_settings':{'property_definitions':[{'property':'State', 'format':'select'},
            {'property':'Done', 'format':'checkbox'}, {'property':'Price', 'format':'number'}]}}

    def object_detail(self, sid, oid):
        if oid == 'tpl':
            return {'type':'template', 'template_for':'task', 'properties':{'name':'Violet', 'State':['Pending']},
                    'blocks':[{'type':'heading_1', 'text':'FROM TEMPLATE'}]}
        if oid == 'c':
            return {'type':'collection', 'collection_items':['a'], 'blocks':[{'type':'dataview',
                'is_collection':True, 'views':[{'name':'All', 'default_template_id':'tpl'}]}]}
        return {'type':'task', 'properties':{'name':'Task', 'State':['Pending'], 'Done':False,
                'Price':12, 'source_object':['tpl']},
                'blocks':[{'type':'table_of_contents'}, {'type':'heading_1','text':'Title'}]}


class TemplateImportTests(unittest.TestCase):
    def test_empty_collection_discovers_its_explicit_template(self):
        engine = Mock()
        engine.inv = {'types':[]}
        engine.sid = 'src'
        engine.names = {}
        engine.source.templates.return_value = [{'id':'tpl','template_for':'task'}]
        documents = {'c':{'blocks':[{'type':'dataview','views':[{'default_template_id':'tpl'}]}]},
                     'tpl':{'type':'template','template_for':'task','properties':{'name':'Empty collection template'}}}
        engine.source_views.document.side_effect = documents.__getitem__
        engine.col_cache = {'collection:c':'destination'}
        engine.memberships = {}
        templates = Templates(engine)
        entries, docs = {}, {}
        templates.discover(entries, docs, {}, [{'id':'c'}])
        self.assertEqual(set(entries), {'tpl'})
        self.assertEqual(templates.scopes('tpl', entries), ['destination'])

    def test_shared_template_values_remap_options_for_each_collection(self):
        engine = Mock()
        engine.mapping = {'tpl':'target-template'}
        engine.results = {'tpl':{'issues':set(), 'errors':[]}}
        engine.property_owner = {'tpl':'first'}
        engine.memberships = {'tpl':{'first','second'}}
        engine.written_properties = {'tpl':{'first.status':{
            'kind':'array','label':'State','format':'select','value':['old-key'],
            'form':{'type':'choice','options':{'old-key':{'name':'Pending'}}}}}}
        engine.property.return_value = ('status', {'type':'choice','options':{'new-key':{'name':'Pending'}}})
        templates=Templates(engine)
        templates.rows={'tpl':{'template_for':'task'}}
        with patch('anytype_templates.set_column_value') as write:
            templates.mirror_values()
        self.assertEqual(write.call_args.args[2:], ('target-template','second','status',['new-key']))

    def run_import(self):
        item = {'id':'a', 'name':'Task', 'type':'task'}
        collection = {'id':'c', 'name':'Tasks', 'type':'collection'}
        inventory = {'all':[item,collection], 'objects':[item], 'collections':[collection],
                     'members':{'c':[item]}, 'types':[{'id':'task','key':'task','name':'Tasks','items':[item]}]}
        plan = {'source_space':{'id':'src','name':'Source'}, 'selection':{'kind':'collection','collection_id':'c'},
                'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create','collection_name':'Tasks'},
                'mode':'simple','files':False,'follow_links':False}
        columns = {}
        def add_column(api, sid, cid, name, key, kind, form):
            pid = 'prop-' + name
            columns.setdefault(cid, []).append({'id':pid,'name':name,'kind':kind,'xFormat':form})
            return pid
        with patch('anytwo_backend.server_version', return_value=(0,4,1)), \
             patch('migration.create_space', return_value='dest'), \
             patch('migration.create_collection', return_value='tasks'), \
             patch('migration.create_object', return_value='page'), \
             patch('anytwo_backend.create_template', return_value='template') as template, \
             patch('migration.anytype_property_definitions', return_value={
                 'state':{'name':'State','format':'select','options':[{'name':'Pending','color':'yellow'}]},
                 'done':{'name':'Done','format':'checkbox'}, 'price':{'name':'Price','format':'number'}}), \
             patch('migration.list_columns', side_effect=lambda api,sid,cid:columns.get(cid,[])), \
             patch('migration.add_column', side_effect=add_column), \
             patch('migration.set_column_value') as values, \
             patch('migration.set_markdown') as bodies, \
             patch('migration.create_saved_views', return_value=('views',[])), \
             patch('anytype_templates.set_default_template') as default, \
             patch('anytype_templates.set_column_value') as lineage:
            engine = Engine(Source(), object(), inventory, plan)
            report = list(engine.run())[-1]
        return report, template, default, bodies, values, lineage, engine

    def test_template_is_native_scoped_and_default_with_properties_and_body(self):
        report, template, default, bodies, values, lineage, engine = self.run_import()
        self.assertEqual(template.call_args.args[3], ['tasks'])
        default.assert_called_once_with(engine.target, 'dest', 'tasks', 'template', preserve_existing=False)
        self.assertEqual({r['source_id'] for r in report['objects']}, {'a','tpl'})
        self.assertEqual(report['templates']['objects'][0]['target_id'], 'template')
        self.assertTrue(any(c.args[2]=='template' and 'FROM TEMPLATE' in c.args[3] for c in bodies.call_args_list))
        self.assertTrue(any(c.args[2]=='template' and c.args[4]=='prop-State' for c in values.call_args_list))
        lineage.assert_called_once_with(engine.target,'dest','page','any','template',{'id':'template','version':1})
        self.assertNotIn('Source object', str(engine.prop_cache))

    def test_toc_becomes_native_dynamic_extension_at_original_position(self):
        _, _, _, bodies, _, _, _ = self.run_import()
        markdown = next(c.args[3] for c in bodies.call_args_list if c.args[2]=='page')
        head = markdown.split('\n')[0]
        data = json.loads(head.removeprefix('<!-- any:block ').removesuffix(' -->'))
        self.assertEqual(data['kind'],'table-of-contents')
        self.assertEqual(data['data'],{})
        self.assertLess(markdown.index('<!-- /any:block'), markdown.index('# Title'))
        self.assertNotIn('ANY2ANY_NOTION_TOC', markdown)

    def test_failed_template_does_not_become_collection_default(self):
        _, _, _, _, _, _, engine = self.run_import()
        engine.results['tpl']['errors'].append('body failed')
        with patch('anytype_templates.set_default_template') as write, patch('anytype_templates.set_column_value'):
            engine.templates.defaults({}, {})
        write.assert_not_called()
        self.assertTrue(engine.templates.warnings)

    def test_existing_default_is_preserved(self):
        with patch('anytwo_backend.local_get',return_value={'meta':{'defaultTemplate':'existing'}}), \
             patch('anytwo_backend.target_write') as write:
            with self.assertRaises(APIError):
                anytwo_backend.set_default_template(type('API',(),{'port':1})(),'s','c','new',preserve_existing=True)
        write.assert_not_called()


class AdvancedFilterTests(unittest.TestCase):
    def converter(self):
        return ViewConverter({'state':[('scope.state',{'format':'select'},
                {'type':'choice','config':{'multiple':False},'options':{'won':{'name':'Gagné'}}})],
            'done':[('scope.done',{'format':'checkbox'},{'type':'checkbox'})],
            'price':[('scope.price',{'format':'number'},{'type':'number'})],
            'relation':[('scope.relation',{'format':'objects'},{'type':'relation'})]}, {}, {}, {}, anytype_controls=True)

    def test_mixed_and_or_with_select_equality_survives_native_ui_conversion(self):
        node = {'operator':'and','filters':[{'property':'Done','condition':'equal','value':False},
            {'operator':'or','filters':[{'property':'State','condition':'equal','value':'Gagné'},
                {'property':'Price','condition':'greater','value':100}]}]}
        records, failures = inline_records(self.converter(), {'views':[{'filters':[node]}]},'scope','instance',set())
        self.assertFalse(failures)
        group=records[0]['query']['anyUi']['filters'][0]
        self.assertEqual(group['conjunction'],'and')
        self.assertEqual(group['children'][1]['conjunction'],'or')
        self.assertEqual(group['children'][1]['children'][0]['condition'],{'kind':'choice','operator':'is','values':['won']})
        for props, expected in [({'Done':False,'State':['Gagné'],'Price':12},True),
                                ({'Done':True,'State':['Gagné'],'Price':120},False),
                                ({'Done':False,'State':['Autre'],'Price':120},True)]:
            self.assertEqual(matches_filter(node,{'properties':props},{}),expected)

    def test_empty_relation_is_scoped_and_expressed_in_native_ui(self):
        node={'property':'Relation','condition':'empty'}
        c=self.converter()
        query=c.predicate(node)
        self.assertEqual(query['$and'][0], {'any.collections':'scope'})
        self.assertIn({'scope.relation':{'$size':0}},query['$and'][1]['$or'])
        records, failures=inline_records(c,{'views':[{'filters':[node]}]},'scope','instance',set())
        self.assertFalse(failures)
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['condition'],
                         {'kind':'choice','operator':'empty','values':[]})
        for value in [None, [], '']:
            self.assertTrue(matches_filter(node,{'properties':{'Relation':value}},{}))

    def test_select_negation_keeps_missing_fields_in_the_correct_collection(self):
        c=self.converter()
        node={'property':'State','condition':'not_equal','value':['Gagné']}
        result=c.predicate(node)
        self.assertEqual(result['$and'],[{'any.collections':'scope'}, {'scope.state':{'$ne':'won'}}])
        records, failures=inline_records(c,{'views':[{'filters':[node]}]},'scope','instance',set())
        self.assertFalse(failures)
        self.assertEqual(records[0]['query']['anyUi']['filters'][0]['condition']['operator'],'is-not')


if __name__ == '__main__':
    unittest.main()
