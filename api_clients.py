"""API clients for Anytype v2 (read only) and Anytwo v1 (opt-in write)."""
from __future__ import annotations

import csv
import io
import os
import json
import re
import socket
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class APIError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


def local_get(port: int, path: str, *, method='GET', body: dict | None = None,
              headers: dict | None = None, timeout=3.0) -> Any:
    if not (1 <= int(port) <= 65535):
        raise APIError('Port invalide.')
    url = f'http://127.0.0.1:{int(port)}{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'Accept': 'application/json', 'User-Agent': 'Any2Any/0.9.1',
                                          **({'Content-Type': 'application/json'} if body is not None else {}),
                                          **(headers or {})})
    try:
        # Requests to the local engines must not traverse configured HTTP proxies.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as response:
            content = response.read(16 * 1024 * 1024)
            if not content:
                return {}
            return json.loads(content.decode('utf-8'))
    except urllib.error.HTTPError as exc:
        snippet = exc.read(500).decode('utf-8', 'replace')
        try:
            detail = json.loads(snippet)
            snippet = detail.get('message') or detail.get('error') or snippet
        except (ValueError, AttributeError):
            pass
        raise APIError(f'HTTP {exc.code} : {snippet}', exc.code) from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
        raise APIError(f'Connexion impossible : {exc}') from exc
    except (UnicodeDecodeError, ValueError) as exc:
        raise APIError('Réponse non JSON : adresse ou port incorrect.') from exc


def unwrap_list(payload: Any, *keys: str) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in (*keys, 'data', 'items', 'results', 'records'):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    raise APIError('Structure de liste inattendue dans la réponse de l’API.')


def item_id(row):
    return str(row.get('id') or row.get('object_id') or row.get('objectId') or
               row.get('spaceId') or row.get('space_id') or row.get('collectionId') or row.get('collection_id') or '')


def item_name(row):
    p = row.get('properties')
    if not row.get('name') and isinstance(p, dict):
        name = p.get('name', '')
    elif not row.get('name') and isinstance(p, list):
        name = next((x.get('text') or x.get('value') for x in p
                     if x.get('key') == 'name' or x.get('name') == 'Name'), '')
    else:
        name = row.get('name')
    if isinstance(name, dict):
        name = name.get('text') or name.get('value')
    return str(name or row.get('snippet') or '(Sans titre)')


def type_key(obj):
    """Normalize v2 string keys and legacy objects with a nested type descriptor."""
    val = obj.get('type') or obj.get('type_key') or obj.get('typeKey') or obj.get('layout') or ''
    if isinstance(val, dict):
        val = val.get('key') or val.get('api_key') or val.get('id') or val.get('name') or ''
    return str(val).strip()


def sort_named(rows):
    return sorted(rows, key=lambda row: (row['name'].casefold(), row['id']))


def is_one_to_one_space(row):
    """Conservative: only rely on explicit flags/kinds, never guesses from names."""
    flags = ('is_one_to_one', 'isOneToOne', 'is_direct_chat', 'isDirectChat', 'is_dm', 'isDm')
    if any(row.get(flag) is True for flag in flags):
        return True
    kind = str(row.get('space_type') or row.get('spaceType') or row.get('kind') or '').casefold()
    return kind in ('one_to_one', 'one-to-one', 'direct_chat', 'direct', 'dm', 'private_chat')


def clean_items(rows):
    result = []
    seen = set()
    for obj in rows:
        id_ = item_id(obj)
        if not id_ or id_ in seen or obj.get('archived') or obj.get('is_deleted'):
            continue
        seen.add(id_)
        result.append({'id': id_, 'name': item_name(obj),
                       'type': type_key(obj),
                       'layout': obj.get('layout') or '',
                       'raw': obj})
    return result


