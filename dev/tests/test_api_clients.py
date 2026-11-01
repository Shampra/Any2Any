import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from api_clients import Anytype, Anytwo, APIError, is_one_to_one_space

class API(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        path = urlsplit(self.path).path
        query = parse_qs(urlsplit(self.path).query)
        status=200
        if path=='/v2/spaces': data={'data':[{'id':'s1','name':'Source'}, {'id':'s2','name':'Achat'}, {'id':'dm','name':'1-to-1','space_type':'direct_chat'}],'has_more':False,'total':3}
        elif path=='/v2/spaces/s1/types': data={'data':[{'id':'type-page','key':'page','name':'Pages','layout':'basic'}],'has_more':False,'total':1}
        elif path=='/v2/spaces/s1/objects': data={'data':[{'id':'c1','name':'Livres','type':'collection'}, {'id':'b1','name':'Dune','type':'page'}], 'total':2, 'has_more':False}
        elif path=='/v2/spaces/s1/collections/c1/objects': data={'data':[{'id':'b1','name':'Dune','type':'page'}], 'total':1, 'has_more':False}
        elif path=='/v2/spaces/s1/objects/b1': data={'id':'b1','properties':{'name':'Dune'},'blocks':[]}
        elif path=='/v1/spaces': data={'spaces':[{'id':'d1','name':'Destination'},{'id':'d2','name':'Bao'}, {'id':'d3','name':'_agentrepo'}, {'id':'d4','name':'Archives'}]}
        elif path=='/v1/spaces/d1/collections': data={'collections':[{'id':'z1','name':'Bin','hidden':True},{'id':'t1','name':'Livres','xKey':'livres'}]}
        else:status=404;data={'message':'not found'}
        response=json.dumps(data).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)

class APIClientsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv=ThreadingHTTPServer(('127.0.0.1',0),API)
        cls.thread=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.thread.start()
        cls.port=cls.srv.server_port
    @classmethod
    def tearDownClass(cls):cls.srv.shutdown();cls.srv.server_close()
    def test_anytype(self):
        client=Anytype(self.port,'example-key')
        self.assertEqual(client.check()['state'],'ok')
        self.assertEqual([x['name'] for x in client.spaces()], ['Achat','Source'])
        self.assertEqual([x['name'] for x in client.types('s1')],['Pages'])
        self.assertEqual(len(client.objects('s1')),2)
        self.assertEqual(client.members('s1','c1')[0]['name'],'Dune')
        self.assertEqual(client.object_detail('s1','b1')['id'],'b1')
    def test_one_to_one_filter_is_conservative(self):
        self.assertFalse(is_one_to_one_space({'name':'Conversation avec Alex'}))
        self.assertTrue(is_one_to_one_space({'space_type':'direct_chat'}))

    def test_anytwo(self):
        client=Anytwo(self.port)
        self.assertEqual([x['name'] for x in client.spaces()],['Archives','Destination'])
        self.assertEqual([x['name'] for x in client.collections('d1')],['Livres'])

if __name__=='__main__':unittest.main()
