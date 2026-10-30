import unittest
from unittest.mock import patch
from migration import Engine
from view_conversion import ViewConverter
from test_inline_views import Source

class MembershipRegressionTests(unittest.TestCase):
    def test_existing_membership_does_not_block_property_copy(self):
        e=Engine(Source(),object(),{'all':[],'types':[],'members':{}},{'source_space':{'id':'src'},'target':{}})
        e.dest_sid='dest';e.mapping={'b':'new-b'};e.memberships={'b':{'real'}}
        spec={'key':'score','name':'Score','format':'number'}
        e.written_properties={'b':{'page.score':{'spec':spec,'label':'Score','value':8}}}
        cv=ViewConverter({'score':[('page.score',spec,{'type':'number'})]},e.mapping,{}, {})
        with patch.object(e,'col',return_value='real'),patch.object(e,'property',return_value=('score',{'type':'number'})),patch('migration.add_membership',side_effect=AssertionError('Redundant membership must not run')) as membership,patch('migration.set_column_value') as value:
            e.inline_scope('a',{'object_id':'col','views':[{}]},['b'],cv,set())
            e.inline_scope('a',{'object_id':'col','views':[{}]},['b'],cv,set())
        membership.assert_not_called();self.assertEqual(value.call_count,2)

    def test_new_membership_is_only_written_once_for_repeated_views(self):
        e=Engine(Source(),object(),{'all':[],'types':[],'members':{}},{'source_space':{'id':'src'},'target':{}})
        e.dest_sid='dest';e.mapping={'b':'new-b'}
        with patch.object(e,'col',return_value='real'),patch('migration.add_membership') as membership:
            for _ in range(2):e.inline_scope('a',{'object_id':'col','views':[{}]},['b'],ViewConverter({},e.mapping,{},{}),set())
        membership.assert_called_once();self.assertEqual(e.memberships['b'],{'real'})

    def test_membership_api_uses_no_body(self):
        from api_clients import add_membership
        with patch('api_clients.target_write') as write:add_membership(object(),'s','o','c')
        self.assertIsNone(write.call_args.args[2])

    def test_full_collection_import_copies_properties_after_page_creation(self):
        class SourceCollection:
            def object_detail(self,sid,oid):
                return {'c':{'type':'collection','collection_items':['a'],'blocks':[{'type':'dataview','is_collection':True,'views':[{'columns':[{'property':'Score'}]}]}]},
                        'a':{'properties':{'name':'A','Score':8},'blocks':[]}}[oid]
        item={'id':'a','name':'A','type':'page'};col={'id':'c','name':'Accounting','type':'collection'}
        inv={'all':[item,col],'objects':[item],'collections':[col],'members':{'c':[item]},'types':[{'id':'page','key':'page','name':'Page','items':[item]}]}
        plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'collection','collection_id':'c'},'target':{'space_mode':'create','space_name':'Dest','collection_mode':'create','collection_name':'Accounting'}}
        e=Engine(SourceCollection(),object(),inv,plan)
        with patch('migration.create_space',return_value='dest'),patch('migration.create_collection',side_effect=['accounting','pages']),patch('migration.create_object',return_value='new-a'),patch('migration.anytype_property_definitions',return_value={'score':{'key':'Score','name':'Score','format':'number'}}),patch.object(e,'property',return_value=('score',{'type':'number'})),patch('migration.add_membership',side_effect=AssertionError('already a member')),patch('migration.set_column_value') as value,patch('migration.create_saved_views',return_value=('views',[])):
            events=list(e.run())
        self.assertIn(('accounting',8),[(c.args[3],c.args[5]) for c in value.call_args_list])
        self.assertEqual(e.memberships['a'],{'accounting'})
        self.assertFalse(events[-1]['collections'][0]['issues'])

    def test_same_source_property_on_two_types_becomes_one_collection_column(self):
        e=Engine(Source(),object(),{'all':[],'types':[],'members':{}},{'source_space':{'id':'src'},'target':{}})
        e.dest_sid='dest';e.mapping={'b':'new-b','c':'new-c'};e.memberships={'b':{'one','real'},'c':{'two','real'}}
        spec={'key':'score','name':'Score','format':'number'}
        e.written_properties={'b':{'one.x':{'spec':spec,'label':'Score','value':8}},'c':{'two.y':{'spec':spec,'label':'Score','value':1}}}
        cv=ViewConverter({'score':[('one.x',spec,{'type':'number'}),('two.y',spec,{'type':'number'})]},e.mapping,{}, {})
        with patch.object(e,'col',return_value='real'),patch.object(e,'property',return_value=('score',{'type':'number'})) as create,patch('migration.set_column_value') as values:
            _,scoped=e.inline_scope('a',{'object_id':'col','views':[{'columns':[{'property':'Score'}]}]},['b','c'],cv,set())
        self.assertEqual(create.call_count,1);self.assertEqual(create.call_args.args[1],'Score')
        self.assertEqual(scoped.fields('score')[0][0],'real.score');self.assertEqual(len(scoped.fields('score')),1)
        self.assertEqual(sorted(c.args[-1] for c in values.call_args_list),[1,8])

    def test_green_palette_alias_is_translated_for_anytwo(self):
        from view_conversion import choice_options
        self.assertEqual(choice_options([{'name':'Won','color':'lime'}],lambda a,b:'won')['won']['color'],'green')

    def test_space_scope_keeps_collection_navigation_pages(self):
        from migration import select_scope
        inv={'objects':[],'collections':[{'id':'c','name':'Nested','type':'collection'}]}
        roots,_,_=select_scope(inv,{'source_space':{'name':'Source'},'selection':{'kind':'space'},'target':{'space_mode':'create','space_name':'Dest'}})
        self.assertEqual([x['id'] for x in roots],['c'])

if __name__=='__main__':unittest.main()
