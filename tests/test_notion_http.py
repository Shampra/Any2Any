import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import server
from notion_demo import SOURCE,PAGE

class NotionHTTPTests(unittest.TestCase):
    def test_import_endpoint_launches_worker_and_poll_returns_report(self):
        import uuid
        import notion_tree
        from notion_demo import DemoNotion
        client=DemoNotion();catalog=client.catalog()
        state={'settings':{'source_kind':'notion','anytwo_port':31310},'demo':False,
               'notion':{'client':client,'catalog':catalog,'nodes':notion_tree.nodes(catalog)},'latest_report':None}
        with patch.object(server,'STATE',state),patch('notion_import_jobs.Engine') as constructor:
            report={'id':'test','source':'notion','status':'done','target_space':'test-space','objects':[],'collections':[],'totals':{'total':1},'warnings':[],'errors':[]}
            constructor.return_value.run.return_value=report
            http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
            base='http://127.0.0.1:'+str(http.server_port)
            def request(path,data=None):
                req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','Origin':base})
                with urllib.request.urlopen(req) as response:return json.load(response)
            try:
                job=request('/api/notion/import',{'request_id':str(uuid.uuid4()),'whole':True,'rules':[],'files':True,'links':True,'destination':{'id':'test-space'}})
                deadline=time.monotonic()+3
                while True:
                    status=request('/api/notion/job?id='+job['id'])
                    if status['state']!='running':break
                    if time.monotonic()>deadline:self.fail('Import did not complete')
                    time.sleep(.01)
                self.assertEqual(status['state'],'done');self.assertEqual(status['result']['target_space'],'test-space')
                self.assertEqual(constructor.call_args.args[3]['files'],True)
                self.assertEqual(constructor.call_args.args[3]['links'],False,'whole workspace disables following links')
                self.assertTrue(server.IMPORT_LOCK.acquire(blocking=False));server.IMPORT_LOCK.release()
            finally:http.shutdown();http.server_close();worker.join()

    def test_read_only_workflow_needs_no_anytype_and_blocks_legacy_import(self):
        state={'settings':{'source_kind':'notion','anytwo_port':31310,'anytype_port':31009},'demo':True,'inventories':{},'latest_report':None}
        with patch.object(server,'STATE',state),patch.object(server,'Anytype',side_effect=AssertionError('Anytype must not be used')):
            http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
            worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
            base='http://127.0.0.1:'+str(http.server_port)
            def request(path,data=None):
                req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','Origin':base})
                with urllib.request.urlopen(req) as response:return json.load(response)
            try:
                self.assertTrue(request('/api/notion/connect',{})['connected'])
                request('/api/notion/catalog?refresh=true')
                self.assertTrue(request('/api/notion/tree')['loaded'])
                with self.assertRaises(urllib.error.HTTPError) as leaf:
                    request('/api/notion/children',{'key':'data_source:'+SOURCE})
                self.assertEqual(leaf.exception.code,400)
                selection=request('/api/notion/tree-selection',{'whole':False,'rules':[{'key':'data_source:'+SOURCE,'include':True}]})
                result=request('/api/notion/preview',{'ticket':selection['ticket'],'ids':[PAGE]})
                self.assertEqual(result['selected_pages'],1);self.assertTrue(result['import_available'])
                job=request('/api/notion/analyse',{'whole':False,'rules':[{'key':'data_source:'+SOURCE,'include':True}]})
                deadline=time.monotonic()+3
                while True:
                    status=request('/api/notion/job?id='+job['id'])
                    if status['state']!='running':break
                    if time.monotonic()>deadline:self.fail('HTTP analysis did not finish')
                    time.sleep(.01)
                self.assertEqual(status['state'],'done');self.assertEqual(status['result']['selected_pages'],1)
                self.assertIn('spaces',request('/api/notion/targets'))
                with self.assertRaises(urllib.error.HTTPError) as refused:request('/api/simulate',{})
                self.assertEqual(refused.exception.code,400)
                self.assertNotIn('notion_token',request('/api/config'))
            finally:http.shutdown();http.server_close();worker.join()

if __name__=='__main__':unittest.main()
