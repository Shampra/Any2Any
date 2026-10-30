import unittest
from unittest.mock import patch
from api_clients import Anytype, Anytwo, anytype_property_definitions
from migration import render_blocks, Engine
from view_conversion import ViewConverter
from inline_views import inline_records
from test_inline_views import Source


class LayoutPropertyTests(unittest.TestCase):
    def test_intentional_empty_paragraphs_survive_between_and_after_content(self):
        out=render_blocks({'blocks':[{'type':'paragraph','text':'A'},
            {'type':'paragraph'},{'type':'paragraph'},{'type':'paragraph','text':'B'},
            {'type':'paragraph'}]}, {},'s',{},False,None,set())
        self.assertEqual(out.split('\n\n'),['A','\u200b','\u200b','B','\u200b'])

    def test_v2_option_endpoint_keeps_colors_and_uses_stable_key(self):
        with patch('api_clients.paginated',side_effect=[
            [{'key':'opaque','id':'legacy','name':'Type','format':'select'}],
            [{'name':'Payé','color':'red'}]]) as get:
            meta=anytype_property_definitions(Anytype(123,'key'),'src')
        self.assertIn('/v2/spaces/src/properties/opaque/options',get.call_args.args[1])
        self.assertEqual(meta['opaque']['options'],[{'name':'Payé','color':'red'}])

    def test_deleted_spaces_are_not_offered_as_import_destinations(self):
        with patch('api_clients.local_get',return_value={'spaces':[
            {'id':'a','name':'Gone','status':'deleted'},
            {'id':'b','name':'Gone too','isDeleted':True},
            {'id':'c','name':'Active','status':'active'},
            {'id':'d','name':'Old API'}]}):
            self.assertEqual([x['id'] for x in Anytwo(123).spaces()],['c','d'])

    def test_hidden_member_properties_are_mirrored_with_choices_and_values(self):
        inv={'all':[],'types':[],'members':{}}
        e=Engine(Source(),object(),inv,{'source_space':{'id':'src'},'target':{}})
        e.dest_sid='dest';e.mapping={'b':'new-b'}
        spec={'key':'status','name':'Status','format':'select'}
        form={'type':'choice','options':{'paid':{'name':'Paid','color':'red'}},'config':{'multiple':False}}
        e.written_properties={'b':{'page.status':{'spec':spec,'label':'Status','value':['paid']}}}
        converter=ViewConverter({'status':[('page.status',spec,form)]},e.mapping,{}, {})
        with patch.object(e,'col',return_value='real'),patch.object(e,'property',return_value=('state',form)) as create,patch('migration.set_column_value') as setvalue,patch('migration.add_membership'):
            _,scoped=e.inline_scope('a',{'object_id':'col','views':[{}]},['b'],converter,set())
        self.assertEqual(create.call_args.kwargs['override'][1]['options']['paid']['color'],'red')
        setvalue.assert_called_once_with(e.target,'dest','new-b','real','state',['paid'])
        self.assertEqual(scoped.fields('status')[0][0],'real.state')

    def test_datetime_sort_keeps_time_precision(self):
        converter=ViewConverter({'created_date':[('real.date',{'format':'date'},{'type':'datetime'})]}, {},{}, {})
        rows,_=inline_records(converter,{'views':[{'sorts':[
            {'property':'created_date','direction':'desc','include_time':True}]}]},'real','instance',set())
        self.assertEqual(rows[0]['query']['sort'][0],'-real.date')

if __name__=='__main__':unittest.main()
