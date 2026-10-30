import unittest
from unittest.mock import patch
from types import SimpleNamespace
from view_conversion import ViewConverter,collection_presentation

class CollectionPresentationTests(unittest.TestCase):
    def test_hidden_tag_visible_columns_and_source_date_sort(self):
        cv=ViewConverter({'tag':[('scope.tag',{'format':'multi_select'},{'type':'choice'})],
            'created_date':[('scope.date',{'format':'date'},{'type':'datetime'})],
            'prix':[('scope.price',{'format':'number'},{'type':'number'})]}, {},{}, {})
        view={'columns':[{'property':'name'},{'property':'created_date'},{'property':'tag','hidden':True},{'property':'prix'}],
              'sorts':[{'property':'created_date','direction':'desc','include_time':True}]}
        _,query,settings=cv.convert(view,{'any.collections':'scope'})
        query,settings=collection_presentation(cv,view,'scope',query,settings,set())
        self.assertEqual(settings['visible'],['name','date','price'])
        self.assertIn('tag',settings['hidden']);self.assertNotIn('tag',settings['visible'])
        self.assertIn('createdAt',settings['hidden'])
        self.assertEqual(query['sort'][0],'-scope.date')
        self.assertEqual(query['anyUi']['sort'],[{'propertyId':'date','dir':'desc'}])
        self.assertEqual(settings['order'][:4],['name','date','tag','price'])

    def test_native_default_view_reuses_existing_host(self):
        from view_conversion import create_saved_views
        cv=ViewConverter({}, {'source':'target'}, {}, {})
        block={'is_collection':True,'views':[{'columns':[{'property':'name'}],'sorts':[{'property':'name'}]}]}
        with patch('view_conversion.local_get',return_value={'records':[{'id':'existing-host'}]}) as lookup,patch('view_conversion.target_write') as create,patch('view_conversion.modify_records') as write:
            root,_=create_saved_views(SimpleNamespace(port=123),'space','collection',block,{'collection_items':['source']},['source'],cv,set(),table_key='default')
        self.assertEqual(root,'existing-host');create.assert_not_called()
        self.assertEqual(write.call_args_list[0].args[4][0]['id'],'default')
        self.assertEqual(write.call_args_list[1].args[4][0]['id'],'default')
        self.assertEqual(write.call_args_list[1].args[4][0]['layoutSettings']['visible'],['name'])

    def test_native_active_view_failure_never_becomes_unfiltered_secondary(self):
        from view_conversion import create_saved_views,UnsupportedView
        cv=ViewConverter({}, {}, {}, {})
        block={'is_collection':True,'views':[{'id':'bad','filters':[{'property':'missing','condition':'equal','value':'x'}]},{'id':'all'}]}
        with patch('view_conversion.local_get') as read,patch('view_conversion.target_write') as create:
            with self.assertRaises(UnsupportedView):create_saved_views(SimpleNamespace(port=123),'space','collection',block,{'collection_items':[]},[],cv,set(),table_key='default')
        read.assert_not_called();create.assert_not_called()

if __name__=='__main__':unittest.main()
