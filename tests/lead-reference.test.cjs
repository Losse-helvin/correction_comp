const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const jquery = require('jquery');
const root = path.resolve(__dirname, '..');
const wait = () => new Promise(r => setTimeout(r, 20));

async function setup(site, opts = {}) {
  const dom = new JSDOM(fs.readFileSync(path.join(root, site, 'index.html'), 'utf8'), {
    url: 'https://example.test/?utm_source=test&gclid=abc&ltm_category=campagne', runScripts: 'outside-only'
  });
  const w = dom.window;
  w.Element.prototype.getClientRects = () => [1];
  w.jQuery = w.$ = jquery(w);
  w.dataLayer = [];
  if (opts.cors) w.UBE_CONFIG_OVERRIDE = { leadApiMode: 'cors' };
  if (opts.consent) w.document.cookie = 'user_cookie_preferences=' + encodeURIComponent(JSON.stringify({ analytics: true, marketing: true }));
  const requests = [];
  let sheetOk = false, sms = { status: 200, body: { success: true } }, pending = null;
  w.navigator.sendBeacon = (url, body) => { requests.push({ kind: 'crm', url, body }); return true; };
  w.fetch = async (url, options) => {
    const kind = url.includes('smspartner') ? 'sms' : url.includes('script.google.com') ? 'sheet' : 'crm-cors';
    requests.push({ kind, url, body: options.body });
    if (kind === 'sms') {
      if (pending) return pending;
      return { ok: sms.status < 400, status: sms.status, text: async () => JSON.stringify(sms.body) };
    }
    if (kind === 'sheet') return { ok: sheetOk, status: sheetOk ? 200 : 500, json: async () => ({ status: sheetOk ? 'ok' : 'error' }) };
    if (opts.cors) return { ok: true, status: 200, json: async () => ({ status: 'ok' }) };
    throw new Error('Unexpected CRM fetch');
  };
  w.eval(fs.readFileSync(path.join(root, site, 'lead-handler.js'), 'utf8'));
  w.eval(fs.readFileSync(path.join(root, site, 'verification-sms.js'), 'utf8'));
  await wait(); w.dispatchEvent(new w.Event('load')); await wait();
  const form = w.document.querySelector('form[data-ubepro-lead="1"]');
  assert.ok(form && w.smsVerification);
  for (const [name, value] of Object.entries({ telephone: '0607080910', mail: 'test@example.test', nom: 'Test', prenom: 'Marie', code_postal: '75001', societe: 'Exemple' })) {
    const el = form.querySelector(`[name="${name}"]`); if (el) el.value = value;
  }
  const consent = form.querySelector('[name="consentement"][value="oui"]'); if (consent) consent.checked = true;
  return { w, dom, form, requests, sheet: v => { sheetOk = v; }, sms: v => { sms = v; }, pending: v => { pending = v; } };
}
async function code(c) { c.form.querySelector('.sms-send').click(); await wait(); }
async function verify(c) { c.form.querySelector('.sms-code').value = '123456'; c.form.querySelector('.sms-check').click(); await wait(); }
async function submit(c) { c.w.jQuery(c.form).trigger('submit'); await wait(); }
const batch = require('./pages-adaptees.json');
for (const site of ['LP_reference', 'vehicules-utilitaires', 'assurance-tns', 'assurance-tns-pro-v2-adw', 'assurance-consultants-societe-conseil', 'assurance-agriculteur', ...batch.map(x => x.site)]) {
  test(`${site} : envoi bloqué puis confirmation Sheets obligatoire en mode no-cors`, async () => {
    const c = await setup(site);
    try {
      await submit(c); assert.equal(c.requests.length, 0);
      await code(c); assert.equal(c.requests[0].body.get('action'), 'envoyer_code');
      assert.equal(c.requests[0].body.get('telephone'), '0607080910');
      c.sms({status:422,body:{message:'Code invalide'}}); await verify(c);
      assert.match(c.form.querySelector('.sms-message').textContent, /Code invalide/);
      assert.equal(c.w.smsVerification.estVerifie(), false);
      c.sms({status:200,body:{success:true}}); await verify(c);
      assert.equal(c.w.smsVerification.estVerifie(), true);
      await submit(c);
      assert.equal(c.requests.filter(x => x.kind === 'crm').length, 1);
      assert.equal(c.requests.filter(x => x.kind === 'sheet').length, 1);
      const blob = c.requests.find(x => x.kind === 'crm').body;
      const encoded = await new Promise((resolve, reject) => {
        const reader = new c.w.FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsText(blob);
      });
      const sent = JSON.parse(encoded).payload;
      assert.equal(sent.formId, c.w.lpLead.config.formId);
      assert.equal(sent.data.telephone, '0607080910');
      assert.equal(sent.data.telephone_verifie, 'oui');
      assert.notEqual(c.form.style.display, 'none');
      assert.equal(c.w.dataLayer.filter(x => x.event === 'formulaire_lead').length, 0);
      c.sheet(true); await submit(c);
      assert.equal(c.form.style.display, 'none');
      const body = c.requests.filter(x => x.kind === 'sheet').at(-1).body;
      assert.equal(body.get('telephone_verifie'), 'oui');
      /* Révision 10/11/2026 : le tracking se collecte SANS consentement.
         Le localStorage est vierge dans ce scénario (aucun choix exprimé) :
         le click ID et la catégorie de l'URL doivent donc remonter. */
      assert.equal(body.get('gclid'), 'abc');
      assert.equal(body.get('categorie'), 'campagne');
      assert.equal(c.w.dataLayer.filter(x => x.event === 'formulaire_lead').length, 1);
    } finally { c.dom.window.close(); }
  });
  test(`${site} : réponse SMS périmée ignorée`, async () => {
    const c = await setup(site); try {
      let resolve; c.pending(new Promise(r => { resolve = r; }));
      c.form.querySelector('.sms-send').click();
      const p = c.form.querySelector('[name="telephone"]'); p.value = '0611111111';
      p.dispatchEvent(new c.w.Event('input', { bubbles: true }));
      resolve({ok:true,status:200,text:async () => '{"success":true}'}); await wait();
      assert.equal(c.form.querySelector('.sms-code-wrap').hidden, true);
      assert.equal(c.w.smsVerification.estVerifie(), false);
      assert.equal(c.form.querySelector('.sms-send').disabled, false);
    } finally { c.dom.window.close(); }
  });
  test(`${site} : consentement marketing, CRM confirmé et honeypot`, async () => {
    const c = await setup(site, {cors:true, consent:true}); try {
      await code(c); await verify(c); await submit(c);
      assert.equal(c.form.style.display, 'none');
      const crm = JSON.parse(c.requests.find(x => x.kind === 'crm-cors').body).payload;
      assert.equal(crm.data.telephone_verifie, 'oui');
      const event = c.w.dataLayer.find(x => x.event === 'formulaire_lead');
      assert.equal(event.gclid, 'abc'); assert.equal(event.categorie, 'campagne');
      assert.equal(event.user_data.email, 'test@example.test');
    } finally { c.dom.window.close(); }
    const d = await setup(site); try {
      await code(d); await verify(d); d.form.querySelector('[name="website"]').value='spam'; await submit(d);
      assert.equal(d.requests.filter(x => x.kind === 'crm' || x.kind === 'sheet').length, 0);
    } finally { d.dom.window.close(); }
  });
  test(`${site} : délai SMS 429 et expiration 410`, async () => {
    const c = await setup(site); try {
      c.sms({status:429,body:{message:'Patientez',retry_after:30}}); await code(c);
      assert.match(c.form.querySelector('.sms-send').textContent, /30 s/);
      c.w.smsVerification.reinitialiser(); c.sms({status:200,body:{success:true}}); await code(c);
      c.sms({status:410,body:{message:'Code expiré'}}); await verify(c);
      assert.match(c.form.querySelector('.sms-message').textContent, /Code expiré/);
      assert.equal(c.w.smsVerification.estVerifie(), false);
    } finally { c.dom.window.close(); }
  });
}