def paginated(port, path, key, *, method='GET', body=None, max_pages=500):
    rows = []
    offset = 0
    page_size = 200
    last = None
    for _ in range(max_pages):
        sep = '&' if '?' in path else '?'
        res = local_get(port, f'{path}{sep}offset={offset}&limit={page_size}',
                        method=method, body=body,
                        headers={'Authorization': f'Bearer {key}'} if key else None, timeout=12)
        batch = unwrap_list(res, 'spaces', 'objects', 'collections')
        rows.extend(batch)
        if isinstance(res, dict):
            has_more = res.get('has_more', res.get('hasMore'))
            total = res.get('total')
            if has_more is False or (isinstance(total, int) and offset + len(batch) >= total):
                return rows
            if has_more is None and len(batch) < page_size:
                return rows
        elif len(batch) < page_size:
            return rows
        if not batch:
            return rows
        ids = tuple(item_id(x) for x in batch)
        if ids == last:
            raise APIError('Pagination bloquée : page répétée par l’API.')
        last = ids
        offset += len(batch)
    raise APIError('Trop de pages : chargement incomplet, opération interrompue.')


@dataclass
class Anytype:
    port: int = 31009
    key: str = ''

    def check(self) -> dict:
        try:
            data = local_get(self.port, '/v2/spaces',
                             headers={'Authorization': f'Bearer {self.key}'} if self.key else None)
            unwrap_list(data, 'spaces')
            return {'state': 'ok' if self.key else 'needs_auth', 'detail': 'API connectée, accès autorisé.' if self.key else 'Clé API requise.'}
        except APIError as e:
            if e.status == 401:
                return {'state': 'needs_auth', 'detail': 'Anytype est ouvert mais demande une autorisation.'}
            if e.status == 403:
                return {'state': 'needs_auth', 'detail': 'Accès refusé : vérifiez les autorisations Anytype.'}
            return {'state': 'error', 'detail': str(e)}

    def request(self, path, *, method='GET', body=None, timeout=12):
        if not self.key:
            raise APIError('Associez d’abord Anytype pour obtenir une clé API.')
        return local_get(self.port, f'/v2{path}', method=method, body=body,
                         headers={'Authorization': f'Bearer {self.key}'}, timeout=timeout)

    def challenge(self):
        return local_get(self.port, '/v2/auth/challenges', method='POST',
                         body={'app_name': 'Anytype-Anytwo Importer'}, timeout=8)

    def finish_pairing(self, challenge_id, code):
        return local_get(self.port, '/v2/auth/api_keys', method='POST',
                         body={'challenge_id': challenge_id, 'code': code}, timeout=10)

    def spaces(self):
        rows = paginated(self.port, '/v2/spaces?ids=full', self.key)
        return sort_named([{'id': item_id(x), 'name': item_name(x)}
                           for x in rows if item_id(x) and not is_one_to_one_space(x)])

    def types(self, space_id):
        sid = urllib.parse.quote(space_id, safe='')
        rows = paginated(self.port, f'/v2/spaces/{sid}/types', self.key)
        result = []
        for x in rows:
            key = str(x.get('key') or x.get('api_key') or x.get('type_key') or x.get('id') or '').strip()
            if key:
                result.append({'id': str(x.get('id') or key), 'key': key,
                               'name': str(x.get('plural_name') or item_name(x)),
                               'layout': x.get('layout') or '',
                               'property_definitions': x.get('property_definitions'),
                               'properties': x.get('properties')})
        return sort_named(result)

    def type_detail(self, space_id, type_key):
        sid = urllib.parse.quote(space_id, safe='')
        key = urllib.parse.quote(type_key, safe='')
        return self.request(f'/spaces/{sid}/types/{key}')

    def objects(self, space_id):
        sid = urllib.parse.quote(space_id, safe='')
        rows = paginated(self.port, f'/v2/spaces/{sid}/objects', self.key)
        return clean_items(rows)

    def members(self, space_id, collection_id):
        sid = urllib.parse.quote(space_id, safe='')
        cid = urllib.parse.quote(collection_id, safe='')
        rows = paginated(self.port, f'/v2/spaces/{sid}/collections/{cid}/objects', self.key)
        return clean_items(rows)

    def object_detail(self, space_id, object_id):
        sid = urllib.parse.quote(space_id, safe='')
        oid = urllib.parse.quote(object_id, safe='')
        return self.request(f'/spaces/{sid}/objects/{oid}?ids=full')


