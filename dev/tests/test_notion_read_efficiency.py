"""Regression tests for request reduction, pruning, retries and space metadata."""
from collections import Counter
import threading
import time
import unittest
from unittest.mock import Mock,patch
from anytwo_backend import APIError,set_space_icon
from notion_cache import ReadCache,session_cache
from notion_source import Notion
from notion_demo import DemoNotion,ROOT,DB,SOURCE,PAGE,CHILD,rich
from notion_routes import budget
from notion_jobs import inspect_job
from notion_import_jobs import start
from notion_migration import Engine
import notion_tree

class EfficientReadsTests(unittest.TestCase):
    def test_complete_inline_values_do_not_make_property_requests(self):
        client=Notion('fake');client.request=Mock(side_effect=AssertionError('unnecessary request'))
        cases=[{'id':'t','type':'title','title':rich('Title')},
               {'id':'r','type':'rich_text','rich_text':rich('Text')},
               {'id':'p','type':'people','people':[]},
               {'id':'a','type':'relation','relation':[{'id':PAGE}],'has_more':False},
               {'id':'f','type':'formula','formula':{'type':'number','number':42}},
               {'id':'z','type':'rollup','rollup':{'type':'number','number':100}}]
        for prop in cases:self.assertEqual(client.complete_property(PAGE,prop),prop)
        client.request.assert_not_called()

    def test_truncation_and_uncertain_calculations_still_read_all_items(self):
        client=Notion('fake');client.request=Mock(return_value={'object':'list','results':[{'relation':{'id':ROOT}}],'has_more':False})
        result=client.complete_property(PAGE,{'id':'r','type':'relation','relation':[],'has_more':True})
        self.assertEqual(result['relation'],[{'id':ROOT}]);client.request.assert_called_once()
        client.request=Mock(return_value={'object':'property_item','type':'formula','formula':{'type':'string','string':'complete'}})
        result=client.complete_property(PAGE,{'id':'f','type':'formula','formula':{'type':'string','string':'possibly truncated'}})
        self.assertEqual(result['formula']['string'],'complete')

    def test_excluded_database_is_never_queried_or_traversed(self):
        client=DemoNotion();catalog=client.catalog();client._read_cache=ReadCache();calls=[];original=client._send
        def send(path,method,body):calls.append(path);return original(path,method,body)
        client._send=send
        selected=notion_tree.select(client,notion_tree.nodes(catalog),[{'key':'page:'+ROOT,'include':True},{'key':'database:'+DB,'include':False}],False,catalog)
        self.assertEqual(set(selected['pages']),{ROOT,CHILD})
        self.assertFalse(any(SOURCE in p or DB in p or PAGE in p for p in calls))

    def test_explicit_reincluded_data_source_restores_its_members(self):
        client=DemoNotion();catalog=client.catalog()
        result=notion_tree.select(client,notion_tree.nodes(catalog),[{'key':'database:'+DB,'include':False},{'key':'data_source:'+SOURCE,'include':True}],True,catalog)
        self.assertIn(PAGE,result['pages']);self.assertIn(SOURCE,result['schemas'])

    def test_known_excluded_parent_blocks_linked_row_but_explicit_reinclude_works(self):
        client=DemoNotion();client._read_cache=ReadCache()
        self.assertEqual(client.selection('page',PAGE,True,excluded=[DB])['pages'],{})
        self.assertIn(PAGE,client.selection('page',PAGE,True,excluded=[DB],allow_excluded_parent=True)['pages'])

    def test_import_can_reuse_analysis_reads_without_destination_calls(self):
        client=DemoNotion();catalog=client.catalog();session={'client':client,'catalog':catalog,'nodes':notion_tree.nodes(catalog)}
        client._read_cache=session_cache(session)
        first=client.selection('page',ROOT,True)
        client._send=Mock(side_effect=AssertionError('cached selection must not request again'))
        second=notion_tree.select(client,session['nodes'],[{'key':'page:'+ROOT,'include':True}],False,catalog)
        self.assertEqual(first['pages'],second['pages']);client._send.assert_not_called()

    def test_cache_has_fixed_lifetime_not_sliding_forever(self):
        session={}
        with patch('time.monotonic',return_value=0):first=session_cache(session)
        with patch('time.monotonic',return_value=1700):self.assertIs(session_cache(session),first)
        with patch('time.monotonic',return_value=1801):self.assertIsNot(session_cache(session),first)

    def test_deadline_is_not_reported_as_internet_failure(self):
        client=Notion('fake');client.interval=0
        def send(*args):client.deadline=time.monotonic()-1;raise TimeoutError()
        client._send=send
        with self.assertRaises(APIError) as caught:client.request('/users/me')
        self.assertEqual(caught.exception.status,504);self.assertNotIn('Internet',str(caught.exception))

    def test_identity_never_confuses_bot_avatar_with_workspace_icon(self):
        client=Notion('fake');client.request=Mock(return_value={'object':'user','id':ROOT,'avatar_url':'https://example.org/bot.png','bot':{'workspace_name':'Sri'}})
        self.assertIsNone(client.identity()['workspace_icon'])

    def test_native_space_icon_uses_index_object_and_file_uri(self):
        api=Mock();api.port=31310
        with patch('anytwo_backend.local_get',return_value={'spaceIndexObjectId':'index'}),patch('anytwo_backend.attach_file',return_value='file') as upload,patch('anytwo_backend.target_write') as write:
            set_space_icon(api,'space','logo.png',b'image','image/png')
        upload.assert_called_once_with(api,'space','index','logo.png',b'image','image/png')
        write.assert_called_once_with(api,'/spaces/space',{'iconCid':'any://f/space/file'},method='PATCH')

    def test_icon_unavailable_is_explicit_and_optional_failure_is_nonfatal(self):
        options={'files':False,'links':False,'destination':{'id':'__create__','name':'Test'}}
        engine=Engine(DemoNotion(),Mock(),{'pages':{},'schemas':{}},options);engine.sid='space'
        engine.copy_workspace_icon();self.assertTrue(engine.report['warnings'])
        engine.selection['workspace_icon']='https://example.org/logo.png'
        with patch('notion_migration.download',return_value=(b'image','image/png','logo.png')),patch('notion_migration.backend.set_space_icon') as write:
            engine.copy_workspace_icon()
        write.assert_called_once_with(engine.target,'space','logo.png',b'image','image/png')

