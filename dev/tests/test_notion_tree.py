import unittest
from unittest.mock import Mock
import notion_tree as tree
from notion_demo import DemoNotion,ROOT,DB,SOURCE,PAGE,CHILD
from notion_routes import handle

class NotionTreeTests(unittest.TestCase):
    def setUp(self):self.client=DemoNotion();self.catalog=self.client.catalog();self.nodes=tree.nodes(self.catalog)
    def test_forest_preserves_page_database_source_row_ancestry(self):
        items={tree.key(x):x for x in tree.forest(self.nodes)}
        self.assertIsNone(items['page:'+ROOT]['parent_key'])
        self.assertEqual(items['database:'+DB]['parent_key'],'page:'+ROOT)
        self.assertEqual(items['data_source:'+SOURCE]['parent_key'],'database:'+DB)
        self.assertEqual(items['page:'+PAGE]['parent_key'],'data_source:'+SOURCE)
    def test_navigation_stops_at_level_two_but_selection_keeps_deeper_rows(self):
        rows={tree.key(x):x for x in tree.navigation(self.nodes)}
        self.assertEqual(rows['page:'+ROOT]['depth'],0)
        self.assertEqual(rows['database:'+DB]['depth'],1)
        self.assertTrue(rows['data_source:'+SOURCE]['selection_leaf'])
        self.assertNotIn('page:'+PAGE,rows)
        selected=tree.select(self.client,self.nodes,[{'key':'data_source:'+SOURCE,'include':True}],False,self.catalog)
        self.assertIn(PAGE,selected['pages'])

    def test_missing_parent_and_cycles_do_not_hide_accessible_nodes(self):
        nodes={'page:a':{'kind':'page','id':'a','name':'A','parent':{'page_id':'b'}},'page:b':{'kind':'page','id':'b','name':'B','parent':{'page_id':'a'}},'page:c':{'kind':'page','id':'c','name':'C','parent':{'page_id':'private'}}}
        self.assertTrue(all(x['parent_key'] is None for x in tree.forest(nodes)))
    def test_lazy_children_stop_at_page_boundary_and_expand_database_sources(self):
        children=tree.children(self.client,self.nodes['page:'+ROOT])
        self.assertEqual({x['id'] for x in children},{CHILD,DB})
        self.assertEqual(tree.children(self.client,self.nodes['database:'+DB])[0]['id'],SOURCE)
        self.assertEqual(tree.children(self.client,self.nodes['data_source:'+SOURCE])[0]['id'],PAGE)
    def test_branch_selection_excludes_child_subtree_and_keeps_other_members(self):
        selection=tree.select(self.client,self.nodes,[{'key':'page:'+ROOT,'include':True},{'key':'database:'+DB,'include':False}],False,self.catalog)
        self.assertEqual(set(selection['pages']),{ROOT,CHILD});self.assertEqual(selection['schemas'],{})
    def test_whole_workspace_can_exclude_then_reinclude_a_deeper_page(self):
        selection=tree.select(self.client,self.nodes,[{'key':'page:'+PAGE,'include':True},{'key':'database:'+DB,'include':False}],True,self.catalog)
        self.assertEqual(set(selection['pages']),{ROOT,CHILD,PAGE});self.assertIn(SOURCE,selection['schemas'])
    def test_unknown_and_duplicate_selection_rules_are_refused(self):
        for rules in ([{'key':'page:unknown','include':True}],[{'key':'page:'+ROOT,'include':True}]*2):
            with self.assertRaises(ValueError):tree.select(self.client,self.nodes,rules,False,self.catalog)
    def test_whole_workspace_includes_manually_added_roots_without_new_search(self):
        self.client.catalog=Mock(side_effect=AssertionError('No fresh search'))
        result=tree.select(self.client,self.nodes,[],True,self.catalog)
        self.assertEqual(len(result['pages']),3)

class NotionTreeRoutesTests(unittest.TestCase):
    def setUp(self):self.state={'settings':{},'demo':True};self.save=Mock()
    def request(self,method,path,data=None,query=''):return handle(method,'/api/notion/'+path,data or {},self.state,self.save,lambda _: 'dpapi:fake',query)
    def test_tree_selection_snapshot_reconnect_and_unknown_children(self):
        self.request('POST','connect');self.request('GET','catalog',query='refresh=true')
        self.assertTrue(self.request('GET','tree')['loaded'])
        with self.assertRaises(ValueError):self.request('POST','children',{'key':'page:unknown'})
        children=self.request('POST','children',{'key':'page:'+ROOT});self.assertEqual(children['expanded'],'page:'+ROOT)
        result=self.request('POST','tree-selection',{'whole':False,'rules':[{'key':'database:'+DB,'include':True}]})
        self.assertEqual([x['id'] for x in result['pages']],[PAGE])
        self.request('POST','connect')
        with self.assertRaises(ValueError):self.request('POST','preview',{'ticket':result['ticket'],'ids':[PAGE]})
    def test_prefetched_children_are_reused_until_inventory_refresh(self):
        self.request('POST','connect');self.request('GET','catalog',query='refresh=true')
        client=self.state['notion']['client'];original=client.children;client.children=Mock(wraps=original)
        first=self.request('POST','children',{'key':'page:'+ROOT,'prefetch':True})
        self.assertIn('page:'+ROOT,first['loaded_nodes'])
        self.request('POST','children',{'key':'page:'+ROOT});self.assertEqual(client.children.call_count,1)
        self.request('GET','catalog',query='refresh=true')
        self.request('POST','children',{'key':'page:'+ROOT});self.assertEqual(client.children.call_count,2)

    def test_level_two_does_not_issue_background_or_foreground_reads(self):
        self.request('POST','connect');self.request('GET','catalog',query='refresh=true')
        client=self.state['notion']['client'];client.request=Mock(side_effect=AssertionError('No deep read'))
        for prefetch in (True,False):
            with self.assertRaises(ValueError):self.request('POST','children',{'key':'data_source:'+SOURCE,'prefetch':prefetch})
        client.request.assert_not_called()

    def test_forget_clears_saved_flag_token_tree_and_selections(self):
        self.request('POST','connect',{'remember':True});status=self.request('GET','status')
        self.assertTrue(status['remembered']);self.assertTrue(status['has_token'])
        self.request('POST','disconnect');status=self.request('GET','status')
        self.assertFalse(status['has_token']);self.assertFalse(status['remembered']);self.assertFalse(status['connected'])
        self.assertEqual(self.state['notion']['selections'],{})

if __name__=='__main__':unittest.main()
