const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const dir = path.resolve(__dirname, '../assurance-estheticiennes-institut-beaute');
const wait = () => new Promise(resolve => setTimeout(resolve, 20));

async function setup(opts = {}) {
  const dom = new JSDOM(fs.readFileSync(path.join(dir, 'index.html'), 'utf8'), {
    url: 'https://example.test/?utm_source=test&gclid=abc&categorie=campagne', runScripts: 'outside-only', pretendToBeVisual: true
  });
  const w = dom.window, requests = [];
  w.scrollTo = () => {};
  w.requestAnimationFrame = () => 0;
  w.dataLayer = [];
  let sheetOk = false, smsData = { success: true }, pending = null;
  if (opts.cors) w.document.querySelector('#leadForm').setAttribute('data-api-mode', 'cors');
  if (opts.consent) w.localStorage.setItem('ubeproCookiePreferencesV1', JSON.stringify({analytics:true,marketing:true}));
  w.navigator.sendBeacon = (url, body) => { requests.push({kind:'crm', url, body}); return true; };
  w.fetch = async (url, requestOptions) => {
    if (url.includes('smspartner')) {
      requests.push({kind:'sms', action:requestOptions.body.get('action'), phone:requestOptions.body.get('telephone')});
      if (pending) return pending;
      return {ok:true, status:200, json:async () => smsData};
    }
    if (url.includes('script.google.com')) {
      requests.push({kind:'sheet', body:requestOptions.body});
      return {ok:sheetOk, status:sheetOk ? 200 : 500, json:async () => ({status:sheetOk ? 'ok' : 'error'})};
    }
    if (url.includes('webflow/get_information.php') && opts.cors) {
      requests.push({kind:'crm-cors', body:requestOptions.body});
      return {ok:true, status:200, json:async () => ({status:'ok'})};
    }
    throw Error('Requête inattendue : ' + url);
  };
  w.eval(fs.readFileSync(path.join(dir, 'script.js'), 'utf8'));
  assert.ok(w.ubeproLead, 'script initialisé');
  const f = w.document.querySelector('#leadForm');
  return { dom, w, f, requests, sheet(v) { sheetOk = v; }, sms(v) { smsData = v; }, pending(v) { pending = v; } };
}

function fillSteps(c) {
  const { f, w } = c;
  const next = () => f.querySelector('#next').click();
  f.querySelector('[data-assurance="rc-pro"]').click(); next();
  f.querySelector('[name="reponse_4"][value="2 à 5 salariés"]').click(); next();
  f.querySelector('[name="reponse_8"]').click(); next();
  f.querySelector('[name="prenom"]').value='Marie'; f.querySelector('[name="nom"]').value='Test'; next();
  f.querySelector('[name="mail"]').value='test@example.test'; next();
  f.querySelector('[name="societe"]').value='Institut'; f.querySelector('[name="code_postal"]').value='75001'; next();
  assert.equal(f.querySelector('.step.is-active').getAttribute('data-step'), '7');
  f.querySelector('[name="telephone"]').value='0607080910';
  f.querySelector('[name="telephone"]').dispatchEvent(new w.Event('input', {bubbles:true}));
  f.querySelector('[name="consentement"][value="oui"]').click();
}
async function verify(c) {
  c.f.querySelector('.sms-send').click(); await wait();
  c.f.querySelector('.sms-code').value='123456';
  c.f.querySelector('.sms-check').click(); await wait();
}

test('parcours original : succès et événement seulement après confirmation Sheets', async () => {
  const c = await setup();
  try {
    fillSteps(c);
    assert.equal(c.f.querySelector('#next').disabled, true);
    await verify(c);
    assert.equal(c.f.querySelector('[name="telephone_verifie"]').value, 'oui');
    c.f.querySelector('#next').click(); await wait();
    assert.equal(c.requests.filter(x=>x.kind==='crm').length, 1);
    assert.equal(c.requests.filter(x=>x.kind==='sheet').length, 1);
    assert.equal(c.f.querySelector('.step-done').classList.contains('is-active'), false);
    assert.equal(c.w.dataLayer.filter(x=>x.event==='formulaire_lead').length, 0);
    assert.match(c.f.querySelector('#formError').textContent, /pas pu transmettre/);
    c.sheet(true); c.f.querySelector('#next').click(); await wait();
    assert.equal(c.f.querySelector('.step-done').classList.contains('is-active'), true);
    assert.equal(c.w.dataLayer.filter(x=>x.event==='formulaire_lead').length, 1);
    const sheet = c.requests.filter(x=>x.kind==='sheet').at(-1).body;
    assert.equal(sheet.get('telephone_verifie'), 'oui');
    assert.equal(sheet.get('gclid'), null);
    assert.notEqual(sheet.get('categorie'), 'campagne');
    assert.equal(c.w.ubeproLead.config.formId, 'a46519725349109k');
    assert.match(sheet.get('reponse_1'), /Responsabilité civile/);
  } finally { c.dom.window.close(); }
});

