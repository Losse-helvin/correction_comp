# Analyse fonctionnelle de référence — `assurance-consultant-conseil-v2`
_Inventaire mémorisé le 2026-10-26 (lecture de `README.md`, `WEBFLOW_EMBED.md`, `index.html`, `js/main.js`) + correspondance d'application sur la LP Assurance TNS. La confirmation du numéro par code SMS est **exclue** de l'application (demandé)._

## A. Inventaire fonctionnel de la référence

### Architecture
- LP statique autonome (`index.html` + `js/main.js` + `css/style.css`), servie sur l'hébergement iframe (`ubepro.helloleadpreprod.fr`) et **embed dans le Webflow public `www.comparateurpro.fr`**.
- Configuration : défauts dans `main.js` (`DEFAULT_CONFIG`), surchargeables par `window.UBEPRO_CONFIG` puis par **attributs `data-*` du `<form>`** (`data-api-endpoint`, `data-api-mode`, `data-form-id`, `data-google-script-url`, `data-source`…).

### Formulaire (7 étapes)
- Navigation par étapes avec barre de progression/compteur, validation par étape avec messages d'erreur FR (`data-err`), **groupes conditionnels** activés/désactivés (+ `required` restauré/retiré, valeurs effacées si masqué), Entrée = Suivant (hors zones exclues), anti double-envoi (`sending`), `submissionId` UUID unique par chargement.
- Validations finales : e-mail `/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/`, code postal `/^\d{5}$/`, mobile FR normalisé (`+33`/`0033` → `0…`, formatage par paires à la saisie), consentement « J'accepte » obligatoire.
- Récapitulatif `autre_info_fj` (multi-lignes) construit depuis les **libellés** des réponses + paires `question_i`/`reponse_i`.

### Anti-spam
- **Honeypot** invisible `website` (créé en JS si absent) : s'il est rempli → écran de succès affiché, **aucun envoi**. Côté Apps Script, le champ `website` est aussi vérifié avant écriture.

