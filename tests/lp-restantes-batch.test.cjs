const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const root=path.resolve(__dirname,'..');
const registre=require('./registre-formid.json');
const wait=()=>new Promise(r=>setTimeout(r,25));
const sites=['alfaromeo-tonale','sauvie-defibrillateurs-en-entreprise','edenred-kadeos','lexus-lbx','paritel','paritel-vous-rembourse','toyota-gamme-hybride','primagaz-obtenez-votre-gaz-propane-a-prix-fixe','cartes-carburant'];
for(const site of sites) test(`${site} : identité, champs métier, SMS et livraison confirmée`,async()=>{
  const vc=new VirtualConsole(), errors=[];vc.on('error',(...a)=>{if(String(a[0]).includes('[lp2site]'))errors.push(a.join(' '));});
  const dom=new JSDOM(fs.readFileSync(path.join(root,site,'index.html'),'utf8'),{url:'https://example.test/?utm_source=source-test&gclid=click',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});
  const w=dom.window;w.HTMLCanvasElement.prototype.getContext=()=>({fillRect(){},getImageData(){return {data:[0,0,0,255]}}});w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});w.scrollTo=()=>{};w.Element.prototype.getClientRects=()=>[1];w.dataLayer=[];w.gtag=()=>{};
  const requests=[];let sheetOk=false;
  w.navigator.sendBeacon=(url,body)=>{requests.push({kind:'crm',url,body});return true;};
  w.fetch=async(url,opts)=>{if(url.includes('smspartner')){requests.push({kind:'sms',body:opts.body});return {ok:true,status:200,text:async()=>'{"success":true}'};} if(url.includes('script.google.com')){requests.push({kind:'sheet',body:opts.body});return {ok:sheetOk,status:sheetOk?200:500,json:async()=>({status:sheetOk?'ok':'error'})};}throw Error('Requête inattendue '+url);};
  try {
    for(const f of ['script.js','lead-handler.js','verification-sms.js'])w.eval(fs.readFileSync(path.join(root,site,f),'utf8'));
    await new Promise(r=>setTimeout(r,400));assert.deepEqual(errors,[]);assert.ok(w.jQuery&&w.lpLead&&w.smsVerification);
    const f=w.document.querySelector('form[data-ubepro-lead="1"]');assert.ok(f);assert.equal(w.lpLead.config.formId,(registre[site]||{}).formId);
    const set=(selector,value)=>{const x=f.querySelector(selector);if(x)x.value=value;return x;};
    const phone=set('[name="telephone"], [name="T-l-phone"]','0607080910');assert.ok(phone);
    set('[name="nom"], [name="Nom"], [name="nom-2"], [name="nom-3"]','Test');set('[name="prenom"], [name="pr-nom-2"]','Marie');
    set('[name="mail"], [name="Email"]','test@example.test');set('[name="societe"], [name="nom-de-la-societe"]','Entreprise');set('[name="code_postal"], [name="Code-postal"], [name="code-postal"]','75001');set('[name="ville"]','Paris');
    const civil=f.querySelector('select[name="Civilit"],select[name="Civilite"],select[name="civilite-5"]');if(civil)civil.selectedIndex=1;
    for(const n of [1,2,3,4,5]) {const r=f.querySelector(`input[type="radio"][name="reponse_${n}"]`);if(r)r.checked=true;const x=f.querySelector(`[name="reponse_${n}"]:not([type="radio"]):not([type="checkbox"]):not([type="hidden"])`);if(x){if(x.tagName==='SELECT')x.selectedIndex=1;else x.value=x.type==='number'?'2':'Réponse';}}
    if(site.startsWith('paritel')){const non=f.querySelector('input[name="reponse_3"][value="Non"]');non.checked=true;set('[name="field-3"]','Opérateur exemple');}
    if(site.startsWith('sauvie-')){for(const x of f.querySelectorAll('select[name="champ-3"],select[name="champ-2"]'))x.selectedIndex=1;f.querySelector('[name="checkbox-2"]').checked=true;}
    const hp=f.querySelector('[name="website"]');hp.value='spam';w.jQuery(f).trigger('submit');await wait();assert.equal(requests.length,0);assert.notEqual(f.style.display,'none','pas de faux succès pour le honeypot');hp.value='';
    w.jQuery(f).trigger('submit');await wait();assert.equal(requests.length,0);
    f.querySelector('.sms-send').click();await wait();f.querySelector('.sms-code').value='123456';f.querySelector('.sms-check').click();await wait();assert.equal(w.smsVerification.estVerifie(),true);
    if(site.startsWith('primagaz-obtenez'))set('[name="reponse_champ_1"]','Gaz propane');
    w.jQuery(f).trigger('submit');await wait();assert.equal(requests.filter(x=>x.kind==='crm').length,1);assert.equal(requests.filter(x=>x.kind==='sheet').length,1);assert.notEqual(f.style.display,'none');assert.equal(w.dataLayer.filter(x=>x.event==='formulaire_lead').length,0);
    const blob=requests.find(x=>x.kind==='crm').body;const raw=await new Promise((resolve,reject)=>{const r=new w.FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsText(blob);});const data=JSON.parse(raw).payload;
    assert.equal(data.formId,(registre[site]||{}).formId);assert.equal(data.data.mail,'test@example.test');assert.equal(data.data.telephone,'0607080910');assert.equal(data.data.telephone_verifie,'oui');/* Révision 10/11/2026 : tracking sans consentement -> le click ID de l'URL remonte. */ assert.equal(data.data.gclid,'click');
    if(site.startsWith('primagaz-obtenez')){assert.equal(data.data.reponse_1,'Gaz propane');assert.equal(requests.find(x=>x.kind==='sheet').body.get('reponse_1'),'Gaz propane');}
    if(site==='cartes-carburant'){assert.equal(data.data.societe,'Entreprise');assert.equal(data.data.prenom,'Marie');assert.equal(w.lpLead.redirectPreview(),'https://www.comparateurpro.fr/radius-remerciement');}
    if(site==='alfaromeo-tonale'){assert.equal(data.data.civilite,'Mr');assert.equal(w.lpLead.redirectPreview(),'https://www.comparateurpro.fr/alfaromeo/tonale-remerciement');}
    if(site==='toyota-gamme-hybride')assert.equal(data.data.reponse_1,'Yaris Hybride');
    if(site.startsWith('paritel')){assert.equal(requests.find(x=>x.kind==='sheet').body.get('reponse_4'),data.data.reponse_4);assert.equal(requests.find(x=>x.kind==='sheet').body.get('reponse_5'),data.data.reponse_5);assert.equal(data.data.operateur_telephonie,'Opérateur exemple');assert.equal(w.lpLead.redirectPreview(),'https://www.comparateurpro.fr/paritel-typ');}
    if(site.startsWith('sauvie-')){assert.equal(data.data.reponse_1,'1');assert.equal(data.data.reponse_2,'Lour mon Défibrillater');assert.equal(data.data.reponse_3,'TPE/PME');assert.equal(data.data.consentement,'oui');}
    sheetOk=true;w.jQuery(f).trigger('submit');await wait();assert.equal(f.style.display,'none');assert.equal(w.dataLayer.filter(x=>x.event==='formulaire_lead').length,1);const evt=w.dataLayer.find(x=>x.event==='formulaire_lead');assert.equal(evt.form_id,(registre[site]||{}).formId);assert.notEqual(evt.form_name,'Assurance-TNS-Pro-Form');assert.equal(evt.lead_type,'standard');/* Révision 10/11/2026 : les conversions améliorées partent sans consentement. */ assert.ok(evt.user_data && evt.user_data.email);
  } finally {dom.window.close();}
});