test('SMS vide refusé et réponses obsolètes ignorées après changement de numéro', async () => {
  const c = await setup();
  try {
    fillSteps(c);
    c.sms({}); c.f.querySelector('.sms-send').click(); await wait();
    assert.equal(c.f.querySelector('.sms-code-wrap').hidden, true);
    assert.equal(c.f.querySelector('[name="telephone_verifie"]').value, 'non');
    let resolve;
    c.pending(new Promise(r=>{resolve=r;}));
    c.f.querySelector('.sms-send').click();
    const phone=c.f.querySelector('[name="telephone"]'); phone.value='0611111111';
    phone.dispatchEvent(new c.w.Event('input',{bubbles:true}));
    resolve({ok:true,status:200,json:async()=>({success:true})}); await wait();
    assert.equal(c.f.querySelector('.sms-code-wrap').hidden, true);
    assert.equal(c.f.querySelector('[name="telephone_verifie"]').value, 'non');
    assert.equal(c.f.querySelector('.sms-send').disabled, false);
  } finally { c.dom.window.close(); }
});

for (const parentOrigin of ['https://www.comparateurpro.fr', 'https://assurance-estheticiennes-instituts-beaute.lp.comparateurpro.fr']) test(`page parente ${parentOrigin} : relais SMS refuse une réponse non JSON`, async () => {
  const { VirtualConsole } = require('jsdom');
  const virtualConsole = new VirtualConsole();
  const dom = new JSDOM('<!doctype html><html><head></head><body><iframe id="lp-assurance-frame" src="/assurance-estheticiennes-institut-beaute/"></iframe></body></html>', {
    url:parentOrigin + '/assurance-estheticiennes-instituts-beaute/', runScripts:'outside-only', pretendToBeVisual:true, virtualConsole
  });
  const w=dom.window, frame=w.document.querySelector('iframe'), messages=[];
  w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
  w.HTMLCanvasElement.prototype.getContext=()=>({fillRect(){},getImageData(){return {data:[0,0,0,255]}}});
  frame.contentWindow.postMessage=(message, origin)=>{ messages.push({message,origin}); };
  w.fetch=async()=>({ok:true,status:200,text:async()=>'<html>erreur</html>'});
  try {
    const script=fs.readFileSync(path.join(dir, '../assurance-estheticiennes-instituts-beaute/script.js'),'utf8');
    assert.ok(!script.includes('__LOCAL_SHIM__'));
    w.eval(script); await wait();
    const init=messages.find(x=>x.message.type==='bridge-init'); assert.ok(init);
    w.dispatchEvent(new w.MessageEvent('message',{source:frame.contentWindow,origin:parentOrigin,data:{channel:'ubepro-assurance-v1',nonce:init.message.nonce,type:'sms-request',requestId:'test-1',params:{action:'envoyer_code',telephone:'0607080910'}}}));
    await wait();
    const response=messages.find(x=>x.message.type==='sms-response');
    assert.ok(response); assert.equal(response.message.ok,false);
  } finally { dom.window.close(); }
});

test('réponse CRM CORS confirmée autorise le succès même si Sheets échoue', async () => {
  const c = await setup({cors:true});
  try {
    fillSteps(c); await verify(c); c.f.querySelector('#next').click(); await wait();
    assert.equal(c.f.querySelector('.step-done').classList.contains('is-active'),true);
    assert.equal(c.w.dataLayer.filter(x=>x.event==='formulaire_lead').length,1);
    const payload=JSON.parse(c.requests.find(x=>x.kind==='crm-cors').body).payload;
    assert.equal(payload.formId,'a46519725349109k');
    assert.equal(payload.data.telephone_verifie,'oui');
    assert.match(payload.data.reponse_1,/Responsabilité civile/);
    assert.notEqual(payload.data.categorie,'campagne');
  } finally { c.dom.window.close(); }
});

test('vérification SMS tardive ne valide pas un nouveau numéro', async () => {
  const c=await setup();
  try {
    fillSteps(c); c.f.querySelector('.sms-send').click(); await wait();
    let resolve; c.pending(new Promise(r=>{resolve=r;}));
    c.f.querySelector('.sms-code').value='123456'; c.f.querySelector('.sms-check').click();
    assert.equal(c.f.querySelector('.sms-check').disabled,true);
    const phone=c.f.querySelector('[name="telephone"]'); phone.value='0611111111';
    phone.dispatchEvent(new c.w.Event('input',{bubbles:true}));
    resolve({ok:true,status:200,json:async()=>({success:true})}); await wait();
    assert.equal(c.f.querySelector('[name="telephone_verifie"]').value,'non');
    assert.equal(c.f.querySelector('#next').disabled,true);
    assert.equal(c.f.querySelector('.sms-check').disabled,false);
  } finally { c.dom.window.close(); }
});

test('la page accepte le suivi consenti du parent esthéticiennes connu, mais pas une origine étrangère', async () => {
  const c=await setup({consent:true});
  try {
    const origin='https://assurance-estheticiennes-instituts-beaute.lp.comparateurpro.fr';
    const nonce='0123456789abcdef0123456789abcdef';
    const send=(from,data)=>c.w.dispatchEvent(new c.w.MessageEvent('message',{source:c.w,origin:from,data:{channel:'ubepro-assurance-v1',...data}}));
    send(origin,{type:'bridge-init',nonce});
    send(origin,{type:'landing-url',nonce,url:origin+'/?utm_source=parent&categorie=esthetique'});
    assert.equal(c.w.ubeproLead.preview().payload.data.source,'parent');
    assert.equal(c.w.ubeproLead.preview().payload.data.categorie,'esthetique');
    send('https://evil.example',{type:'landing-url',nonce,url:'https://evil.example/?utm_source=attaque'});
    assert.equal(c.w.ubeproLead.preview().payload.data.source,'parent');
  } finally { c.dom.window.close(); }
});
