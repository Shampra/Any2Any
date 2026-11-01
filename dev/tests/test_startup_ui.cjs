'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
function harness({fail=false,dev=false}={}){
 const elements=new Map(),calls=[],activations=[];let document;
 class Element{
  constructor(){this.value='';this.textContent='';this.handlers={};this.children=[];const classes=new Set(['hidden']);this.classList={toggle:(s,v)=>{v?classes.add(s):classes.delete(s);},contains:s=>classes.has(s),add:s=>classes.add(s),remove:s=>classes.delete(s)};}
  addEventListener(name,fn){this.handlers[name]=fn;}setAttribute(){}focus(){document.activeElement=this;}
  append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}querySelector(){return new Element();}remove(){}
 }
 const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
 document={getElementById:get,createElement:()=>new Element(),querySelector:()=>new Element(),querySelectorAll:()=>[],addEventListener(){},activeElement:null};
 const context={document,window:{NotionSource:{activate:async()=>activations.push('notion'),closeSettings(){},closeLoading(){}},addEventListener(){},location:{origin:'http://localhost'}},fetch:async(path,options={})=>{
  calls.push([path,options.method||'GET']);let data={};let ok=true;
  if(path==='/api/config'&&!options.method)data={choose_source_on_start:!dev,profile:dev?'notion-dev':'unified',source_kind:dev?'notion':'anytype',demo:true};
  else if(path==='/api/config'&&fail){ok=false;data={error:'Cannot save settings'};}
  else if(path.startsWith('/api/check/'))data={state:'error',detail:'Client not running'};
  return {ok,json:async()=>data};
 },setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,clearInterval(){},console};
 vm.createContext(context);vm.runInContext(fs.readFileSync('app/static/app.js','utf8'),context);return{get,calls,activations,context};
}
const flush=async()=>{for(let i=0;i<10;i++)await new Promise(r=>setImmediate(r));};
(async()=>{
 let h=harness();await flush();assert.equal(h.calls.length,1);assert.equal(h.get('source-overlay').classList.contains('hidden'),false,'welcome before network access checks');
 await h.get('choose-notion').handlers.click();await flush();assert.deepEqual(h.activations,['notion']);assert.equal(h.get('source-kind').value,'notion');assert(h.get('source-overlay').classList.contains('hidden'));
 h=harness();await flush();await h.get('choose-anytype').handlers.click();await flush();assert(h.calls.some(([p])=>p==='/api/check/anytype'));assert(h.calls.some(([p])=>p==='/api/check/anytwo'));assert.equal(h.activations.length,0);
 h=harness({fail:true});await flush();await h.get('choose-notion').handlers.click();await flush();assert.equal(h.activations.length,0);assert.equal(h.get('source-overlay').classList.contains('hidden'),false);assert.equal(h.get('choose-notion').disabled,false);
 h=harness({dev:true});await flush();assert.deepEqual(h.activations,['notion'],'explicit dev profile keeps direct access');
 console.log('4 startup scenarios passed: explicit source choice, source-specific checks, retry after save failure and isolated dev launch.');
})().catch(e=>{console.error(e);process.exit(1)});
