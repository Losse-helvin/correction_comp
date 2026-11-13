const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const root = path.resolve(__dirname, '..');
const PARENT = 'assurance-estheticiennes-instituts-beaute';
const CHILD = 'assurance-estheticiennes-institut-beaute';
const CHANNEL = 'ubepro-assurance-v1';

/**
 * Le wrapper (page hôte) affiche la LP enfant dans une iframe. Chacune a son
 * propre dataLayer : l'événement poussé dans l'iframe n'est jamais vu par le
 * conteneur GTM de la page hôte. Le wrapper doit donc relayer la conversion.
 */
function chargerParent() {
  const dom = new JSDOM(fs.readFileSync(path.join(root, PARENT, 'index.html'), 'utf8'), {
    url: 'https://assurance-estheticiennes-instituts-beaute.lp.comparateurpro.fr/',
    runScripts: 'outside-only',
    pretendToBeVisual: true,
  });
  const w = dom.window;
  w.HTMLCanvasElement.prototype.getContext = () => ({ fillRect() {}, getImageData() { return { data: [0, 0, 0, 255] }; } });
  w.scrollTo = () => {};
  w.dataLayer = [];
  w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
  w.Element.prototype.getClientRects = () => [1];
  const frame = w.document.getElementById('lp-assurance-frame');
  // Intercepte ce que le parent envoie à l'iframe pour récupérer le nonce du pont.
  const envoyes = [];
  frame.contentWindow.postMessage = (message) => { envoyes.push(message); };
  w.eval(fs.readFileSync(path.join(root, PARENT, 'script.js'), 'utf8'));
  const nonce = () => {
    const init = envoyes.filter((m) => m && m.type === 'bridge-init').pop();
    return init && init.nonce;
  };
  return { dom, w, frame, envoyes, nonce };
}

function messageParent(w, frame, data) {
  const origin = new URL(frame.getAttribute('src'), w.location.href).origin;
  w.dispatchEvent(new w.MessageEvent('message', { data, origin, source: frame.contentWindow }));
  return origin;
}

test("le wrapper pousse formulaire_lead quand l'iframe signale une conversion", () => {
  const { dom, w, frame, nonce } = chargerParent();
  try {
    assert.ok(frame, 'iframe présente');
    // Poignée de main : la page enfant annonce qu'elle est prête, le parent génère le nonce.
    messageParent(w, frame, { channel: CHANNEL, type: 'bridge-ready' });
    const n = nonce();
    assert.ok(n && n.length >= 16, 'nonce transmis à l’iframe');
    // L'enfant signale la conversion validée, en portant le nonce du pont.
    messageParent(w, frame, { channel: CHANNEL, type: 'lead-submitted', nonce: n });
    assert.equal(w.dataLayer.filter((x) => x && x.event === 'formulaire_lead').length, 1);
  } finally {
    dom.window.close();
  }
});

test('un message sans nonce valide ne déclenche rien', () => {
  const { dom, w, frame } = chargerParent();
  try {
    messageParent(w, frame, { channel: CHANNEL, type: 'bridge-ready' });
    messageParent(w, frame, { channel: CHANNEL, type: 'lead-submitted', nonce: 'nonce-invalide-000000000' });
    assert.equal(w.dataLayer.filter((x) => x && x.event === 'formulaire_lead').length, 0);
  } finally {
    dom.window.close();
  }
});

test("un message d'une origine non autorisée ne déclenche rien", () => {
  const { dom, w, frame, nonce } = chargerParent();
  try {
    messageParent(w, frame, { channel: CHANNEL, type: 'bridge-ready' });
    const n = nonce();
    w.dispatchEvent(new w.MessageEvent('message', {
      data: { channel: CHANNEL, type: 'lead-submitted', nonce: n },
      origin: 'https://exemple-malveillant.test',
      source: frame.contentWindow,
    }));
    assert.equal(w.dataLayer.filter((x) => x && x.event === 'formulaire_lead').length, 0);
  } finally {
    dom.window.close();
  }
});

test("l'iframe enfant signale la conversion au parent après validation", () => {
  const code = fs.readFileSync(path.join(root, CHILD, 'script.js'), 'utf8');
  // Le signal doit être émis dans pushLeadEvents, juste après le push dataLayer.
  const push = code.indexOf('window.dataLayer.push(eventData)');
  const signal = code.indexOf("parentBridgePost({ type: 'lead-submitted' })");
  assert.ok(push !== -1, 'push dataLayer présent');
  assert.ok(signal !== -1, 'signalement parent présent');
  assert.ok(signal > push, 'le signalement suit le push dataLayer');
  const fin = code.indexOf('function submitLead', push);
  assert.ok(signal < fin, 'le signalement reste dans pushLeadEvents');
});
