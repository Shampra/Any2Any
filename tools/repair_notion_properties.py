"""Repair imported synthetic properties in an explicitly selected space without recreating data or page bodies."""
import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server
import anytwo_backend as backend
from notion_migration import Engine,number_descriptor

MODEL='40a8845c-26f6-817c-b253-d56cd670f883'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--space-id',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();SPACE=args.space_id
    reports=[]
    for path in (server.CONFIG_DIR/'reports').glob('notion-*.json'):
        try:report=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):continue
        if report.get('target_space')==SPACE and MODEL in report.get('mapping',{}):reports.append((path.stat().st_mtime,path,report))
    if not reports:raise SystemExit('Bilan source du modèle dans Sri introuvable ; aucune écriture.')
    _,report_path,report=max(reports,key=lambda x:x[0])
    # Only this known synthetic report/space; no credentials or cloud calls needed.
    raw=json.loads(server.CONFIG_PATH.read_text(encoding='utf-8'));api=backend.Anytwo(raw.get('anytwo_port') or 31310)
    if not any(x['id']==SPACE for x in api.spaces()):raise SystemExit('Espace attendu absent ; aucune écriture.')
    metas=backend.local_get(api.port,f'/v1/spaces/{SPACE}/collections')['collections'];meta={x['id']:x for x in metas}
    owned={c['source_id']:c['target_id'] for c in report['collections'] if c['name'] in ('Tâches de test','Projets de test')}
    schemas={k:v for k,v in report.get('source_schemas',{}).items() if k in owned}
    if len(owned)!=2 or len(schemas)!=2:raise SystemExit('Schémas du modèle ambigus ; aucune écriture.')
    e=Engine(None,api,{'pages':{},'schemas':schemas,'warnings':[]},{'files':False,'links':False,'destination':{'id':SPACE}})
    e.sid=SPACE;e.collections=owned;e.collection_handles={s:meta[c]['xKey'] for s,c in owned.items()}
    columns={c:backend.list_columns(api,SPACE,c) for c in owned.values()};before=deepcopy(columns)
    for s,c in owned.items():
        for p in columns[c]:
            spec=json.loads((p.get('xFormat',{}).get('any2any') or {}).get('sourceSettings','{}'))
            if spec.get('id'):e.props[(s,spec['id'])]=(p['id'],p.get('kind'),p['xFormat'])
    patches=[]
    for s,c in owned.items():
        for p in columns[c]:
            spec=json.loads((p.get('xFormat',{}).get('any2any') or {}).get('sourceSettings','{}'));kind=spec.get('type')
            changes={}
            if kind=='relation':
                _,form=e.shape(s,p['name'],spec)
                if form['type']!='relation':raise SystemExit('Restriction de relation non résolue ; aucune écriture.')
                changes={'xFormat.relation.targetTypes':form['relation']['targetTypes'],'xFormat.config.multiple':form['config']['multiple']}
                e.props[(s,spec['id'])]=(p['id'],p['kind'],{**p['xFormat'],**form})
            elif kind=='number':
                form=number_descriptor(spec);changes={'xFormat.type':form['type']}
                changes.update({'xFormat.config.'+key:value for key,value in form.get('config',{}).items()})
            if changes:patches.append({'collection':c,'property':p['id'],'name':p['name'],'set':changes})
    for s,c in owned.items():
        for p in columns[c]:
            spec=json.loads((p.get('xFormat',{}).get('any2any') or {}).get('sourceSettings','{}'))
            if spec.get('type')=='rollup':
                _,form=e.rollup_shape(s,spec)
                if form['type']!='rollup':raise SystemExit('Rollup du modèle non résolu ; aucune écriture.')
                patches.append({'collection':c,'property':p['id'],'name':p['name'],'set':{'xFormat.anyui.rollup':form['anyui']['rollup']}})
    targets=set(report['mapping'].values());query={'filter':{'id':{'$in':sorted(targets)}},'limit':10000}
    objects=backend.local_get(api.port,f'/v1/spaces/{SPACE}/objects/query',method='POST',body=query)['records']
    values={x['id']:{c:x.get(c) for c in owned.values()} for x in objects}
    links=[]
    for row in report['objects']:
        if row['name'] not in ('Modèle de test — Any2Any','Sous-page de démonstration'):continue
        blocks=backend.local_get(api.port,f'/v1/spaces/{SPACE}/query',method='POST',body={'objectId':row['target_id'],'dataset':'editor_blocks','sort':['nav.pos'],'limit':10000})['records']
        top=[b for b in blocks if not b.get('nav',{}).get('parentId') and b.get('text','').strip()]
        if top:
            first=top[0];match=re.fullmatch(r'\[↑ [^\n]+\]\(any://o/'+re.escape(SPACE)+r'/([^ )]+)\)',first.get('text',''))
            if first.get('type')=='paragraph' and match and match[1] in targets:links.append({'page':row['target_id'],'name':row['name'],'block':first})
    print(json.dumps({'properties':[p['name'] for p in patches],'generated_parent_links':len(links),'apply':args.apply},ensure_ascii=False),flush=True)
    if not args.apply:return
    backup=ROOT/'reports'/('before-notion-property-repair-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    backup.write_text(json.dumps({'report':str(report_path),'space':SPACE,'properties':before,'parent_links':links,'values':values},ensure_ascii=False,indent=2),encoding='utf-8')
    for patch in patches:
        backend.target_write(api,f'/spaces/{SPACE}/collections/{patch["collection"]}/properties/{patch["property"]}',{'set':patch['set']},method='PATCH')
    for link in links:
        backend.target_write(api,f'/spaces/{SPACE}/objects/{link["page"]}/editor/editor_blocks/blocks/'+quote(link['block']['id'],safe=':'),None,method='DELETE')
    owners=[{**meta[c],'properties':backend.list_columns(api,SPACE,c)} for c in owned.values()]
    after=backend.local_get(api.port,f'/v1/spaces/{SPACE}/objects/query',method='POST',body=query)['records']
    assert values=={x['id']:{c:x.get(c) for c in owned.values()} for x in after},'Valeurs de propriétés modifiées de manière inattendue'
    result={'space':SPACE,'owners':owners,'objects':after,'patches':patches,'removed_parent_links':len(links),'backup':str(backup)}
    (ROOT/'reports/notion-property-repair.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Propriétés corrigées, valeurs inchangées et liens parents artificiels retirés.',flush=True)


if __name__=='__main__':main()
