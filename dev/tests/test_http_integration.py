"""Real HTTP JSON + binary roundtrip, with in-memory fake services."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from urllib.parse import urlsplit
from api_clients import Anytype, Anytwo
from migration import Engine

class APIStub(BaseHTTPRequestHandler):
    calls=[]
    def log_message(self,*args): pass
    def answer(self,code,data):
        content=json.dumps(data).encode() if not isinstance(data,bytes) else data
        self.send_response(code);self.send_header('Content-Type','application/json' if not isinstance(data,bytes) else 'image/png')
        self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def do_GET(self):
        url=urlsplit(self.path);path=url.path
        if path.endswith('/properties') and path.startswith('/v2/'):
            return self.answer(200, {'data':[{'key':'Rating','name':'Rating','format':'number'}], 'has_more':False})
        if path=='/v2/spaces/src/types/book':
            return self.answer(200,{'property_definitions':[{'property':'Rating','format':'number'},
                                                               {'property':'EmptyColumn','name':'EmptyColumn','format':'text'}]})
        if path=='/v2/spaces/src/objects/a':
            return self.answer(200, {'properties':{'name':'Dune','Rating':4},'blocks':[
                {'type':'paragraph','text':'Voir [Herbert](anytype://object?objectId=b)'},
                {'type':'image','object_id':'file-1','name':'cover.png','mime_type':'image/png'},
                {'type':'dataview','id':'embed'}]})
        if path=='/v2/spaces/src/objects/b':
            return self.answer(200,{'properties':{'name':'Herbert'},'blocks':[{'type':'paragraph','text':'Auteur'}]})
        if path=='/v2/spaces/src/files/file-1/content': return self.answer(200,b'\x89PNG\r\nFake')
        if path.endswith('/properties') and path.startswith('/v1/'):
            return self.answer(200,{'properties':self.server.columns.get(path,[])})
        return self.answer(404,{'message':'Unexpected GET '+path})
    def do_POST(self):
        path=urlsplit(self.path).path
        size=int(self.headers.get('Content-Length','0'));raw=self.rfile.read(size)
        self.calls.append((self.server.label,'POST',path,raw))
        if path=='/v1/spaces':return self.answer(201,{'id':'dest'})
        if path.endswith('/collections') and path.startswith('/v1/spaces/'):
            self.server.coll_count+=1
            return self.answer(201,{'collectionId':'coll'+str(self.server.coll_count)})
        if path.endswith('/objects') and path.startswith('/v1/spaces/'):
            self.server.obj_count+=1
            return self.answer(201,{'objectId':'new'+str(self.server.obj_count)})
        if path.endswith('/properties') and path.startswith('/v1/spaces/'):
            data=json.loads(raw)
            self.server.prop_count+=1
            prop={'id':'p'+str(self.server.prop_count), **data}
            self.server.columns.setdefault(path,[]).append(prop)
            return self.answer(201,{'propId':prop['id']})
        if '/files' in path and path.startswith('/v1/'):
            return self.answer(201,{'id':'uploaded-file-1'})
        if '/set/' in path:return self.answer(200,{'versionId':'v1','recordIds':[]})
        return self.answer(404,{'message':'Unexpected POST '+path})
    def do_PUT(self):
        path=urlsplit(self.path).path
        size=int(self.headers.get('Content-Length','0'));raw=self.rfile.read(size)
        self.calls.append((self.server.label,'PUT',path,raw))
        if path.endswith('/editor/editor_blocks/markdown'):
            return self.answer(200,{'inserted':['b'],'updated':[],'deleted':[],'unchanged':0})
        return self.answer(404,{'message':'Unexpected PUT '+path})

class RealHTTPEngineTests(unittest.TestCase):
    def test_end_to_end_http_binary_and_properties(self):
        servers=[];APIStub.calls=[]
        try:
            for name in ('source','target'):
                srv=ThreadingHTTPServer(('127.0.0.1',0),APIStub)
                srv.label=name;srv.columns={};srv.coll_count=0;srv.obj_count=0;srv.prop_count=0
                thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start();servers.append(srv)
            a={'id':'a','name':'Dune','type':'book'};b={'id':'b','name':'Herbert','type':'book'}
            col={'id':'c','name':'Bibliothèque','type':'collection'}
            inv={'objects':[a,b], 'all':[a,b,col],'collections':[col],'members':{'c':[a]},
                 'types':[{'id':'book','key':'book','name':'Books','items':[a,b]}]}
            plan={'source_space':{'id':'src','name':'Maison'},
                  'selection':{'kind':'collection','collection_id':'c'},
                  'target':{'space_mode':'create','space_name':'Transfert','collection_mode':'create',
                            'collection_name':'Bibliothèque','type_mappings':[]},
                  'mode':'simple','follow_links':True,'files':True}
            events=list(Engine(Anytype(servers[0].server_port,'api-key'),
                               Anytwo(servers[1].server_port),inv,plan).run())
            report=events[-1];self.assertEqual(report['event'],'summary')
            self.assertEqual(report['totals']['total'],2)
            self.assertEqual(report['totals']['error'],0)
            self.assertEqual(servers[1].obj_count,2)
            self.assertGreaterEqual(servers[1].prop_count,2) # Rating and empty column
            puts=[x for x in APIStub.calls if x[1]=='PUT']
            self.assertEqual(len(puts),2)
            content=json.loads(puts[0][3])['content']
            self.assertIn('any://o/dest/new2',content)
            self.assertIn('any://f/dest/uploaded-file-1',content)
            self.assertIn('Attention : collection ou vue intégrée non importée',content)
            uploads=[x for x in APIStub.calls if '/files' in x[2]]
            self.assertEqual(uploads[0][3],b'\x89PNG\r\nFake')
        finally:
            for srv in servers: srv.shutdown();srv.server_close()

if __name__=='__main__':unittest.main()
