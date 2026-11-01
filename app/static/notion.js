'use strict';
window.NotionSource=(()=>{
  const $=id=>document.getElementById(id);
  const N={connected:false,spaceSelected:false,busy:false,nodes:new Map(),expanded:new Set(),loaded:new Set(),rules:new Map(),whole:false,pageCount:0,ticket:null,bound:false,identity:null,analysisActive:false,job:null,prefetchEpoch:0,prefetchPromise:null,prefetchTried:new Set(),inventoryLoading:false,inventoryReady:false,inventoryCache:null,inventoryError:null,config:{},anytwoReady:false,destinationBusy:false,validating:false,targetSpaces:[],targetSpacesLoaded:false};
  const hide=(id,value)=>$(id).classList.toggle('hidden',value);
  const write=(id,value)=>$(id).textContent=value;
  const key=node=>node.kind+':'+node.id;
  async function api(path,data){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),path==='connect'?7000:120000);
    try{
      const response=await fetch('/api/notion/'+path,{signal:controller.signal,cache:'no-store',...(data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})});
      const value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Réponse locale indisponible.');return value;
    }catch(error){if(error.name==='AbortError')throw Error(path==='connect'?'Notion ne répond pas assez vite. Vérifiez Internet puis réessayez. Le client Notion peut rester fermé.':'Délai de réponse dépassé. Réessayez ou ajoutez une page/base par son lien.');throw error;}
    finally{clearTimeout(timer);}
  }
  function importDetail(status){
    const m=status.metrics||{},phases={selection:'Recherche des descendants',reading:'Lecture des contenus',writing:'Écriture dans Anytwo',done:'Terminé'};
    const labels={pages:'pages',blocks:'blocs',properties:'propriétés',queries:'bases',schemas:'schémas',views:'vues'};
    const types=Object.entries(m.request_types||{}).map(([key,count])=>`${labels[key]||key} : ${count}`).join(', ');
    return `${Math.floor(status.elapsed)} s · ${status.requests} requête(s) Notion · ${status.reused_requests||0} lecture(s) réutilisée(s) · ${phases[m.phase]||'Import vers Anytwo'}${m.pages!==undefined?` · ${m.pages} page(s), ${m.blocks||0} bloc(s)`:''}${types?` · Requêtes : ${types}`:''}`;
  }
  function credential(value){
    const available=Boolean(value.has_token);hide('notion-token-entry',available);hide('notion-token-available',!available);
    $('notion-remember').checked=Boolean(value.remembered);
    $('notion-remember').closest('label').classList.toggle('hidden',available&&value.remembered);
    write('notion-token-available',value.remembered?'Un jeton mémorisé est disponible sur cet ordinateur. Vous pouvez valider la connexion sans le saisir à nouveau.':'Un jeton est disponible pour cette session.');
    $('notion-forget').classList.toggle('hidden',!available&&!N.connected);
  }
  function controls(){
    $('notion-forget').disabled=N.busy;
    $('notion-connect').disabled=N.busy||N.connected;
    $('notion-connect').classList.toggle('confirmed',N.connected&&!N.validating);
    write('notion-connect',N.validating?'Vérification…':N.connected?'✓ Connexion validée':'Valider la connexion');if($('source-kind').value==='notion')$('source-kind').disabled=N.busy;
    $('notion-space').disabled=N.busy||!N.connected||N.inventoryLoading;
    $('notion-resolve').disabled=N.busy||!N.connected||!N.spaceSelected;
    $('notion-refresh').disabled=N.busy||!N.connected||!N.spaceSelected||N.inventoryLoading;
    $('notion-links-option').disabled=N.busy||N.whole;$('notion-files-option').disabled=N.busy;
    $('notion-whole').disabled=N.busy||!N.spaceSelected||N.inventoryLoading||!N.nodes.size;
    $('notion-analyse').disabled=N.busy||!N.connected||!N.spaceSelected||N.inventoryLoading||!(N.whole||[...N.rules.values()].some(Boolean));
    $('notion-target-check').disabled=N.busy||!N.connected;
    const selected=N.whole||[...N.rules.values()].some(Boolean),dest=$('notion-target').value;
    $('notion-import').disabled=N.busy||!N.connected||!N.spaceSelected||!selected||!N.anytwoReady||!dest||(dest==='__create__'&&!$('notion-target-name').value.trim())||Boolean(N.config.demo);
    $('notion-import').title=N.config.demo?'Aucune écriture en mode démo':'Créer les données sélectionnées dans Anytwo';
    $('notion-target').disabled=N.busy||!N.targetSpacesLoaded;$('notion-target-name').disabled=N.busy;
    $('notion-anytwo-save').disabled=N.destinationBusy||N.busy;
    $('notion-settings-continue').disabled=!N.inventoryReady||N.inventoryLoading;hide('notion-show-loading',!N.inventoryLoading);
    for(const el of $('notion-tree').querySelectorAll('button,input'))el.disabled=N.busy;
  }
  async function action(task){
    if(N.busy)return false;N.busy=true;controls();
    const started=Date.now();let message=null;
    const progress=setInterval(()=>{if(message===null)message=$('notion-status').textContent;const text=`${message} (${Math.floor((Date.now()-started)/1000)} s)`;write('notion-status',text);if(N.spaceSelected&&!N.analysisActive)write('notion-prefetch-status',text);},1000);
    try{await task();return true;}catch(error){write('notion-status',error.message);if(N.spaceSelected&&!N.analysisActive)write('notion-prefetch-status',error.message);if(N.analysisActive){write('notion-analysis-stage',error.message);$('notion-analysis-progress').classList.add('error');}return false;}
    finally{clearInterval(progress);if(N.analysisActive){hide('notion-analysis-spinner',true);hide('notion-cancel',true);N.analysisActive=false;N.job=null;}N.busy=false;controls();}
  }
  function invalidate(){N.ticket=null;N.pageCount=0;hide('notion-analysis-progress',true);hide('notion-report-area',true);$('notion-analysis').replaceChildren();renderSelection();}
  function renderSelection(){
    const selected=N.whole||[...N.rules.values()].some(Boolean);hide('notion-empty-target',selected);hide('notion-configured-target',!selected);
    const included=[...N.rules].filter(([,include])=>include);const node=included.length===1?N.nodes.get(included[0][0]):null;
    write('notion-selection-name',N.whole?(N.identity?.workspace_name||'Tout l’espace'):node?.name||`${included.length} branches sélectionnées`);
    destinationSummary();write('notion-pages',N.pageCount?`${N.pageCount} page(s) dans la sélection analysée.`:N.whole?'Tout le contenu accessible est sélectionné, sous réserve des branches décochées.':`${[...N.rules.values()].filter(Boolean).length} branche(s) sélectionnée(s), ${[...N.rules.values()].filter(x=>!x).length} exclusion(s). Les pages seront comptées lors de l’analyse.`);}
  function effective(k){
    const seen=new Set();while(k&&!seen.has(k)){if(N.rules.has(k))return N.rules.get(k);seen.add(k);k=N.nodes.get(k)?.parent_key;}return N.whole;
  }
  function descendant(k,ancestor){const seen=new Set();while(k&&!seen.has(k)){if(k===ancestor)return true;seen.add(k);k=N.nodes.get(k)?.parent_key;}return false;}
  function setRule(k,value){for(const child of [...N.rules.keys()])if(descendant(child,k))N.rules.delete(child);N.rules.set(k,value);invalidate();renderTree();controls();}
  function tree(value,render=true){if(value.loaded_nodes)N.loaded=new Set(value.loaded_nodes);N.nodes=new Map(value.nodes.map(node=>[key(node),node]));if(render)renderTree();controls();}
  function renderTree(){
    const root=$('notion-tree');root.replaceChildren();root.setAttribute('aria-busy',String(N.inventoryLoading));
    if(N.inventoryLoading){const progress=document.createElement('div');progress.className='notion-tree-loading';progress.setAttribute('role','status');const spinner=document.createElement('span');spinner.className='loader';const message=document.createElement('span');message.textContent='Recherche des éléments en cours…';progress.append(spinner,message);root.append(progress);return;}
    if(N.inventoryError&&N.nodes.size){const error=document.createElement('p');error.setAttribute('role','alert');error.textContent=N.inventoryError;root.append(error);}
    $('notion-whole').checked=N.whole;$('notion-whole').indeterminate=N.whole&&[...N.rules.values()].some(x=>!x);
    const children=parent=>[...N.nodes.values()].filter(node=>node.parent_key===parent);
    const visited=new Set();
    function append(node,container,depth=0){
      const k=key(node);if(visited.has(k))return;visited.add(k);
      const item=document.createElement('div');item.className='notion-tree-item';const row=document.createElement('div');row.className='notion-tree-row';
      const leaf=depth>=2||node.selection_leaf;const toggle=document.createElement(leaf?'span':'button');toggle.className='notion-tree-toggle';toggle.textContent=N.expanded.has(k)?'▾':'▸';toggle.setAttribute('aria-label',(N.expanded.has(k)?'Replier ':'Déplier ')+node.name);toggle.setAttribute('aria-expanded',String(N.expanded.has(k)));
      if(!leaf)toggle.addEventListener('click',async()=>{
        if(N.expanded.has(k)){N.expanded.delete(k);renderTree();controls();return;}
        if(N.loaded.has(k)){N.expanded.add(k);renderTree();controls();return;}
        await action(async()=>{write('notion-status','Lecture des enfants de « '+node.name+' »…');write('notion-prefetch-status','Lecture des enfants de « '+node.name+' »…');if(N.prefetchPromise)await N.prefetchPromise;const result=await api('children',{key:k});N.expanded.add(k);tree(result);write('notion-status','Branche chargée.');write('notion-prefetch-status','Branche chargée.');});
      });
      const label=document.createElement('label');label.className='check-row';const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=effective(k);checkbox.indeterminate=[...N.rules].some(([child,value])=>child!==k&&descendant(child,k)&&value!==effective(k));checkbox.addEventListener('change',()=>setRule(k,checkbox.checked));
      const name=document.createElement('span');name.textContent=node.name;const badge=document.createElement('small');badge.className='muted-text';badge.textContent={page:'Page',database:'Base',data_source:'Source de données'}[node.kind];label.append(checkbox,name);row.append(toggle,label,badge);item.append(row);container.append(item);
      if(leaf){const note=document.createElement('small');note.className='muted-text';note.textContent='Descendants inclus avec cet élément, sans sélection individuelle.';item.append(note);}
      if(!leaf&&N.expanded.has(k)){
        const nested=document.createElement('div');nested.className='notion-tree-children';item.append(nested);const items=children(k);for(const child of items)append(child,nested,depth+1);
        if(!items.length){const empty=document.createElement('p');empty.className='muted-text';empty.textContent='Aucun sous-élément accessible.';nested.append(empty);}
      }
    }
    const roots=children(null);for(const node of roots.filter(x=>!x.unresolved_parent))append(node,root);
    const unresolved=roots.filter(x=>x.unresolved_parent);
    if(unresolved.length){const title=document.createElement('h3');title.className='notion-other-heading';title.textContent='Autres éléments accessibles qui ne sont pas des pages de premier niveau';root.append(title);for(const node of unresolved)append(node,root);}
    if(!N.nodes.size){const empty=document.createElement('p');empty.textContent=N.inventoryError?N.inventoryError:N.connected&&!N.spaceSelected?'Choisissez un espace pour afficher ses éléments.':N.connected?'Aucun élément repéré. Mettez à jour ou ajoutez une page/base par son lien.':'Validez la connexion pour charger les éléments accessibles.';root.append(empty);}
  }
  function stopPrefetch(){N.prefetchEpoch++;N.prefetchTried.clear();write('notion-prefetch-status','');}
  function prefetch(){
    const epoch=++N.prefetchEpoch;N.prefetchTried.clear();const started=Date.now();
    async function step(){
      if(epoch!==N.prefetchEpoch||!N.connected||!N.spaceSelected||$('source-kind').value!=='notion')return;
      if(N.busy||N.inventoryLoading||N.prefetchPromise){setTimeout(step,500);return;}
      if(N.prefetchTried.size>=60||Date.now()-started>120000){write('notion-prefetch-status',`${N.loaded.size} branche(s) disponibles. Les autres seront chargées à la demande.`);return;}
      function depth(node){let count=0,k=node.parent_key;const seen=new Set();while(k&&!seen.has(k)){seen.add(k);count++;k=N.nodes.get(k)?.parent_key;}return count;}
      const node=[...N.nodes.values()].filter(x=>depth(x)<2&&!x.selection_leaf&&!N.loaded.has(key(x))&&!N.prefetchTried.has(key(x))).sort((a,b)=>depth(a)-depth(b))[0];
      if(!node){write('notion-prefetch-status',`Préchargement terminé : ${N.loaded.size} branche(s) disponibles. Les autres seront chargées à la demande.`);return;}
      const k=key(node);N.prefetchTried.add(k);write('notion-prefetch-status',`Préchargement en arrière-plan · ${N.loaded.size} branche(s) disponibles…`);
      const pending=(async()=>{try{const result=await api('children',{key:k,prefetch:true});if(epoch===N.prefetchEpoch&&$('source-kind').value==='notion'){tree(result,false);controls();}}catch(error){/* Foreground expansion retries and displays any failure. */}})();
      N.prefetchPromise=pending;await pending;if(N.prefetchPromise===pending)N.prefetchPromise=null;
      if(epoch===N.prefetchEpoch)setTimeout(step,300);
    }
    setTimeout(step,300);
  }
  function openLoading(){hide('notion-settings-overlay',true);hide('notion-loading-overlay',false);$('notion-loading-dismiss').focus();}
  function closeLoading(){const visible=!$('notion-loading-overlay').classList.contains('hidden');hide('notion-loading-overlay',true);if(visible&&$('source-kind').value==='notion')$('connection-button').focus();}
  function loadingState(message,working=true){write('notion-loading-message',message);hide('notion-loading-spinner',!working);}
  function dialogKeys(event,id,close){
    if(event.key==='Escape')close();
    if(event.key==='Tab'){const fields=[...$(id).querySelectorAll('button,input,select,a[href],summary,[tabindex]')].filter(x=>!x.disabled&&x.tabIndex>=0&&x.getClientRects().length);const first=fields[0],last=fields.at(-1);if(first&&event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(last&&!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
  }
  function dialogState(message,working=false){write('notion-dialog-stage',message);hide('notion-connection-spinner',!working);}
  function openSettings(){
    closeLoading();hide('notion-settings-overlay',false);$('notion-anytwo-port').value=N.config.anytwo_port||'';
    const field=N.connected?$('notion-settings-close'):$('notion-token-entry').classList.contains('hidden')?$('notion-connect'):$('notion-token');field.focus();
  }
  function closeSettings(){hide('notion-settings-overlay',true);if($('source-kind').value==='notion')(N.connected&&!N.spaceSelected?$('notion-space'):$('connection-button')).focus();}
  function apiIndicator(){
    if($('source-kind').value!=='notion')return;const ready=N.connected&&N.anytwoReady;write('connection-text',ready?'APIs connectées':N.connected?'Notion connecté · Anytwo à vérifier':'Configurer les API');
    $('connection-button').classList.toggle('api-failed',!ready);
    $('mini-dot').className='dot '+(ready?'ok':'error');hide('mini-warning',ready);
    $('connection-button').setAttribute('aria-label','Configurer les API Notion et Anytwo');$('connection-button').title='Configurer les API Notion et Anytwo';
  }
  async function checkDestination(save=false){
    if(N.destinationBusy)return false;N.destinationBusy=true;controls();write('notion-anytwo-status','Vérification de l’API Anytwo locale…');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);
    try{
      if(save){const raw=$('notion-anytwo-port').value.trim(),port=raw===''?null:Number(raw);if(port!==null&&(!Number.isInteger(port)||port<1||port>65535))throw Error('Port Anytwo invalide.');const response=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({anytwo_port:port}),signal:controller.signal});const value=await response.json();if(!response.ok||value.error)throw Error(value.error||'Configuration non enregistrée.');N.config.anytwo_port=port;}
      const response=await fetch('/api/check/anytwo',{cache:'no-store',signal:controller.signal});const result=await response.json();
      if(!response.ok||result.state!=='ok')throw Error(result.detail||result.error||'Anytwo indisponible. Ouvrez le client Anytwo puis réessayez.');
      N.anytwoReady=true;write('notion-anytwo-status',result.detail||'API Anytwo disponible.');return true;
    }catch(error){N.anytwoReady=false;write('notion-anytwo-status',error.name==='AbortError'?'Anytwo ne répond pas. Ouvrez le client et vérifiez son API locale.':error.message);return false;}
    finally{clearTimeout(timer);N.destinationBusy=false;apiIndicator();controls();}
  }
  function connection(value){
    N.connected=value.connected;N.identity=value.identity||null;write('notion-status',value.connected?'Connexion Notion validée.':'Non connecté.');write('connection-text',value.connected?'Notion connecté':'Notion à connecter');
    $('mini-dot').className='dot '+(value.connected?'ok':'error');hide('mini-warning',value.connected);
    N.targetSpaces=[];N.targetSpacesLoaded=false;$('notion-target').replaceChildren();$('notion-target').value='';$('notion-target').disabled=true;$('notion-target-name').value=value.identity?.workspace_name||'Import Notion';destinationSummary();
    N.spaceSelected=false;const select=$('notion-space');select.replaceChildren();
    const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Choisir un espace…';select.append(placeholder);
    if(value.connected){const option=document.createElement('option');option.textContent=value.identity?.workspace_name||'Espace de la connexion Notion';option.value='connected';select.append(option);}
    select.value='';credential(value);apiIndicator();controls();
  }
  async function refresh({initial=false}={}){
    if(!N.connected||(!N.spaceSelected&&!initial)||N.inventoryLoading)return false;stopPrefetch();const epoch=N.prefetchEpoch;N.inventoryLoading=true;N.inventoryError=null;N.inventoryReady=false;controls();renderTree();if(initial){dialogState('✓ Connexion Notion validée. Chargement en arrière-plan.',false);loadingState('Récupération des éléments de premier niveau…');openLoading();}const started=Date.now();
    write('notion-status','Connexion validée. Chargement des racines en arrière-plan…');
    const timer=setInterval(()=>{const message=`Recherche des éléments en cours… ${Math.floor((Date.now()-started)/1000)} s`;write('notion-prefetch-status',message);if(initial)loadingState(message,true);},1000);
    let ok=false;
    try{
      if(N.prefetchPromise)await N.prefetchPromise;
      const catalog=await api('catalog?refresh=true');const result=await api('tree');
      if(epoch!==N.prefetchEpoch)return false;
      N.inventoryCache={tree:result,warnings:catalog.warnings};N.inventoryReady=true;N.rules.clear();N.whole=false;N.expanded.clear();N.loaded.clear();invalidate();if(N.spaceSelected)tree(result);write('notion-catalog-status',catalog.warnings.join(' '));write('notion-status','Espace chargé. Cochez tout l’espace ou choisissez des branches.');ok=true;
    }catch(error){if(epoch===N.prefetchEpoch){N.inventoryError=error.message;write('notion-status',error.message);write('notion-prefetch-status',error.message);if(initial){dialogState(error.message,false);loadingState(error.message,false);}}}
    finally{clearInterval(timer);N.inventoryLoading=false;renderTree();controls();}
    if(ok)write('notion-prefetch-status','Premier niveau chargé.');if(ok&&N.spaceSelected)prefetch();if(ok&&initial){loadingState('Données Notion prêtes.',false);closeLoading();dialogState('Données Notion prêtes. Choisissez ensuite l’espace à parcourir.',false);}return ok;
  }
  async function connect(){
    N.validating=true;controls();dialogState('Vérification de la connexion Notion…',true);stopPrefetch();const ok=await action(async()=>{write('notion-status','Validation du jeton et de la lecture du contenu…');
      try{N.inventoryReady=false;N.inventoryCache=null;N.inventoryError=null;connection(await api('connect',{token:$('notion-token').value.trim(),remember:$('notion-remember').checked}));N.nodes.clear();N.rules.clear();N.whole=false;N.loaded.clear();N.expanded.clear();invalidate();renderTree();write('notion-status','Connexion Notion validée. Choisissez un espace pour afficher ses éléments.');}
      finally{$('notion-token').value='';}
    });
    N.validating=false;controls();
    if(!ok){N.connected=false;N.spaceSelected=false;N.nodes.clear();N.rules.clear();N.whole=false;invalidate();renderTree();$('notion-space').value='';apiIndicator();controls();dialogState($('notion-status').textContent,false);return false;}
    const ready=await refresh({initial:true});controls();return ready;
  }
  function paragraph(root,value,tag='p'){const el=document.createElement(tag);el.textContent=value;root.append(el);return el;}
  async function analyse(){if(N.busy)return;N.analysisActive=true;await action(async()=>{
    hide('notion-report-area',false);hide('notion-analysis-progress',false);hide('notion-analysis-spinner',false);hide('notion-cancel',false);$('notion-cancel').disabled=false;
    $('notion-analysis-progress').classList.remove('error');write('notion-analysis-stage','Préparation de la sélection…');write('notion-analysis-detail','0 s · lecture seule, aucune écriture.');
    $('notion-analysis-progress').scrollIntoView({block:'nearest'});$('notion-analysis').replaceChildren();
    write('notion-status','Analyse en cours : progression dans la zone de sélection.');
    if(N.prefetchPromise)await N.prefetchPromise;
    const job=await api('analyse',{files:$('notion-files-option').checked,links:!N.whole&&$('notion-links-option').checked,whole:N.whole,rules:[...N.rules].map(([key,include])=>({key,include}))});N.job=job.id;
    let status;
    do{
      status=await api('job?id='+encodeURIComponent(job.id));write('notion-analysis-stage',status.message);write('notion-analysis-detail',importDetail(status)+' · lecture seule.');
      if(status.state==='running')await new Promise(resolve=>setTimeout(resolve,600));
    }while(status.state==='running');
    if(status.state==='cancelled'){write('notion-status',status.message);return;}
    if(status.state!=='done')throw Error(status.message);
    const data=status.result;N.pageCount=data.selected_pages;renderSelection();const root=$('notion-analysis');root.replaceChildren();
    paragraph(root,`${data.selected_pages} page(s) analysée(s) — aucune écriture.`, 'h3');
    paragraph(root,'Blocs : '+Object.entries(data.blocks).map(([type,count])=>`${type} (${count})`).join(', '));
    paragraph(root,'Propriétés : '+Object.entries(data.property_types).map(([type,count])=>`${type} (${count})`).join(', '));
    paragraph(root,`${data.data_sources.length} source(s) avec schéma ; ${data.views.length} vue(s) repérée(s).`);
    for(const message of data.warnings)paragraph(root,message);
    const table=document.createElement('table');table.className='notion-compatibility';
    const head=document.createElement('tr');for(const title of ['Catégorie','Élément','Nombre','Conversion prévue','Détail'])paragraph(head,title,'th');table.append(head);
    const states={native:'Équivalent identifié',adaptation:'À adapter',snapshot:'Valeur figée',unavailable:'Non disponible',review:'À vérifier'};
    for(const item of data.compatibility.items){const row=document.createElement('tr');for(const value of [item.category,item.type,String(item.count),states[item.conversion],item.note])paragraph(row,value,'td');table.append(row);}root.append(table);
    for(const note of data.compatibility.notes)paragraph(root,note);
    paragraph(root,data.next_step);
    const button=document.createElement('button');button.className='btn ghost';button.textContent='Télécharger cette analyse';
    button.addEventListener('click',()=>{const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='analyse-notion-any2any.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});root.append(button);
    write('notion-status','Vérification terminée. Vous pouvez lancer l’import.');
  });}
  function downloadReport(root,data){
    const button=paragraph(root,'Télécharger le bilan JSON','button');button.className='btn ghost';
    button.addEventListener('click',()=>{const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='import-notion-'+data.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  }
  async function runImport(){
    if($('notion-import').disabled||N.busy)return;N.analysisActive=true;
    await action(async()=>{
      hide('notion-report-area',false);hide('notion-analysis-progress',false);hide('notion-analysis-spinner',false);hide('notion-cancel',false);$('notion-cancel').disabled=false;$('notion-analysis-progress').classList.remove('error');$('notion-analysis').replaceChildren();
      write('notion-analysis-stage','Lecture de la sélection avant import…');write('notion-analysis-detail','Notion reste en lecture seule.');$('notion-report-area').scrollIntoView({block:'start'});
      if(N.prefetchPromise)await N.prefetchPromise;
      const request={request_id:crypto.randomUUID(),whole:N.whole,rules:[...N.rules].map(([key,include])=>({key,include})),files:$('notion-files-option').checked,links:!N.whole&&$('notion-links-option').checked,destination:{id:$('notion-target').value,name:$('notion-target-name').value.trim()}};
      const job=await api('import',request);N.job=job.id;let status;
      do{status=await api('job?id='+encodeURIComponent(job.id));write('notion-analysis-stage',status.message);write('notion-analysis-detail',importDetail(status));if(status.state==='running')await new Promise(resolve=>setTimeout(resolve,600));}while(status.state==='running');
      const root=$('notion-analysis'),report=status.result;
      if(report){
        paragraph(root,report.status==='interrupted'?'Import interrompu':report.status==='partial'?'Import terminé avec adaptations':'Import terminé','h3');
        paragraph(root,`${report.totals.total||0} page(s) · ${(report.collections||[]).length} collection(s) · ${new Set((report.files||[]).map(x=>x.target_id)).size} fichier(s).`);
        for(const message of [...(report.errors||[]),...(report.warnings||[])])paragraph(root,message);
        for(const object of report.objects||[]){const details=document.createElement('details');paragraph(details,object.name+' · '+object.status,'summary');for(const message of [...object.issues,...object.errors])paragraph(details,message);if(object.target_id){const a=paragraph(details,'Ouvrir dans Anytwo','a');a.href='any://o/'+report.target_space+'/'+object.target_id;}root.append(details);}
        downloadReport(root,report);
      }
      if(status.state!=='done')throw Error(status.message);
      write('notion-status','Import terminé. Consultez le bilan.');write('notion-analysis-stage','Import terminé. Consultez le bilan des adaptations.');
    });
  }
  function destinationSummary(){
    const create=$('notion-target').value==='__create__';hide('notion-target-name-row',!create);
    const included=[...N.rules].filter(([,include])=>include);
    const single=!N.whole&&N.rules.size===1&&included.length===1?N.nodes.get(included[0][0]):null;
    write('notion-collection-policy',single&&['database','data_source'].includes(single.kind)?`« ${single.name} » : création d’une collection et de son supertag avec les propriétés source. Aucune fusion avec une collection existante.`:'Chaque source de données devient une collection avec son supertag et ses propriétés. Les pages membres reçoivent ce supertag ; les pages ordinaires restent des pages.');
    const target=N.targetSpaces.find(x=>x.id===$('notion-target').value);
    write('notion-destination-summary',create?'Espace à créer : '+($('notion-target-name').value.trim()||'nom à renseigner'):target?'Espace existant : '+target.name:'Vérifiez Anytwo pour choisir ou créer un espace.');
  }
  async function targets(){await action(async()=>{
    write('notion-target-status','Vérification du client Anytwo local…');if(N.prefetchPromise)await N.prefetchPromise;
    const response=await fetch('/api/check/anytwo',{cache:'no-store'});const check=await response.json();
    if(check.state!=='ok'){N.anytwoReady=false;apiIndicator();write('notion-target-status',check.detail||'Anytwo indisponible.');throw Error(check.detail||'Anytwo indisponible.');}N.anytwoReady=true;apiIndicator();
    const data=await api('targets');const select=$('notion-target');select.replaceChildren();
    for(const item of [{id:'__create__',name:'Créer un nouvel espace lors de l’import'},...data.spaces]){const option=document.createElement('option');option.value=item.id;option.textContent=item.name;select.append(option);}
    N.targetSpaces=data.spaces;N.targetSpacesLoaded=true;const name=N.identity?.workspace_name||'Import Notion';const matches=data.spaces.filter(x=>x.name===name);select.value=matches.length===1?matches[0].id:'__create__';$('notion-target-name').value=name;select.disabled=false;destinationSummary();write('notion-target-status','Anytwo disponible. Choisissez la destination puis testez ou lancez l’import.');
  });}
  function bind(){if(N.bound)return;N.bound=true;
    $('notion-cancel').addEventListener('click',async()=>{if(!N.job)return;$('notion-cancel').disabled=true;try{const result=await api('cancel',{id:N.job});write('notion-analysis-stage',result.message);}catch(error){write('notion-analysis-stage',error.message);$('notion-cancel').disabled=false;}});
    $('notion-space').addEventListener('change',async()=>{
      stopPrefetch();N.spaceSelected=N.connected&&$('notion-space').value==='connected';N.nodes.clear();N.rules.clear();N.whole=false;N.expanded.clear();N.loaded.clear();invalidate();renderTree();write('notion-catalog-status','');controls();
      if(N.spaceSelected){if(N.inventoryReady&&N.inventoryCache){tree(N.inventoryCache.tree);write('notion-catalog-status',N.inventoryCache.warnings.join(' '));prefetch();}else await refresh();if(N.anytwoReady)await targets();}
    });
    $('notion-connect').addEventListener('click',()=>connect());$('notion-refresh').addEventListener('click',()=>refresh());
    $('notion-loading-close').addEventListener('click',closeLoading);$('notion-loading-dismiss').addEventListener('click',closeLoading);$('notion-show-loading').addEventListener('click',openLoading);$('notion-loading-overlay').addEventListener('keydown',event=>dialogKeys(event,'notion-loading-overlay',closeLoading));
    $('notion-settings-close').addEventListener('click',closeSettings);$('notion-settings-continue').addEventListener('click',closeSettings);$('notion-anytwo-save').addEventListener('click',()=>checkDestination(true));
    $('notion-settings-overlay').addEventListener('keydown',event=>dialogKeys(event,'notion-settings-overlay',closeSettings));
    $('notion-whole').addEventListener('change',()=>{N.whole=$('notion-whole').checked;if(N.whole)$('notion-links-option').checked=false;N.rules.clear();invalidate();renderTree();controls();});
    $('notion-forget').addEventListener('click',()=>action(async()=>{
      stopPrefetch();if(N.prefetchPromise)await N.prefetchPromise;await api('disconnect',{});N.inventoryReady=false;N.inventoryCache=null;N.inventoryError=null;N.nodes.clear();N.rules.clear();N.whole=false;N.expanded.clear();N.loaded.clear();invalidate();$('notion-token').value='';write('notion-catalog-status','');connection({connected:false,has_token:false,remembered:false});renderTree();write('notion-status','Jeton oublié. Saisissez un nouveau jeton pour vous connecter.');
    }));
    $('notion-resolve').addEventListener('click',()=>action(async()=>{
      write('notion-status','Recherche de l’élément…');await api('resolve',{reference:$('notion-reference').value});invalidate();tree(await api('tree'));write('notion-status','Élément ajouté à l’arborescence.');
    }));
    $('notion-target').addEventListener('change',()=>{destinationSummary();controls();});$('notion-target-name').addEventListener('input',()=>{destinationSummary();controls();});
    $('notion-import').addEventListener('click',runImport);
    for(const id of ['notion-files-option','notion-links-option'])$(id).addEventListener('change',()=>{invalidate();controls();});
    $('notion-analyse').addEventListener('click',analyse);$('notion-target-check').addEventListener('click',targets);
  }
  async function activate(config){
    bind();N.config=config;stopPrefetch();hide('notion-token-entry',true);openSettings();dialogState('Vérification des accès…',true);
    try{
      if(N.prefetchPromise)await N.prefetchPromise;
      const data=await api('status');connection(data);N.nodes.clear();N.rules.clear();N.whole=false;N.spaceSelected=false;N.expanded.clear();N.loaded.clear();N.inventoryReady=false;N.inventoryCache=null;N.inventoryError=null;invalidate();renderTree();
      if(data.has_token||config.demo){await Promise.all([connect(),checkDestination()]);}
      else{dialogState('Configurez votre jeton Notion pour continuer.',false);write('notion-status','Saisissez le jeton et autorisez le contenu dans Notion.');$('notion-token').focus();await checkDestination();}
    }catch(error){dialogState(error.message,false);write('notion-status',error.message);}
    controls();
  }
  return {activate,openSettings,closeSettings,closeLoading};
})();
