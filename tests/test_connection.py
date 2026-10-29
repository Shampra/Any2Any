"""Compatibility and port probing regression tests for the local Anytwo engine."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from api_clients import candidate_anytwo_ports, probe_anytwo, discover_anytwo_port


class Engine(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        if self.path == '/v1/health':
            status = 200
            data = {'status': 'ok', 'account': 'test-account', 'version': '0.2.3'}
        elif self.path == '/v1/spaces':
            status = 200
            data = {'spaces': [{'id': 's123', 'name': 'Espace de test'}]}
        else:
            status = 404
            data = {'message':'route not found'}
        encoded=json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class EngineWithoutHealth(Engine):
    def do_GET(self):
        if self.path == '/v1/health':
            self.send_response(404); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(b'{"message":"not found"}')
        else:
            super().do_GET()


class ConnectionTests(unittest.TestCase):
    def test_current_default_port_and_user_preference(self):
        ports=candidate_anytwo_ports()
        self.assertEqual(ports[0],31310)
        self.assertIn(7001,ports)
        self.assertEqual(candidate_anytwo_ports(54321)[0],54321)
    def test_health_and_spacelist(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Engine)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            self.assertEqual(probe_anytwo(server.server_port)['state'],'ok')
            self.assertEqual(discover_anytwo_port(server.server_port),server.server_port)
        finally:
            server.shutdown();server.server_close()
    def test_older_engine_without_health_route(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),EngineWithoutHealth)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            self.assertEqual(probe_anytwo(server.server_port)['state'],'ok')
        finally:
            server.shutdown();server.server_close()

if __name__ == '__main__':unittest.main()
