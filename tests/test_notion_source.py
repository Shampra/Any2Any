import io
import json
import unittest
import urllib.error
from unittest.mock import Mock,patch
from notion_source import Notion,notion_id,API_VERSION
from notion_demo import DemoNotion,ROOT,SOURCE,PAGE,DB,listed
from notion_routes import handle
from api_clients import APIError

class NotionClientTests(unittest.TestCase):
    def client(self):
        client=Notion('fake-unit-token');client.interval=0;return client

    def test_parse_link_uses_object_path_and_not_view_id(self):
        self.assertEqual(notion_id('https://www.notion.so/Title-'+ROOT.replace('-','')+'?v='+SOURCE),ROOT)
        with self.assertRaises(ValueError):notion_id('https://example.com/'+ROOT)

    def test_only_documented_read_operations_are_allowed(self):
        client=self.client();client._send=Mock()
        for method,path in [('POST','/pages'),('PATCH','/pages/'+PAGE),('DELETE','/views/'+PAGE),('GET','https://evil.example/users/me')]:
            with self.subTest(method=method),self.assertRaises(APIError):client.request(path,method=method)
        client._send.assert_not_called()

    def test_expired_operation_budget_stops_before_request(self):
        client=self.client();client.deadline=0;client._send=Mock()
        with self.assertRaises(APIError) as failure:client.identity()
        self.assertEqual(failure.exception.status,504);client._send.assert_not_called()

    def test_api_headers_and_host_are_fixed(self):
        client=self.client();response=Mock();response.read.return_value=b'{"object":"user","id":"bot"}'
        client._opener.open=Mock(return_value=Mock(__enter__=Mock(return_value=response),__exit__=Mock(return_value=False)))
        client.request('/users/me');req=client._opener.open.call_args.args[0]
        self.assertEqual(req.full_url,'https://api.notion.com/v1/users/me')
        self.assertEqual(req.get_header('Notion-version'),API_VERSION)
        self.assertEqual(req.get_header('Authorization'),'Bearer fake-unit-token')

    def test_search_cursor_pagination_keeps_second_page(self):
        client=self.client();client._send=Mock(side_effect=[{'results':[{'id':'a'}],'has_more':True,'next_cursor':'cursor'},listed([{'id':'b'}])])
        self.assertEqual([r['id'] for r in client.paginate('/search',method='POST')],['a','b'])
        self.assertEqual(client._send.call_args.args[2]['start_cursor'],'cursor')

    def test_incomplete_and_repeated_cursor_are_refused(self):
        for pages in ([{'results':[],'has_more':True,'next_cursor':'same'}]*2,
                      [{'results':[],'has_more':False,'request_status':{'type':'incomplete','incomplete_reason':'query_result_limit_reached'}}]):
            client=self.client();client._send=Mock(side_effect=pages)
            with self.assertRaises(APIError):client.paginate('/search',method='POST')

    def test_auth_error_never_contains_token(self):
        client=self.client();client._send=Mock(side_effect=urllib.error.HTTPError('url',401,'fake-unit-token',{},io.BytesIO(b'fake-unit-token')))
        with self.assertRaises(APIError) as failure:client.identity()
        self.assertNotIn('fake-unit-token',str(failure.exception))

    def test_short_rate_limit_is_retried_for_read_only_request(self):
        client=self.client();client._send=Mock(side_effect=[urllib.error.HTTPError('url',429,'rate',{'Retry-After':'0'},None),{'object':'user','id':'bot'}])
        client.identity();self.assertEqual(client._send.call_count,2)

    def test_multisource_catalog_deduplicates_database_container(self):
        client=DemoNotion();catalog=client.catalog()
        self.assertEqual(len(catalog['databases']),1);self.assertEqual(catalog['data_sources'][0]['id'],SOURCE)
        self.assertTrue(catalog['warnings'])

    def test_page_scope_subpages_and_database_members_are_optional(self):
        client=DemoNotion()
        without=client.selection('page',ROOT,False);self.assertEqual(set(without['pages']),{ROOT})
        with_children=client.selection('page',ROOT,True)
        self.assertEqual(len(with_children['pages']),3);self.assertIn(PAGE,with_children['pages'])
        self.assertEqual(set(with_children['schemas']),{SOURCE})

    def test_analysis_has_snapshot_policy_and_no_import(self):
        client=DemoNotion();selection=client.selection('data_source',SOURCE,False)
        result=client.analyse(selection,[PAGE])
        self.assertTrue(result['import_available']);self.assertFalse(result['source_modified'])
        self.assertEqual(result['views'][0]['configuration']['properties'][1]['visible'],False)
        formula=next(x for x in result['compatibility']['items'] if x['type']=='formula')
        self.assertEqual(formula['conversion'],'snapshot')

