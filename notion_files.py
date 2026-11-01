"""Bounded, unauthenticated download of public Notion attachment URLs."""
import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from anytwo_backend import APIError

LIMIT=100*1024*1024


def validate_url(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise APIError('Pièce jointe : URL HTTPS publique requise.')
    try:addresses=socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
    except OSError:raise APIError('Hôte de pièce jointe indisponible.') from None
    if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
        raise APIError('Pièce jointe : adresse réseau locale ou privée refusée.')


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def filename(value,fallback='fichier'):
    value=str(value or fallback).replace('\\','/').rsplit('/',1)[-1]
    value=''.join(c for c in value if ord(c)>=32 and c not in '<>:"|?*')
    return value[:220].strip(' .') or fallback


def download(url,preferred='',check=lambda:None):
    validate_url(url);check()
    # Never forward the Notion API token, including to signed file URLs.
    req=urllib.request.Request(url,headers={'User-Agent':'Any2Any-Notion'})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}),PublicRedirect()).open(req,timeout=25) as response:
            if int(response.headers.get('Content-Length') or 0)>LIMIT:raise APIError('Pièce jointe supérieure à 100 Mo.')
            chunks=[];size=0
            while True:
                check();chunk=response.read(min(1024*1024,LIMIT+1-size))
                if not chunk:break
                chunks.append(chunk);size+=len(chunk)
                if size>LIMIT:raise APIError('Pièce jointe supérieure à 100 Mo.')
            header=Message();header['Content-Disposition']=response.headers.get('Content-Disposition','')
            name=preferred or header.get_filename() or urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/',1)[-1])
            return b''.join(chunks),response.headers.get_content_type(),filename(name)
    except (urllib.error.URLError,OSError,ValueError):
        raise APIError('Téléchargement de pièce jointe impossible ; URL expirée ou hébergeur indisponible.') from None