### CRM (production HelloLead)
- Endpoint : `https://mc.hellolead.pro/mon_compte/api/webflow/get_information.php`
- Enveloppe JSON : `{ payload: { formId, id, data } }` — `formId: ADW_LP_ASSURANCE_CONSULTANT` (à enregistrer côté CRM), `id` = UUID de soumission.
- `data` : identité/contact nettoyés (`mail` en minuscules, téléphone normalisé, CP sans espaces), `source` (voir tracking), `categorie`, `consentement`, `question_i`/`reponse_i`, `autre_info_fj`, extras tracking seulement si consentis.
- Transport `data-api-mode="nocors"` : **`sendBeacon`** (Blob `text/plain`) puis repli `fetch no-cors` (timeout 6 s) — état `unverified` (l'insertion n'est pas confirmable côté navigateur : le CRM ne renvoie pas d'en-tête CORS). Mode `cors` disponible : POST JSON + exigence `{"status":"ok"}`.

### Google Sheets (Apps Script partagé AGV/AMR)
- URL Web App confirmée par l'utilisateur (`script.google.com/macros/s/AKfycbwr…/exec`).
- POST **champs plats** `application/x-www-form-urlencoded` (`URLSearchParams`), mode CORS, timeout 15 s, **JSON validé** (`status: "ok"` exigé, même sur HTTP 200).
- Mapping schéma AGV/AMR : `form_id`, `id_lead`, identité, `solution` ← `reponse_1` (500 car. max), `enjeu` ← `autre_info_fj` (500 max), `question_1..3`/`reponse_1..3` uniquement, `source`, `categorie`, `website: ''`, `civilite`/`ville`/`site` vides, extras tracking (`user`, `utm_*`, `ltm_*`, click IDs, `page_url`, `page_referrer`, `user_agent`, `langue`) seulement si présents dans `data`.

### Consentement (RGPD + Consent Mode)
- Préférences `{necessary, analytics, marketing, choiceMade}` stockées `localStorage['ubeproCookiePreferencesV1']` (+ legacy `cookiesChoice` accept/refuse).
- Dans le `<head>` **avant GTM** : Consent Mode **default = tout denied** (`wait_for_update: 500`), puis `update` immédiat si un choix est déjà enregistré. La bannière (#cookies : accept/refuse/préférences + cases analytics/marketing) met à jour le Consent Mode à chaque choix.
- **Filtrage des données par consentement** : analytics ⇒ `utm_*`/`ltm_*`/`source`/`page_url`/`page_referrer`/`user_agent`/`langue` ; marketing ⇒ `gclid`/`msclkid`/`fbclid`. Sans consentement : purge du tracking stocké (`sessionStorage`), événement GTM minimal.

### Tracking URL
- `TRACKING_DEFS` avec **alias** : `source ← ltm_source>utm_source>source`, `categorie`, `user`, `utm_source/medium/campaign/content/term/id/category/user`, `ltm_source/category/typ/user`, `gclid/msclkid/fbclid`. Lecture query **et** hash (`#…?…`). Valeurs nettoyées (espaces, `<>`, 500 car.).
- Persistance `sessionStorage` (clés `ubepro_tracking_v1`, `ubepro_tracking_page_url_v1`, `ubepro_public_landing_url_v1`) — uniquement pour les clés consenties.
- `source` CRM/Sheets : `ltm_source` d'abord, sinon `data-source="LP CONSULTANTS"` (secours). `ltm_source` transmis uniquement avec consentement analytics.
- `page_url` = URL publique filtrée par consentement (`filterUrlByConsent`) ; `page_referrer` réduit à origine+chemin.

### Pont iframe Webflow (postMessage sécurisé)
- Canal `ubepro-assurance-v1`, origine parente autorisée unique `https://www.comparateurpro.fr`, **nonce** ≥ 16 émis par le parent (`bridge-init`), l'iframe signale `bridge-ready`, renvoie `consent-state`, reçoit `landing-url` (URL de campagne publique **filtrée par le parent selon les consentements**, chemin public vérifié) → alimente tracking + `page_url`.
- ~~Proxy SMS par le parent (`sms-request`/`sms-response`)~~ → **exclu chez TNS**.

### GTM
- Conteneur **GTM-53SH7D7F** (script head + noscript body), chargé sans condition.
- Événement `formulaire_lead` poussé **à la soumission valide** (avant le résultat des livraisons) : `{form_id, lead_type}` + `page_url`/`categorie`/UTM/LTM si analytics + click IDs si marketing. **Aucune donnée personnelle** dans l'événement de la référence.

### UX de fin de parcours
- Livraisons CRM + Sheets en **parallèle** (`Promise.all`) avec états : succès si **au moins une** livraison aboutit ; sinon message d'erreur FR + réactivation du bouton (nouvel essai possible). Messages « Merci… » différenciés selon confirmation Sheets/CRM.
- Outils QA exposés : `window.ubeproLead.preview()`, `.googleSheetPreview()`, `window.ubeproTracking.inspect()`, logs via `CONFIG.debug`.

### Confirmation téléphone par code SMS — ⛔ NON PORTÉE
Endpoint smspartner, UI code à 6 chiffres, cooldown 120 s, `telephone_verifie`, blocage du bouton : **entièrement exclus** sur la LP TNS (demande explicite ; déjà retirés en PR #1).

---

## B. Correspondance d'application → LP Assurance TNS (ce dossier)
_Tout est porté dans `lead-handler.js` ; **aucune modification de `style.css` ni du design, et même aucune du HTML** (honeypot et champ récap créés en JS, invisibles)._

| Fonctionnalité référence | Application TNS |
|---|---|
| CRM prod + enveloppe `{payload:{formId,id,data}}`, transport nocors (beacon→fetch), mode cors dispo | ✅ Identique. `formId = ADW_LP_ASSURANCE_TNS` (**à enregistrer côté CRM**) |
| Sheets AGV/AMR (même URL `/exec`), champs plats, `status:"ok"` vérifié, mapping q1–q3/`solution`/`enjeu`≤500 | ✅ Identique ; `solution` ← types de contrat TNS, `enjeu` ← récap TNS (régime, auto-entrepreneur, salariés, assurances pro, véhicules, assureur, état société) |
| Honeypot `website` | ✅ Créé en JS (styles inline, aucun CSS touché) : rempli ⇒ « Merci ! » sans aucun envoi |
| Consentement filtrant (analytics/marketing) | ✅ Lu depuis le cookie de la bannière TNS existante `user_cookie_preferences` (JSON) + replis référence ; relu à chaque envoi et après clic bannière |
| Tracking alias + session + purge + hash + `page_url` filtrée | ✅ Porté (clés `tns_tracking_v1`…), étendu `gbraid/wbraid/ttclid` ; champs cachés TNS remplis avec les valeurs consenties uniquement |
| `source` : `ltm_source` prioritaire, secours étiqueté LP | ✅ Secours `LP TNS` (`TNS_CONFIG.source`) |
| Pont iframe (nonce, origine unique, `landing-url`, `consent-state`) | ✅ Porté sans la partie SMS ; chemin public via `TNS_CONFIG.publicLandingPath` (à renseigner si embed : voir `docs/WEBFLOW_EMBED-TNS.md`) |
| GTM `formulaire_lead` consenti-gated | ✅ Schéma référence + **noms d'événements historiques TNS conservés** (`formulaire_micro_entrepreneur` si auto-entrepreneur = Oui, avec `lead_type`) ; `user_data` (conversions améliorées) **uniquement si marketing** |
| Livraisons parallèles + états + erreur si tout échoue | ✅ Identique (CRM `unverified` compte comme transmis ; sinon message FR + bouton réactivé) |
| Validations e-mail / CP / téléphone normalisé | ✅ Portées ; **fixe + mobile acceptés** chez TNS (choix assumé : pas de SMS ⇒ ne pas perdre les leads fixe ; la référence exige 06/07 pour son SMS) |
| QA `ubeproLead.preview()` / `ubeproTracking.inspect()` | ✅ `window.tnsLead.preview()`, `.googleSheetPreview()`, `window.tnsTracking.inspect()` |
| Spécifique TNS conservé (absent de la référence) | Sauvegarde `localStorage` + **redirection `ltm_typ`** page de remerciement, interception Formly jQuery + native, texte « Merci ! » d'origine |
| SMS (code, API smspartner, `telephone_verifie`) | ⛔ **Non porté** — le champ n'est même pas émis |