@dataclass
class Anytwo:
    port: int

    def spaces(self):
        data = local_get(self.port, '/v1/spaces', timeout=3)
        rows = unwrap_list(data, 'spaces')
        return sort_named([{'id': item_id(x), 'name': item_name(x)} for x in rows
                           if item_id(x) and not item_name(x).strip().startswith('_')
                           and item_name(x).strip().casefold() != 'bao'])

    def collections(self, space_id):
        sid = urllib.parse.quote(space_id, safe='')
        rows = unwrap_list(local_get(self.port, f'/v1/spaces/{sid}/collections', timeout=8), 'collections')
        return sort_named([{'id': item_id(x), 'name': item_name(x)} for x in rows if item_id(x)
                and not x.get('hidden')
                and str(x.get('xKey') or x.get('x_key') or '').lower() not in ('collection', 'bin', 'miniapp')
                and item_name(x).lower() not in ('bin', 'miniapp', 'collection')])


def probe_anytwo(port: int) -> dict:
    """Distinguish unavailable ports, bootstrapping, authentication and valid API."""
    try:
        # A few preview builds expose /v1/spaces without /v1/health.
        health = None
        try:
            health = local_get(port, '/v1/health', timeout=1.8)
        except APIError as exc:
            if exc.status not in (404, 405):
                raise
        if health is not None and (not isinstance(health, dict) or 'status' not in health):
            raise APIError('Réponse /v1/health inattendue (ce port ne semble pas être Anytwo).')
        spaces = Anytwo(port).spaces()
        return {'state': 'ok', 'detail': f'API connectée sur le port {port} · {len(spaces)} espace(s) visible(s).',
                'port': port}
    except APIError as exc:
        return {'state': 'error', 'detail': f'Port {port} : {exc}'}


def windows_any_listening_ports() -> list[int]:
    """Windows-native fallback when psutil is not installed (no dependencies)."""
    if os.name != 'nt':
        return []
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    try:
        tasks = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True,
                               text=True, errors='replace', timeout=5,
                               creationflags=flags, check=True).stdout
        pids = {int(row[1]) for row in csv.reader(io.StringIO(tasks))
                if len(row) >= 2 and row[0].strip().lower() in
                ('any.exe', 'anytype-any.exe') and row[1].strip().isdigit()}
        if not pids:
            return []
        table = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True,
                               text=True, errors='replace', timeout=5,
                               creationflags=flags, check=True).stdout
        ports = []
        for line in table.splitlines():
            fields = line.split()
            if len(fields) >= 5 and fields[0].upper() == 'TCP' and fields[-1].isdigit():
                hostport = fields[1].rsplit(':', 1)
                if len(hostport) == 2 and fields[-1] and int(fields[-1]) in pids \
                        and (fields[-2].upper() in ('LISTENING', 'LISTEN', 'ÉCOUTE', 'ECOUTE')
                             or fields[2].endswith(':0')):
                    try:
                        ports.append(int(hostport[1]))
                    except ValueError:
                        pass
        return ports
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def candidate_anytwo_ports(preferred: int | None = None) -> list[int]:
    candidates = [int(preferred)] if preferred else []
    # Current reported desktop port, documented SDK default, and older builds.
    candidates.extend([31310, 7001, 2657, 5344])
    try:
        import psutil
        pids = set()
        for process in psutil.process_iter(['pid', 'name']):
            name = str(process.info.get('name') or '').lower()
            if name in ('any.exe', 'any', 'anytype-any', 'any.app'):
                pids.add(process.info['pid'])
        if pids:
            for conn in psutil.net_connections(kind='inet'):
                if conn.pid in pids and conn.status == 'LISTEN' and conn.laddr:
                    candidates.append(conn.laddr.port)
    except Exception:
        pass
    candidates.extend(windows_any_listening_ports())
    return list(dict.fromkeys(p for p in candidates if 1 <= p <= 65535))


