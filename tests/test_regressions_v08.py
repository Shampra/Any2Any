"""CSV MIME and filename regression tests (file previews, Anytwo)."""
import unittest
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs
from api_clients import APIError, Anytype, Anytwo
from migration import Engine, file_metadata, resolve_file_mime, safe_filename


class FileSource:
    def __init__(self, docs=None):
        self.docs = docs or {}
        self.lookups = []

    def object_detail(self, sid, fid):
        self.lookups.append(fid)
        if fid not in self.docs:
            raise APIError('File object not exposed')
        return self.docs[fid]


class CsvUploadHTTPStub(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/v2/spaces/space-src/files/csv-id/content':
            data = b'col1,col2\n1,2\n'
            mime = 'application/octet-stream'
        elif path == '/v1/spaces/space-dest/files/uploadedcsv':
            data = json.dumps({'id': 'uploadedcsv',
                               'mime': self.server.received['mime'],
                               'name': self.server.received['name']}).encode()
            mime = 'application/json'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != '/v1/spaces/space-dest/objects/new-page/files':
            self.send_error(404)
            return
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.server.received = {'mime': self.headers.get('Content-Type'),
                                'name': parse_qs(url.query).get('name', [''])[0],
                                'bytes': data}
        payload = b'{"id":"uploadedcsv"}'
        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class RegressionV08(unittest.TestCase):
    def engine(self, source=None, objects=None):
        src = source or FileSource()
        inv = {'all': objects or [], 'objects': [], 'types': [], 'collections': [], 'members': {}}
        plan = {'source_space': {'id': 'space-src', 'name': 'Source'}, 'target': {}}
        engine = Engine(src, object(), inv, plan)
        engine.dest_sid = 'space-dest'
        engine.mapping = {'page-id': 'new-page'}
        engine.results = {'page-id': {'issues': set()}}
        return engine

    def test_csv_is_text_csv_even_if_anytype_claims_generic_or_excel(self):
        for supplied in (None, 'application/octet-stream', 'binary/octet-stream',
                         'application/vnd.ms-excel', 'text/plain; charset=utf-8'):
            with self.subTest(supplied=supplied):
                self.assertEqual(resolve_file_mime('export.CSV', supplied, 'application/octet-stream'),
                                 'text/csv')

    def test_existing_working_formats_keep_specific_mime(self):
        cases = [
            ('outil.bat', 'text/plain', 'application/octet-stream', 'text/plain'),
            ('classeur.xls', 'application/vnd.ms-excel', 'application/octet-stream', 'application/vnd.ms-excel'),
            ('calendrier.ics', 'text/calendar', 'application/octet-stream', 'text/calendar'),
            ('application.log', 'text/plain', 'application/octet-stream', 'text/plain'),
            ('photo.png', 'image/png', 'application/octet-stream', 'image/png'),
        ]
        for name, declared, detected, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(resolve_file_mime(name, declared, detected), expected)
        self.assertEqual(resolve_file_mime('liste.txt', None, 'application/octet-stream'), 'text/plain')

    def test_csv_upload_preserves_name_and_type_and_uri(self):
        engine = self.engine()
        with patch('migration.anytype_download', return_value=(b'col1,col2\na,b\n', 'application/octet-stream')) as download, \
             patch('migration.attach_file', return_value='uploaded'), \
             patch('migration.get_file_info', return_value={'mime': 'text/csv'}) as verify:
            from migration import attach_file
            uri = engine.add_file('page-id', 'csv-id', 'data.csv', None)
            self.assertEqual(uri, 'any://f/space-dest/uploaded')
            attach_file.assert_called_once_with(engine.target, 'space-dest', 'new-page', 'data.csv',
                                                b'col1,col2\na,b\n', 'text/csv')
            verify.assert_called_once()
            self.assertEqual(engine.results['page-id']['issues'], set())
            self.assertEqual(engine.add_file('page-id', 'csv-id', 'data.csv', None), uri)
            download.assert_called_once()

    def test_file_property_recovers_original_name_from_inventory(self):
        engine = self.engine(objects=[{'id':'file-csv','name':'Documents 2026.csv'}])
        with patch('migration.anytype_download', return_value=(b'a;b\n1;2', 'application/octet-stream')), \
             patch('migration.attach_file', return_value='new-file') as upload, \
             patch('migration.get_file_info', return_value={'mime':'text/csv'}):
            engine.add_file('page-id', 'file-csv', 'Documents-file-csv', None)
            self.assertEqual(upload.call_args.args[3], 'Documents 2026.csv')
            self.assertEqual(upload.call_args.args[5], 'text/csv')
        self.assertEqual(engine.source.lookups, [])  # no extra network call needed

    def test_file_property_recovers_original_name_from_file_object(self):
        source = FileSource({'file-csv': {'properties': {'name': 'Export commandes.csv',
                                                        'mime_type': 'application/octet-stream'}}})
        engine = self.engine(source)
        with patch('migration.anytype_download', return_value=(b'a,b\n1,2', 'application/octet-stream')), \
             patch('migration.attach_file', return_value='new-file') as upload, \
             patch('migration.get_file_info', side_effect=APIError('Old build')):
            engine.add_file('page-id', 'file-csv', 'Pieces_jointes-file-csv', None)
            self.assertEqual(upload.call_args.args[3], 'Export commandes.csv')
            self.assertEqual(upload.call_args.args[5], 'text/csv')
        self.assertEqual(source.lookups, ['file-csv'])
        self.assertEqual(engine.results['page-id']['issues'], set())

    def test_readback_mime_mismatch_is_reported_not_silenced(self):
        engine = self.engine()
        with patch('migration.anytype_download', return_value=(b'a,b\n1,2', 'text/csv')), \
             patch('migration.attach_file', return_value='new-file'), \
             patch('migration.get_file_info', return_value={'mime': 'application/octet-stream'}):
            engine.add_file('page-id', 'csv-id', 'donnees.csv', None)
        self.assertTrue(any('application/octet-stream' in issue
                            for issue in engine.results['page-id']['issues']))

    def test_source_mime_text_csv_adds_extension_if_missing(self):
        engine = self.engine()
        with patch('migration.anytype_download', return_value=(b'a,b\n1,2', 'text/csv')), \
             patch('migration.attach_file', return_value='new-file') as upload, \
             patch('migration.get_file_info', return_value={'mime':'text/csv'}):
            engine.add_file('page-id', 'file-csv', 'Export', None)
            self.assertEqual(upload.call_args.args[3], 'Export.csv')
            self.assertEqual(upload.call_args.args[5], 'text/csv')

    def test_safe_filename_never_transmits_local_path(self):
        self.assertEqual(safe_filename('C:\\Users\\Me\\document.csv'), 'document.csv')
        self.assertEqual(safe_filename('/tmp/report.csv'), 'report.csv')
        self.assertEqual(file_metadata({'properties': {'filename':'exports.csv'}})[0], 'exports.csv')

    def test_csv_real_http_request_has_correct_content_type_and_filename(self):
        servers = []
        try:
            for label in ('source', 'target'):
                srv = ThreadingHTTPServer(('127.0.0.1', 0), CsvUploadHTTPStub)
                srv.received = None
                srv.label = label
                threading.Thread(target=srv.serve_forever, daemon=True).start()
                servers.append(srv)
            engine = self.engine(Anytype(servers[0].server_port, 'test-key'))
            engine.target = Anytwo(servers[1].server_port)
            uri = engine.add_file('page-id', 'csv-id', 'Tableau.csv', None)
            self.assertEqual(uri, 'any://f/space-dest/uploadedcsv')
            self.assertEqual(servers[1].received, {
                'mime': 'text/csv', 'name': 'Tableau.csv', 'bytes': b'col1,col2\n1,2\n'})
            self.assertEqual(engine.results['page-id']['issues'], set())
        finally:
            for srv in servers:
                srv.shutdown()
                srv.server_close()


if __name__ == '__main__':
    unittest.main()
