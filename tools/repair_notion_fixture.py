"""Repair the imported synthetic model only; keep a backup and all page identities."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server
import anytwo_backend as backend
from notion_source import Notion,title
from notion_migration import Engine
from notion_content import Content
from notion_native import prepare_synced,finalise
from file_transfer import FileLibrary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    settings=server.load_settings();old=json.loads((ROOT/'reports/notion-integration.json').read_text(encoding='utf-8'))
    page='40a8845c-26f6-817c-b253-d56cd670f883';source=Notion(settings['notion_token']);target=backend.Anytwo(settings['anytwo_port'])
    space=next(x for x in target.spaces() if x['id']==old['target_space'])
    if space['name']!='Test import Notion — Any2Any 2026-10-31 19-49-19':raise SystemExit('Refus : espace de test attendu absent.')
    if title(source.page(page))!='Modèle de test — Any2Any':raise SystemExit('Refus : source différente du modèle.')
    sid=space['id'];oid=old['mapping'][page]
    record=backend.local_get(target.port,f'/v1/spaces/{sid}/properties/{oid}')['record']
    if record.get('any',{}).get('name')!='Modèle de test — Any2Any':raise SystemExit('Refus : cible différente du modèle.')
    before=backend.local_get(target.port,f'/v1/spaces/{sid}/objects/{oid}/editor/editor_blocks/markdown')
    roots=backend.local_get(target.port,f'/v1/spaces/{sid}/objects/query',method='POST',body={'filter':{'any.type':'dataview'},'limit':100})['records']
    hosts={oid}|{x['target_id'] for x in old['collections']}
    generated=[r for r in roots if r.get('dataview',{}).get('host') in hosts and r.get('any',{}).get('name') in ('Vues Anytype','Vues Notion')]
    if not args.apply:
        print(json.dumps({'space':space['name'],'page':oid,'technical_names_to_clear':len(generated),'write':False},ensure_ascii=False));return
    backup=ROOT/'reports'/('before-notion-native-repair-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    backup.write_text(json.dumps({'page':oid,'space':sid,'markdown':before,'technical_objects':generated},ensure_ascii=False,indent=2),encoding='utf-8')
    selection=source.selection('page',page,True)
    e=Engine(source,target,selection,old['options'],resume=old,progress=lambda message:print(message,flush=True))
    e.collect();e.library=FileLibrary(target,sid);prepare_synced(e)
    content=Content(e,page).render(e.blocks[page])
    (ROOT/'reports/notion-native-candidate.md').write_text(content,encoding='utf-8')
    backend.set_markdown(target,sid,oid,content);finalise(e)
    for row in generated:backend.set_column_value(target,sid,row['id'],'any','name',None)
    after=backend.local_get(target.port,f'/v1/spaces/{sid}/objects/{oid}/editor/editor_blocks/markdown')
    (ROOT/'reports/notion-native-readback.md').write_text(after['content'],encoding='utf-8')
    checks=[]
    for row in generated:
        value=backend.local_get(target.port,f'/v1/spaces/{sid}/properties/{row["id"]}')['record']
        checks.append({'id':row['id'],'name':value.get('any',{}).get('name'),'host':value.get('dataview',{}).get('host')})
    result={'page':oid,'space':sid,'issues':sorted(e.issues(page)),'synced_blocks':e.report.get('synced_blocks'),
            'technical_objects':checks,'backup':str(backup)}
    (ROOT/'reports/notion-native-repair.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