def discover_anytwo_port(preferred: int | None = None) -> int | None:
    """Check real Anytwo /v1 API; never mistake an arbitrary service for Anytwo."""
    for port in candidate_anytwo_ports(preferred):
        # TCP probe avoids multi-second HTTP timeouts on absent ports.
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.25):
                pass
        except (OSError, TimeoutError):
            continue
        if probe_anytwo(port)['state'] == 'ok':
            return port
    return None

# --- Write operations used by the opt-in importer (never called by checks). ---

def local_binary(port, path, *, method='GET', data=None, content_type=None,
                 headers=None, max_bytes=100 * 1024 * 1024, timeout=45):
    """Bounded binary transfer, loopback only, and no environment proxies."""
    req_headers = {'User-Agent': 'Any2Any/0.9.1', **(headers or {})}
    if content_type:
        req_headers['Content-Type'] = content_type
    req = urllib.request.Request(f'http://127.0.0.1:{int(port)}{path}',
                                 data=data, method=method, headers=req_headers)
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as resp:
            length = resp.headers.get('Content-Length')
            if length and int(length) > max_bytes:
                raise APIError(f'Fichier supérieur à {max_bytes//1024//1024} Mo (limite de sécurité).')
            content = resp.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise APIError(f'Fichier supérieur à {max_bytes//1024//1024} Mo (limite de sécurité).')
            return content, resp.headers.get('Content-Type', 'application/octet-stream')
    except urllib.error.HTTPError as exc:
        raise APIError(f'HTTP {exc.code} pour le fichier : {exc.read(200).decode("utf8", "replace")}', exc.code) from exc
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
        raise APIError(f'Transfert de fichier impossible : {exc}') from exc


def anytype_property_definitions(api: Anytype, space_id: str) -> dict:
    """v2 property vocabulary; tolerate permission/version differences with warning at caller."""
    sid = urllib.parse.quote(space_id, safe='')
    rows = paginated(api.port, f'/v2/spaces/{sid}/properties', api.key)
    mapping = {}
    for prop in rows:
        for name in (prop.get('key'), prop.get('name'), prop.get('id')):
            if name:
                mapping[str(name).casefold()] = prop
    return mapping


def anytype_download(api: Anytype, space_id: str, file_id: str):
    sid = urllib.parse.quote(space_id, safe='')
    fid = urllib.parse.quote(file_id, safe='')
    return local_binary(api.port, f'/v2/spaces/{sid}/files/{fid}/content',
                        headers={'Authorization': f'Bearer {api.key}'})


def _segment(value):
    return urllib.parse.quote(str(value), safe='')


def target_write(api: Anytwo, path, body, *, method='POST', timeout=25):
    return local_get(api.port, f'/v1{path}', method=method, body=body, timeout=timeout)


def create_space(api: Anytwo, name):
    answer = target_write(api, '/spaces', {'name': name})
    sid = answer.get('id') or answer.get('spaceId')
    if not sid: raise APIError('Création de l’espace : ID absent de la réponse.')
    return str(sid)


def create_collection(api: Anytwo, sid, name, xkey):
    answer = target_write(api, f'/spaces/{_segment(sid)}/collections', {'name': name, 'xKey': xkey})
    cid = answer.get('collectionId')
    if not cid: raise APIError('Création de la collection : ID absent de la réponse.')
    return str(cid)


