'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Element{
 constructor(tag='div'){this.tagName=tag;this.children=[];this.handlers={};this.value='';this.attributes={};this.disabled=false;this._text='';const classes=new Set();this.classList={toggle:(name,force)=>{const add=force===undefined?!classes.has(name):force;add?classes.add(name):classes.delete(name);},contains:name=>classes.has(name),add:name=>classes.add(name),remove:name=>classes.delete(name)};}
 append(...items){for(const item of items){item.parent=this;this.children.push(item);}}
 replaceChildren(...items){this.children=[];this._text='';this.append(...items);}
 set value(value){this._value=String(value);}get value(){return this._value;}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join(' ');}
 addEventListener(name,handler){this.handlers[name]=handler;}setAttribute(name,value){this.attributes[name]=value;}
 closest(){return this.parent||this.label||(this.label=new Element('label'));}focus(){}scrollIntoView(){}
 querySelectorAll(selector){return this.children.flatMap(child=>[...(selector.split(',').includes(child.tagName)?[child]:[]),...child.querySelectorAll(selector)]);}
}
const root={id:'root',name:'Gastronomie',kind:'page',parent_key:null,unresolved_parent:false};
const other={id:'other',name:'Autre page',kind:'page',parent_key:null,unresolved_parent:true};
const flush=async()=>{for(let i=0;i<15;i++)await new Promise(resolve=>setImmediate(resolve));};
function harness({saved=false,deferred=null,rejectToken=false,nodes=[root,other],spaces=[],importResult=null}={}){
 const elements=new Map(),calls=[],timers=[];const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};get('source-kind').value='notion';let connected=false;
 const snapshot={nodes,loaded_nodes:[],loaded:true};
 const context={window:{},document:{getElementById:get,createElement:tag=>new Element(tag)},AbortController,crypto:{randomUUID:()=> 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},setTimeout:(fn,delay)=>{timers.push({fn,delay});return timers.length;},clearTimeout(){},setInterval:()=>0,clearInterval(){},fetch:async(path,options={})=>{
   const body=options.body?JSON.parse(options.body):null;calls.push({path,body});let value;
   if(path.endsWith('/status'))value={connected,has_token:saved,remembered:saved,identity:{workspace_name:'Workspace'}};
   else if(path.endsWith('/connect')){if(rejectToken)throw Error('Jeton Notion invalide.');connected=true;value={connected:true,has_token:true,remembered:saved,identity:{workspace_name:'Workspace'}};}
   else if(path.includes('/catalog?')){if(deferred)await deferred.promise;value={warnings:[]};}
   else if(path.endsWith('/tree'))value=snapshot;
   else if(path.endsWith('/children')){snapshot.loaded_nodes.push(body.key);value={...snapshot,expanded:body.key};}
   else if(path.endsWith('/targets'))value={spaces};
   else if(path.endsWith('/import'))value={id:'job',state:'running'};
   else if(path.includes('/job?id='))value={state:'done',elapsed:1,requests:12,message:'Import terminé',result:importResult};
   else if(path==='/api/check/anytwo')value={state:'ok',detail:'Anytwo connecté'};
   else value={};
   return {ok:true,json:async()=>value};
 }};
 vm.createContext(context);vm.runInContext(fs.readFileSync('app/static/notion.js','utf8'),context);
 return {api:context.window.NotionSource,get,calls,timers,all:element=>element.children.flatMap(x=>[x,...h.all(x)])};
}
let h;
async function testSavedLoadingAndSelection(){
 let resolve;const deferred={promise:new Promise(r=>resolve=r)};h=harness({saved:true,deferred});
 const pending=h.api.activate({anytwo_port:31310});await flush();
 assert(h.calls.some(x=>x.path.endsWith('/connect')),'saved token is automatically checked');
 assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),true);
 assert.equal(h.get('notion-loading-overlay').classList.contains('hidden'),false);
 assert.match(h.get('notion-loading-message').textContent,/Récupération|Recherche/);
 assert.equal(h.get('notion-connect').disabled,true);assert.match(h.get('notion-connect').textContent,/Connexion validée/);assert.equal(h.get('notion-connect').classList.contains('confirmed'),true);
 await h.get('notion-loading-dismiss').handlers.click();assert.equal(h.get('notion-loading-overlay').classList.contains('hidden'),true);
 assert.match(h.get('notion-tree').textContent,/Recherche des éléments en cours/);assert(!h.get('notion-tree').textContent.includes('Aucun'));
 resolve();await pending;assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),true);assert.equal(h.get('notion-space').value,'');
 const before=h.calls.filter(x=>x.path.includes('/catalog?')).length;
 h.get('notion-space').value='connected';await h.get('notion-space').handlers.change();
 assert.equal(h.calls.filter(x=>x.path.includes('/catalog?')).length,before,'space choice reuses loaded first level');
 assert(h.get('notion-tree').textContent.includes('Gastronomie'));
 assert.equal(h.get('notion-empty-target').classList.contains('hidden'),false);assert.equal(h.get('notion-configured-target').classList.contains('hidden'),true);
 h.api.openSettings();assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),false);assert.equal(h.get('notion-anytwo-port').value,'31310');h.api.closeSettings();
}
async function testSettingsReopenedDuringLoading(){let resolve;const deferred={promise:new Promise(r=>resolve=r)};h=harness({saved:true,deferred});const pending=h.api.activate({});await flush();h.api.openSettings();assert.equal(h.get('notion-loading-overlay').classList.contains('hidden'),true);assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),false);assert.equal(h.get('notion-connect').classList.contains('confirmed'),true);resolve();await pending;assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),false,'completion must not close settings reopened by user');h.api.closeSettings();}
async function testNoSavedToken(){h=harness();await h.api.activate({});assert(!h.calls.some(x=>x.path.endsWith('/connect')));assert.equal(h.get('notion-token-entry').classList.contains('hidden'),false);assert.match(h.get('notion-dialog-stage').textContent,/Configurez votre jeton/);}
async function testDestinationSettings(){h=harness({saved:true});await h.api.activate({anytwo_port:31310});h.api.openSettings();h.get('notion-anytwo-port').value='31311';await h.get('notion-anytwo-save').handlers.click();assert(h.calls.some(x=>x.path==='/api/config'&&x.body.anytwo_port===31311));assert.match(h.get('notion-anytwo-status').textContent,/Anytwo connecté/);h.get('notion-anytwo-port').value='invalid';await h.get('notion-anytwo-save').handlers.click();assert.match(h.get('notion-anytwo-status').textContent,/Port Anytwo invalide/);}
async function testRejectedToken(){h=harness({saved:true,rejectToken:true});await h.api.activate({});assert.equal(h.get('notion-settings-overlay').classList.contains('hidden'),false);assert.match(h.get('notion-dialog-stage').textContent,/Jeton Notion invalide/);assert(!h.calls.some(x=>x.path.includes('/catalog?')));assert.equal(h.get('notion-space').disabled,true);}
async function testPersistentOtherEntriesAndPrefetch(){
 h=harness({saved:true});await h.api.activate({});h.get('notion-space').value='connected';await h.get('notion-space').handlers.change();
 const nodes=h.all(h.get('notion-tree'));assert(nodes.some(x=>x.tagName==='h3'&&x.textContent.includes('ne sont pas des pages de premier niveau')));assert(!nodes.some(x=>x.tagName==='details'));
 const label=nodes.find(x=>x.tagName==='label'&&x.textContent.includes('Autre page'));const checkbox=label.children[0];checkbox.checked=true;await checkbox.handlers.change();
 assert(h.get('notion-tree').textContent.includes('Autre page'));assert(h.all(h.get('notion-tree')).some(x=>x.tagName==='h3'));
 for(let i=0;i<2;i++){const index=h.timers.findIndex(x=>x.delay===300);assert(index>=0);const timer=h.timers.splice(index,1)[0];await timer.fn();await flush();}
 assert(h.calls.some(x=>x.path.endsWith('/children')&&x.body.key==='page:other'&&x.body.prefetch),'other entries are prefetched too');
}
async function testDepthLimitAndDestinationDefault(){
 const level1={id:'l1',name:'Niveau 1',kind:'page',parent_key:'page:root'};
 const level2={id:'l2',name:'Niveau 2',kind:'database',parent_key:'page:l1'};
 const level3={id:'l3',name:'Masqué',kind:'page',parent_key:'database:l2'};
 h=harness({saved:true,nodes:[root,level1,level2,level3],spaces:[{id:'same',name:'Workspace'},{id:'else',name:'Autre'}]});await h.api.activate({});
 h.get('notion-space').value='connected';await h.get('notion-space').handlers.change();
 for(const name of ['Gastronomie','Niveau 1']){const toggle=h.all(h.get('notion-tree')).find(x=>x.tagName==='button'&&x.attributes['aria-label']==='Déplier '+name);await toggle.handlers.click();}
 assert(h.get('notion-tree').textContent.includes('Niveau 2'));assert(!h.get('notion-tree').textContent.includes('Masqué'));
 assert(!h.all(h.get('notion-tree')).some(x=>x.tagName==='button'&&x.attributes['aria-label']==='Déplier Niveau 2'));
 for(let i=0;i<5;i++){const index=h.timers.findIndex(x=>x.delay===300);if(index<0)break;await h.timers.splice(index,1)[0].fn();await flush();}
 assert(!h.calls.some(x=>x.path.endsWith('/children')&&['database:l2','page:l3'].includes(x.body.key)));
 await h.get('notion-target-check').handlers.click();assert.equal(h.get('notion-target').value,'same');
 h.get('notion-target').value='__create__';await h.get('notion-target').handlers.change();assert.equal(h.get('notion-target-name').value,'Workspace');assert(!h.get('notion-target-name-row').classList.contains('hidden'));
 const label=h.all(h.get('notion-tree')).find(x=>x.tagName==='label'&&x.textContent.includes('Niveau 2'));label.children[0].checked=true;await label.children[0].handlers.change();assert.match(h.get('notion-collection-policy').textContent,/Niveau 2/);assert.equal(h.get('notion-configured-target').classList.contains('hidden'),false);assert.equal(h.get('notion-selection-name').textContent,'Niveau 2');
 h.get('notion-links-option').checked=true;h.get('notion-whole').checked=true;await h.get('notion-whole').handlers.change();assert.equal(h.get('notion-links-option').disabled,true);assert.equal(h.get('notion-links-option').checked,false);
 h=harness({saved:true,spaces:[]});await h.api.activate({});await h.get('notion-target-check').handlers.click();assert.equal(h.get('notion-target').value,'__create__');assert.equal(h.get('notion-target-name').value,'Workspace');
}
async function testImportLaunchAndReport(){
 h=harness({saved:true,importResult:{id:'run',status:'partial',target_space:'space',totals:{total:1},collections:[],files:[],errors:[],warnings:[],objects:[{name:'Gastronomie',target_id:'target',status:'partial',issues:['Formule figée'],errors:[]}]}});
 await h.api.activate({});h.get('notion-space').value='connected';await h.get('notion-space').handlers.change();assert.equal(h.get('notion-import').disabled,true);
 const label=h.all(h.get('notion-tree')).find(x=>x.tagName==='label'&&x.textContent.includes('Gastronomie'));label.children[0].checked=true;await label.children[0].handlers.change();
 h.get('notion-files-option').checked=true;h.get('notion-links-option').checked=true;assert.equal(h.get('notion-import').disabled,false);
 await h.get('notion-import').handlers.click();const request=h.calls.find(x=>x.path.endsWith('/import')).body;
 assert.equal(request.files,true);assert.equal(request.links,true);assert.equal(request.destination.name,'Workspace');assert.equal(request.rules[0].key,'page:root');
 assert.match(h.get('notion-analysis').textContent,/Import terminé avec adaptations/);assert.match(h.get('notion-analysis').textContent,/Formule figée/);assert.match(h.get('notion-analysis').textContent,/Télécharger le bilan/);
 assert.equal(h.get('notion-import').disabled,false);assert.equal(h.get('source-kind').disabled,false);
}
(async()=>{await testSavedLoadingAndSelection();await testSettingsReopenedDuringLoading();await testNoSavedToken();await testRejectedToken();await testDestinationSettings();await testPersistentOtherEntriesAndPrefetch();await testDepthLimitAndDestinationDefault();await testImportLaunchAndReport();console.log('8 Notion UI scenarios passed: confirmed connection/loading dismissal, settings reopened during loading, no-token settings, rejected token, destination API settings, persistent other entries and prefetch.');})().catch(error=>{console.error(error);process.exitCode=1;});
