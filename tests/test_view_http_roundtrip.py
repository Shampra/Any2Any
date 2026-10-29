"""Full importer + HTTP contract for views, with two disposable fake servers."""
import json
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit
from test_http_integration import APIStub
from api_clients import Anytype, Anytwo
from migration import Engine


class ViewsAPI(APIStub):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/v2/spaces/src/objects/c':
            return self.answer(200,{'id':'c','type_internal_key':'collection','collection_items':['a'],
                'blocks':[{'id':'primary','type':'dataview','is_collection':True,'views':[
                    {'name':'Rated','filters':[{'property':'Rating','condition':'greater','value':3}],
                     'sorts':[{'property':'Rating','direction':'desc'}]}]}]})
        if path=='/v2/spaces/src/objects/a':
            return self.answer(200,{'properties':{'name':'Dune','Rating':4},'blocks':[
                {'type':'paragraph','text':'BEFORE'},
                {'id':'inline','type':'dataview','object_id':'c','views':[{'name':'Inline',
                    'filters':[{'property':'Rating','condition':'greater','value':3}]}]},
                {'type':'paragraph','text':'AFTER'}]})
        super().do_GET()

    def do_POST(self):
        if urlsplit(self.path).path=='/v1/spaces/dest/modify':
            raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
            self.calls.append((self.server.label,'POST',urlsplit(self.path).path,raw))
            body=json.loads(raw)
            required={'dataviews':{'name','pos'},'views':{'name','pos','dataview','layout'}}
            for record in body['records']:
                fields={op['path']:op['value'] for op in record['ops']}
                if not required[body['dataset']].issubset(fields):
                    return self.answer(400,{'message':'missing view fields'})
            return self.answer(200,{'recordIds':[r['id'] for r in body['records']],'rejections':[]})
        super().do_POST()


class ViewHTTPTests(unittest.TestCase):
    def test_views_after_properties_and_source_unchanged(self):
        servers=[];APIStub.calls=[]
        try:
            for label in ('source','target'):
                server=ThreadingHTTPServer(('127.0.0.1',0),getattr(self,'handler_class',ViewsAPI))
                server.label=label;server.columns={};server.coll_count=0;server.obj_count=0;server.prop_count=0
                threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server)
            page={'id':'a','name':'Dune','type':'book'}
            collection={'id':'c','name':'Library','type':'collection'}
            inventory={'all':[page,collection],'objects':[page],'collections':[collection],
                'members':{'c':[page]},'types':[{'key':'book','id':'book','name':'Books','items':[page]}]}
            plan={'source_space':{'id':'src','name':'Source'},'selection':{'kind':'collection','collection_id':'c'},
                'target':{'space_mode':'create','space_name':'Destination','collection_mode':'create','collection_name':'Library','type_mappings':[]},
                'mode':'simple','follow_links':False,'files':False}
            result=list(Engine(Anytype(servers[0].server_port,'test-key'),Anytwo(servers[1].server_port),inventory,plan).run())[-1]
            self.assertEqual(len(result['objects']),1)
            self.assertEqual([v['status'] for v in result['views']],['created','created'])
            calls=APIStub.calls
            self.assertFalse(any(label=='source' for label,method,path,raw in calls))
            property_index=next(i for i,c in enumerate(calls) if '/set/' in c[2])
            view_indices=[i for i,c in enumerate(calls) if c[2].endswith('/modify')]
            self.assertTrue(all(i>property_index for i in view_indices))
            view_bodies=[json.loads(calls[i][3]) for i in view_indices if json.loads(calls[i][3])['dataset']=='views']
            self.assertEqual(len(view_bodies),2)
            for body in view_bodies:
                fields={op['path']:op['value'] for op in body['records'][0]['ops']}
                self.assertEqual(fields['query']['filter']['$and'][0],{'id':{'$in':['new1']}})
                self.assertIn('coll2.p1',json.dumps(fields['query']))
            content=json.loads(next(c[3] for c in calls if c[1]=='PUT'))['content']
            self.assertLess(content.index('BEFORE'),content.index('Vue :'))
            self.assertLess(content.index('Vue :'),content.index('AFTER'))
            self.assertFalse(result['objects'][0]['errors'])
        finally:
            for server in servers:server.shutdown();server.server_close()



class PropertiesAPI(ViewsAPI):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/v2/spaces/src/properties':
            return self.answer(200,{'data':[{'key':'Rating','name':'Rating','format':'number'},
                {'key':'Status','name':'Status','format':'select','options':[{'name':'Ready','color':'teal'},'Unused']},
                {'key':'Related','name':'Related','format':'objects'}],'has_more':False})
        if path=='/v2/spaces/src/types/book':
            return self.answer(200,{'property_definitions':[{'property':'Rating','format':'number'},
                {'property':'Status','format':'select','description':'Workflow', 'readonly':True,
                 'options':[{'name':'Ready','color':'teal'},'Unused']},
                {'property':'Related','format':'objects','max_count':1,'object_types':['type-book']}]})
        if path=='/v2/spaces/src/objects/a':
            return self.answer(200,{'properties':{'name':'Dune','Rating':4,'Status':'Ready','Related':['a']},
                'blocks':[{'type':'paragraph','text':'BEFORE'},
                    {'type':'dataview','object_id':'c','views':[{'filters':[{'property':'Rating','condition':'greater','value':3}]}]},
                    {'type':'paragraph','text':'AFTER'}]})
        super().do_GET()


class PropertyHTTPTests(ViewHTTPTests):
    handler_class=PropertiesAPI

    def test_views_after_properties_and_source_unchanged(self):
        super().test_views_after_properties_and_source_unchanged()
        properties=[json.loads(c[3]) for c in APIStub.calls if c[1]=='POST' and c[2].endswith('/properties')]
        status=next(p for p in properties if p['name']=='Status')
        self.assertEqual(status['description'],'Workflow')
        options=list(status['xFormat']['options'].values())
        self.assertEqual([o['name'] for o in options],['Ready','Unused'])
        self.assertEqual(options[0]['color'],'teal')
        self.assertTrue(json.loads(status['xFormat']['any2any']['sourceSettings'])['readonly'])
        related=next(p for p in properties if p['name']=='Related')
        self.assertFalse(related['xFormat']['config']['multiple'])
        self.assertEqual(related['xFormat']['relation']['targetTypes'],['coll2'])
        values=[json.loads(c[3]) for c in APIStub.calls if '/set/' in c[2]]
        self.assertTrue(any(v==['any://new1'] for row in values for v in row['patch'].values()))


if __name__=='__main__':unittest.main()