def create_object(api: Anytwo, sid, name, collections, emoji=None, icon_warnings=None):
    # The exact object-emoji field is client-version dependent. We only attempt
    # the intrinsic value (never put an icon in the content) and retry safely
    # when the engine rejects this optional field.
    base = {'type': 'page', 'collections': list(dict.fromkeys(collections)),
            'initialProperties': {'any': {'name': name}}}
    if emoji:
        candidate = json.loads(json.dumps(base))
        candidate['initialProperties']['any']['iconEmoji'] = emoji
        try:
            answer = target_write(api, f'/spaces/{_segment(sid)}/objects', candidate)
            oid = answer.get('objectId')
            if not oid:
                raise APIError('Création de l’objet : ID absent de la réponse.')
            return str(oid)
        except APIError as exc:
            if exc.status not in (400, 422):
                raise
            if icon_warnings is not None:
                icon_warnings.append('Icône emoji non reconnue par l’API Anytwo ; non ajoutée au contenu')
    answer = target_write(api, f'/spaces/{_segment(sid)}/objects', base)
    oid = answer.get('objectId')
    if not oid: raise APIError('Création de l’objet : ID absent de la réponse.')
    return str(oid)


def add_membership(api: Anytwo, sid, oid, cid):
    target_write(api, f'/spaces/{_segment(sid)}/properties/{_segment(oid)}/collections/{_segment(cid)}', {})


def list_columns(api: Anytwo, sid, cid):
    return unwrap_list(local_get(api.port, f'/v1/spaces/{_segment(sid)}/collections/{_segment(cid)}/properties', timeout=12), 'properties')


def add_column(api: Anytwo, sid, cid, name, xkey, kind, fmt=None):
    payload = {'name': name, 'xKey': xkey, 'kind': kind}
    if fmt: payload['xFormat'] = fmt
    data = target_write(api, f'/spaces/{_segment(sid)}/collections/{_segment(cid)}/properties', payload)
    pid = data.get('propId')
    if not pid: raise APIError('Création de la propriété : ID absent de la réponse.')
    return str(pid)


def set_column_value(api: Anytwo, sid, oid, cid, prop_id, value):
    target_write(api, f'/spaces/{_segment(sid)}/properties/{_segment(oid)}/set/{_segment(cid)}',
                 {'patch': {prop_id: value}})


def set_markdown(api: Anytwo, sid, oid, content):
    return target_write(api, f'/spaces/{_segment(sid)}/objects/{_segment(oid)}/editor/editor_blocks/markdown',
                        {'content': content}, method='PUT', timeout=35)


def append_markdown(api: Anytwo, sid, oid, content):
    if not content.strip(): return
    return target_write(api, f'/spaces/{_segment(sid)}/objects/{_segment(oid)}/editor/editor_blocks/markdown/append',
                        {'content': content}, method='POST', timeout=35)


def attach_file(api: Anytwo, sid, oid, name, content, mime):
    path = f'/v1/spaces/{_segment(sid)}/objects/{_segment(oid)}/files?name={_segment(name)}'
    data, _ = local_binary(api.port, path, method='POST', data=content,
                           content_type=mime, max_bytes=105 * 1024 * 1024)
    try:
        reply = json.loads(data.decode('utf8'))
    except (UnicodeError, ValueError) as exc:
        raise APIError('Réponse d’attachement de fichier non JSON.') from exc
    fid = reply.get('id') or reply.get('fileId')
    if not fid: raise APIError('Fichier transféré mais identifiant Anytwo absent.')
    return str(fid)


def get_file_info(api: Anytwo, sid, fid):
    """Read back Anytwo's persisted file metadata after a CSV upload.

    Not all preview builds implement this route. Callers must treat an APIError
    here as a non-fatal, unavailable verification rather than a failed upload.
    """
    return local_get(api.port,
                     f'/v1/spaces/{_segment(sid)}/files/{_segment(fid)}', timeout=5)


def create_editor_block(api: Anytwo, sid: str, oid: str, kind: str, text: str,
                        style: dict | None = None, parent_id: str = '') -> str:
    """Add a native editor block, with open-ended style validated by the engine."""
    body = {'type': kind, 'text': text}
    if style:
        body['style'] = style
    if parent_id:
        body['nav'] = {'parentId': parent_id}
    result = target_write(api, f'/spaces/{_segment(sid)}/objects/{_segment(oid)}/editor/editor_blocks/blocks', body)
    ids = result.get('recordIds') or []
    if not ids:
        raise APIError('Création du bloc : aucun identifiant retourné.')
    return str(ids[0])
