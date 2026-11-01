"use strict";
const $=id=>document.getElementById(id);
let challengeId='';
async function api(url,options={}){
  const res=await fetch(url,{cache:'no-store',...options});const data=await res.json();
  if(!res.ok || data.error)throw Error(data.error||'Erreur HTTP '+res.status);
  return data;
}
const post=(url,body)=>api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function show(text,type=''){ $('status').textContent=text;$('status').className='pair-status '+type; }
async function start(){
  $('code').disabled=true;$('submit').disabled=true;$('retry').hidden=true;
  show('Envoi de la demande à Anytype…');
  try{
    const port=Number(new URLSearchParams(location.search).get('port'))||31009;
    await post('/api/config',{anytype_port:port});
    const out=await post('/api/pair/start',{});
    if(!out.challenge_id)throw Error('Anytype n’a pas retourné de challenge_id.');
    challengeId=out.challenge_id;
    $('code').disabled=false;$('submit').disabled=false;
    show('Demande envoyée. Choisissez les autorisations dans Anytype, puis saisissez le code ici.');
    $('code').focus();
  }catch(err){show('Impossible de démarrer : '+err.message,'error');$('retry').hidden=false;}
}
async function finish(){
  const code=$('code').value.trim();
  if(!/^\d{4}$/.test(code)){show('Le code doit contenir exactement quatre chiffres.','error');return;}
  $('submit').disabled=true;show('Vérification du code…');
  try{
    await post('/api/pair/finish',{challenge_id:challengeId,code});
    show('Accès autorisé et enregistré. Vous pouvez fermer cette fenêtre.','ok');
    $('code').disabled=true;
    if(window.opener && !window.opener.closed)window.opener.postMessage({type:'anytype-paired'},window.location.origin);
    $('submit').textContent='Fermer';$('submit').disabled=false;$('submit').onclick=()=>window.close();
  }catch(err){show('Impossible de valider : '+err.message,'error');$('submit').disabled=false;}
}
$('submit').addEventListener('click',finish);$('retry').addEventListener('click',start);
$('code').addEventListener('keydown',e=>{if(e.key==='Enter'&&!$('submit').disabled)finish();});
start();