for(const site of ['edenred-kadeos','lexus-lbx','paritel','paritel-vous-rembourse','toyota-gamme-hybride','primagaz-obtenez-votre-gaz-propane-a-prix-fixe','cartes-carburant']) test(`${site} : navigation des étapes d'origine`,async()=>{
  const vc=new VirtualConsole();const dom=new JSDOM(fs.readFileSync(path.join(root,site,'index.html'),'utf8'),{url:'https://example.test/',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:vc});const w=dom.window;
  w.HTMLCanvasElement.prototype.getContext=()=>({fillRect(){},getImageData(){return {data:[0,0,0,255]}}});w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});w.scrollTo=()=>{};w.gtag=()=>{};w.dataLayer=[];
  w.Element.prototype.getClientRects=function(){for(let e=this;e;e=e.parentElement)if(e.style.display==='none')return [];return [1];};
  // Neutraliser aussi les compteurs du bundle externe pendant le test.
  w.XMLHttpRequest=function(){this.open=()=>{};this.setRequestHeader=()=>{};this.send=()=>{};};
  let deliveries=0;w.navigator.sendBeacon=()=>{deliveries++;return true;};w.fetch=async(url)=>{if(url.includes('smspartner'))return {ok:true,status:200,text:async()=>'{"success":true}'}; if(url.includes('script.google.com')){deliveries++;return {ok:true,status:200,json:async()=>({status:'ok'})};}throw Error('Requête inattendue');};
  try {
    for(const file of ['script.js','lead-handler.js','verification-sms.js'])w.eval(fs.readFileSync(path.join(root,site,file),'utf8'));
    await new Promise(r=>setTimeout(r,400));const form=w.document.querySelector('form[data-ubepro-lead]');const steps=[...form.querySelectorAll('[data-form="step"]')];assert.ok(steps.length>1);
    function fillStep(step) { for(const el of step.querySelectorAll('input,select')) {
      if(el.name==='website')continue;
      if(el.type==='radio') { if(!form.querySelector(`input[type="radio"][name="${el.name}"]:checked`))el.checked=true; }
      else if(el.tagName==='SELECT')el.selectedIndex=1;
      else if(el.type==='email')el.value='test@example.test';
      else if(el.type==='text')el.value=el.name==='telephone'?'0607080910':el.name.includes('postal')?'75001':'Test';
      else if(el.type==='number')el.value='2';
      el.dispatchEvent(new w.Event('input',{bubbles:true}));el.dispatchEvent(new w.Event('change',{bubbles:true}));
    }}
    for(let i=0;i<steps.length-1;i++){
      assert.notEqual(steps[i].style.display,'none',`étape ${i+1} visible`);fillStep(steps[i]);
      const next=steps[i].querySelector('[data-form="next-btn"]');assert.ok(next,`bouton suivant étape ${i+1}`);next.click();await new Promise(r=>setTimeout(r,550));
      assert.equal(steps[i].style.display,'none',`étape ${i+1} quittée`);assert.notEqual(steps[i+1].style.display,'none',`étape ${i+2} visible`);assert.equal(deliveries,0);
    }
    fillStep(steps.at(-1));
    if(site==='cartes-carburant') {
      steps.at(-1).querySelector('[data-form="back-btn"]').click();await new Promise(r=>setTimeout(r,550));
      assert.notEqual(steps.at(-2).style.display,'none','retour à l’étape précédente');assert.equal(deliveries,0,'aucune soumission au retour');
      fillStep(steps.at(-2));steps.at(-2).querySelector('[data-form="next-btn"]').click();await new Promise(r=>setTimeout(r,550));fillStep(steps.at(-1));
      assert.notEqual(steps.at(-1).style.display,'none','retour à la dernière étape');
    }
    const sms=form.querySelector('.sms-verification');assert.ok(sms.getClientRects().length,'vérification SMS visible en fin de parcours');
    assert.equal(deliveries,0);
    const final=steps.at(-1).querySelector('[data-form="submit-btn" i]') || steps.at(-1).querySelector('input[type="submit"]');assert.ok(final);
    final.click();await wait();assert.equal(deliveries,0,'soumission bloquée avant SMS');
    sms.querySelector('.sms-send').click();await wait();sms.querySelector('.sms-code').value='123456';sms.querySelector('.sms-check').click();await wait();assert.equal(w.smsVerification.estVerifie(),true);
    final.click();await new Promise(r=>setTimeout(r,300));assert.equal(deliveries,2,'disabled='+final.disabled+' html='+final.outerHTML+' ; clic réel transmet au CRM et à Sheets ; '+[...form.querySelectorAll('[role=status]')].map(x=>x.textContent).join(' / ')+' ; '+JSON.stringify(w.lpLead.preview().payload.data));assert.equal(form.style.display,'none');
  } finally {dom.window.close();}
});
