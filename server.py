"""Local Anytype / Notion → Anytwo migrator. Python 3.10+; no remote hosting."""
from __future__ import annotations
import argparse
import base64
import json
import os
import pathlib
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app_version import VERSION
from api_clients import Anytype, Anytwo, APIError, discover_anytwo_port, probe_anytwo, candidate_anytwo_ports
from logic import build_inventory, summary_inventory, simulate
from migration import Engine

ROOT = pathlib.Path(getattr(sys, '_MEIPASS', pathlib.Path(__file__).resolve().parent))
from runtime_profile import get_profile, PROFILES, seed_unified_settings
RUNTIME_PROFILE = get_profile()
CONFIG_DIR = RUNTIME_PROFILE.config_dir
CONFIG_PATH = CONFIG_DIR / 'settings.json'
STATIC = ROOT / 'static'
STATE = {'settings': {}, 'inventories': {}, 'demo': False, 'latest_report': None}
LOCK = threading.RLock()
IMPORT_LOCK = threading.Lock()


def protected_encode(secret):
    if os.name != 'nt':
        return 'plain:' + secret
    try:
        import ctypes
        from ctypes import wintypes
        class BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
        data = secret.encode('utf-8')
        source = ctypes.create_string_buffer(data)
        blob = BLOB(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
        output = BLOB()
        if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(blob), None, None, None, None, 0, ctypes.byref(output)):
            raise OSError('DPAPI encryption failed')
        result = ctypes.string_at(output.pbData, output.cbData)
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
        ctypes.windll.kernel32.LocalFree(output.pbData)
        return 'dpapi:' + base64.b64encode(result).decode()
    except Exception:
        # Not silently stored in cleartext on Windows.
        return ''


def protected_decode(encoded):
    if encoded.startswith('plain:') and os.name != 'nt':
        return encoded[6:]
    if not encoded.startswith('dpapi:') or os.name != 'nt':
        return ''
    try:
        import ctypes
        from ctypes import wintypes
        class BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
        data = base64.b64decode(encoded[6:])
        source = ctypes.create_string_buffer(data)
        blob = BLOB(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
        output = BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob), None, None, None, None, 0, ctypes.byref(output)):
            return ''
        result = ctypes.string_at(output.pbData, output.cbData).decode('utf-8')
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
        ctypes.windll.kernel32.LocalFree(output.pbData)
        return result
    except Exception:
        return ''


def load_settings():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        return {'anytwo_port': data.get('anytwo_port', 31310),
                'anytype_port': data.get('anytype_port', 31009),
                'anytype_key': protected_decode(data.get('anytype_key', '')),
                'notion_token':protected_decode(data.get('notion_token','')),
                'notion_remember':bool(data.get('notion_token')),
                'source_kind':data.get('source_kind','notion' if RUNTIME_PROFILE.name=='notion-dev' else 'anytype')}
    except (OSError, ValueError, TypeError):
        return {'anytwo_port': 31310, 'anytype_port': 31009, 'anytype_key': '', 'notion_token':'','notion_remember':False,
                'source_kind':'notion' if RUNTIME_PROFILE.name=='notion-dev' else 'anytype'}


def save_settings():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    settings = STATE['settings']
    encoded = protected_encode(settings.get('anytype_key', '')) if settings.get('anytype_key') else ''
    data = {'anytwo_port': settings.get('anytwo_port'),
            'anytype_port': settings.get('anytype_port', 31009),
            'anytype_key': encoded,
            'source_kind':settings.get('source_kind','notion'),
            'notion_token':protected_encode(settings.get('notion_token','')) if settings.get('notion_remember') else ''}
    tmp = CONFIG_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    if os.name != 'nt':
        tmp.chmod(0o600)
    tmp.replace(CONFIG_PATH)


def save_notion_report(report):
    """Checkpoint each import in its isolated profile, without source credentials."""
    folder=CONFIG_DIR/'reports';folder.mkdir(parents=True,exist_ok=True)
    path=folder/('notion-'+str(report['id'])+'.json')
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(path)
    with LOCK:STATE['latest_report']=report


