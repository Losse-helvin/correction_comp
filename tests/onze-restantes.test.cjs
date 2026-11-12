const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'), wait=()=>new Promise(r=>setTimeout(r,30));
const registre=require('./registre-formid.json');
const sites=['assurance-test-telephone','assurances-professionnelles','formulaire-globale','gamme-de-rayonnage-actiflip-hd','gamme-de-rayonnage-actiflip-v4','lexus-lbx-2','rc-pro-consultant-conseil-adw','typ-formulaires-typ-secu-form','voiture-nouveau-range-rover','voiture-range-rover','volvo'];
for(const site of sites)test(`${site} : formulaires indépendants, SMS et confirmation`,async()=>{
 const errors=[];const vc=new VirtualConsole();vc.on('error',v=>{if(String(v).includes('[lp2site]'))errors.push(String(v));});
 const dom=new JSDOM(fs.readFileSync(path.join(root,site,'index.html'),'utf8'),{url:'https://example.test/?utm_source=test&gclid=click',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});const w=dom.window;
 w.HTMLCanvasElement.prototype.getContext=()=>({fillRect(){},getImageData(){return {data:[0,0,0,255]}}});w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});w.scrollTo=()=>{};w.Element.prototype.getClientRects=()=>[1];w.dataLayer=[];w.gtag=()=>{};
 if(site==='rc-pro-consultant-conseil-adw')w.MutationObserver=class{observe(){} disconnect(){} takeRecords(){return []}};
 w.XMLHttpRequest=function(){this.open=()=>{};this.setRequestHeader=()=>{};this.send=()=>{};};
 let sheetOk=false;const req=[];w.navigator.sendBeacon=(url,body)=>{req.push({kind:'crm',body});return true;};w.fetch=async(url,opts)=>{if(url.includes('smspartner'))return{ok:true,status:200,text:async()=>'{"success":true}'};if(url.includes('script.google.com')){req.push({kind:'sheet',body:opts.body});return{ok:sheetOk,status:sheetOk?200:500,json:async()=>({status:sheetOk?'ok':'error'})};}throw Error('Réseau inattendu '+url)};
 try {
  for(const file of ['script.js','lead-handler.js','verification-sms.js'])w.eval(fs.readFileSync(path.join(root,site,file),'utf8'));await new Promise(r=>setTimeout(r,500));assert.deepEqual(errors,[]);
  const forms=[...w.document.querySelectorAll('form[data-ubepro-lead="1"]')];assert.equal(forms.length,['volvo','lexus-lbx-2','voiture-nouveau-range-rover'].includes(site)?2:1);
  for(const [index,f] of forms.entries()){
   assert.ok(f.lpLead&&f.smsVerification,`modules du formulaire ${index}`);assert.equal(f.lpLead.config.formId,(registre[site]||{}).formId);
   const name=(names)=>{for(const n of names){const e=[...f.querySelectorAll('[name]')].find(x=>x.name.toLowerCase()===n.toLowerCase()&&x.type!=='checkbox'&&x.type!=='radio');if(e)return e;}return null;};
   const set=(names,value)=>{let el=name(names);if(el){el.value=value;el.dispatchEvent(new w.Event('input',{bubbles:true}));el.dispatchEvent(new w.Event('change',{bubbles:true}));}return el;};
   set(['nom','nom-2'],'Test');set(['prenom','prenom-2'],'Marie');set(['mail','email','email-2'],'test@example.test');set(['societe'],'Société');set(['code_postal','Code-postal'],'75001');
   const phone=set(['telephone','telephone-2'],'060708091'+index);assert.ok(phone);
   for(const select of f.querySelectorAll('select'))if(select.name==='civilite'||select.name.startsWith('Motorisation')||select.name.toLowerCase().startsWith('type-d-usage'))select.selectedIndex=Math.min(1,select.options.length-1);
   for(const [n,value] of [['consentement','oui'],['M','Monsieur'],['st','Société']]){const radio=f.querySelector(`input[name="${n}"][value="${value}"]`);if(radio)radio.checked=true;}
   if(site==='rc-pro-consultant-conseil-adw'){f.querySelector('[name="g"]').checked=true;f.querySelector('#rg').checked=true;}
   const submit=()=>f.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
   let before=req.length;submit();await wait();assert.equal(req.length,before,'aucune livraison avant validation SMS');
   f.querySelector('.sms-send').click();await wait();f.querySelector('.sms-code').value='123456';f.querySelector('.sms-check').click();await wait();assert.equal(f.smsVerification.estVerifie(),true, 'téléphone='+phone.value+' message='+f.querySelector('.sms-message').textContent);
   if(forms.length>1&&index===0)assert.equal(forms[1].smsVerification.estVerifie(),false,'le deuxième téléphone reste non vérifié');
   submit();await wait();assert.equal(req.length,before+2,'tentatives CRM et Sheets ; values='+JSON.stringify([...f.querySelectorAll('input[required]')].map(x=>[x.name,x.value,x.checked]))+' invalid='+[...f.querySelectorAll(':invalid')].map(x=>x.outerHTML).join(' | ')+' messages='+[...f.querySelectorAll('[role=status]')].map(x=>x.textContent).join(' | '));assert.notEqual(f.style.display,'none');if(site==='rc-pro-consultant-conseil-adw')assert.equal(f.querySelector('#s4').classList.contains('active'),false);
   const raw=await new Promise((resolve,reject)=>{const r=new w.FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsText(req[before].body);});const data=JSON.parse(raw).payload;assert.equal(data.formId,(registre[site]||{}).formId);assert.equal(data.data.telephone,'060708091'+index);assert.equal(data.data.mail,site==='gamme-de-rayonnage-actiflip-v4'?'':'test@example.test');assert.equal(data.data.telephone_verifie,'oui');/* Révision 10/11/2026 : tracking sans consentement. */ assert.equal(data.data.gclid,'click');
   if(site.startsWith('voiture-'))assert.equal(data.data.consentement_email,'non');
   if(site==='rc-pro-consultant-conseil-adw'){assert.equal(data.data.consentement,'oui');assert.ok(data.data.reponse_1);assert.equal(data.data.reponse_3,'1');}
   sheetOk=true;submit();await wait();if(site==='rc-pro-consultant-conseil-adw')assert.equal(f.querySelector('#s4').classList.contains('active'),true);else assert.equal(f.style.display,'none');sheetOk=false;
  }
 } finally {dom.window.close();}
});
