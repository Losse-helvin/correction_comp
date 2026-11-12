# Embed Webflow — LP Assurance Consultants & Societe de Conseil (optionnel, si la LP est iframée)

À n'utiliser **que** si la LP CONSULTANTS SOCIETE CONSEIL est intégrée en iframe dans une page `www.comparateurpro.fr` (même modèle que la LP Consultants). Ce snippet transmet à l'iframe l'URL de campagne publique **après consentement**, paramètres filtrés selon les choix analytics/marketing. Contrairement à la LP Consultants, **aucune requête SMS ne transite** (pas de confirmation par code sur la TNS).

⚠️ Avant publication :
1. Remplacez le `src` ci-dessous par l'URL d'hébergement réel de la LP CONSULTANTS SOCIETE CONSEIL (ne jamais mettre l'URL Webflow du wrapper : boucle d'iframes).
2. Dans `lead-handler.js` (côté LP), renseignez `publicLandingPath` avec le chemin public exact (ex. `'/assurance-consultants-societe-conseil-pro'`) pour verrouiller l'URL acceptée.

```html
<style>
  .lp-tns-frame {
    display: block;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    border: 0;
  }
</style>

<iframe
  id="lp-tns-frame"
  class="lp-tns-frame"
  src="https://REMPLACER-PAR-L-HEBERGEMENT-DE-LA-LP-TNS/"
  title="Assurance protection sociale pour dirigeants et indépendants"
  loading="eager"
  referrerpolicy="strict-origin-when-cross-origin">
</iframe>

<script>
(function () {
  'use strict';

  var frame = document.getElementById('lp-tns-frame');
  var parentOrigins = ['https://www.comparateurpro.fr'];
  var channel = 'ubepro-assurance-v1';
  if (!frame || parentOrigins.indexOf(window.location.origin) === -1) return;

  var frameOrigin;
  try {
    frameOrigin = new URL(frame.getAttribute('src'), window.location.href).origin;
  } catch (error) {
    return;
  }

  var nonce = '';

  function makeNonce() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    } catch (error) {}
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (char) {
      var random = Math.random() * 16 | 0;
      var value = char === 'x' ? random : (random & 3 | 8);
      return value.toString(16);
    });
  }

  function postToFrame(message) {
    if (!nonce || !frame.contentWindow) return;
    var payload = Object.assign({ channel: channel, nonce: nonce }, message || {});
    frame.contentWindow.postMessage(payload, frameOrigin);
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
      var clickId = ['gclid', 'gbraid', 'wbraid', 'msclkid', 'fbclid', 'ttclid'].indexOf(normalized) !== -1;
      if ((analytics && isAnalyticsParam(normalized)) || (marketing && clickId)) {
        result.searchParams.append(key, value);
      }
    });
    return result.href;
  }

  function startBridge() {
    if (!nonce) nonce = makeNonce();
    postToFrame({ type: 'bridge-init' });
  }

  window.addEventListener('message', function (event) {
    if (event.source !== frame.contentWindow || event.origin !== frameOrigin) return;
    var message = event.data;
    if (!message || message.channel !== channel) return;

    if (message.type === 'bridge-ready') {
      startBridge();
      return;
    }

    if (!nonce || message.nonce !== nonce) return;

    if (message.type === 'consent-state') {
      var analytics = message.choiceMade === true && message.analytics === true;
      var marketing = message.choiceMade === true && message.marketing === true;
      if (!analytics && !marketing) return;
      postToFrame({ type: 'landing-url', url: campaignUrlForConsent(analytics, marketing) });
    }
  });

  frame.addEventListener('load', startBridge);
  window.setTimeout(startBridge, 0);
})();
</script>
```

## Résultat attendu
- Après consentement analytics, la LP reçoit l'URL de campagne publique (`www.comparateurpro.fr`) et ses `utm_*`/`ltm_*` : ils alimentent `page_url`, les champs de tracking, le CRM/Sheets et l'événement GTM. Le champ `source` prend `ltm_source` en priorité ; `LP CONSULTANTS SOCIETE CONSEIL` sert de secours.
- `gclid`/`gbraid`/`wbraid`/`msclkid`/`fbclid`/`ttclid` ne sont transmis qu'après consentement marketing.
- Aucun appel SMS : la LP CONSULTANTS SOCIETE CONSEIL récupère uniquement le contact.