for (const site of ['LP_reference', 'vehicules-utilitaires', 'assurance-tns', 'assurance-tns-pro-v2-adw', 'assurance-consultants-societe-conseil', 'assurance-agriculteur', ...batch.map(x => x.site)]) test(`${site} : bundle réel chargé et soumission jQuery`, async () => {
  const { VirtualConsole } = require('jsdom');
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('error', (...a) => { if (String(a[0]).includes('[lp2site]')) errors.push(a.join(' ')); });
  const dom = new JSDOM(fs.readFileSync(path.join(root, site, 'index.html'), 'utf8'), {
    url: 'https://example.test/', runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole
  });
  const w = dom.window;
  w.HTMLCanvasElement.prototype.getContext = () => ({ fillStyle:'', fillRect(){}, getImageData(){return {data:[0,0,0,255]};} });
  w.matchMedia = () => ({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
  w.scrollTo = () => {};
  w.Element.prototype.getClientRects = () => [1];
  w.dataLayer = []; w.gtag = () => {};
  const calls = []; let sheetOk = false;
  w.navigator.sendBeacon = () => { calls.push('crm'); return true; };
  w.fetch = async (url, options) => {
    if (url.includes('smspartner')) { calls.push(options.body.get('action')); return {ok:true,status:200,text:async()=>'{"success":true}'}; }
    if (url.includes('script.google.com')) { calls.push('sheet'); return {ok:sheetOk,status:sheetOk ? 200 : 500,json:async()=>({status:sheetOk ? 'ok' : 'error'})}; }
    throw Error('Requête non prévue : ' + url);
  };
  try {
    for (const file of ['script.js', 'lead-handler.js', 'verification-sms.js']) w.eval(fs.readFileSync(path.join(root, site, file), 'utf8'));
    await new Promise(r => setTimeout(r, 400));
    assert.deepEqual(errors, []);
    assert.ok(w.jQuery && w.smsVerification && w.lpLead);
    const f = w.document.querySelector('form[data-ubepro-lead="1"]');
    f.querySelector('[name="telephone"]').value = '0607080910';
    f.querySelector('[name="mail"]').value = 'test@example.test';
    const postal = f.querySelector('[name="code_postal"]'); if (postal) postal.value = '75001';
    const accept = f.querySelector('[name="consentement"][value="oui"]'); if (accept) accept.checked = true;
    w.jQuery(f).trigger('submit'); await wait(); assert.deepEqual(calls, []);
    f.querySelector('.sms-send').click(); await wait();
    f.querySelector('.sms-code').value='123456'; f.querySelector('.sms-check').click(); await wait();
    assert.equal(w.smsVerification.estVerifie(), true);
    w.jQuery(f).trigger('submit'); await wait();
    assert.notEqual(f.style.display, 'none');
    assert.equal(w.dataLayer.filter(x => x.event === 'formulaire_lead').length, 0);
    sheetOk = true; w.jQuery(f).trigger('submit'); await wait();
    assert.equal(f.style.display, 'none');
    assert.equal(w.dataLayer.filter(x => x.event === 'formulaire_lead').length, 1);
    assert.equal(calls.filter(x => x === 'crm').length, 2);
    assert.equal(calls.filter(x => x === 'sheet').length, 2);
  } finally { dom.window.close(); }
});

for (const [site, expected] of [
  ['assurance-tns', 'n51697025492127l'],
  ['assurance-tns-pro-v2-adw', 'i16952589797203d'],
  ['assurance-consultants-societe-conseil', 'a59107373586363o'],
  ['assurance-agriculteur', 'g52511870188750m']
]) test(`${site} : identité et réponse métier conservées`, async () => {
  const c = await setup(site, {cors:true});
  try {
    const check = c.form.querySelector('input[type="checkbox"][name="reponse_1_1"]');
    assert.ok(check); check.checked = true;
    await code(c); await verify(c); await submit(c);
    const payload = JSON.parse(c.requests.find(x => x.kind === 'crm-cors').body).payload;
    assert.equal(payload.formId, expected);
    const label = c.form.querySelector('[name="reponse_lib_1_1"]');
    assert.equal(payload.data.reponse_1, label.value);
    assert.equal(payload.data.question_1, c.form.querySelector('[name="question_1"]').value);
    assert.equal(payload.data.telephone_verifie, 'oui');
  } finally { c.dom.window.close(); }
});

for (const {site, formId} of batch) test(`${site} : identité et réponses de chaque question`, async () => {
  const c = await setup(site);
  try {
    const names = new Set([...c.form.querySelectorAll('[name]')].map(x=>x.name));
    const questions = [...names].filter(n=>/^question_\d+$/.test(n));
    // Une page de coordonnées peut ne contenir aucune question métier.
    for (const q of questions) {
      const n = q.split('_')[1];
      const checks = [...c.form.querySelectorAll(`input[type="checkbox"][name^="reponse_${n}_"]`)];
      const radio = c.form.querySelector(`input[type="radio"][name="reponse_${n}"]`);
      const text = [...c.form.querySelectorAll(`[name="reponse_${n}"]`)].find(x=>!['radio','checkbox','hidden'].includes(x.type));
      if (checks.length) checks[0].checked = true;
      else if (radio) radio.checked = true;
      else if (text && text.tagName === 'SELECT') { const opt = [...text.options].find(o => o.value); if (opt) text.value = opt.value; }
      else if (text) text.value = 'Réponse test';
    }
    const payload = c.w.lpLead.preview().payload;
    assert.equal(payload.formId, formId);
    for (const q of questions) {
      const n=q.split('_')[1]; const checks=[...c.form.querySelectorAll(`input[type="checkbox"][name^="reponse_${n}_"]`)];
      const radio=c.form.querySelector(`input[type="radio"][name="reponse_${n}"]`);
      const text=[...c.form.querySelectorAll(`[name="reponse_${n}"]`)].find(x=>!['radio','checkbox','hidden'].includes(x.type));
      assert.equal(payload.data[q], c.form.querySelector(`[name="${q}"]`).value.trim(), q);
      if (checks.length || radio || text) assert.ok(payload.data[`reponse_${n}`], `réponse ${n} manquante`);
    }
  } finally { c.dom.window.close(); }
});

for (const [site, question] of [['assurance-tns', 7], ['assurance-tns-pro-v2-adw', 7], ['assurance-consultants-societe-conseil', 7], ['assurance-professionnelle-iard', 2]]) test(`${site} : choix et texte du même champ préservés`, async () => {
  const c = await setup(site);
  try {
    const radio = c.form.querySelector(`input[type="radio"][name="reponse_${question}"]`);
    const text = c.form.querySelector(`input[type="text"][name="reponse_${question}"]`);
    assert.ok(radio && text); radio.checked = true; text.value = 'Précision test';
    const answer = c.w.lpLead.preview().payload.data[`reponse_${question}`];
    assert.ok(answer.includes(radio.value));
    assert.ok(answer.includes('Précision test'));
  } finally { c.dom.window.close(); }
});

for (const [site, target] of [
  ['edenred-ticket-restaurant-juillet-v1', 'https://www.comparateurpro.fr/edenred-typ'],
  ['suivi-de-vehicules', 'https://www.comparateurpro.fr/radius-telematics-typ'],
  ['ticket-restaurant-', 'https://www.comparateurpro.fr/edenred-typ'],
  ['ticket-restaurant-septembre', 'https://www.comparateurpro.fr/edenred-typ'],
  ['ticket-restaurant-septembre-btp', 'https://www.comparateurpro.fr/edenred-typ']
]) test(`${site} : destination de remerciement conservée après confirmation`, async () => {
  const c = await setup(site);
  try {
    assert.equal(c.w.lpLead.redirectPreview(), target);
    c.form.setAttribute('data-redirect', 'javascript:alert(1)');
    assert.equal(c.w.lpLead.redirectPreview(), '');
  } finally { c.dom.window.close(); }
});

for (const [site, target] of [
  ['mercedes-benz-mercedes-benz-evito', 'https://www.comparateurpro.fr/mercedes-vous-remercie'],
  ['mercedes-benz-nouvel-ecitan-fourgon', 'https://www.comparateurpro.fr/mercedes-vous-remercie'],
  ['mercedes-benz-sprinter', 'https://www.comparateurpro.fr/mercedes-vous-remercie']
]) test(`${site} : redirection métier conservée`, async () => {
  const c = await setup(site);
  try { assert.equal(c.w.lpLead.redirectPreview(), target); }
  finally { c.dom.window.close(); }
});

test('SMS : une ancienne réponse ne peut pas remplacer une nouvelle demande du même numéro', async () => {
  const c = await setup('assurance-tns');
  try {
    let first, second;
    c.pending(new Promise(r => { first = r; }));
    c.form.querySelector('.sms-send').click();
    const phone = c.form.querySelector('[name="telephone"]');
    phone.value = '0611111111'; phone.dispatchEvent(new c.w.Event('input', {bubbles:true}));
    phone.value = '0607080910'; phone.dispatchEvent(new c.w.Event('input', {bubbles:true}));
    c.pending(new Promise(r => { second = r; })); c.form.querySelector('.sms-send').click();
    first({ok:true,status:200,text:async()=>'{"success":true}'}); await wait();
    assert.equal(c.form.querySelector('.sms-code-wrap').hidden, true);
    second({ok:true,status:200,text:async()=>'{"success":true}'}); await wait();
    assert.equal(c.form.querySelector('.sms-code-wrap').hidden, false);
  } finally { c.dom.window.close(); }
});

test('SMS : modifier le numéro pendant une vérification ne bloque pas le bouton suivant', async () => {
  const c = await setup('assurance-tns');
  try {
    await code(c);
    let resolve; c.pending(new Promise(r => { resolve = r; }));
    c.form.querySelector('.sms-code').value='123456'; c.form.querySelector('.sms-check').click();
    assert.equal(c.form.querySelector('.sms-check').disabled, true);
    const phone=c.form.querySelector('[name="telephone"]'); phone.value='0611111111';
    phone.dispatchEvent(new c.w.Event('input', {bubbles:true}));
    assert.equal(c.form.querySelector('.sms-check').disabled, false);
    resolve({ok:true,status:200,text:async()=>'{"success":true}'}); await wait();
    assert.equal(c.w.smsVerification.estVerifie(), false);
  } finally { c.dom.window.close(); }
});

test('Les formId de toutes les pages adaptées sont uniques', () => {
  const pages = ['LP_reference', 'vehicules-utilitaires', 'assurance-tns', 'assurance-tns-pro-v2-adw', 'assurance-consultants-societe-conseil', 'assurance-agriculteur', ...batch.map(x => x.site)];
  const ids = pages.map(site => {
    const script = fs.readFileSync(path.join(root, site, 'lead-handler.js'), 'utf8');
    const match = script.match(/\bformId:\s*['"]([^'"]+)['"]/); assert.ok(match, site); return match[1];
  });
  assert.equal(new Set(ids).size, ids.length);
});

test('SMS : une réponse 200 sans données ne valide ni l’envoi ni le numéro', async () => {
  const c = await setup('assurance-tns');
  try {
    c.sms({status:200,body:{}}); await code(c);
    assert.equal(c.form.querySelector('.sms-code-wrap').hidden, true);
    assert.match(c.form.querySelector('.sms-message').textContent, /Réponse invalide/);
    c.sms({status:200,body:{success:true}}); await code(c);
    c.sms({status:200,body:{}}); await verify(c);
    assert.equal(c.w.smsVerification.estVerifie(), false);
    await submit(c); assert.equal(c.requests.filter(x => x.kind === 'crm' || x.kind === 'sheet').length, 0);
  } finally { c.dom.window.close(); }
});
