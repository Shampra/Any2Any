import threading
import time
import unittest
from unittest.mock import Mock
from api_clients import APIError
from notion_demo import DemoNotion,ROOT,DB
from notion_jobs import start,inspect_job
from notion_routes import budget
import notion_tree as tree

class ParentRepairTests(unittest.TestCase):
    def test_block_parent_is_bridged_without_promoting_nested_database_to_root(self):
        client=DemoNotion();items=tree.nodes(client.catalog());node=items['database:'+DB]
        node['parent']={'type':'block_id','block_id':'88888888-8888-8888-8888-888888888888'}
        client.block=Mock(return_value={'object':'block','parent':{'type':'page_id','page_id':ROOT}})
        tree.repair(client,items)
        roots=[x for x in tree.forest(items) if x['parent_key'] is None]
        self.assertEqual([x['id'] for x in roots],[ROOT]);client.block.assert_called_once()
    def test_missing_search_parent_is_loaded_and_inaccessible_parent_is_labelled(self):
        client=DemoNotion();catalog=client.catalog();catalog['pages']=[x for x in catalog['pages'] if x['id']!=ROOT]
        items=tree.nodes(catalog);tree.repair(client,items)
        self.assertIn('page:'+ROOT,items)
        client.page=Mock(side_effect=APIError('not shared',404));items={'database:'+DB:items['database:'+DB]};items['database:'+DB].pop('ancestor_id',None)
        tree.repair(client,items);self.assertTrue(tree.forest(items)[0]['unresolved_parent'])

class AnalysisJobsTests(unittest.TestCase):
    def session(self):
        client=DemoNotion();catalog=client.catalog()
        return {'client':client,'catalog':catalog,'nodes':tree.nodes(catalog)}
    def wait(self,session,jid):
        for _ in range(200):
            result=inspect_job('GET','/api/notion/job',{},'id='+jid,session)
            if result['state']!='running':return result
            time.sleep(.005)
        self.fail('Job did not finish')
    def test_job_reports_result_and_reuses_content_read_during_selection(self):
        session=self.session();client=session['client'];original=client._send;calls=[]
        def send(path,method,body):calls.append(path);return original(path,method,body)
        client._send=send
        jid=start(session,{'whole':True,'rules':[]},threading.RLock(),budget)['id']
        result=self.wait(session,jid)
        self.assertEqual(result['state'],'done');self.assertEqual(result['result']['selected_pages'],3)
        path='/blocks/'+ROOT+'/children?page_size=100'
        self.assertEqual(calls.count(path),1);self.assertIsNone(client.progress);self.assertIsNone(client._child_cache)
    def test_poll_and_cancel_remain_responsive_while_api_lock_is_held(self):
        session=self.session();lock=threading.RLock()
        with lock:
            jid=start(session,{'whole':True,'rules':[]},lock,budget)['id']
            self.assertEqual(inspect_job('GET','/api/notion/job',{},'id='+jid,session)['state'],'running')
            inspect_job('POST','/api/notion/cancel',{'id':jid},'',session)
        self.assertEqual(self.wait(session,jid)['state'],'cancelled')
    def test_unexpected_failure_has_terminal_error_without_exception_secrets(self):
        session=self.session();session['client'].selection=Mock(side_effect=RuntimeError('SECRET'))
        jid=start(session,{'whole':True,'rules':[]},threading.RLock(),budget)['id'];result=self.wait(session,jid)
        self.assertEqual(result['state'],'error');self.assertNotIn('SECRET',result['message'])
    def test_unknown_job_and_out_of_scope_branch_are_refused(self):
        session=self.session()
        with self.assertRaises(ValueError):inspect_job('GET','/api/notion/job',{},'id=unknown',session)
        with self.assertRaises(ValueError):start(session,{'rules':[{'key':'page:unknown','include':True}]},threading.RLock(),budget)

if __name__=='__main__':unittest.main()
