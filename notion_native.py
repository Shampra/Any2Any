"""Native desktop envelopes and references, checked against the installed client.

The HTTP Markdown bridge alone does not describe these client-owned formats.
TOCs are static block links; synced blocks remain shared inside Anytwo only.
"""
import hashlib
import json
import re
from urllib.parse import quote
import anytwo_backend as backend
from anytwo_backend import APIError, _segment
from inline_views import instance_id


def marker(kind,page,block):
    return 'ANY2ANY_NOTION_'+kind.upper()+'_'+hashlib.sha256((page+'\0'+block).encode()).hexdigest()[:24]


def envelope(kind,instance,data,body):
    header={'v':1,'kind':kind,'schema':1,'instance':instance,'data':data}
    # -- is forbidden inside envelope JSON by the client's canonical parser.
    opening=json.dumps(header,ensure_ascii=False,separators=(',',':')).replace('--',r'\u002d\u002d')
    closing=json.dumps({'instance':instance},separators=(',',':'))
    return '<!-- any:block '+opening+' -->\n\n'+body+'\n\n<!-- /any:block '+closing+' -->'


def caption_text(value):
    """Canonical plain-caption encoding used by the desktop image-caption node."""
    lines=str(value).replace('\r\n','\n').replace('\r','\n').split('\n')
    nonblank=[line for line in lines if line.strip()]
    lines=nonblank if nonblank else [''.join(lines)]
    result=[]
    for line in lines:
        line=line.replace('&','&amp;').replace('\u200c','&#8204;')
        line=re.sub(r'([\\`*_\[\]<>~|])',r'\\\1',line)
        line=re.sub(r'^([ \t]*)([#>+\-=])',r'\1\\\2',line)
        line=re.sub(r'^([ \t]*)(\d+)([.)])(?=[ \t])',r'\1\2\\\3',line)
        line=re.sub(r'\b(https?)(:)',lambda m:m[1]+'\u200c'+m[2],line,flags=re.I)
        line=line.replace('@','\u200c@')
        line=re.sub(r'\bwww\.',lambda m:m[0][:-1]+'\u200c.',line,flags=re.I)
        line=line.replace('\t','&#9;')
        line=re.sub(r'^ +',lambda m:'&#32;'*len(m[0]),line)
        line=re.sub(r' +$',lambda m:'&#32;'*len(m[0]),line)
        result.append(line)
    return '\n'.join(result)


def caption_image(image,caption,host,block):
    return envelope('image-caption',instance_id(host,'caption:'+block),{},image+'\n\n'+caption_text(caption))


def prepare_synced(engine):
    sources={};references=[]
    for page in engine.pages:
        pending=[page];seen=set()
        while pending:
            parent=pending.pop()
            if parent in seen:continue
            seen.add(parent)
            for block in engine.blocks.get(parent,[]):
                kind=block.get('type');data=block.get(kind) or {}
                if kind=='synced_block':
                    original=(data.get('synced_from') or {}).get('block_id')
                    if original:references.append((original,page,block['id']))
                    else:sources.setdefault(block['id'],{'page':page,'placement':block['id']})
                if block.get('has_children') and kind not in ('child_page','child_database'):pending.append(block['id'])
    for original,page,placement in references:
        if original not in sources:
            sources[original]={'page':page,'placement':placement,'outside':True}
    engine.synced_sources=sources


def synced_block(engine,page,block,body,plan):
    original=((block.get('synced_block') or {}).get('synced_from') or {}).get('block_id') or block['id']
    source=engine.synced_sources[original]
    instance=instance_id(engine.mapping[page],'synced:'+block['id'])
    own=source['page']==page and source['placement']==block['id']
    data={'role':'source'} if own else {'role':'reference',
        'ref':'any://o/'+engine.sid+'/'+engine.mapping[source['page']]+'/editor_blocks/'+marker('pending',page,original),
        'sourceInstance':instance_id(engine.mapping[source['page']],'synced:'+source['placement'])}
    plan['synced'].append({'original':original,'instance':instance,'role':data['role']})
    if own and source.get('outside'):engine.issues(page).add('Original du bloc synchronisé hors sélection : original Anytwo créé dans sa première occurrence importée')
    return envelope('synced-block',instance,data,body)


