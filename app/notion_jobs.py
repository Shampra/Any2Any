"""In-memory, cancellable read-only analysis jobs; polling never holds the API lock."""
from copy import deepcopy
import threading
import json
from notion_cache import session_cache
import time
import uuid
from urllib.parse import parse_qs
from api_clients import APIError
import notion_tree


def inspect_job(method,path,data,query,session):
    jid=data.get('id') if method=='POST' else parse_qs(query).get('id',[''])[0]
    job=session.get('jobs',{}).get(jid)
    if job is None:raise ValueError('Analyse introuvable ou connexion changée. Relancez l’analyse.')
    if path=='/api/notion/cancel' and method=='POST':job['cancel'].set()
    elif path!='/api/notion/job' or method!='GET':raise ValueError('Opération d’analyse inconnue.')
    with job['lock']:
        value={k:job[k] for k in ('id','state','message','requests')}
        value['elapsed']=round(time.monotonic()-job['started'],1)
        if job.get('metrics') is not None:value['metrics']=deepcopy(job['metrics'])
        value['reused_requests']=job['cache'].hits-job['initial_hits']
        if job.get('result') is not None:value['result']=job['result']
        if job['cancel'].is_set() and job['state']=='running':value['message']='Annulation demandée ; fin de la requête en cours…'
        return value


def start(session,data,api_lock,budget):
    rules=deepcopy(data.get('rules'));whole=data.get('whole',False)
    files=data.get('files',True);links=data.get('links',False)
    if not isinstance(files,bool) or not isinstance(links,bool):raise ValueError('Options d’import invalides.')
    if whole:links=False
    # Validate shape/authorization before creating a worker (without remote requests).
    if not isinstance(whole,bool) or not isinstance(rules,list) or len(rules)>200:raise ValueError('Sélection invalide.')
    visible={notion_tree.key(x) for x in notion_tree.navigation(session['nodes'])}
    for rule in rules:
        if not isinstance(rule,dict) or rule.get('key') not in visible or not isinstance(rule.get('include'),bool):raise ValueError('Branche inconnue. Rechargez l’arborescence.')
    jobs=session.setdefault('jobs',{})
    if any(job['state']=='running' for job in jobs.values()):raise ValueError('Une analyse est déjà en cours.')
    while len(jobs)>=4:jobs.pop(next(iter(jobs)))
    fingerprint=json.dumps({'whole':whole,'rules':sorted(rules,key=lambda x:x['key']),'files':files,'links':links},sort_keys=True)
    checkpoint=session.get('analysis_checkpoint')
    resumed=bool(checkpoint and checkpoint['fingerprint']==fingerprint and time.monotonic()-checkpoint['updated']<300)
    if not resumed:checkpoint={'fingerprint':fingerprint,'cache':session_cache(session),'updated':time.monotonic()}
    session['analysis_checkpoint']=checkpoint
    job={'cache':checkpoint['cache'],'initial_hits':checkpoint['cache'].hits,'id':str(uuid.uuid4()),'state':'running','message':'Préparation de la sélection…','requests':0,'metrics':{'phase':'selection','pages':0,'blocks':0,'request_types':{}},'started':time.monotonic(),'lock':threading.Lock(),'cancel':threading.Event()}
    jobs[job['id']]=job
    known=deepcopy(session['nodes']);catalog=deepcopy(session['catalog']);client=session['client']
    def check_cancel():
        if job['cancel'].is_set():raise APIError('Analyse annulée.',499)
    def telemetry(path):
        category=('properties' if '/properties/' in path else 'blocks' if '/blocks/' in path else 'queries' if '/query' in path else 'pages' if '/pages/' in path else 'views' if '/views' in path else 'schemas')
        with job['lock']:
            counts=job['metrics']['request_types'];counts[category]=counts.get(category,0)+1
    def statistics(**values):
        with job['lock']:job['metrics'].update(values)
    def progress(message):
        check_cancel()
        with job['lock']:
            if message:job['message']=message
            else:job['requests']+=1
    def run():
        try:
            with api_lock:
                previous=client.progress;cache=client._child_cache;read_cache=client._read_cache;cancel=client.check_cancel;telemetry_before=client.telemetry;statistics_before=client.statistics
                try:
                    client.progress=progress;client._child_cache={};client._read_cache=checkpoint['cache'];client.check_cancel=check_cancel;client.telemetry=telemetry;client.statistics=statistics
                    with budget(client,900):
                        progress('Reprise des lectures déjà terminées…' if resumed else 'Parcours des branches sélectionnées…')
                        selection=notion_tree.select(client,known,rules,whole,catalog)
                        if links:
                            from notion_migration import Engine
                            preview=Engine(client,None,selection,{'files':files,'links':True,'destination':{'id':'__create__','name':'Analyse'}},progress,check_cancel)
                            preview.collect();selection=preview.selection
                        statistics(phase='reading',pages=len(selection['pages']))
                        progress('Lecture des blocs et propriétés…')
                        result=client.analyse(selection,list(selection['pages']))
                        result['import_options']={'files':files,'links':links}
                        if not files:result['warnings'].append('Option fichiers désactivée : les pièces jointes ne seront pas récupérées.')
                        statistics(phase='done')
                        progress('Analyse terminée.')
                        if resumed:result['warnings'].append('Analyse reprise avec les lectures récentes conservées en mémoire. Utilisez Mettre à jour pour repartir de données entièrement relues.')
                    session.pop('analysis_checkpoint',None)
                    with job['lock']:job.update(state='done',result=result,message='Analyse terminée.')
                finally:
                    checkpoint['updated']=time.monotonic()
                    client.progress=previous;client._child_cache=cache;client._read_cache=read_cache;client.check_cancel=cancel;client.telemetry=telemetry_before;client.statistics=statistics_before
        except APIError as exc:
            message='Analyse trop longue. Relancez la même sélection dans les cinq minutes pour reprendre les lectures terminées, ou utilisez Mettre à jour pour repartir de zéro.' if exc.status==504 else str(exc)
            with job['lock']:job.update(state='cancelled' if exc.status==499 else 'error',message=message)
        except ValueError as exc:
            with job['lock']:job.update(state='error',message=str(exc))
        except Exception:
            with job['lock']:job.update(state='error',message='L’analyse a échoué pendant la lecture des données Notion. Réessayez avec une branche plus petite.')
    threading.Thread(target=run,daemon=True,name='notion-analysis').start()
    return {'id':job['id'],'state':'running'}
