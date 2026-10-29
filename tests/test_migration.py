import unittest
from unittest.mock import patch
from migration import (Engine, render_blocks, source_format, column_shape, custom_properties,
                       discover_documents, select_scope, declared_properties, declared_column_shape, APIError)


class Source:
    def object_detail(self, sid, oid):
        return {
            'a': {'properties':{'name':'Ma super page','Score':4,'État':'À faire'},
                  'blocks':[{'type':'paragraph','text':'Voir le détail'},
                            {'type':'link','object_id':'b'},
                            {'type':'dataview','id':'view-1'},
                            {'type':'paragraph','background_color':'red','text':'Autre'}]},
            'b': {'properties':{'name':'Ma sous-page'},
                  'blocks':[{'type':'paragraph','text':'Suite'}]},
        }[oid]


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.a={'id':'a','name':'Ma super page','type':'page'}
        self.b={'id':'b','name':'Ma sous-page','type':'page'}
        self.col={'id':'c','name':'Truc','type':'collection'}
        self.inv={'all':[self.a,self.b,self.col],'objects':[self.a,self.b],
                  'collections':[self.col],'members':{'c':[self.a]},
                  'types':[{'id':'tp','key':'page','name':'Pages','items':[self.a,self.b]}]}
        self.plan={'source_space':{'id':'src','name':'Source'},
                   'selection':{'kind':'collection','collection_id':'c'},
                   'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create',
                             'collection_name':'Truc','type_mappings':[]},
                   'mode':'simple','follow_links':True,'files':False}

    def test_discovery_reason_linked(self):
        chosen,why,collections=select_scope(self.inv,self.plan)
        entries,docs,errs=discover_documents(Source(),'src',self.inv,chosen,why,True)
        self.assertEqual(set(entries),{'a','b'})
        self.assertIn('Lié à « Ma super page »',why['b'])

    def test_unsupported_block_explicit_placeholder_and_warning_once(self):
        warnings=set()
        text=render_blocks(Source().object_detail('src','a'),{'a':'targeta','b':'targetb'},'dest',
                           {'b':'Ma sous-page'},False,lambda *_:None,warnings)
        self.assertIn('**Attention : collection ou vue intégrée non importée.**',text)
        self.assertIn('any://o/dest/targetb',text)
        self.assertIn('Collection / vue intégrée non reproduite',warnings)
        self.assertIn('Couleur d’arrière-plan de bloc',warnings)

    def test_property_types(self):
        self.assertEqual(column_shape('checkbox',True,set())[0],'boolean')
        self.assertEqual(column_shape('number',2,set())[0],'number')
        self.assertEqual(column_shape('date','2026-10-21',set())[2],{'$date':'2026-10-21T00:00:00Z'})
        self.assertNotIn('name',custom_properties({'properties':{'name':'Test','Rating':3}}))
        self.assertIn('Rating',custom_properties({'properties':{'name':'Test','Rating':3}}))

    def test_two_passes_reasons_report_no_duplicates(self):
        fake_columns={}
        ids=[]
        def create_obj(target,sid,name,cols):
            oid='new'+str(len(ids)+1);ids.append((name,list(cols)))
            return oid
        def add_column(target,sid,cid,name,xkey,kind,fmt):
            data={'id':'prop-'+name,'name':name,'kind':kind,'xFormat':fmt}
            fake_columns.setdefault(cid,[]).append(data)
            return data['id']
        with patch('migration.create_space',return_value='dest'),\
             patch('migration.create_collection',return_value='coll1'),\
             patch('migration.create_object',side_effect=create_obj),\
             patch('migration.anytype_property_definitions',return_value={'score':{'format':'number'},'état':{'format':'select'}}),\
             patch('migration.list_columns',side_effect=lambda t,s,c:fake_columns.get(c,[])),\
             patch('migration.add_column',side_effect=add_column),\
             patch('migration.set_column_value') as set_value,\
             patch('migration.set_markdown') as set_body:
            events=list(Engine(Source(),object(),self.inv,self.plan).run())
        result=events[-1]
        self.assertEqual(result['event'],'summary')
        self.assertEqual(len(result['objects']),2)
        self.assertEqual(set(x[0] for x in ids),{'Ma super page','Ma sous-page'})
        self.assertTrue(any('Lié à' in r for r in next(o for o in result['objects'] if o['source_id']=='b')['reason']))
        self.assertIn('Collection / vue intégrée non reproduite',result['warnings'])
        self.assertTrue(set_body.called)
        self.assertTrue(set_value.called)

    def test_declared_empty_properties_and_colours(self):
        vocab={'rating':{'name':'Évaluation','format':'number'}}
        defs=declared_properties({'property_definitions':[
            {'property':'rating'}, {'property':'colour','name':'Couleur','format':'select',
                                    'options':[{'name':'Orange','color':'orange'}]},
            {'property':'name','name':'Name','format':'text'}]},vocab)
        self.assertEqual([d['name'] for d in defs],['Évaluation','Couleur'])
        kind,form=declared_column_shape(defs[1])
        self.assertEqual(kind,'array')
        self.assertEqual(next(iter(form['options'].values()))['color'],'orange')

    def test_no_sync_writes(self):
        self.plan['mode']='sync'
        with patch('migration.create_space') as create:
            with self.assertRaises(APIError): list(Engine(Source(),object(),self.inv,self.plan).run())
            create.assert_not_called()


if __name__=='__main__': unittest.main()