def records(engine,page):
    result=backend.local_get(engine.target.port,f'/v1/spaces/{_segment(engine.sid)}/query',method='POST',
        body={'objectId':engine.mapping[page],'dataset':'editor_blocks','sort':['nav.pos'],'limit':10000},timeout=20)
    if result.get('hasMore') or result.get('has_more'):raise APIError('Lecture des blocs cible incomplète ; liens natifs non finalisés.')
    return result.get('records',[])


def patch_block(engine,page,bid,changes):
    engine.check()
    # This desktop build matches block route IDs before percent-decoding ':';
    # batch-created IDs use '<change>:<ordinal>'. ':' is legal in a path segment.
    block_path=quote(str(bid),safe=':')
    return backend.target_write(engine.target,f'/spaces/{_segment(engine.sid)}/objects/{_segment(engine.mapping[page])}/editor/editor_blocks/blocks/{block_path}',{'set':changes},method='PATCH')


def opening(row):
    value=row.get('text','')
    match=re.fullmatch(r'<!-- any:block (\{.*\}) -->',value)
    if not match:return None
    try:return json.loads(match[1])
    except ValueError:return None


def finalise(engine):
    """Resolve API-allocated block IDs after all page bodies have been written."""
    rows={};sources={}
    for page,plan in engine.content_plans.items():
        if not (plan['tocs'] or plan['synced']):continue
        if engine.results[page].get('errors'):continue
        engine.check();rows[page]=records(engine,page)
        for spec in plan['synced']:
            if spec['role']!='source':continue
            matches=[r for r in rows[page] if (opening(r) or {}).get('instance')==spec['instance']]
            if len(matches)==1:sources[spec['original']]={'page':page,'block':matches[0]['id'],'instance':spec['instance']}
            else:engine.issues(page).add('Identifiant du bloc synchronisé original non résolu')
    for page,target_rows in rows.items():
        plan=engine.content_plans[page];used=set();links=[]
        for heading in plan['headings']:
            matches=[r for r in target_rows if r['id'] not in used and r.get('type')=='heading'
                     and r.get('text')==heading['text'] and r.get('style',{}).get('level',1)==heading['level']]
            if not matches:
                engine.issues(page).add('Titre non adressable dans le sommaire : '+heading['label']);continue
            row=matches[0];used.add(row['id'])
            from notion_content import escape
            uri='any://o/'+engine.sid+'/'+engine.mapping[page]+'/editor_blocks/'+row['id']
            links.append('    '*(heading['level']-1)+'- ['+escape(heading['label'])+']('+uri+')')
        for token in plan['tocs']:
            matches=[r for r in target_rows if r.get('text')==token]
            if len(matches)!=1:engine.issues(page).add('Emplacement du sommaire non résolu');continue
            patch_block(engine,page,matches[0]['id'],{'text':'\n'.join(links) if links else 'Sommaire : aucun titre accessible.'})
            engine.issues(page).add('Sommaire importé en liens de blocs ; mise à jour automatique non conservée')
        for spec in plan['synced']:
            if spec['role']!='reference':continue
            matches=[r for r in target_rows if (opening(r) or {}).get('instance')==spec['instance']]
            if len(matches)!=1:engine.issues(page).add('Occurrence de bloc synchronisé non résolue');continue
            source=sources.get(spec['original']);head=opening(matches[0])
            if source:
                head['data']['ref']='any://o/'+engine.sid+'/'+engine.mapping[source['page']]+'/editor_blocks/'+source['block']
                head['data']['sourceInstance']=source['instance']
            else:
                head['data']={'role':'source'};engine.issues(page).add('Original synchronisé indisponible : copie autonome conservée')
            encoded=json.dumps(head,ensure_ascii=False,separators=(',',':')).replace('--',r'\u002d\u002d')
            patch_block(engine,page,matches[0]['id'],{'text':'<!-- any:block '+encoded+' -->'})
        engine.results[page]['status']='partial' if engine.issues(page) or engine.results[page].get('errors') else 'imported'
        engine.checkpoint()
    engine.report['synced_blocks']={key:{'page':value['page'],'block':value['block'],'instance':value['instance']} for key,value in sources.items()}
