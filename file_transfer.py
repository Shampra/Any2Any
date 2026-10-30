"""Filename provenance and space-local, content-verified file reuse."""
import hashlib
import re
import unicodedata
from api_clients import APIError,local_get,local_binary,unwrap_list,_segment


def strip_import_prefix(name):
    # Keep hash-only and SHA-256 filenames. Strip only the 32-hex + readable
    # basename convention observed in imported clipboard attachments.
    stem=name.rsplit('.',1)[0]
    if re.fullmatch(r'[0-9a-fA-F]{32,}',stem):return name
    match=re.match(r'^[0-9a-fA-F]{32}(.+)$',name)
    if not match:return name
    suffix=match[1].lstrip('_- ')
    if not suffix or suffix.startswith('.') or not any(c.isalpha() for c in suffix.rsplit('.',1)[0]):return name
    return suffix


def filename_key(name):
    return unicodedata.normalize('NFC',strip_import_prefix(str(name))).casefold()


class FileLibrary:
    def __init__(self,api,sid):
        self.api=api;self.sid=sid;self.rows=None;self.hashes={};self.known={}

    def find(self,name,content):
        digest=hashlib.sha256(content).hexdigest();key=(filename_key(name),digest)
        if key in self.known:return self.known[key]
        if self.rows is None:
            self.rows=[]
            try:
                result=local_get(self.api.port,f'/v1/spaces/{_segment(self.sid)}/files?limit=10000',timeout=12)
                self.rows=unwrap_list(result,'files')
            except (APIError,AttributeError):pass  # older clients: upload normally
        for row in self.rows:
            fid=row.get('fileId') or row.get('id')
            if not fid or row.get('variant') or filename_key(row.get('name',''))!=key[0]:continue
            if row.get('size')!=len(content):continue
            if fid not in self.hashes:
                try:
                    data,_=local_binary(self.api.port,f'/v1/spaces/{_segment(self.sid)}/files/{_segment(fid)}/content',max_bytes=100*1024*1024)
                    self.hashes[fid]=hashlib.sha256(data).hexdigest()
                except (APIError,AttributeError):self.hashes[fid]=None
            if self.hashes[fid]==digest:
                self.known[key]=str(fid)
                return str(fid)
        return None

    def register(self,name,content,fid):
        self.known[(filename_key(name),hashlib.sha256(content).hexdigest())]=str(fid)
