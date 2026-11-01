"""Explicit integration check on the authored test fixture, never general user data."""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'../app'))
import server
from notion_source import Notion,notion_id,title
from notion_migration import Engine
from anytwo_backend import Anytwo,local_get,_segment


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--page',required=True);parser.add_argument('--apply',action='store_true');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    settings=server.load_settings();source=Notion(settings.get('notion_token',''));page=source.page(notion_id(args.page))
    if title(page)!='Modèle de test — Any2Any':raise SystemExit('Refus : la page doit être le modèle de test demandé, pas des données personnelles.')
    selection=source.selection('page',page['id'],True)
    print('Source de test :',len(selection['pages']),'pages,',len(selection['schemas']),'sources',flush=True)
    name='Test import Notion — Any2Any '+datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    report_path=ROOT/'reports'/'notion-integration.json';report_path.parent.mkdir(exist_ok=True)
    def save(report):
        temp=report_path.with_suffix('.tmp');temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(report_path)
    resume=json.loads(report_path.read_text(encoding='utf-8')) if args.resume else None
    if resume:name=resume['options']['destination']['name']
    engine=Engine(source,Anytwo(settings['anytwo_port']),selection,{'files':True,'links':False,'destination':{'id':'__create__','name':name}},lambda message:print(message,flush=True),save=save,resume=resume)
    if not args.apply:
        engine.collect();print('Prélecture complète réussie. Aucune écriture Anytwo.');return
    try:report=engine.run()
    except Exception as exc:
        engine.report['status']='interrupted';engine.report['errors'].append(str(exc));engine.checkpoint();raise
    print(json.dumps({'status':report['status'],'space':engine.sid,'name':name,'totals':report['totals'],'files':len({x['target_id'] for x in report.get('files',[])})},ensure_ascii=False),flush=True)
    verified=[]
    for oid,target in engine.mapping.items():
        data=local_get(engine.target.port,f'/v1/spaces/{_segment(engine.sid)}/objects/{_segment(target)}/editor/editor_blocks/markdown',timeout=15)
        content=data.get('content','');verified.append({'name':engine.names[oid],'target_id':target,'characters':len(content),'inline_view':'inline-view' in content,'toggle':'any:collapsible' in content,'file':'any://f/' in content})
    (ROOT/'reports'/'notion-integration-readback.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'readback':verified},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
