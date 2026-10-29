'use strict';
const $ = id => document.getElementById(id);
const S = {
  config: {}, sourceSpaces: [], targetSpaces: [], inventory: null,
  sourceSpaceId: '', selection: {kind:null, collectionId:null, typeKeys:[], ids:[]}, expandedTypes: new Set(), settingsOpen:false, mappingPrefs:{},
  mode: 'simple', importRunning:false, lastReport:null, targetCollections: [], loadingInventory:false, simulation:null,
  challengeId:'', connecting:false, apiReady:false, checks:{anytwo:null, anytype:null}, inventoryTicket:0, refreshing:false,
};
const hidden = (el, yes) => { (typeof el==='string'?$(el):el).classList.toggle('hidden',!!yes); };
const label = (id, value) => $(id).textContent = value;
const selectOption = (value, text) => { const op = document.createElement('option'); op.value=value; op.textContent=text; return op; };
const toast = msg => { let d=document.createElement('div');d.className='toast';d.textContent=msg;$('toast-container').append(d);setTimeout(()=>d.remove(),4600); };
async function request(path, options={}) {
  let resp = await fetch(path, {cache:'no-store',...options});
  let data = await resp.json();
  if (!resp.ok || data.error) throw Error(data.error || 'Erreur HTTP '+resp.status);
  return data;
}
function post(path, data){return request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
function logCheck(message){let e=$('check-logs');let div=document.createElement('div');div.textContent=message;e.append(div);e.scrollTop=e.scrollHeight;}
function checkDisplay(id, result){
  const ok=result.state==='ok'; const icon=$(id+'-check-icon');
  icon.className='check-state '+(ok?'ok':'error');icon.textContent=ok?'✓':'!';
  label(id+'-check-text', result.detail);
}
function apiReady(){return S.apiReady === true;}
function setApiAvailability(ready, checking=false){
  S.apiReady=Boolean(ready);
  const chip=$('connection-button');
  chip.classList.toggle('api-failed',!ready && !checking);
  chip.setAttribute('aria-label',checking?'Vérification des API':ready?'APIs connectées':'Attention : accès aux API indisponible. Ouvrir les paramètres');
  chip.title=checking?'Vérification des API':ready?'APIs connectées':'Attention : API indisponibles — ouvrir les paramètres';
  $('mini-dot').className='dot '+(checking?'':ready?'ok':'error');
  hidden('mini-warning',ready||checking);
  label('connection-text',checking?'Vérification des API':ready?'APIs connectées':'⚠ API indisponibles');
  hidden('offline-notice',ready||checking);
  const workspace=document.querySelector('.workspace');
  workspace.inert=!ready;
  workspace.classList.toggle('connection-unavailable',!ready);
  $('source-space').disabled=!ready;
  $('refresh-data').disabled=!ready||S.refreshing;
  updateImportButton();
  $('test-btn').disabled=!ready || !S.selection.kind || S.importRunning;
}
async function runChecks(){
  if(S.connecting) return;
  S.connecting=true;
  setApiAvailability(false,true);
  hidden('connection-overlay',false);
  hidden('close-settings',true);
  hidden('connect-help',true);
  hidden('continue-btn',true);
  $('check-logs').replaceChildren();
  for(const name of ['anytwo','anytype']){
    label(name+'-check-text','Vérification en cours…');
    $(name+'-check-icon').className='check-state';$(name+'-check-icon').replaceChildren();
    let spinner=document.createElement('span');spinner.className='loader';$(name+'-check-icon').append(spinner);
  }
  logCheck('Vérification accès Anytwo…');
  const checks={};
  const one=async name=>{
    try{checks[name]=await request('/api/check/'+name);}
    catch(err){checks[name]={state:'error',detail:err.message};}
    checkDisplay(name,checks[name]);
    logCheck(name+' : '+(checks[name].state==='ok'?'OK ✓':'action requise — '+checks[name].detail));
  };
  try{
    await one('anytwo');
    logCheck('Vérification accès Anytype…');
    await one('anytype');
    S.checks=checks;
    const ok=checks.anytwo.state==='ok' && checks.anytype.state==='ok';
    setApiAvailability(ok);
    if(ok){
      hidden('connect-help',!S.settingsOpen);
      hidden('continue-btn',S.settingsOpen);
      if(S.settingsOpen){
        hidden('anytwo-settings',false);hidden('anytype-settings',false);
      }
      try{
        await loadSpaces();
        if(!S.settingsOpen)hidden('connection-overlay',true);
      }catch(err){
        setApiAvailability(false);
        logCheck('Chargement des espaces : '+err.message);
        toast('Chargement des espaces : '+err.message);
        hidden('connection-overlay',false);
        hidden('connect-help',false);
        label('settings-hint','Impossible de charger les espaces. Vérifiez les connexions et les autorisations.');
      }
    }else{
      hidden('connect-help',false);
      hidden('anytwo-settings',!S.settingsOpen && checks.anytwo.state==='ok');
      hidden('anytype-settings',!S.settingsOpen && checks.anytype.state==='ok');
    }
  }finally{
    S.connecting=false;
    // Même en échec, la fenêtre de connexion peut être fermée après les vérifications.
    hidden('close-settings',false);
  }
}
async function loadConfig(){
  let c=await request('/api/config'); S.config=c;
  label('demo-badge','Mode démo');hidden('demo-badge',!c.demo);
  $('anytype-port').value=c.anytype_port||31009;
  $('anytwo-port').value=c.anytwo_port||31310;updateImportButton();
}
async function saveAndCheck(){
  try{
    let body={anytwo_port:$('anytwo-port').value.trim()||null,anytype_port:Number($('anytype-port').value)||31009};
    let key=$('anytype-key').value.trim();if(key)body.anytype_key=key;
    await post('/api/config',body);await runChecks();
  }catch(e){toast('Configuration : '+e.message);}
}
async function pairStart(){
  const win=window.open('/pair.html?port='+encodeURIComponent($('anytype-port').value || '31009'),'anytype-auth','popup,width=450,height=610,resizable=yes,scrollbars=yes');
  if(win){win.focus();return;}
  // If pop-ups are blocked, retain the inline authorization flow.
  try{
    await post('/api/config',{anytype_port:Number($('anytype-port').value)||31009});
    const data=await post('/api/pair/start',{});
    S.challengeId=data.challenge_id;
    if(!S.challengeId)throw Error('Challenge absent dans la réponse Anytype.');
    hidden('pair-code-area',false);
    toast('La fenêtre séparée a été bloquée : le code peut être saisi ici après avoir quitté Anytype (Alt+Tab).');
  }catch(e){toast('Appairage : '+e.message);}
}
async function pairFinish(){try{
  const code=$('pair-code').value.trim();
  if(!/^\d{4}$/.test(code))throw Error('Saisissez le code à quatre chiffres.');
  await post('/api/pair/finish',{challenge_id:S.challengeId,code});
  hidden('pair-code-area',true);toast('Autorisation Anytype enregistrée.');await runChecks();
}catch(e){toast('Code Anytype : '+e.message);}}
async function loadSpaces(){
  const data=await request('/api/spaces');
  const sorted = arr => [...arr].sort((a,b)=>a.name.localeCompare(b.name,'fr',{sensitivity:'base'}));
  S.sourceSpaces=sorted(data.source); S.targetSpaces=sorted(data.target);
  const source=$('source-space');source.replaceChildren();
  S.sourceSpaces.forEach(x=>source.append(selectOption(x.id,x.name)));
  if(!S.sourceSpaceId || !S.sourceSpaces.some(x=>x.id===S.sourceSpaceId))S.sourceSpaceId=S.sourceSpaces[0]?.id||'';
  source.value=S.sourceSpaceId;
  await loadInventory();
}

// Recharge les deux API, sans perdre la sélection et le paramétrage en cours.
// Après un import, une destination qui vient d'être créée devient une entrée existante.
async function refreshData({afterImport=false}={}){
  if(!apiReady() || S.refreshing || S.importRunning) return;
  S.refreshing=true;
  const refresh=$('refresh-data');refresh.disabled=true;
  const previousSelection={...S.selection,typeKeys:[...S.selection.typeKeys],ids:[...S.selection.ids]};
  const previousSource=S.sourceSpaceId;
  const destination=$('destination-space').value;
  const chosenSpace=S.targetSpaces.find(x=>'existing:'+x.id===destination);
  const desiredName=chosenSpace?.name || (destination==='__create_same__'?activeSource().name:$('custom-space').value.trim());
  const oldCollection=$('destination-collection').value;
  const oldCollectionName=oldCollection==='__create__'?$('custom-collection').value.trim():S.targetCollections.find(x=>'existing:'+x.id===oldCollection)?.name;
  const withCollection=$('import-into-collection').checked;
  const storedMappings={...S.mappingPrefs};saveTypeMappings();Object.assign(storedMappings,S.mappingPrefs);
  try {
    const data=await request('/api/spaces');
    const sorted=a=>[...a].sort((x,y)=>x.name.localeCompare(y.name,'fr',{sensitivity:'base'}));
    S.sourceSpaces=sorted(data.source);S.targetSpaces=sorted(data.target);
    const source=$('source-space');source.replaceChildren();
    S.sourceSpaces.forEach(x=>source.append(selectOption(x.id,x.name)));
    S.sourceSpaceId=S.sourceSpaces.some(x=>x.id===previousSource)?previousSource:(S.sourceSpaces[0]?.id||'');
    source.value=S.sourceSpaceId;
    await loadInventory();
    if(S.sourceSpaceId===previousSource && S.inventory){
      const inv=S.inventory;
      const ids=new Set(inv.objects.map(x=>x.id));
      const collections=new Set(inv.collections.map(x=>x.id));
      const types=new Set(inv.types.map(x=>x.key));
      const valid=previousSelection.kind==='space'||
        previousSelection.kind==='collection'&&collections.has(previousSelection.collectionId)||
        previousSelection.kind==='types'&&previousSelection.typeKeys.every(k=>types.has(k))||
        previousSelection.kind==='objects'&&previousSelection.ids.every(k=>ids.has(k));
      if(valid){S.selection=previousSelection;S.mappingPrefs=storedMappings;renderSelection();renderTarget({skipCollectionRefresh:true});}
    }
    if(S.selection.kind){
      const newlyCreatedSpace=(afterImport&&S.lastReport?.created?.space?.name===desiredName)?S.lastReport.created.space:null;
      const newChoice=newlyCreatedSpace && S.targetSpaces.some(x=>x.id===newlyCreatedSpace.id)?'existing:'+newlyCreatedSpace.id:
        chosenSpace && S.targetSpaces.some(x=>x.id===chosenSpace.id)?'existing:'+chosenSpace.id:
        (afterImport && S.targetSpaces.find(x=>x.name.toLocaleLowerCase()===desiredName.toLocaleLowerCase())
          ?'existing:'+S.targetSpaces.find(x=>x.name.toLocaleLowerCase()===desiredName.toLocaleLowerCase()).id
          :destination);
      const select=$('destination-space');
      if([...select.options].some(x=>x.value===newChoice))select.value=newChoice;
      if(destination==='__create_custom__')$('custom-space').value=desiredName;
      await refreshCollections();
      hidden('custom-space-wrapper',select.value!=='__create_custom__');
      const coll=$('destination-collection');
      const createdCol=(afterImport?S.lastReport?.created?.collection_details||[]:[]).find(x=>x.name===oldCollectionName);
      const foundCol=S.targetCollections.find(x=>x.id===createdCol?.id) || S.targetCollections.find(x=>x.name===oldCollectionName);
      const nextCol=(afterImport&&foundCol)?'existing:'+foundCol.id:oldCollection;
      if([...coll.options].some(x=>x.value===nextCol))coll.value=nextCol;
      $('custom-collection').value=oldCollectionName||$('custom-collection').value;
      $('import-into-collection').checked=withCollection;
      if(afterImport){
        for(const [key,pref] of Object.entries(S.mappingPrefs)){
          if(pref.choice==='__create__'){
            const details=(S.lastReport?.created?.collection_details||[]).find(x=>x.name===pref.name);
            const existing=S.targetCollections.find(x=>x.id===details?.id) || S.targetCollections.find(x=>x.name===pref.name);
            if(existing)S.mappingPrefs[key]={choice:'existing:'+existing.id,name:pref.name};
          }
        }
      }
      renderTypeMappings();updateCollectionDestination();
    }
    if(!afterImport)toast('Espaces, collections et éléments actualisés.');
  }catch(e){toast('Actualisation : '+e.message);}
  finally{S.refreshing=false;refresh.disabled=false;}
}

function blankSelection(){return {kind:null,collectionId:null,typeKeys:[],ids:[]};}
async function loadInventory(){
  const ticket=++S.inventoryTicket;
  S.selection=blankSelection(); S.expandedTypes.clear(); S.mappingPrefs={}; S.inventory=null;
  renderSelection();renderTarget();
  if(!S.sourceSpaceId){label('inventory-notes','Aucun espace autorisé ou disponible.');return;}
  S.loadingInventory=true;hidden('inventory-progress',false);
  label('inventory-notes','Lecture des objets, des types et des collections de cet espace…');
  try{
    const inv=await request('/api/inventory?space_id='+encodeURIComponent(S.sourceSpaceId));
    if(ticket!==S.inventoryTicket)return;
    S.inventory=inv;
    renderSelection();
    label('inventory-notes',`${inv.stats.total} objets · ${inv.stats.collections} collections · ${inv.stats.types} types. Les types incluent aussi les objets présents dans des collections.`);
  }catch(e){
    if(ticket!==S.inventoryTicket)return;
    label('inventory-notes','Impossible de charger cet espace : '+e.message);
    toast('Inventaire : '+e.message);
  }finally{if(ticket===S.inventoryTicket){S.loadingInventory=false;hidden('inventory-progress',true);}}
}
function emptyItem(message){const el=document.createElement('div');el.className='inventory-notes';el.textContent=message;return el;}
function rowElement(item, disabled=false){
  const checked=S.selection.kind==='collection'&&S.selection.collectionId===item.id;
  const el=document.createElement('label');el.className='item-row'+(disabled?' disabled':'')+(checked?' selected':'');
  const inp=document.createElement('input');inp.type='checkbox';inp.checked=checked;inp.disabled=disabled;
  inp.addEventListener('change',()=>toggleCollection(item.id));
  const icon=document.createElement('span');icon.className='item-icon';icon.textContent='▤';
  const name=document.createElement('span');name.className='item-name';name.textContent=item.name;
  const count=document.createElement('span');count.className='item-count';count.textContent=item.count;
  el.append(inp,icon,name,count);return el;
}
function renderTypes(){
  const panel=$('type-list');panel.replaceChildren();
  const inv=S.inventory, s=S.selection;
  if(!inv){panel.append(emptyItem('Choisissez un espace'));return;}
  const search=$('search-types').value.toLocaleLowerCase().trim();
  let any=false;
  for(const type of inv.types){
    const filtered=type.items.filter(obj=>obj.name.toLocaleLowerCase().includes(search));
    if(search&&!type.name.toLocaleLowerCase().includes(search)&&!filtered.length)continue;
    any=true;
    const active=s.kind==='types'&&s.typeKeys.includes(type.key);
    const typeDisabled=s.kind==='space'||s.kind==='collection'||s.kind==='objects';
    const box=document.createElement('div');box.className='type-unit';
    const row=document.createElement('div');row.className='item-row type-row'+(active?' selected':'')+(typeDisabled?' disabled':'');
    const cb=document.createElement('input');cb.type='checkbox';cb.checked=active;cb.disabled=typeDisabled;
    cb.setAttribute('aria-label','Importer tous les objets de '+type.name);
    cb.addEventListener('change',()=>toggleType(type.key));
    const icon=document.createElement('span');icon.className='item-icon';icon.textContent=type.generic?'▧':'▦';
    const title=document.createElement('span');title.className='item-name';title.textContent=type.name;
    const count=document.createElement('span');count.className='item-count';count.textContent=type.count;
    const detail=document.createElement('button');detail.type='button';detail.className='eye-btn'+(S.expandedTypes.has(type.key)?' active':'');
    detail.title='Voir les objets de '+type.name;detail.setAttribute('aria-label',detail.title);
    detail.setAttribute('aria-expanded',String(S.expandedTypes.has(type.key)));detail.innerHTML='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>'; 
    detail.addEventListener('click',()=>{if(S.expandedTypes.has(type.key))S.expandedTypes.delete(type.key);else S.expandedTypes.add(type.key);renderSelection();});
    row.append(cb,icon,title,count,detail);box.append(row);
    if(S.expandedTypes.has(type.key)){
      const items=document.createElement('div');items.className='type-object-list'+(s.kind==='types'?' unavailable':'');
      const objectDisabled=s.kind==='space'||s.kind==='collection'||s.kind==='types';
      const displayed=search&&!type.name.toLocaleLowerCase().includes(search)?filtered:type.items;
      for(const obj of displayed){
        const checked=s.kind==='objects'&&s.ids.includes(obj.id);
        const ob=document.createElement('label');ob.className='item-row object-row'+(objectDisabled?' disabled':'')+(checked?' selected':'');
        const input=document.createElement('input');input.type='checkbox';input.checked=checked;input.disabled=objectDisabled;
        input.addEventListener('change',()=>toggleObject(obj.id));
        const n=document.createElement('span');n.className='item-name';n.textContent=obj.name;
        ob.append(input,n);items.append(ob);
      }
      if(!displayed.length)items.append(emptyItem('Aucun objet'));
      box.append(items);
    }
    panel.append(box);
  }
  if(!any)panel.append(emptyItem('Aucun type correspondant'));
}
function renderSelection(){
  const inv=S.inventory,s=S.selection;
  $('all-space').checked=s.kind==='space';
  label('collection-count',inv?.collections.length||0);
  label('type-count',inv?.types.length||0);
  const cbox=$('collection-list');cbox.replaceChildren();
  if(inv){
    const disabled=s.kind==='space'||s.kind==='types'||s.kind==='objects';
    inv.collections.forEach(x=>cbox.append(rowElement(x, disabled||(s.kind==='collection'&&s.collectionId!==x.id))));
    if(!inv.collections.length)cbox.append(emptyItem('Aucune collection'));
  }else cbox.append(emptyItem('Choisissez un espace'));
  renderTypes();
  $('test-btn').disabled=!apiReady() || !Boolean(s.kind);
}
function selectAllSpace(){S.selection=$('all-space').checked?{...blankSelection(),kind:'space'}:blankSelection();renderSelection();renderTarget();}
function toggleCollection(id){S.selection=S.selection.kind==='collection'&&S.selection.collectionId===id?blankSelection():{...blankSelection(),kind:'collection',collectionId:id};renderSelection();renderTarget();}
function toggleType(key){
  saveTypeMappings();
  const keys=S.selection.kind==='types'?[...S.selection.typeKeys]:[];
  const next=keys.includes(key)?keys.filter(x=>x!==key):[...keys,key];
  S.selection=next.length?{...blankSelection(),kind:'types',typeKeys:next}:blankSelection();
  renderSelection();renderTarget();
}
function toggleObject(id){
  saveTypeMappings();
  const ids=S.selection.kind==='objects'?[...S.selection.ids]:[];
  const next=ids.includes(id)?ids.filter(x=>x!==id):[...ids,id];
  S.selection=next.length?{...blankSelection(),kind:'objects',ids:next}:blankSelection();
  renderSelection();renderTarget();
}
function activeSource(){return S.sourceSpaces.find(x=>x.id===S.sourceSpaceId)||{id:'',name:''};}
function chosenCollection(){return S.inventory?.collections.find(x=>x.id===S.selection.collectionId)||null;}
function chosenTypes(){return S.inventory?.types.filter(t=>S.selection.typeKeys.includes(t.key))||[];}
function mappedTypes(){
  if(S.selection.kind==='types')return chosenTypes();
  if(S.selection.kind!=='objects')return [];
  const ids=new Set(S.selection.ids);
  return S.inventory?.types.filter(t=>t.requires_collection && t.items.some(o=>ids.has(o.id)))||[];
}
function renderTarget({skipCollectionRefresh=false}={}){
  const selected=!!S.selection.kind;
  hidden('empty-target',selected);hidden('configured-target',!selected);
  const requiredForObjects=S.selection.kind==='objects' && mappedTypes().length>0;
  hidden('collection-settings',!selected||!['collection','objects'].includes(S.selection.kind)||requiredForObjects);
  hidden('type-settings',!selected||!['types','objects'].includes(S.selection.kind)||!mappedTypes().length);
  const hint=$('type-settings').querySelector('.field-hint');
  hint.textContent= S.selection.kind==='objects'
    ?'Les objets sélectionnés ayant des propriétés (ou un statut indéterminé) doivent rejoindre une collection de leur type. Les autres objets restent hors collection.'
    :'Une collection est obligatoire dès que des propriétés existent ou que leur absence ne peut être confirmée. Les types sans propriétés identifiées peuvent rester hors collection.';
  if(!selected){$('test-btn').disabled=true;$('import-btn').disabled=true;return;}
  const src=activeSource(),coll=chosenCollection(), types=chosenTypes();
  let name=S.selection.kind==='space'?src.name:S.selection.kind==='collection'?coll?.name:
    S.selection.kind==='types'?types.map(t=>t.name).join(', '):`${S.selection.ids.length} objet(s)`;
  label('selected-name',name||'—');
  label('selected-detail',S.selection.kind==='space'?'Espace complet':S.selection.kind==='collection'?`${coll?.count||0} objets`:
    S.selection.kind==='types'?`${types.length} type(s) sélectionné(s)`:'Sélection d’objets individuels');
  const select=$('destination-space');select.replaceChildren();
  const match=S.targetSpaces.find(x=>x.name.toLocaleLowerCase()===src.name.toLocaleLowerCase());
  select.append(selectOption('__create_same__',`Créer l’espace « ${src.name} »`));
  select.append(selectOption('__create_custom__','Créer un nouvel espace…'));
  S.targetSpaces.forEach(x=>select.append(selectOption('existing:'+x.id,'Espace existant · '+x.name)));
  select.value=match?'existing:'+match.id:'__create_same__';
  $('custom-space').value=src.name;
  hidden('import-into-collection-wrapper',S.selection.kind!=='objects'||requiredForObjects);
  $('import-into-collection').checked=false;
  $('custom-collection').value=S.selection.kind==='collection'?coll?.name||'':'';
  updateSpaceDestination(skipCollectionRefresh);
  updateImportButton();
}
function updateSpaceDestination(skipRefresh=false){
  const value=$('destination-space').value;
  hidden('custom-space-wrapper',value!=='__create_custom__');
  label('space-hint',value.startsWith('existing:')?'Un espace Anytwo existant sera réutilisé.':'Le nouvel espace ne sera pas créé pendant le test.');
  if(!skipRefresh)return refreshCollections().catch(err=>toast('Collections Anytwo : '+err.message));
}
async function refreshCollections(){
  const value=$('destination-space').value,isNew=!value.startsWith('existing:');
  const col=$('destination-collection');col.replaceChildren(selectOption('__create__','Créer une nouvelle collection'));
  S.targetCollections=[];
  if(!isNew&&S.selection.kind!=='space'){
    const id=value.slice('existing:'.length);
    try{
      const resp=await request('/api/collections?space_id='+encodeURIComponent(id));
      if($('destination-space').value!==value)return;
      S.targetCollections=resp.collections;
      resp.collections.forEach(c=>col.append(selectOption('existing:'+c.id,'Collection existante · '+c.name)));
    }catch(e){toast('Impossible de lire les collections Anytwo : '+e.message);}
  }
  col.value='__create__';updateCollectionDestination();renderTypeMappings();
}
function saveTypeMappings(){
  if(!['types','objects'].includes(S.selection.kind))return;
  for(const el of document.querySelectorAll('.type-map')){
    S.mappingPrefs[el.dataset.key]={choice:el.querySelector('select').value,
      name:el.querySelector('input').value};
  }
}
function renderTypeMappings(){
  const panel=$('type-mappings');panel.replaceChildren();
  if(!['types','objects'].includes(S.selection.kind))return;
  for(const t of mappedTypes()){
    const row=document.createElement('div');row.className='type-map';row.dataset.key=t.key;
    const header=document.createElement('div');header.className='type-map-head';
    const title=document.createElement('strong');title.textContent=t.name;
    const count=document.createElement('small');count.textContent=t.count+' objet(s)';header.append(title,count);
    const select=document.createElement('select');select.className='type-map-select';
    if(!t.requires_collection)select.append(selectOption('none','Sans collection (aucune propriété identifiée)'));
    select.append(selectOption('__create__','Créer une nouvelle collection'));
    S.targetCollections.forEach(c=>select.append(selectOption('existing:'+c.id,'Collection existante · '+c.name)));
    const saved=S.mappingPrefs[t.key];
    select.value=saved&&[...select.options].some(x=>x.value===saved.choice)?saved.choice:(t.generic&&!t.requires_collection?'none':'__create__');
    if(t.requires_collection){
      const hint=document.createElement('p');hint.className='type-map-hint required';
      hint.textContent=t.property_state==='yes'?'Propriétés détectées : collection obligatoire.':'Propriétés non vérifiables à ce stade : collection conseillée pour éviter toute perte.';
      row.append(header,select);
      const input=document.createElement('input');input.className='text-input type-map-name';input.maxLength=120;
      input.placeholder='Nom de la nouvelle collection';input.value=saved?.name||t.name;
      const update=()=>hidden(input,select.value!=='__create__');
      select.addEventListener('change',update);update();row.append(input,hint);panel.append(row);
      continue;
    }
    const input=document.createElement('input');input.className='text-input type-map-name';input.maxLength=120;
    input.placeholder='Nom de la nouvelle collection';input.value=saved?.name||t.name;
    const update=()=>hidden(input,select.value!=='__create__');
    select.addEventListener('change',update);update();row.append(header,select,input);panel.append(row);
  }
}
function updateCollectionDestination(){
  hidden('custom-collection-wrapper',$('destination-collection').value!=='__create__');
  hidden('collection-chooser',S.selection.kind==='objects'&&!$('import-into-collection').checked);
  hidden('collection-settings',!['collection','objects'].includes(S.selection.kind) ||
    (S.selection.kind==='objects' && mappedTypes().length>0));
}
function plan(){
  const src=activeSource(),spaceValue=$('destination-space').value;
  const spaceRow=S.targetSpaces.find(x=>'existing:'+x.id===spaceValue);
  const spaceName=spaceRow?.name||(spaceValue==='__create_same__'?src.name:$('custom-space').value.trim());
  const shouldHaveCollection=S.selection.kind==='collection'||
    (S.selection.kind==='objects'&&mappedTypes().length===0&&$('import-into-collection').checked);
  const target={space_mode:spaceRow?'existing':'create',space_id:spaceRow?.id||null,space_name:spaceName,collection_mode:'none',collection_name:'',type_mappings:[]};
  if(shouldHaveCollection){
    const choice=$('destination-collection').value;
    const row=S.targetCollections.find(x=>'existing:'+x.id===choice);
    target.collection_mode=row?'existing':'create';target.collection_id=row?.id||null;
    target.collection_name=row?.name||$('custom-collection').value.trim();
  }
  if(['types','objects'].includes(S.selection.kind)){
    target.type_mappings=[...document.querySelectorAll('.type-map')].map(el=>{
      const choice=el.querySelector('select').value;
      const found=S.targetCollections.find(x=>'existing:'+x.id===choice);
      return {key:el.dataset.key,collection_mode:choice==='none'?'none':found?'existing':'create',
        collection_id:found?.id||null,collection_name:found?.name||el.querySelector('input').value.trim()};
    });
  }
  return {mode:S.mode,source_space:src,selection:{kind:S.selection.kind,collection_id:S.selection.collectionId,
    type_keys:S.selection.typeKeys,ids:S.selection.ids},target,
    files:$('files-option').checked,follow_links:$('links-option').checked};
}

function updateImportButton(){
  $('import-btn').disabled= !apiReady() || !S.selection.kind || S.config.demo || S.mode!=='simple' || S.importRunning;
  label('actions-notice',!apiReady()?'API indisponibles : l’interface reste consultable, mais aucun test ou import n’est possible.':
    S.mode!=='simple'?'Synchronisation en cours de développement : utilisez Import simple.':
    S.config.demo?'Import désactivé en mode démonstration.':
    'L’import crée des données dans Anytwo après confirmation. Tester ne modifie rien.');
}
function renderFinalReport(report){
  S.lastReport=report;
  const root=$('import-report');root.replaceChildren();hidden(root,false);
  const totals=report.totals||{};
  const heading=document.createElement('h3');heading.textContent=`Bilan : ${totals.total||0} objet(s), ${totals.imported||0} complet(s), ${totals.partial||0} partiel(s), ${totals.error||0} erreur(s)`;
  root.append(heading);
  if(report.status==='interrupted'){
    const fatal=document.createElement('strong');fatal.className='report-error';
    fatal.textContent='Import interrompu : le bilan ci-dessous est partiel. Les créations déjà effectuées ne sont pas annulées.';
    root.append(fatal);
  }
  for(const message of report.errors||[]){
    const e=document.createElement('p');e.className='report-error';e.textContent='Erreur générale : '+message;root.append(e);
  }
  for(const col of report.collections||[]){
    if(!(col.issues||[]).length)continue;
    const line=document.createElement('p');line.className='report-issue';
    line.textContent='Collection « '+col.name+' » : '+col.issues.join(' ; ');root.append(line);
  }
  const warnings=Object.entries(report.warnings||{});
  if(warnings.length){
    const box=document.createElement('div');box.className='report-warning-box';
    const label=document.createElement('strong');label.textContent='Incompatibilités regroupées';box.append(label);
    for(const [problem,count] of warnings){const p=document.createElement('p');p.textContent=`${problem} · ${count} occurrence(s)`;box.append(p);}
    root.append(box);
  }
  for(const item of report.objects||[]){
    const el=document.createElement('details');el.className='report-item';el.open=item.status!=='imported';
    const summary=document.createElement('summary');
    summary.textContent=`${item.name} — ${item.status==='imported'?'Importé':item.status==='partial'?'Import partiel':'Échec'} (${(item.reason||[]).join('; ')})`;
    el.append(summary);
    if(item.target_id){const i=document.createElement('small');i.textContent='ID Anytwo : '+item.target_id;el.append(i);}
    for(const issue of item.issues||[]){const p=document.createElement('p');p.className='report-issue';p.textContent='Contenu non reproduit : '+issue;el.append(p);}
    for(const error of item.errors||[]){const p=document.createElement('p');p.className='report-error';p.textContent='Erreur : '+error;el.append(p);}
    root.append(el);
  }
  hidden('export-report',false);
}
async function startImport(){
  if(!apiReady())return toast('API indisponibles : import désactivé.');
  const p=plan();
  if(!p.target.space_name)return toast('Définissez un espace de destination.');
  if(p.target.collection_mode==='create'&&!p.target.collection_name)return toast('Indiquez le nom de la collection.');
  if(p.target.type_mappings.some(t=>t.collection_mode==='create'&&!t.collection_name))return toast('Indiquez le nom de chaque collection.');
  if(!window.confirm('Importer dans Anytwo ?\n\nDes espaces, collections, propriétés et objets vont être créés ou complétés. Aucun retour arrière automatique.\n\nIl est conseillé de commencer par un espace de test.'))return;
  hidden('log-overlay',false);hidden('import-report',true);hidden('export-report',true);
  $('log-lines').replaceChildren();S.lastReport=null;
  label('log-eyebrow','IMPORT RÉEL');label('log-title','Import Anytype → Anytwo');
  label('log-status','Import en cours : ne fermez pas cette fenêtre.');
  S.importRunning=true;updateImportButton();$('test-btn').disabled=true;
  const controller=new AbortController();S.simulation=controller;
  try {
    const res=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p),signal:controller.signal});
    if(!res.ok){const msg=await res.json();throw Error(msg.error||'Erreur HTTP '+res.status);}
    const reader=res.body.getReader(),decoder=new TextDecoder();let buf='',hadEnd=false;
    while(true){const {value,done}=await reader.read();buf+=decoder.decode(value||new Uint8Array(),{stream:!done});
      const parts=buf.split('\n');buf=parts.pop();
      for(const line of parts){if(!line.trim())continue;const evt=JSON.parse(line);
        if(evt.event==='message')appendLog(evt.message);
        else if(evt.event==='object')appendLog(`${evt.name} — ${evt.status} · ${evt.issues.length} adaptation(s), ${evt.errors.length} erreur(s)`);
        else if(evt.event==='summary'){renderFinalReport(evt);hadEnd=true;}
        else if(evt.event==='fatal'){appendLog('! '+evt.message);label('log-status','Import interrompu : modifications partielles possibles.');}
      }
      if(done)break;
    }
    if(hadEnd)label('log-status',S.lastReport?.status==='interrupted'?'Import interrompu · bilan partiel ci-dessous.':'Import terminé · bilan ci-dessous.');
    else label('log-status','Import interrompu · modifications partielles possibles.');
  }catch(e){if(e.name==='AbortError')appendLog('! Connexion au journal interrompue : des écritures ont pu être réalisées.');
    else appendLog('! '+e.message);label('log-status','Import interrompu : vérifiez Anytwo avant de recommencer.');
  }finally{S.importRunning=false;S.simulation=null;updateImportButton();$('test-btn').disabled=false;await refreshData({afterImport:true});}
}
function appendLog(message){
  const el=document.createElement('div');el.className='log-line '+(message.includes('!')?'warning':message.startsWith('→')?'info':'');
  el.textContent='› '+message;$('log-lines').append(el);
  $('log-lines').scrollTop=$('log-lines').scrollHeight;
  label('log-counter',`${$('log-lines').childElementCount} événement(s)`);
}
async function simulate(){
  if(!apiReady())return toast('API indisponibles : simulation désactivée.');
  let p=plan();
  if(!p.target.space_name)return toast('Indiquez le nom de l’espace de destination.');
  if(p.target.collection_mode==='create'&&!p.target.collection_name)return toast('Indiquez le nom de la nouvelle collection.');
  if(p.target.type_mappings.some(t=>t.collection_mode==='create'&&!t.collection_name))return toast('Indiquez un nom pour chaque nouvelle collection.');
  hidden('log-overlay',false);hidden('import-report',true);hidden('export-report',true);$('log-lines').replaceChildren();label('log-eyebrow','SIMULATION');label('log-title','Vérification de l’import');label('log-status','Lecture des données, simulation en cours…');
  $('test-btn').disabled=true;
  let abort=new AbortController();S.simulation=abort;
  try{
    let response=await fetch('/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p),signal:abort.signal});
    if(!response.ok){let error=await response.json();throw Error(error.error||'Erreur '+response.status);}
    const reader=response.body.getReader(), decoder=new TextDecoder();let buffer='';
    let done=false;
    while(!done){const r=await reader.read();done=r.done;buffer+=decoder.decode(r.value||new Uint8Array(),{stream:!done});
      const lines=buffer.split('\n');buffer=lines.pop();
      for(const line of lines){if(!line.trim())continue;const item=JSON.parse(line);
        if(item.message)appendLog(item.message);
        if(item.error){appendLog('! '+item.error);label('log-status','Simulation interrompue par une erreur.');}
        if(item.done)label('log-status','Simulation terminée · aucun changement appliqué.');
      }
    }
  }catch(e){if(e.name!=='AbortError'){appendLog('! '+e.message);label('log-status','Impossible de terminer la simulation.');}}
  finally{S.simulation=null;$('test-btn').disabled=false;}
}
function closeLog(){if(S.importRunning){toast('Import en cours : attendez la fin avant de fermer le journal.');return;}if(S.simulation){S.simulation.abort();S.simulation=null;}hidden('log-overlay',true);}
function openSettings(){
  S.settingsOpen=true;
  hidden('connection-overlay',false);hidden('connect-help',false);
  hidden('anytwo-settings',false);hidden('anytype-settings',false);
  hidden('close-settings',S.connecting);hidden('continue-btn',true);
  label('settings-title','Paramètres de connexion');
  label('settings-hint','Modifiez les ports ou l’autorisation, puis cliquez sur « Enregistrer et vérifier ».');
}
function closeSettings(){
  if(S.connecting)return;
  S.settingsOpen=false;
  hidden('connection-overlay',true);
}
function openCompatibility(){
  S.lastFocused=document.activeElement;
  hidden('compat-overlay',false);
  $('close-compat').focus();
}
function closeCompatibility(){
  hidden('compat-overlay',true);
  S.lastFocused?.focus();
}
function bindEvents(){
  $('compat-details').addEventListener('click',openCompatibility);
  $('close-compat').addEventListener('click',closeCompatibility);
  $('ack-compat').addEventListener('click',closeCompatibility);
  $('compat-overlay').addEventListener('click',e=>{if(e.target===e.currentTarget)closeCompatibility();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('compat-overlay').classList.contains('hidden'))closeCompatibility();});
  window.addEventListener('message',async event=>{
    if(event.origin!==window.location.origin||event.data?.type!=='anytype-paired')return;
    await loadConfig();await runChecks();
  });
  $('connection-button').addEventListener('click',openSettings);
  $('close-settings').addEventListener('click',closeSettings);
  $('retry-btn').addEventListener('click',saveAndCheck);
  $('continue-btn').addEventListener('click',()=>hidden('connection-overlay',true));
  $('pair-btn').addEventListener('click',pairStart);
  $('finish-pair-btn').addEventListener('click',pairFinish);
  $('manual-key-toggle').addEventListener('click',()=>hidden('manual-key-section',!$('manual-key-section').classList.contains('hidden')));
  $('source-space').addEventListener('change',async e=>{S.sourceSpaceId=e.target.value;await loadInventory();});
  $('refresh-data').addEventListener('click',()=>refreshData());
  $('all-space').addEventListener('change',selectAllSpace);
  $('search-types').addEventListener('input',renderSelection);
  $('destination-space').addEventListener('change',()=>{S.mappingPrefs={};updateSpaceDestination();});
  $('destination-collection').addEventListener('change',updateCollectionDestination);
  $('import-into-collection').addEventListener('change',updateCollectionDestination);
  $('mode-help').addEventListener('click',()=>hidden('help-pop',!$('help-pop').classList.contains('hidden')));
  document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{
    S.mode=button.dataset.mode;updateImportButton();
    document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===S.mode));
  }));
  $('test-btn').addEventListener('click',simulate);
  $('import-btn').addEventListener('click',startImport);
  $('export-report').addEventListener('click',()=>{if(!S.lastReport)return;const blob=new Blob([JSON.stringify(S.lastReport,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='bilan-import-anytype-anytwo.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  $('close-log').addEventListener('click',closeLog);$('stop-log').addEventListener('click',closeLog);
}
(async function init(){bindEvents();try{await loadConfig();await runChecks();}catch(e){
  toast('Initialisation : '+e.message);
  S.checks={anytwo:{state:'error',detail:e.message},anytype:{state:'error',detail:e.message}};
  setApiAvailability(false);
  hidden('connect-help',false);hidden('close-settings',false);
  label('settings-hint','Impossible de vérifier les API. Consultez les paramètres ou fermez cette fenêtre pour parcourir l’interface.');
  S.connecting=false;
}})();
