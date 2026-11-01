from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import unittest
import urllib.error
from unittest.mock import Mock
from api_clients import APIError
from notion_cache import ReadCache
from notion_source import Notion
from notion_demo import ROOT,DemoNotion,listed,page
from notion_routes import budget
from notion_jobs import start,inspect_job
import notion_tree

class FlatNotion(Notion):
    """A page with many child pages; artificial network latency, no cloud calls."""
    def __init__(self,count=16,latency=.01):
        super().__init__('fake');self.interval=0;self.latency=latency;self.children_ids=[f'{i:08x}-aaaa-bbbb-cccc-111111111111' for i in range(count)]
        self.active=0;self.maximum=0;self.calls=[];self.metrics=threading.Lock()
    def _send(self,path,method,body):
        with self.metrics:self.active+=1;self.maximum=max(self.maximum,self.active);self.calls.append(path)
        try:
            time.sleep(self.latency)
            clean=path.split('?')[0]
            if clean.startswith('/pages/'):return page(clean.split('/')[-1],'Page',{'type':'workspace','workspace':True} if clean.endswith(ROOT) else {'type':'page_id','page_id':ROOT})
            if clean=='/blocks/'+ROOT+'/children':return listed([{'id':oid,'type':'child_page','has_children':False} for oid in self.children_ids])
            return listed([{'id':'text','type':'paragraph','has_children':False}])
        finally:
            with self.metrics:self.active-=1

class ParallelReadTests(unittest.TestCase):
    def test_page_discovery_overlaps_reads_and_limits_inflight_to_four(self):
        client=FlatNotion();client._read_cache=ReadCache();client._child_cache={}
        selection=client.selection('page',ROOT,True);result=client.analyse(selection,list(selection['pages']))
        self.assertEqual(result['selected_pages'],17);self.assertGreater(client.maximum,1);self.assertLessEqual(client.maximum,4)
        self.assertTrue(all(count==1 for count in Counter(client.calls).values()))
    def test_global_pacing_is_shared_by_all_workers(self):
        client=Notion('fake');client.interval=.02;starts=[];lock=threading.Lock()
        def send(*args):
            with lock:starts.append(time.monotonic())
            time.sleep(.035);return {'ok':True}
        client._send=send
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:client.request('/users/me'),range(8)))
        starts.sort();self.assertTrue(all(b-a>=.017 for a,b in zip(starts,starts[1:])))
    def test_singleflight_cache_deduplicates_concurrent_requests(self):
        client=Notion('fake');client.interval=0;client._read_cache=ReadCache();entered=threading.Event();release=threading.Event()
        def send(*args):entered.set();release.wait(1);return {'value':[1]}
        client._send=Mock(side_effect=send)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(client.request,'/users/me') for _ in range(4)];self.assertTrue(entered.wait(1));release.set();values=[f.result() for f in futures]
        self.assertEqual(client._send.call_count,1);values[0]['value'].append(2);self.assertEqual(values[1]['value'],[1])
    def test_overload_cooldown_is_observed_before_retry(self):
        client=Notion('fake');client.interval=0;starts=[]
        def send(*args):
            starts.append(time.monotonic())
            if len(starts)==1:raise urllib.error.HTTPError('url',529,'overload',{'Retry-After':'.04'},None)
            return {'ok':True}
        client._send=send;client.request('/users/me');self.assertGreaterEqual(starts[1]-starts[0],.035)
    def test_cancel_interrupts_rate_wait(self):
        client=Notion('fake');client._cooldown=time.monotonic()+60;client.check_cancel=Mock(side_effect=APIError('cancelled',499));client._send=Mock()
        with self.assertRaises(APIError):client.request('/users/me')
        client._send.assert_not_called()

class CheckpointTests(unittest.TestCase):
    def wait(self,session,jid):
        for _ in range(400):
            result=inspect_job('GET','/api/notion/job',{},'id='+jid,session)
            if result['state']!='running':return result
            time.sleep(.005)
        self.fail('Job did not finish')
    def test_retry_after_timeout_reuses_successful_reads_and_refresh_discards_checkpoint(self):
        client=DemoNotion();catalog=client.catalog();session={'client':client,'catalog':catalog,'nodes':notion_tree.nodes(catalog)}
        original=client._send;calls=[];fail=[True]
        def send(path,method,body):
            calls.append(path)
            if path.startswith('/views') and fail[0]:raise APIError('timeout',504)
            return original(path,method,body)
        client._send=send;analyse=client.analyse
        def fail_after_reads(selection,ids):
            result=analyse(selection,ids)
            if fail[0]:raise APIError('timeout',504)
            return result
        client.analyse=fail_after_reads
        first=self.wait(session,start(session,{'whole':True,'rules':[]},threading.RLock(),budget)['id']);self.assertEqual(first['state'],'error')
        before=Counter(calls);fail[0]=False
        second=self.wait(session,start(session,{'whole':True,'rules':[]},threading.RLock(),budget)['id']);self.assertEqual(second['state'],'done')
        child='/blocks/'+ROOT+'/children?page_size=100';self.assertEqual(Counter(calls)[child],before[child]);self.assertGreater(second['reused_requests'],0)
        self.assertNotIn('analysis_checkpoint',session);self.assertIsNone(client._read_cache)
    def test_inventory_refresh_invalidates_any_saved_checkpoint(self):
        from notion_routes import handle
        state={'settings':{},'demo':True};save=Mock()
        handle('POST','/api/notion/connect',{},state,save,lambda _: 'dpapi:fake')
        state['notion']['analysis_checkpoint']={'cache':ReadCache()}
        handle('GET','/api/notion/catalog',{},state,save,lambda _: 'dpapi:fake',query='refresh=true')
        self.assertNotIn('analysis_checkpoint',state['notion'])

    def test_cache_memory_limit_does_not_prevent_uncached_reads(self):
        cache=ReadCache(limit=0);load=Mock(return_value={'large':'payload'})
        cache.read('key',load,lambda:None);cache.read('key',load,lambda:None);self.assertEqual(load.call_count,2);self.assertEqual(cache.size,0)

if __name__=='__main__':unittest.main()