class NotionRouteTests(unittest.TestCase):
    def setUp(self):self.state={'settings':{},'demo':True};self.save=Mock()
    def request(self,method,path,data=None):return handle(method,'/api/notion/'+path,data or {},self.state,self.save,lambda value:'dpapi:fake')
    def connect(self):
        result=self.request('POST','connect')
        handle('GET','/api/notion/catalog',{},self.state,self.save,lambda _: 'dpapi:fake',query='refresh=true')
        return result

    def test_connect_validates_read_access_without_loading_full_catalog(self):
        self.state['demo']=False
        with patch('notion_routes.Notion') as constructor:
            client=constructor.return_value;client.deadline=None;client.identity.return_value={'name':'test'}
            result=self.request('POST','connect',{'token':'fake'})
            self.assertTrue(result['connected']);client.catalog.assert_not_called()
            client.request.assert_called_once_with('/search',method='POST',body={'page_size':1})
            self.assertIsNone(client.deadline)

    def test_connection_uses_five_second_budget_without_desktop_detection(self):
        import time
        self.state['demo']=False
        with patch('notion_routes.Notion') as constructor:
            client=constructor.return_value;client.deadline=None
            def identity():
                remaining=client.deadline-time.monotonic()
                self.assertGreater(remaining,0);self.assertLessEqual(remaining,5)
                return {'name':'Cloud connection'}
            client.identity.side_effect=identity
            self.request('POST','connect',{'token':'fake'})
            self.assertIsNone(client.deadline)

    def test_another_read_does_not_leave_connection_waiting_for_global_lock(self):
        import threading,time
        from notion_routes import LOCK
        ready=threading.Event();release=threading.Event()
        def hold():
            with LOCK:ready.set();release.wait(3)
        worker=threading.Thread(target=hold);worker.start();self.assertTrue(ready.wait(1))
        started=time.monotonic()
        try:
            with self.assertRaises(APIError) as failure:self.request('POST','connect',{})
            self.assertEqual(failure.exception.status,409);self.assertLess(time.monotonic()-started,1)
        finally:release.set();worker.join()

    def test_connection_never_returns_a_credential(self):
        result=self.connect();self.assertTrue(result['connected']);self.assertNotIn('token',result)
        self.assertNotIn('notion_token',json.dumps(self.request('GET','status')));self.save.assert_not_called()

    def test_selection_is_invalidated_on_reconnection(self):
        self.connect();selection=self.request('POST','selection',{'kind':'data_source','id':SOURCE,'include_subpages':False})
        self.connect()
        with self.assertRaises(ValueError):self.request('POST','preview',{'ticket':selection['ticket'],'ids':[PAGE]})

    def test_cannot_preview_an_unselected_page(self):
        self.connect();selection=self.request('POST','selection',{'kind':'data_source','id':SOURCE,'include_subpages':False})
        with self.assertRaises(ValueError):self.request('POST','preview',{'ticket':selection['ticket'],'ids':[ROOT]})

    def test_demo_manual_reference_is_scoped_and_selection_is_available(self):
        self.connect();result=self.request('POST','resolve',{'reference':ROOT})
        self.assertEqual(result['object']['kind'],'page')
        selection=self.request('POST','selection',{'kind':'page','id':ROOT,'include_subpages':True})
        self.assertEqual(len(selection['pages']),3)

    def test_failed_connection_preserves_previous_session_and_settings(self):
        self.connect();old=self.state['notion'];self.state['demo']=False
        with patch('notion_routes.Notion') as constructor:
            constructor.return_value.identity.side_effect=APIError('invalid')
            with self.assertRaises(APIError):self.request('POST','connect',{'token':'invalid'})
        self.assertIs(self.state['notion'],old);self.save.assert_not_called()

    def test_remember_requires_protected_storage(self):
        self.state['demo']=False
        with self.assertRaises(APIError):handle('POST','/api/notion/connect',{'token':'fake','remember':True},self.state,self.save,lambda _: '')
        self.save.assert_not_called()

if __name__=='__main__':unittest.main()