def demo_inventory(space_id):
    """Demonstrates that Type and Collection are independent dimensions."""
    def obj(id_, name, type_, layout='basic'):
        fields = [{'key':'rating','value':4}] if type_ in ('book', 'movie') else []
        return {'id': id_, 'name': name, 'type': type_, 'layout': layout,
                'raw': {'properties': fields}}
    cols = [obj('col-books','Ma bibliothèque','collection','collection'),
            obj('col-films','Films à voir','collection','collection'),
            obj('col-projects','Mes projets','collection','collection')]
    objs = [obj('book-dune','Dune','book'), obj('book-1984','1984','book'),
            obj('book-author','Frank Herbert','author'),obj('film-dune','Dune (film)','movie'),
            obj('film-inter','Interstellar','movie'),obj('proj-one','Refonte du site','task'),
            obj('stand-1','Notes personnelles','note','note'),
            obj('stand-2','Idées de lecture','page'),obj('stand-3','Réunion du lundi','page'),
            obj('contact','Camille Martin','contact')]
    groups = [
        {'id':'type-author','key':'author','name':'Authors','layout':'basic','generic':False,'items':[objs[2]]},
        {'id':'type-book','key':'book','name':'Books','layout':'basic','generic':False,'items':objs[:2]},
        {'id':'type-contact','key':'contact','name':'Contacts','layout':'basic','generic':False,'items':[objs[9]]},
        {'id':'type-movie','key':'movie','name':'Movies','layout':'basic','generic':False,'items':objs[3:5]},
        {'id':'type-note','key':'note','name':'Notes','layout':'note','generic':True,'items':[objs[6]]},
        {'id':'type-page','key':'page','name':'Pages','layout':'basic','generic':True,'items':objs[7:9]},
        {'id':'type-task','key':'task','name':'Tasks','layout':'todo','generic':False,'items':[objs[5]]}]
    for t in groups:
        state = 'no' if t['generic'] else 'yes'
        t['property_state'] = state
        t['requires_collection'] = state != 'no'
    member = {'col-books':objs[:3], 'col-films':[objs[3]],'col-projects':[objs[5]]}
    claimed = {x['id'] for group in member.values() for x in group}
    standalone = [x for x in objs if x['id'] not in claimed]
    return {'all':cols+objs,'objects':objs,'collections':cols,'members':member,
            'types':groups,'standalone':standalone,
            'stats':{'total':len(cols+objs),'collections':len(cols),
                     'types':len(groups),'standalone':len(standalone)}}


class DemoAnytype:
    def object_detail(self, space_id, objid):
        if objid == 'book-dune':
            return {'blocks':[{'type':'text','text':'Roman de Frank Herbert',
                               'target_id':'book-author'}, {'type':'link','target':'film-dune'}]}
        if objid == 'stand-2':
            return {'properties':{'objects':['book-dune']}}
        return {'blocks': []}


