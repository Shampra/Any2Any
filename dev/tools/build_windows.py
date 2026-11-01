"""Build and verify the standalone Windows distribution (development dependency only)."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from app_version import VERSION


def package_windows(bundle,root=ROOT,output=None):
    root=Path(root).resolve();bundle=Path(bundle).resolve()
    if not (bundle/'Any2Any.exe').is_file():raise ValueError('Missing Windows executable')
    if not (bundle/'_internal').is_dir():raise ValueError('Missing bundled runtime')
    contents={p.relative_to(bundle).as_posix():p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
    for name in ('README.md','README.en.md','LICENSE','CHANGELOG.md'):
        contents['documentation/'+name]=(root/name).read_bytes()
    for name in ('NOTES-TECHNIQUES.fr.md','NOTION-API.fr.md','NOTION-IMPORT.fr.md'):
        contents['documentation/docs/'+name]=(root/'docs'/name).read_bytes()
    manifest={name:hashlib.sha256(content).hexdigest() for name,content in contents.items()}
    contents['documentation/BUILD.json']=json.dumps({'version':VERSION,'platform':'Windows x64','sha256':manifest},indent=2).encode()
    output=Path(output or root/('dev/dist/Any2Any-Windows-'+VERSION+'.zip'));output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,content in sorted(contents.items()):archive.writestr(name,content)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(digest+'  '+output.name+'\n',encoding='utf-8')
    return output


def smoke_windows(archive):
    with tempfile.TemporaryDirectory(prefix='any2any-windows-check-') as folder:
        with zipfile.ZipFile(archive) as package:package.extractall(folder)
        root=Path(folder)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        env={**os.environ,'APPDATA':str(Path(folder)/'settings'),'ANY2ANY_PROFILE':'unified'}
        proc=subprocess.Popen([str(root/'Any2Any.exe'),'--demo','--no-browser','--port',str(port)],cwd=root,env=env,
                              stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));base=f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                if proc.poll() is not None:raise RuntimeError('Bundled application exited: '+proc.stderr.read().decode(errors='replace'))
                try:
                    config=json.load(opener.open(base+'/api/config',timeout=1));break
                except OSError:time.sleep(.2)
            else:raise RuntimeError('Bundled application did not start')
            assert config['version']==VERSION and config['profile']=='unified' and config['demo']
            assert 'choose-notion' in opener.open(base+'/').read().decode()
            assert b'NotionSource' in opener.open(base+'/notion.js').read()
            for kind in ('anytype','anytwo'):assert json.load(opener.open(base+'/api/check/'+kind))['state']=='ok'
            req=urllib.request.Request(base+'/api/notion/connect',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
            assert json.load(opener.open(req))['connected']
        finally:
            if proc.poll() is None:proc.terminate()
            proc.wait(timeout=15)
    print('Extracted standalone EXE: both demo sources and embedded static files verified; no Python installation required.')


def main():
    if os.name!='nt':raise RuntimeError('Build the Windows executable on Windows')
    import PyInstaller.__main__
    build=ROOT/'dev/build';build.mkdir(parents=True,exist_ok=True)
    PyInstaller.__main__.run(['--noconfirm','--clean','--onedir','--console','--name','Any2Any','--paths',str(ROOT/'app'),
        '--add-data',str(ROOT/'app/static')+os.pathsep+'static','--distpath',str(build/'windows'),
        '--workpath',str(build/'pyinstaller'),'--specpath',str(build),str(ROOT/'app/server.py')])
    bundle=build/'windows/Any2Any'
    licenses=bundle/'documentation/licenses';licenses.mkdir(parents=True,exist_ok=True)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():(licenses/'Python-LICENSE.txt').write_bytes(python_license.read_bytes())
    from importlib.metadata import distribution
    dist=distribution('pyinstaller')
    for file in dist.files or ():
        if str(file).endswith(('COPYING.txt','LICENSE.txt')):
            source=Path(dist.locate_file(file))
            if source.is_file():(licenses/('PyInstaller-'+source.name)).write_bytes(source.read_bytes())
    output=package_windows(bundle);smoke_windows(output);print(output)

if __name__=='__main__':main()
