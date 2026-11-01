"""Publish the tested source archive from GitHub Actions using its ephemeral token."""
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
sys.path.insert(0,str(ROOT/'dev'))
from app_version import VERSION
from tools.build_release import build

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


def request(url,token,body=None,*,method='GET',content_type='application/json'):
    if urllib.parse.urlsplit(url).hostname not in ('api.github.com','uploads.github.com'):raise ValueError('Unexpected GitHub API host')
    data=json.dumps(body).encode('utf-8') if isinstance(body,dict) else body
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',
             'User-Agent':'Any2Any-release/'+VERSION,'Content-Type':content_type}
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=120) as response:return json.load(response)


def publish(require_windows=False):
    repo=os.environ.get('GITHUB_REPOSITORY','');sha=os.environ.get('GITHUB_SHA','');token=os.environ.get('GH_TOKEN','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo) or not re.fullmatch(r'[0-9a-f]{40}',sha) or not token:
        raise ValueError('GitHub Actions repository, commit and ephemeral token are required')
    tag='v'+VERSION;base='https://api.github.com/repos/'+repo
    archive,_,_=build();notes=(ROOT/'docs/releases'/ (VERSION+'.md')).read_text(encoding='utf-8')
    assets_to_upload=[(archive,'application/zip'),(archive.with_suffix('.sha256'),'text/plain')]
    if require_windows:
        windows=ROOT/('dev/dist/Any2Any-Windows-'+VERSION+'.zip')
        if not windows.is_file() or not windows.with_suffix('.sha256').is_file():raise ValueError('Verified Windows archive is required before publication')
        assets_to_upload.extend([(windows,'application/zip'),(windows.with_suffix('.sha256'),'text/plain')])
    try:release=request(base+'/releases/tags/'+tag,token)
    except urllib.error.HTTPError as exc:
        if exc.code!=404:raise
        release=request(base+'/releases',token,{'tag_name':tag,'target_commitish':sha,'name':'Any2Any '+VERSION+' — Anytype + Notion',
                                                'body':notes,'draft':True,'prerelease':True},method='POST')
    if not release['draft']:
        raise ValueError('Release already published; refusing to overwrite it')
    if release.get('target_commitish') not in (sha,'release/unified'):
        raise ValueError('Existing draft targets another commit; refusing to overwrite it')
    existing={asset['name'] for asset in release.get('assets',[])}
    for path,mime in assets_to_upload:
        if path.name in existing:raise ValueError('Draft already has an asset with this name; inspect it before retrying')
        upload=release['upload_url'].split('{',1)[0]+'?'+urllib.parse.urlencode({'name':path.name})
        answer=request(upload,token,path.read_bytes(),method='POST',content_type=mime)
        if answer.get('size')!=path.stat().st_size:raise ValueError('Uploaded asset size mismatch')
    result=request(base+'/releases/'+str(release['id']),token,{'draft':False,'prerelease':True,'body':notes},method='PATCH')
    print('Published '+result['html_url'])


if __name__=='__main__':publish(require_windows=True)
