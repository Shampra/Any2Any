"""Background import lifecycle, sharing the application's destination write lock."""
from copy import deepcopy
import threading
import time
import uuid
import json
from anytwo_backend import APIError, Anytwo
from notion_cache import session_cache
import notion_tree
from notion_migration import Engine, validate_options


def start(session,data,api_lock,import_lock,budget,port,save_report):
    options=validate_options(data)
    if data.get('whole'):options['links']=False
    try:request_id=str(uuid.UUID(data.get('request_id','')))
    except (ValueError,TypeError,AttributeError):raise ValueError('Identifiant de lancement invalide.') from None
    jobs=session.setdefault('jobs',{})
    for job in jobs.values():
        if job.get('request_id')==request_id:return {'id':job['id'],'state':job['state']}
    rules=deepcopy(data.get('rules'));whole=data.get('whole',False)
    visible={notion_tree.key(x) for x in notion_tree.navigation(session['nodes'])}
    if not isinstance(whole,bool) or not isinstance(rules,list) or len(rules)>200:raise ValueError('Sélection invalide.')
    for rule in rules:
        if not isinstance(rule,dict) or rule.get('key') not in visible or not isinstance(rule.get('include'),bool):raise ValueError('Sélection inconnue : actualisez les données.')
    if not whole and not any(x['include'] for x in rules):raise ValueError('Sélectionnez un élément à importer.')
    if any(j['state']=='running' for j in jobs.values()):raise APIError('Une opération Notion est déjà en cours.',409)
    if not import_lock.acquire(blocking=False):raise APIError('Un import est déjà en cours.',409)
    fingerprint=json.dumps({'whole':whole,'rules':sorted(rules,key=lambda x:x['key']),'options':options},sort_keys=True)
    checkpoint=session.get('import_checkpoint')
    resumed=bool(checkpoint and checkpoint['fingerprint']==fingerprint and time.monotonic()-checkpoint['updated']<1800)
    if not resumed:checkpoint={'fingerprint':fingerprint,'updated':time.monotonic()}
    session['import_checkpoint']=checkpoint
    cache=checkpoint['cache'] if resumed else session_cache(session)
    checkpoint['cache']=cache
    job={'id':str(uuid.uuid4()),'request_id':request_id,'kind':'import','state':'running','message':'Lecture de la sélection avant import…',
                          'requests':0,'cache':cache,'initial_hits':cache.hits,'metrics':{'phase':'selection','pages':0,'blocks':0,'request_types':{}},'started':time.monotonic(),'lock':threading.Lock(),'cancel':threading.Event()}
    while len(jobs)>=4:jobs.pop(next(iter(jobs)))
    jobs[job['id']]=job
    client=session['client'];known=deepcopy(session['nodes']);catalog=deepcopy(session['catalog'])
    def check():
        if job['cancel'].is_set():raise APIError('Import arrêté. Les éléments déjà créés sont conservés ; consultez le bilan avant de relancer.',499)
    def telemetry(path):
        category=('properties' if '/properties/' in path else 'blocks' if '/blocks/' in path else 'queries' if '/query' in path else 'pages' if '/pages/' in path else 'views' if '/views' in path else 'schemas')
        with job['lock']:
            counts=job['metrics']['request_types'];counts[category]=counts.get(category,0)+1
    def metrics(**values):
        with job['lock']:job['metrics'].update(values)
    def progress(message):
        check()
        with job['lock']:
            if message:job['message']=message
            else:job['requests']+=1
    def persist(report):
        with job['lock']:report['reading_metrics']=deepcopy(job['metrics']);report['reading_metrics'].update(requests=job['requests'],reused_requests=cache.hits-job['initial_hits'])
        save_report(report)
    def run():
        engine=None
        try:
            with api_lock:
                previous=(client.progress,client._child_cache,client._read_cache,client.check_cancel,client.telemetry,client.statistics)
                try:
                    client.progress=progress;client._child_cache={};client._read_cache=cache;client.check_cancel=check;client.telemetry=telemetry;client.statistics=metrics
                    with budget(client,900):
                        progress('Reprise des lectures récentes…' if resumed else 'Parcours des branches sélectionnées…')
                        selection=notion_tree.select(client,known,rules,whole,catalog)
                        metrics(pages=len(selection['pages']))
                        selection['workspace_icon']=session.get('identity',{}).get('workspace_icon')
                        engine=Engine(client,Anytwo(port),selection,options,progress,check,persist)
                        engine.metrics=metrics
                        result=engine.run()
                        metrics(phase='done')
                    session.pop('import_checkpoint',None)
                    with job['lock']:job.update(state='done',message='Import terminé. Consultez les adaptations dans le bilan.',result=result)
                finally:
                    checkpoint['updated']=time.monotonic()
                    client.progress,client._child_cache,client._read_cache,client.check_cancel,client.telemetry,client.statistics=previous
        except Exception as exc:
            message=str(exc) if isinstance(exc,(APIError,ValueError)) else 'Import interrompu par une erreur inattendue. Consultez le bilan des éléments déjà créés.'
            cancelled=isinstance(exc,APIError) and exc.status==499
            if isinstance(exc,APIError) and exc.status==504:
                message='Délai de lecture Notion atteint.'
            if engine and (engine.report.get('target_space') or job['metrics']['phase']=='writing'):
                message+=' L’écriture dans Anytwo a commencé : consultez le bilan et la destination avant de relancer.'
            elif not cancelled:
                message+=' Aucun élément n’a été créé dans Anytwo. Relancez la même sélection dans les 30 minutes, sans fermer l’application, pour réutiliser les lectures terminées.'
            if engine:
                engine.report['status']='interrupted';engine.report['errors'].append(message)
                try:engine.checkpoint()
                except OSError:pass
            with job['lock']:job.update(state='cancelled' if cancelled else 'error',message=message,result=engine.report if engine else None)
        finally:import_lock.release()
    threading.Thread(target=run,daemon=True,name='notion-import').start()
    return {'id':job['id'],'state':'running'}
