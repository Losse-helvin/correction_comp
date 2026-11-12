# Relais SMS du wrapper — `assurance-consultant-societe-conseil-v2`

_Ajouté le 2026-10-26. Cette page n'a pas de formulaire : c'est la LP chargée dans l'iframe qui affiche la vérification SMS. Le rôle du wrapper est d'exécuter les appels SMS pour son compte (relais parent), exactement comme le snippet `WEBFLOW_EMBED.md` de la LP de référence._

## Protocole (format « référence », canal `ubepro-assurance-v1`)
1. L'enfant envoie `bridge-ready` → le wrapper génère un **nonce** et répond `bridge-init` (le nonce protège tous les échanges suivants).
2. L'enfant envoie `consent-state` (ses choix analytics/marketing) → le wrapper répond `landing-url` avec l'URL publique **filtrée selon le consentement** (utm/ltm ⇒ analytics ; gclid/msclkid/fbclid ⇒ marketing).
3. **SMS** : l'enfant envoie `sms-request` `{requestId, params:{action: envoyer_code|verifier_code, telephone, code?}}` (avec nonce) → le wrapper valide (mobile 06/07, code 6 chiffres — 422 local sinon), fait le `POST` vers `https://mc.hellolead.pro/mon_compte/api/smspartner/envoi_code_verification.php` en `URLSearchParams`, lit le corps JSON **même en erreur HTTP**, puis répond `sms-response` `{requestId, status, ok, data}`. L'affichage des erreurs (422/404/409/410/429 + délai restant/502) est fait par l'enfant.
4. Le format « LP du dépôt » (`bridge` + `consent-state-request`/`landing-url-request`) reste géré en parallèle si l'iframe pointe un jour vers une LP traitée du dépôt.

## Conditions d'efficacité (vérifier avant prod)
- **Origine parent acceptée par l'enfant** : la LP de référence n'accepte les messages parent que depuis ses origines autorisées (historiquement `https://www.comparateurpro.fr`). Servir ce wrapper depuis une origine autorisée, ou ajouter le domaine du wrapper aux origines parentes de la LP hébergée.
- **CORS API SMS** : les POST SMS partent du navigateur **depuis l'origine du wrapper** — l'API doit l'autoriser.
- **Origines parentes du relais** : la liste `allowedParents` de `bridge.js` doit contenir l'origine de déploiement du wrapper.
- Servir en **HTTPS** (postMessage cible toujours `frameOrigin`, jamais `*`).

## QA (console de la page wrapper)
`lpBridge` → `{version, smsEndpoint, protocole}`. Dans la console de l'iframe, suivre le parcours SMS complet (envoi → code → badge « ✓ Numéro vérifié »).
