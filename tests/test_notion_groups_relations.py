from copy import deepcopy
import json
import re
import unittest
from unittest.mock import Mock,patch
from notion_demo import DemoNotion,ROOT,DB,SOURCE,SCHEMA,rich
from notion_migration import Engine
from notion_views import normalise,converter
from view_conversion import create_saved_views,ViewConverter,UnsupportedView

OTHER='66666666-6666-6666-6666-666666666666'

class GroupAndTextTests(unittest.TestCase):
    def engine(self):
        e=Engine(DemoNotion(),Mock(),{'pages':{},'schemas':{SOURCE:deepcopy(SCHEMA)}},{'files':False,'links':False,'destination':{'id':'space'}})
        e.sid='space';e.collections={SOURCE:'collection'}
        e.props[(SOURCE,'state')]=('state-target','array',{'type':'choice','options':{'todo':{'name':'À faire'}}})
        e.schemas[SOURCE]['properties']['Text']={'id':'text','type':'rich_text'}
        e.props[(SOURCE,'text')]=('text-target','string',{'type':'text'})
        return e

    def test_collection_grouping_and_board_columns_use_client_schema(self):
        e=self.engine()
        for kind in ('table','board'):
            view={'id':'view','type':kind,'configuration':{'group_by':{'property_id':'state','sort':{'type':'ascending'},'hide_empty_groups':True}}}
            normalized=normalise(view,e.schemas[SOURCE],set())
            self.assertEqual(normalized['type'],'table' if kind=='table' else 'kanban')
            with patch('view_conversion.modify_records') as write:
                create_saved_views(e.target,e.sid,'collection',{'is_collection':True,'views':[normalized]}, {'type':'collection','collection_items':[]},[],converter(e,SOURCE),set(),root_id='host',table_key='default')
            record=write.call_args_list[-1].args[-1][0]
            if kind=='table':
                self.assertEqual(record['query']['groupBy'],{'propId':'state-target'})
                group=record['query']['anyUi']['group']
            else:group=record['layoutSettings']['boardColumns'];self.assertEqual(record['layout'],'board')
            self.assertEqual(group['propertyId'],'state-target');self.assertEqual(group['sort'],'asc');self.assertTrue(group['hideEmpty'])

    def test_unnamed_board_has_a_meaningful_default_label(self):
        self.assertEqual(normalise({'name':'Untitled','type':'board'},SCHEMA)['name'],'Tableau Kanban')

    def test_text_contains_is_native_and_literal_without_weakening_anytype(self):
        e=self.engine();view=normalise({'type':'table','quick_filters':{'text':{'rich_text':{'contains':'A.B [x]'}}}},e.schemas[SOURCE])
        condition=view['filters'][0];self.assertEqual(condition['condition'],'notion_contains')
        predicate=converter(e,SOURCE).predicate(condition)
        regex=predicate['$and'][1]['collection.text-target']['$regex']
        self.assertTrue(re.search(regex,'a.b [X]'));self.assertIsNone(re.search(regex,'aZb x'))
        with patch('view_conversion.modify_records') as write:
            create_saved_views(e.target,e.sid,'collection',{'is_collection':True,'views':[view]}, {'type':'collection','collection_items':[]},[],converter(e,SOURCE),set(),root_id='host',table_key='default')
        record=write.call_args_list[-1].args[-1][0]
        self.assertEqual(record['query']['anyUi']['filters'][0]['condition']['operator'],'contains')
        base=ViewConverter({'text': [('collection.text-target',{'format':'text'}, {'type':'text'})]}, {}, {}, {})
        with self.assertRaises(UnsupportedView):base.predicate({'property':'text','condition':'contains','value':'A.B'})

class InverseAndAverageTests(unittest.TestCase):
    def engine(self):
        relation={'id':'forward','name':'Related','type':'relation','relation':{'data_source_id':OTHER,'type':'dual_property','dual_property':{'synced_property_id':'back%3Aid'}}}
        reverse={'id':'back:id','name':'Back','type':'relation','relation':{'data_source_id':SOURCE,'type':'dual_property','dual_property':{'synced_property_id':'forward'}}}
        score={'id':'score','name':'Score','type':'number','number':{'format':'number'}}
        e=Engine(None,Mock(),{'pages':{},'schemas':{SOURCE:{'properties':{'Related':relation}},OTHER:{'properties':{'Back':reverse,'Score':score}}}}, {'files':False,'links':False,'destination':{'id':'space'}})
        e.sid='space';e.collections={SOURCE:'left',OTHER:'right'};e.collection_handles={SOURCE:'left-handle',OTHER:'right-handle'}
        for sid,name,pid in ((SOURCE,'Related','forward-target'),(OTHER,'Back','back-target'),(OTHER,'Score','score-target')):
            prop=e.schemas[sid]['properties'][name];kind,form=e.shape(sid,name,prop);e.props[(sid,prop['id'])]=(pid,kind,form)
        return e

    def test_dual_relation_definitions_are_paired_both_ways(self):
        e=self.engine()
        with patch('notion_migration.backend.target_write') as write:e.link_inverse_relations()
        self.assertEqual(write.call_count,2)
        forward=e.props[(SOURCE,'forward')][2]['anyui'];reverse=e.props[(OTHER,'back:id')][2]['anyui']
        self.assertEqual(forward,{'inverseOwner':'right','inverseProperty':'back-target'})
        self.assertEqual(reverse,{'inverseOwner':'left','inverseProperty':'forward-target'})
        self.assertTrue(all(call.kwargs['method']=='PATCH' for call in write.call_args_list))

    def test_missing_reverse_property_is_reported_without_creating_duplicates(self):
        e=self.engine();e.schemas[OTHER]['properties'].pop('Back');e.props.pop((OTHER,'back:id'))
        with patch('notion_migration.backend.target_write') as write:e.link_inverse_relations()
        write.assert_not_called();self.assertTrue(e.report['warnings'])

    def test_average_rollup_uses_mapped_relation_and_target_property(self):
        e=self.engine();rollup={'id':'mean','type':'rollup','rollup':{'relation_property_id':'forward','rollup_property_id':'score','function':'average'}}
        kind,form=e.rollup_shape(SOURCE,rollup)
        self.assertEqual(kind,'object');self.assertEqual(form['type'],'rollup')
        config=json.loads(form['anyui']['rollup'])
        self.assertEqual(config['calculate'],'average')
        self.assertEqual(config['relation'],{'direction':'own','ownerId':'left','propertyId':'forward-target'})
        self.assertEqual(config['target'],{'ownerId':'right','propertyId':'score-target'})

if __name__=='__main__':unittest.main()