class Handler(BaseHTTPRequestHandler):
    server_version = 'Any2AnyUI/' + VERSION
    def log_message(self, fmt, *args):
        if os.getenv('IMPORTER_DEBUG'):
            super().log_message(fmt, *args)

    def _headers(self, content_type, code=200, length=None):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        if length is not None:
            self.send_header('Content-Length', str(length))
        self.end_headers()

    def response(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self._headers('application/json; charset=utf-8', code, len(data))
        self.wfile.write(data)

    def fail(self, err):
        self.response({'error': str(err)}, 400 if not isinstance(err, APIError) else 502)

    def _origin_ok(self):
        origin = self.headers.get('Origin')
        if not origin:
            return True
        hostname = f'http://127.0.0.1:{self.server.server_port}'
        return origin in (hostname, f'http://localhost:{self.server.server_port}')

    def _json(self):
        content_type = self.headers.get('Content-Type','')
        if not content_type.startswith('application/json'):
            raise ValueError('Requête JSON attendue.')
        size = int(self.headers.get('Content-Length', '0'))
        if not 0 <= size <= 1_000_000:
            raise ValueError('Requête trop volumineuse.')
        return json.loads(self.rfile.read(size) or b'{}')

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == '/':
            path = '/index.html'
        if path in ('/index.html', '/app.js', '/style.css', '/pair.html', '/pair.js', '/i18n.js', '/anytwo-logo.png', '/notion.js'):
            file = STATIC / path.lstrip('/')
            if file.exists():
                data = file.read_bytes()
                mime = ('image/png' if path.endswith('png') else 'text/html' if path.endswith('html') else
                        'text/javascript' if path.endswith('js') else 'text/css')
                self._headers(f'{mime}; charset=utf-8', length=len(data))
                self.wfile.write(data)
                return
        if not self._origin_ok():
            self.response({'error': 'Origine refusée.'}, 403)
            return
        try:
            if path.startswith('/api/notion/'):
                from notion_routes import handle
                return self.response(handle('GET',path,{},STATE,save_settings,protected_encode,urllib.parse.urlsplit(self.path).query))
            if path == '/api/check/anytype':
                if STATE['demo']:
                    return self.response({'state':'ok','detail':'Mode démonstration'})
                s = STATE['settings']
                return self.response(Anytype(s['anytype_port'], s['anytype_key']).check())
            if path == '/api/check/anytwo':
                if STATE['demo']:
                    return self.response({'state':'ok','detail':'Mode démonstration','port':31310})
                with LOCK:
                    preferred = STATE['settings'].get('anytwo_port')
                port = discover_anytwo_port(preferred)
                if port:
                    result = probe_anytwo(port)
                    if result['state'] == 'ok':
                        with LOCK:
                            STATE['settings']['anytwo_port'] = port
                            save_settings()
                        return self.response(result)
                # Probe first configured port for an actionable status instead of a generic error.
                initial = int(preferred or 31310)
                diagnostics = probe_anytwo(initial)
                if 'Connexion impossible' in diagnostics.get('detail', ''):
                    diagnostics['detail'] = (
                        f'Anytwo non détecté (port {initial}). Vérifiez que le client est ouvert '
                        'et que son moteur local est démarré. Vous pouvez saisir le port utilisé par any.exe.')
                diagnostics['tested_ports'] = candidate_anytwo_ports(preferred)
                return self.response(diagnostics)
            if path == '/api/spaces':
                if STATE['demo']:
                    return self.response({'source':[{'id':'demo-a','name':'Archives'},
                                                    {'id':'demo-b','name':'Espace personnel'},
                                                    {'id':'demo-c','name':'Projets'}],
                                          'target':[{'id':'local-b','name':'Espace de test'},
                                                    {'id':'local-a','name':'Espace personnel'}]})
                s = STATE['settings']
                return self.response({'source':Anytype(s['anytype_port'], s['anytype_key']).spaces(),
                                      'target':Anytwo(s['anytwo_port']).spaces()})
            if path == '/api/inventory':
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                sid = qs.get('space_id', [''])[0]
                if not sid:
                    raise APIError('Espace source manquant.')
                if STATE['demo']:
                    inventory = demo_inventory(sid)
                else:
                    s = STATE['settings']
                    inventory = build_inventory(Anytype(s['anytype_port'], s['anytype_key']), sid)
                with LOCK:
                    STATE['inventories'][sid] = inventory
                return self.response(summary_inventory(inventory))
            if path == '/api/collections':
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                sid = qs.get('space_id', [''])[0]
                if STATE['demo']:
                    collections = [{'id':'target-books','name':'Livres existants'},
                                   {'id':'target-films','name':'Films'}]
                else:
                    collections = Anytwo(STATE['settings']['anytwo_port']).collections(sid)
                return self.response({'collections':collections})
            if path == '/api/report/latest':
                if STATE.get('latest_report') is None:
                    return self.response({'error':'Pas de rapport disponible.'},404)
                return self.response(STATE['latest_report'])
            if path == '/api/config':
                s = STATE['settings']
                return self.response({'anytype_port':s.get('anytype_port',31009),
                                      'anytwo_port':s.get('anytwo_port',31310),
                                      'anytype_has_key':bool(s.get('anytype_key')),
                                      'demo':STATE['demo'],
                                      'profile':RUNTIME_PROFILE.name,
                                      'version':VERSION,
                                      'notion_available':True,
                                      'notion_import_available':not STATE['demo'],
                                      'choose_source_on_start':RUNTIME_PROFILE.name=='unified',
                                      'notion_has_token':bool(s.get('notion_token')),
                                      'source_kind':s.get('source_kind','notion' if RUNTIME_PROFILE.name=='notion-dev' else 'anytype')})
            self.response({'error':'Ressource introuvable'},404)
        except (APIError, ValueError, KeyError, TypeError) as exc:
            self.fail(exc)

    def do_POST(self):
        if not self._origin_ok():
            return self.response({'error':'Origine refusée.'},403)
        try:
            data = self._json()
            path = urllib.parse.urlsplit(self.path).path
            if path.startswith('/api/notion/'):
                from notion_routes import handle
                return self.response(handle('POST',path,data,STATE,save_settings,protected_encode,
                                            import_lock=IMPORT_LOCK,save_report=save_notion_report))
            if path == '/api/config':
                if 'source_kind' in data:
                    if data['source_kind'] not in ('anytype','notion'):raise ValueError('Source inconnue.')
                    STATE['settings']['source_kind']=data['source_kind']
                if STATE['demo']:
                    return self.response({'ok':True})
                s = STATE['settings']
                for k in ('anytype_port', 'anytwo_port'):
                    if k in data:
                        p = data[k]
                        s[k] = None if (p is None or str(p).strip() == '') and k == 'anytwo_port' else int(p)
                        if s[k] is not None and not 1 <= s[k] <= 65535:
                            raise ValueError(f'Port {k} invalide.')
                if 'anytype_key' in data:
                    s['anytype_key'] = str(data['anytype_key']).strip()
                save_settings()
                return self.response({'ok':True})
            if path == '/api/pair/start':
                return self.response(Anytype(STATE['settings']['anytype_port']).challenge())
            if path == '/api/pair/finish':
                result = Anytype(STATE['settings']['anytype_port']).finish_pairing(
                    data.get('challenge_id',''), data.get('code',''))
                key = result.get('api_key')
                if not key:
                    raise APIError('Anytype n’a pas renvoyé de clé API.')
                STATE['settings']['anytype_key'] = key
                save_settings()
                return self.response({'ok':True})
            if path == '/api/simulate':
                if STATE['settings'].get('source_kind')=='notion':raise ValueError('Utilisez l’analyse Notion dédiée.')
                self._stream_test(data)
                return
            if path == '/api/import':
                self._stream_import(data)
                return
            return self.response({'error':'Ressource introuvable'},404)
        except (APIError, ValueError, KeyError, TypeError) as exc:
            self.fail(exc)

    def _stream_import(self, plan):
        if plan.get('source_kind')=='notion' or STATE['settings'].get('source_kind')=='notion':
            return self.response({'error':'Import Notion non encore activé ; utilisez son analyse sans écriture.'},400)
        if STATE['demo']:
            return self.response({'error':'Import réel désactivé dans le mode démonstration.'},400)
        sid=(plan.get('source_space') or {}).get('id')
        inventory=STATE['inventories'].get(sid)
        if inventory is None or not sid:
            return self.response({'error':'Recharger l’inventaire Anytype avant l’import.'},400)
        if plan.get('mode') != 'simple':
            return self.response({'error':'Le mode synchronisation ne permet pas encore l’import réel.'},400)
        if not IMPORT_LOCK.acquire(blocking=False):
            return self.response({'error':'Un autre import est déjà en cours.'},409)
        with LOCK:
            STATE['latest_report']=None
        self._headers('application/x-ndjson; charset=utf-8')
        report=None
        engine=None
        try:
            s=STATE['settings']
            source=Anytype(s['anytype_port'],s['anytype_key'])
            target=Anytwo(s['anytwo_port'])
            engine=Engine(source,target,inventory,plan)
            for event in engine.run():
                if event.get('event')=='summary':
                    report={k:v for k,v in event.items() if k!='event'}
                self.wfile.write((json.dumps(event, ensure_ascii=False)+'\n').encode('utf-8'))
                self.wfile.flush()
        except (APIError, ValueError, KeyError, TypeError, OSError) as exc:
            if engine is not None:
                for result in engine.results.values():
                    if result['status'] in ('pending','created'):
                        result['errors'].append('Traitement interrompu avant la fin de cet objet.')
                        result['status']='partial' if result['target_id'] else 'error'
                report=engine.finish_report(status='interrupted',error=str(exc))
            else:
                report={'status':'interrupted','objects':[],'errors':[str(exc)],
                        'warnings':{},'totals':{'imported':0,'partial':0,'error':0,'total':0}}
            for event in ({'event':'fatal','message':str(exc)},{'event':'summary',**report}):
                try:
                    self.wfile.write((json.dumps(event,ensure_ascii=False)+'\n').encode('utf-8'))
                    self.wfile.flush()
                except OSError: break
        finally:
            if report:
                with LOCK:
                    STATE['latest_report']=report
                try:
                    d=CONFIG_DIR/'reports';d.mkdir(parents=True,exist_ok=True)
                    path=d/('import-'+__import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
                    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                except OSError:
                    pass
            IMPORT_LOCK.release()

    def _stream_test(self, plan):
        sid = (plan.get('source_space') or {}).get('id')
        inventory = STATE['inventories'].get(sid)
        if inventory is None:
            return self.response({'error':'Inventaire manquant : rechargez l’espace.'},400)
        s = STATE['settings']
        api = DemoAnytype() if STATE['demo'] else Anytype(s['anytype_port'], s['anytype_key'])
        self._headers('application/x-ndjson; charset=utf-8')
        try:
            for message in simulate(api, inventory, plan):
                line = json.dumps({'message':message}, ensure_ascii=False).encode('utf-8') + b'\n'
                self.wfile.write(line)
                self.wfile.flush()
            self.wfile.write(b'{"done":true}\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return
        except (APIError, ValueError, KeyError, TypeError) as exc:
            try:
                self.wfile.write((json.dumps({'error':str(exc)}, ensure_ascii=False)+'\n').encode('utf-8'))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass


def find_available(start):
    for port in range(start, start+20):
        sock = socket.socket()
        try:
            sock.bind(('127.0.0.1',port))
            return port
        except OSError:
            pass
        finally:
            sock.close()
    raise RuntimeError('Aucun port web local disponible.')


def configure_runtime(profile_name):
    global RUNTIME_PROFILE, CONFIG_DIR, CONFIG_PATH
    RUNTIME_PROFILE=get_profile(profile_name)
    CONFIG_DIR=RUNTIME_PROFILE.config_dir
    CONFIG_PATH=CONFIG_DIR/'settings.json'


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    parser = argparse.ArgumentParser(description='Any2Any : importer Anytype ou Notion dans Anytwo.')
    parser.add_argument('--demo', action='store_true', help='Interface avec données fictives sans APIs')
    parser.add_argument('--profile', choices=tuple(PROFILES), default=RUNTIME_PROFILE.name, help='Profil de configuration (application commune ou développement isolé)')
    parser.add_argument('--port', type=int, default=None, help='Port web (par défaut : celui du profil)')
    parser.add_argument('--no-browser', action='store_true', help='Ne pas ouvrir le navigateur')
    args = parser.parse_args()
    configure_runtime(args.profile)
    STATE['demo'] = args.demo
    seed_unified_settings(RUNTIME_PROFILE)
    STATE['settings'] = load_settings()
    port = find_available(args.port if args.port is not None else RUNTIME_PROFILE.port)
    server = ThreadingHTTPServer(('127.0.0.1',port), Handler)
    url = f'http://127.0.0.1:{port}'
    print(f'Any2Any [{RUNTIME_PROFILE.name}] · Anytype / Notion → Anytwo : {url}', flush=True)
    print(f'Configuration et rapports isolés : {CONFIG_DIR}',flush=True)
    print('Anytype : API locale. Notion : API Internet. Les sources restent en lecture seule.',flush=True)
    print('Mode démo : aucun import réel.' if args.demo else 'Import simple disponible : écriture dans Anytwo après confirmation.', flush=True)
    if not args.no_browser:
        threading.Timer(0.6, lambda:webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
