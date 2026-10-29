import unittest
from api_clients import clean_items, APIError
from logic import build_inventory, simulate, identify_links, property_state, summary_inventory

class FakeSource:
    def types(self, sid):
        return [{'id':'type-page', 'key':'page', 'name':'Pages', 'layout':'basic', 'property_definitions': []}]
    def objects(self, sid):
        return clean_items([
            {'id':'c','name':'Collection X','type':'collection'},
            {'id':'a','name':'Alpha','type':'page','properties':[]},
            {'id':'b','name':'Beta','type':'page','properties':[]},
            {'id':'z','name':'Zeta','type':'page','properties':[]}])
    def members(self, sid, cid):
        return clean_items([{'id':'a','name':'Alpha','type':'page'},
                            {'id':'b','name':'Beta','type':'page'}])
    def object_detail(self, sid, oid):
        return {'blocks':[{'type':'link','target_id':'z'}]} if oid=='a' else {}

class LogicTests(unittest.TestCase):
    def test_inventory(self):
        inv=build_inventory(FakeSource(),'s')
        self.assertEqual([x['id'] for x in inv['collections']], ['c'])
        self.assertEqual([x['id'] for x in inv['standalone']], ['z'])
        self.assertEqual(len(inv['members']['c']), 2)

    def test_types_include_collection_members(self):
        inv=build_inventory(FakeSource(),'s')
        self.assertEqual(len(inv['types']),1)
        self.assertEqual(inv['types'][0]['name'],'Pages')
        self.assertEqual({x['id'] for x in inv['types'][0]['items']},{'a','b','z'})

    def test_multiple_types_simulation(self):
        inv=build_inventory(FakeSource(),'s')
        plan={'source_space':{'id':'s','name':'Source'},
              'selection':{'kind':'types','type_keys':['page']},
              'target':{'space_mode':'create','space_name':'Destination',
                        'type_mappings':[{'key':'page','collection_mode':'none'}]},
              'follow_links':False,'files':False}
        log='\n'.join(simulate(FakeSource(), inv,plan))
        self.assertIn('TYPE : Pages — 3 objets',log)
        self.assertIn('sans collection',log)
        self.assertIn('3 objet(s)',log)

    def test_custom_fields_require_collection(self):
        self.assertEqual(property_state({'property_definitions':[{'name':'Year'}]},[]),'yes')
        self.assertEqual(property_state({'property_definitions':[]},[{'raw':{'properties':[]}}]),'no')
        self.assertEqual(property_state({'property_definitions':[]},[{'raw':{}}]),'unknown')
        self.assertEqual(property_state({'property_definitions':[{'name':'Created by'}, {'name':'Last Modified Date'}]},[]),'no')

        class WithProps(FakeSource):
            def types(self,sid):
                return [{'id':'type-page','key':'page','name':'Pages',
                         'property_definitions':[{'name':'Status'}]}]
        inv=build_inventory(WithProps(),'s')
        self.assertTrue(summary_inventory(inv)['types'][0]['requires_collection'])
        plan={'source_space':{'id':'s','name':'Source'},
              'selection':{'kind':'types','type_keys':['page']},
              'target':{'space_mode':'create','space_name':'Destination',
                        'type_mappings':[{'key':'page','collection_mode':'none'}]},
              'follow_links':False,'files':False}
        with self.assertRaisesRegex(APIError,'doit être importé dans une collection'):
            list(simulate(WithProps(),inv,plan))
        plan['target']['type_mappings']=[{'key':'page','collection_mode':'create','collection_name':'Pages'}]
        self.assertIn('nouvelle collection « Pages »','\n'.join(simulate(WithProps(),inv,plan)))

    def test_individual_with_props_requires_type_mapping(self):
        class WithProps(FakeSource):
            def types(self,sid):
                return [{'id':'type-page','key':'page','name':'Pages',
                         'property_definitions':[{'name':'Tags'}]}]
        inv=build_inventory(WithProps(),'s')
        plan={'source_space':{'id':'s','name':'Source'},
              'selection':{'kind':'objects','ids':['a']},
              'target':{'space_mode':'create','space_name':'Destination'},
              'follow_links':False,'files':False}
        with self.assertRaisesRegex(APIError,'obligatoire'):
            list(simulate(WithProps(),inv,plan))
        plan['target']['type_mappings']=[{'key':'page','collection_mode':'create','collection_name':'Pages personnalisées'}]
        self.assertIn('Pages personnalisées','\n'.join(simulate(WithProps(),inv,plan)))

    def test_links_conservative(self):
        self.assertEqual(identify_links({'blocks':[{'target':'z','text':'z'}]}, {'z','a'},'a'),{'z'})
        self.assertEqual(identify_links({'text':'z'}, {'z'},'a'),set())

    def test_simulate_without_or_with_links(self):
        inv=build_inventory(FakeSource(),'s')
        plan={'source_space':{'id':'s','name':'Source'},'selection':{'kind':'collection','collection_id':'c'},
              'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create','collection_name':'X'},
              'follow_links':False,'files':False}
        result='\n'.join(simulate(FakeSource(),inv,plan))
        self.assertIn('2 éléments',result)
        self.assertIn('non suivi',result)
        self.assertNotIn('OBJET : Zeta',result)
        plan['follow_links']=True
        result='\n'.join(simulate(FakeSource(),inv,plan))
        self.assertIn('OBJET : Zeta',result)
        self.assertIn('3 objet(s)',result)

    def test_invalid_name(self):
        inv=build_inventory(FakeSource(),'s')
        plan={'source_space':{'id':'s'}, 'selection':{'kind':'space'},'target':{'space_name':''}}
        with self.assertRaises(APIError): list(simulate(FakeSource(),inv,plan))

if __name__=='__main__':unittest.main()
