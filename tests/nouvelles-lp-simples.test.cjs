const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const root=path.resolve(__dirname,'..');
const registre=require('./registre-formid.json');
const wait=()=>new Promise(r=>setTimeout(r,25));

for (const site of ['primagaz', 'dacia-jogger', 'renault-capture', 'intuis', 'sage-gestion-de-la-paie-hd', 'ayvens-france', 'mitsubishi-fuso']) {
  test(`${site} : champs, SMS, routage et confirmation de livraison`, async () => {
    const errors=[];
    const virtualConsole=new VirtualConsole();
    virtualConsole.on('error',(...v)=>{if(String(v[0]).includes('[lp2site]')) errors.push(v.join(' '));});
    const dom=new JSDOM(fs.readFileSync(path.join(root,site,'index.html'),'utf8'),{
      url:'https://example.test/?utm_source=test&gclid=click', runScripts:'outside-only',pretendToBeVisual:true,virtualConsole
    });
    const w=dom.window;
    w.HTMLCanvasElement.prototype.getContext=()=>({fillRect(){},getImageData(){return {data:[0,0,0,255]}}});
    w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
    w.scrollTo=()=>{}; w.Element.prototype.getClientRects=()=>[1];
    w.dataLayer=[]; w.gtag=()=>{};
    const requests=[]; let sheets=false;
    w.navigator.sendBeacon=(url,body)=>{requests.push({kind:'crm',url,body});return true;};
    w.fetch=async(url,opts)=>{
      if(url.includes('smspartner')){requests.push({kind:'sms',url,body:opts.body});return {ok:true,status:200,text:async()=>'{"success":true}'};}
      if(url.includes('script.google.com')){requests.push({kind:'sheet',url,body:opts.body});return {ok:sheets,status:sheets?200:500,json:async()=>({status:sheets?'ok':'error'})};}
      throw Error('Requête inattendue: '+url);
    };
    try {
      for(const file of ['script.js','lead-handler.js','verification-sms.js']) w.eval(fs.readFileSync(path.join(root,site,file),'utf8'));
      await new Promise(r=>setTimeout(r,400));
      assert.deepEqual(errors,[]); assert.ok(w.jQuery && w.lpLead && w.smsVerification);
      const form=w.document.querySelector('form[data-ubepro-lead="1"]');
      assert.ok(form); assert.equal(w.lpLead.config.formId,(registre[site]||{}).formId);
      assert.equal(w.lpLead.config.leadApiUrl,'https://mc.hellolead.pro/mon_compte/api/webflow/get_information.php');
      const phone=form.querySelector('[name="telephone"]');phone.value='0607080910';
      form.querySelector('[name="nom"]').value='Test';form.querySelector('[name="prenom"]').value='Marie';
      const company=form.querySelector('[name="societe"]');if(company)company.value='Entreprise';
      const postal=form.querySelector('[name="code_postal"]');if(postal)postal.value='75001';
      const city=form.querySelector('[name="ville"]');if(city)city.value='Paris';
      const email=form.querySelector('[name="email"], [name="mail-2"], [name="mail"]');email.value='test@example.test';
      const civilite=form.querySelector('select[name="civilite"]');if(civilite)civilite.value='1';
      const q=form.querySelector('input[type="radio"][name="reponse_1"]');if(q)q.checked=true;
      if(site==='ayvens-france') {
        form.querySelector('[name="reponse_1"]').value='123456789';
        for(const n of [2,3,4,5])form.querySelector(`input[type="radio"][name="reponse_${n}"]`).checked=true;
      }
      if(site==='mitsubishi-fuso') {
        form.querySelector('input[type="radio"][name="reponse_2"]').checked=true;
        form.querySelector('input[type="checkbox"][name="reponse_4"]').checked=true;
      }
      w.jQuery(form).trigger('submit');await wait();assert.equal(requests.length,0);
      form.querySelector('.sms-send').click();await wait();
      form.querySelector('.sms-code').value='123456';form.querySelector('.sms-check').click();await wait();
      assert.equal(w.smsVerification.estVerifie(),true);
      const checkbox=form.querySelector('[name="checkbox"]');
      if (checkbox) {
        assert.equal(w.lpLead.preview().payload.data.consentement, 'non');
        if (checkbox.required) {
          w.jQuery(form).trigger('submit'); await wait();
          assert.equal(requests.filter(x=>x.kind==='crm'||x.kind==='sheet').length,0, 'case obligatoire non cochée');
        }
        checkbox.checked=true;
      }
      const nom=form.querySelector('[name="nom"]');nom.value='';
      w.jQuery(form).trigger('submit');await wait();
      assert.equal(requests.filter(x=>x.kind==='crm'||x.kind==='sheet').length,0,'champ obligatoire vérifié');
      nom.value='Test';w.jQuery(form).trigger('submit');await wait();
      assert.equal(requests.filter(x=>x.kind==='crm').length,1);
      assert.equal(requests.filter(x=>x.kind==='sheet').length,1);
      assert.notEqual(form.style.display,'none');assert.equal(w.dataLayer.filter(x=>x.event==='formulaire_lead').length,0);
      const blob=requests.find(x=>x.kind==='crm').body;
      const raw=await new Promise((resolve,reject)=>{const reader=new w.FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsText(blob);});
      const payload=JSON.parse(raw).payload;
      assert.equal(payload.formId,(registre[site]||{}).formId);assert.equal(payload.data.mail,'test@example.test');
      assert.equal(payload.data.telephone_verifie,'oui');/* Révision 10/11/2026 : tracking sans consentement. */ assert.equal(payload.data.gclid,'click');
      if(civilite)assert.equal(payload.data.civilite,'1');
      if(q)assert.equal(payload.data.reponse_1,q.value);
      if(checkbox)assert.equal(payload.data.consentement,'oui');
      if(site==='sage-gestion-de-la-paie-hd')assert.equal(w.lpLead.redirectPreview(),'https://devis.comparateurpro.fr/sage-gestion-de-paie-typ/');
      if(site==='mitsubishi-fuso') {
        assert.equal(w.lpLead.redirectPreview(),'https://www.comparateurpro.fr/mitsubishi-fuso-remerciement');
        assert.equal(payload.data.reponse_4,'oui');assert.equal(payload.data.reponse_5,'non');
        const sheetBody=requests.find(x=>x.kind==='sheet').body;
        assert.equal(sheetBody.get('reponse_4'),'oui');assert.equal(sheetBody.get('reponse_5'),'non');
      }
      if(site==='ayvens-france') {
        assert.equal(payload.data.reponse_1,'123456789');
        for(const n of [2,3,4,5])assert.equal(payload.data[`reponse_${n}`],form.querySelector(`input[name="reponse_${n}"]:checked`).value);
        const sheetBody=requests.find(x=>x.kind==='sheet').body;
        assert.equal(sheetBody.get('reponse_4'),payload.data.reponse_4);
        assert.equal(sheetBody.get('reponse_5'),payload.data.reponse_5);
      }
      sheets=true;w.jQuery(form).trigger('submit');await wait();
      assert.equal(form.style.display,'none');assert.equal(w.dataLayer.filter(x=>x.event==='formulaire_lead').length,1);
    } finally {dom.window.close();}
  });
}
