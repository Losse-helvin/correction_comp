/**
 * Pont parent (page wrapper) -> iframe de la LP Assurance.
 * Protocole : ubepro-assurance-v1 (double format, voir ci-dessous).
 *
 * Roles :
 * - relayer le consentement et l'URL publique de la page parente (UTM,
 *   click IDs, ltm_*) vers l'iframe pour l'attribution des leads ;
 * - RELAIS SMS (ajoute le 2026-10-26) : executer pour le compte de
 *   l'iframe les appels a l'API SMS Partner (envoyer_code /
 *   verifier_code), comme le snippet parent de la LP de reference
 *   (WEBFLOW_EMBED.md), et lui renvoyer le statut HTTP + le JSON lu
 *   meme en erreur (422/404/409/410/429/502 geres cote enfant).
 *
 * Deux formats de messages sont supportes :
 * - format "reference" : { channel: 'ubepro-assurance-v1', nonce, type }
 *   avec poignee de main bridge-ready -> bridge-init (nonce), messages
 *   consent-state / landing-url / sms-request / sms-response ;
 * - format "LP du depot" : { bridge: 'ubepro-assurance-v1', type } avec
 *   consent-state(-request) / landing-url(-request), conserve si
 *   l'iframe pointe un jour vers une LP traitee du depot.
 *
 * Prerequis pour le SMS (voir docs/VERIFICATION-SMS.md) :
 * - la LP enfant doit autoriser l'origine de CETTE page comme parent ;
 * - l'API SMS doit autoriser en CORS l'origine de cette page (les POST
 *   partent du navigateur, depuis le domaine du wrapper).
 */
