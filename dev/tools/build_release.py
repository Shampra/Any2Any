"""Build a reproducible source distribution with an explicit public-file allowlist."""
import hashlib
import json
import sys
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
sys.path.insert(0,str(ROOT/'dev'))
from app_version import VERSION
APP_FILES=('app_version.py', 'anytwo_backend.py', 'api_clients.py', 'chat_archives.py', 'file_transfer.py', 'inline_views.py', 'logic.py', 'migration.py', 'notion_cache.py', 'notion_compatibility.py', 'notion_content.py', 'notion_demo.py', 'notion_files.py', 'notion_icons.py', 'notion_import_jobs.py', 'notion_jobs.py', 'notion_migration.py', 'notion_native.py', 'notion_routes.py', 'notion_source.py', 'notion_tree.py', 'notion_views.py', 'rich_content.py', 'runtime_profile.py', 'server.py', 'source_views.py', 'view_conversion.py')
PUBLIC_FILES=('README.md','README.en.md','LICENSE','CHANGELOG.md','demarrer.bat','demo.bat',
              'docs/NOTES-TECHNIQUES.fr.md','docs/NOTION-API.fr.md','docs/NOTION-IMPORT.fr.md')


def build(root=ROOT,output=None):
    root=Path(root).resolve();output=Path(output or root/('dev/dist/Any2Any-'+VERSION+'.zip'))
    paths=[root/'app'/name for name in APP_FILES]+[root/name for name in PUBLIC_FILES]
    paths.extend(p for p in (root/'app/static').rglob('*') if p.is_file() and p.suffix in ('.js','.css','.html','.png','.svg','.ico','.woff2') and not any(part.startswith('.') for part in p.relative_to(root/'app/static').parts))
    contents={}
    for path in sorted(paths):
        if not path.resolve().is_relative_to(root):raise ValueError('Distribution file escapes the source directory')
        contents[path.relative_to(root).as_posix()]=path.read_bytes()
    manifest={name:hashlib.sha256(content).hexdigest() for name,content in contents.items()}
    contents['docs/BUILD.json']=(json.dumps({'version':VERSION,'sha256':manifest},ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,content in sorted(contents.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,content)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(digest+'  '+output.name+'\n',encoding='utf-8')
    return output,len(contents),digest


if __name__=='__main__':
    output,count,digest=build();print(str(output));print(str(count)+' public files; SHA-256 '+digest)