class ImportReadRetryTests(unittest.TestCase):
    def wait(self,session,jid):
        for _ in range(400):
            status=inspect_job('GET','/api/notion/job',{},'id='+jid,session)
            if status['state']!='running':return status
            time.sleep(.005)
        self.fail('worker did not finish')

    def test_failed_read_relaunch_reuses_reads_and_reports_categories(self):
        client=DemoNotion();catalog=client.catalog();session={'client':client,'catalog':catalog,'nodes':notion_tree.nodes(catalog)}
        original=client._send;calls=[];fail=[True]
        def send(path,method,body):
            calls.append(path)
            if path.startswith('/pages/'+CHILD) and fail[0]:raise APIError('deadline',504)
            return original(path,method,body)
        client._send=send
        options={'whole':True,'rules':[],'files':False,'links':False,'destination':{'id':'space'}}
        import uuid
        lock=threading.Lock()
        first=self.wait(session,start(session,{**options,'request_id':str(uuid.uuid4())},threading.RLock(),lock,budget,31310,Mock())['id'])
        self.assertEqual(first['state'],'error');self.assertIn('30 minutes',first['message'])
        self.assertTrue(first['metrics']['request_types']);before=Counter(calls);fail[0]=False
        with patch('notion_import_jobs.Engine') as engine:
            engine.return_value.run.return_value={'status':'done'}
            second=self.wait(session,start(session,{**options,'request_id':str(uuid.uuid4())},threading.RLock(),lock,budget,31310,Mock())['id'])
        self.assertEqual(second['state'],'done');self.assertGreater(second['reused_requests'],0)
        path='/blocks/'+ROOT+'/children?page_size=100'
        self.assertEqual(Counter(calls)[path],before[path]);self.assertIsNone(client.telemetry);self.assertIsNone(client.statistics)

if __name__=='__main__':unittest.main()