(function () {
  'use strict';

  var FRAME_ID = 'lp-assurance-frame';
  var CHANNEL = 'ubepro-assurance-v1';
  var SMS_ENDPOINT = 'https://mc.hellolead.pro/mon_compte/api/smspartner/envoi_code_verification.php';
  var allowedParents = [
    'https://www.comparateurpro.fr',
    'https://comparateurpro.fr',
    'https://assurance-consultant-societe-conseil-v2.lp.comparateurpro.fr',
    'https://comparateur-pro.webflow.io'
  ];

  var iframe = null;
  var manualConsent = null;
  var nonce = '';

  function getIframe() {
    iframe = iframe || document.getElementById(FRAME_ID);
    return iframe;
  }

  function parentIsAllowed() {
    return allowedParents.indexOf(window.location.origin) !== -1;
  }

  function frameOrigin() {
    var frame = getIframe();
    if (!frame) return '';
    try {
      return new URL(frame.getAttribute('src'), window.location.href).origin;
    } catch (e) {
      return 'https://www.ubepro.com';
    }
  }

  function makeNonce() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    } catch (e) {}
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 3 | 8)).toString(16);
    });
  }

  /* ---------------- Format "LP du depot" (historique) ---------------- */

  function post(type, payload) {
    var frame = getIframe();
    if (!frame || !frame.contentWindow || !parentIsAllowed()) return false;
    var message = { bridge: CHANNEL, type: type };
    Object.keys(payload || {}).forEach(function (key) {
      message[key] = payload[key];
    });
    frame.contentWindow.postMessage(message, frameOrigin());
    return true;
  }

  function denied() {
    return {
      analytics_storage: 'denied',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    };
  }

  function granted() {
    return {
      analytics_storage: 'granted',
      ad_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted'
    };
  }

  function getConsent() {
    if (manualConsent !== null) return manualConsent ? granted() : denied();
    try {
      if (window.CookieConsent) {
        return {
          analytics_storage: window.CookieConsent.acceptedCategory('analytics') ? 'granted' : 'denied',
          ad_storage: window.CookieConsent.acceptedCategory('marketing') ? 'granted' : 'denied',
          ad_user_data: window.CookieConsent.acceptedCategory('marketing') ? 'granted' : 'denied',
          ad_personalization: window.CookieConsent.acceptedCategory('marketing') ? 'granted' : 'denied'
        };
      }
      var raw = window.localStorage && window.localStorage.getItem('user_cookie_preferences');
      if (raw) {
        var preferences = JSON.parse(raw);
        return {
          analytics_storage: preferences.analytics ? 'granted' : 'denied',
          ad_storage: preferences.marketing ? 'granted' : 'denied',
          ad_user_data: preferences.marketing ? 'granted' : 'denied',
          ad_personalization: preferences.marketing ? 'granted' : 'denied'
        };
      }
    } catch (e) {}
    return denied();
  }

  function sendConsent() {
    if (!parentIsAllowed()) {
      post('consent-state', { consent: denied() });
      return denied();
    }
    post('consent-state', { consent: getConsent() });
    return getConsent();
  }

  function sendLandingUrl(force) {
    var url = parentIsAllowed() || force ? window.location.href : '';
    return post('landing-url', { url: url });
  }

  /**
   * API manuelle pour le CMP ou les tests :
   * window.setAssuranceConsent(true|false|null)
   */
  window.setAssuranceConsent = function (value) {
    manualConsent = value === null ? null : Boolean(value);
    return sendConsent();
  };

  [
    'cookieconsent_accept',
    'cookieconsent_deHarbor',
    'user_cookie_preferences_changed'
  ].forEach(function (eventName) {
    document.addEventListener(eventName, function () {
      sendConsent();
    });
  });

  /* ---------------- Format "reference" + relais SMS ---------------- */

  function postRef(message) {
    var frame = getIframe();
    if (!frame || !frame.contentWindow || !nonce || !parentIsAllowed()) return false;
    var payload = { channel: CHANNEL, nonce: nonce };
    Object.keys(message || {}).forEach(function (key) {
      payload[key] = message[key];
    });
    frame.contentWindow.postMessage(payload, frameOrigin());
    return true;
  }

  function startRefBridge() {
    if (!getIframe()) return;
    if (!nonce) nonce = makeNonce();
    // bridge-init porte le nonce que l'enfant memorisera.
    postRef({ type: 'bridge-init' });
  }

  function isAnalyticsParam(key) {
    var normalized = String(key || '').toLowerCase();
    return /^(utm_|ltm_)/.test(normalized) ||
      ['source', 'categorie', 'category', 'medium', 'campaign', 'content', 'term', 'user', 'campaign_id'].indexOf(normalized) !== -1;
  }

  function campaignUrlForConsent(analytics, marketing) {
    var current = new URL(window.location.href);
    var result = new URL(current.origin + current.pathname);
    current.searchParams.forEach(function (value, key) {
      var normalized = key.toLowerCase();
      var clickId = ['gclid', 'msclkid', 'fbclid'].indexOf(normalized) !== -1;
      if ((analytics && isAnalyticsParam(normalized)) || (marketing && clickId)) {
        result.searchParams.append(key, value);
      }
    });
    return result.href;
  }

  function sendSmsResponse(requestId, status, ok, data) {
    postRef({
      type: 'sms-response',
      requestId: requestId,
      status: Number(status) || 0,
      ok: ok === true,
      data: data && typeof data === 'object' ? data : {}
    });
  }

  function handleSmsRequest(message) {
    var requestId = String(message.requestId || '');
    var params = message.params || {};
    var action = String(params.action || '');
    var telephone = String(params.telephone || '').replace(/\D/g, '');
    var code = String(params.code || '').replace(/\D/g, '');

    if (!requestId || requestId.length > 100 || !/^0[67]\d{8}$/.test(telephone) ||
        (action !== 'envoyer_code' && action !== 'verifier_code') ||
        (action === 'verifier_code' && !/^\d{6}$/.test(code))) {
      sendSmsResponse(requestId, 422, false, { message: 'Numéro, action ou code invalide.' });
      return;
    }

    var body = new URLSearchParams();
    body.set('action', action);
    body.set('telephone', telephone);
    if (action === 'verifier_code') body.set('code', code);

    fetch(SMS_ENDPOINT, {
      method: 'POST',
      mode: 'cors',
      credentials: 'omit',
      body: body
    }).then(function (response) {
      // Lire le corps (JSON si possible) meme en erreur HTTP : l'enfant
      // affiche le message et le delai restant (429) qu'il contient.
      return response.text().then(function (text) {
        var data = {};
        try { data = text ? JSON.parse(text) : {}; }
        catch (error) { data = text ? { message: text.slice(0, 500) } : {}; }
        sendSmsResponse(requestId, response.status, response.ok, data);
      });
    }).catch(function () {
      sendSmsResponse(requestId, 0, false, { message: 'Connexion impossible au service SMS.' });
    });
  }

  /* ---------------- Ecoute des messages de l'iframe ---------------- */

  window.addEventListener('message', function (event) {
    var frame = getIframe();
    if (!frame || event.source !== frame.contentWindow || event.origin !== frameOrigin()) return;
    var message = event.data;
    if (!message || typeof message !== 'object') return;

    // Format de reference (channel + nonce)
    if (message.channel === CHANNEL) {
      if (message.type === 'bridge-ready') {
        startRefBridge();
        return;
      }
      if (!nonce || message.nonce !== nonce) return;
      if (message.type === 'consent-state') {
        var analytics = message.choiceMade === true && message.analytics === true;
        var marketing = message.choiceMade === true && message.marketing === true;
        if (!analytics && !marketing) return;
        postRef({ type: 'landing-url', url: campaignUrlForConsent(analytics, marketing) });
      } else if (message.type === 'sms-request') {
        if (parentIsAllowed()) {
          handleSmsRequest(message);
        } else {
          sendSmsResponse(String(message.requestId || ''), 0, false,
            { message: 'Origine parente non autorisée pour le relais SMS.' });
        }
      }
      return;
    }

    // Format des LP du depot (bridge + requetes)
    if (message.bridge === CHANNEL) {
      if (message.type === 'consent-state-request') {
        sendConsent();
      } else if (message.type === 'landing-url-request') {
        sendLandingUrl(false);
      }
    }
  });

  function initialize() {
    var frame = getIframe();
    if (!frame) return;
    if (frame.addEventListener) frame.addEventListener('load', startRefBridge);
    startRefBridge();
    sendConsent();
    sendLandingUrl(false);
    [300, 1000, 3000].forEach(function (delay) {
      window.setTimeout(function () {
        startRefBridge();
        sendConsent();
        sendLandingUrl(false);
      }, delay);
    });
  }

  /* API QA */
  window.lpBridge = Object.freeze({
    version: '2026-10-26-bridge2-sms1',
    smsEndpoint: SMS_ENDPOINT,
    protocole: CHANNEL
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
