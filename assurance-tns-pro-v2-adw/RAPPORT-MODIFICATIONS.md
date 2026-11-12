# Rapport de modifications — `assurance-tns-pro-v2-adw`
_Intervention « solution rapide & efficace » — 2026-10-26_

## 1. Analyse rapide (avant intervention)
- Landing page Webflow convertie (lp2site) pour **ComparateurPro / HelloLead** : assurance protection sociale TNS (mutuelle santé, prévoyance, épargne-retraite Madelin).
- Formulaire **multistep 10 étapes** : type de contrat → régime → statut → nb salariés → assurances pro → assureur actuel → e-mail → société/CP → société existante → nom/prénom → téléphone + consentement.
- Tracking : **GTM-53SH7D7F**, Consent Mode V2, bandeau cookies, événement `dataLayer` = `formulaire_lead` (ou `formulaire_micro_entrepreneur`), sauvegarde `localStorage` + redirection `ltm_typ`.
- ⚠️ Constat n°1 : l'image de fond du haut de page (`img/hero-background.jpg`) montrait un **salon de beauté / spa** — hors sujet total pour une assurance TNS.
- ⚠️ Constat n°2 : **deux** systèmes de vérification par code SMS dans `script.js`.

## 2. Nouvelle image de fond (haut de page)
- ✅ Nouvelle image générée : **`img/hero-tns-pro.jpg`** (1376×768, 120 Ko) — 3 dirigeants/indépendants français en bureau lumineux, sujets à gauche, zone claire à droite derrière le formulaire.
- ✅ `style.css` : règle `.background-assurance-professionel.right-form-assurance.form-2-assurance` → nouvelle image + `background-position: left center`.
- ✅ Ancienne image `img/hero-background.jpg` supprimée (récupérable via Git).
- ✅ `<link rel="preload" as="image">` ajouté (LCP).

## 3. Suppression de la confirmation par code SMS → contact simple
Retiré de `script.js` (≈ 12 400 caractères) :
- ❌ Système **actif** « smspartner » : API `mc.hellolead.pro/mon_compte/api/smspartner/envoi_code_verification.php`, boutons injectés « Recevoir le code / Vérifier », compte à rebours 120 s, champ masqué `telephone_verifie`, **blocage du bouton Valider** tant que le numéro n'était pas vérifié.
- ❌ Ancien système **Axialys** (code mort, aucun élément HTML) : `…/api/axialys/envoi_code_verification.php`, handlers `.btn-verification`, `.champ-telephone-verification`, etc.
- ❌ Blocage résiduel dans `verification_champ()` + masque de saisie de l'ancien champ code.

Remplacé par une **validation contact simple** (~1 Ko) :
- Le bouton **Valider** redevient piloté par la logique d'origine : champs requis + « J'accepte » coché.
- Au submit : simple contrôle du **format téléphone FR (10 chiffres, fixe ou mobile)** avec message d'erreur inline — **aucun envoi de SMS, aucun code, aucun appel API externe**.
- Le reste du parcours est inchangé : envoi du lead, `dataLayer`, `localStorage`, redirection TYP.

> ⚠️ **Côté CRM** : si un filtre rejetait les leads sans `telephone_verifie=oui`, le désactiver — ce champ n'est plus émis (comportement voulu : on récupère le contact, point).

## 4. Correctifs SEO rapides (bonus, signalés dans l'ancien rapport)
- `lang="en"` → **`lang="fr"`**
- **H1** ajouté (le titre principal était un `<div>`, 0 H1 avant)
- Meta description complétée (était tronquée : « …vous avez l'assuran »)

## 5. Vérifications effectuées
- `node --check script.js` ✅ syntaxe valide
- Recherche exhaustive des endpoints/classes SMS dans `script.js` + `index.html` → **0 occurrence** ✅
- Test serveur local : page + `style.css` + `script.js` + nouvelle image → HTTP 200 ✅
- Restent dans `style.css` quelques classes CSS orphelines de l'ancien OTP (`.champ-telephone-verification`, etc.) : inertes, sans effet.

## 6. Correctif soumission formulaire — fini le « Oops! Something went wrong » (2026-10-26)
- **Cause** : le cœur Webflow du bundle envoie le formulaire vers `https://webflow.com/api/v1/form/<site-id>` → échec systématique hors hébergement Webflow (test local, hébergement statique…) → affichage de `.w-form-fail` (« Oops! … »).
- **Correctif (le plus simple/efficace)** : un bloc « SOUMISSION AUTONOME DU LEAD » dans `script.js` intercepte l'envoi **avant** Webflow (écouteur `submit` en phase de capture sur `document`), uniquement à la dernière étape (bouton Valider visible). Il reproduit le comportement d'origine : validation téléphone FR + consentement → `dataLayer` (`formulaire_lead` / `formulaire_micro_entrepreneur`) → `localStorage` → message **« Merci ! »** (`.w-form-done`) → redirection `?ltm_typ=` après 3 s. Anti double-envoi inclus.
- **Envoi CRM optionnel en 1 ligne** : variable `LEAD_ENDPOINT` en tête du bloc (rechercher « LEAD_ENDPOINT » dans `script.js`). Vide par défaut = tracking GTM seul. Collez-y l'URL d'un webhook (Make, Zapier, Google Apps Script vers Sheets, endpoint HelloLead…) pour recevoir chaque lead en POST JSON.
- **Tests fonctionnels (jsdom, DOM réel de la page)** : 4/4 ✅ — cas réel (téléphone valide + « J'accepte ») → succès affiché, Webflow jamais appelé, `formulaire_lead` poussé, contact sauvegardé · téléphone invalide → message d'erreur clair, aucun envoi · soumission en cours de parcours → non interceptée (le multistep garde la main) · consentement absent → bloqué avec message clair.

## 7. Correctif définitif soumission — vraie source identifiée (2026-10-26)
Le §6 ne suffisait pas en navigateur réel (retesté par l'utilisateur : « Oops! » persistant). Décodage de la librairie multistep obfusquée (**Formly**) effectué :
- Au clic sur « Valider », Formly fait `e.preventDefault()` puis `$('[data-form="multistep"]').submit()` : envoi **simulé par jQuery**, qui n'appelle que les handlers jQuery — les `addEventListener` natifs (correctif §6) sont **contournés**.
- Le handler Webflow (délégué jQuery sur `.w-form form`) partait donc en AJAX vers `webflow.com/api/v1/form/...` → échec hors Webflow → « Oops! ».

**Correctif en 3 couches :**
1. **Racine HTML** : le wrapper du formulaire n'a plus la classe `w-form` (→ `form-autonome`, marge compensée en CSS). Le sélecteur délégué de Webflow `.w-form form` ne correspond plus **jamais**.
2. **Couche jQuery** (le vrai chemin Formly) : nouveau fichier **`lead-handler.js`** (chargé après `script.js`, isolé du bundle) : à DOM ready, `$('.form-ass').off('submit')` puis handler propre avec `preventDefault` + `stopPropagation` → Webflow ne peut plus être appelé, même via `.submit()`.
3. **Couche native** : capture `submit` sur `document` (touche Entrée, etc.), aucune navigation native possible.

Le traitement du lead (validation FR + consentement, `dataLayer`, `localStorage`, redirection TYP, « Merci ! », webhook `LEAD_ENDPOINT` optionnel) est inchangé — la constante est désormais en tête de **`lead-handler.js`**. L'ancien bloc du §6 a été retiré de `script.js`.

**Tests (jsdom + vrai jQuery 3.7, écosystème réel simulé : clic Formly `.submit()`, handler délégué Webflow espion, anciens handlers)** : 4/4 ✅ — vrai parcours → « Merci ! », Webflow appelé 0 fois (avec et sans la classe `w-form`) · événement natif → 1 seul envoi · téléphone invalide → message clair, aucun envoi.

> ⚠️ **Test local** : extraire le ZIP dans un **nouveau dossier** (ou Ctrl+F5) pour éviter le cache navigateur sur `index.html`/`script.js` (mêmes noms de fichiers).

## 8. Fonctionnalités production : CRM + Google Sheets + GTM + Tracking URL (2026-10-26)
Configuration centralisée dans `LEAD_CONFIG` en tête de **`lead-handler.js`** (2 URL à coller). Guide complet : **`docs/CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md`**.
- **CRM** : POST JSON (ou `form`) vers `crm.url` — payload = champs bruts (compatibles Webflow) + champs normalisés (`email`, `telephone_e164` +33…, besoins en libellés lisibles, tracking). Envoyé en `keepalive`, repli `no-cors`, jamais bloquant.
- **Google Sheets** : POST `no-cors` vers `googleSheet.url` (Web App Apps Script). Script prêt à déployer fourni : **`docs/Code.gs`** (onglet « Leads », 34 colonnes, anti-injection formules, verrou anti-concurrence, notification e-mail optionnelle).
- **GTM** (GTM-53SH7D7F, déjà présent) : événement `formulaire_lead` / `formulaire_micro_entrepreneur` **enrichi** — `form_name`, `lead_source/categorie`, `utm_*`, click IDs et `user_data` (e-mail, téléphone E.164, nom, CP, FR) pour les **conversions améliorées** Google Ads (hachage côté Google). Consent Mode V2 inchangé.
- **Tracking URL** : capture + persistance (`localStorage`) de `utm_source/medium/campaign/term/content`, `gclid/gbraid/wbraid`, `fbclid`, `msclkid`, `ttclid` + mapping partenaire d'origine (`source ← ltm_source > utm_source`, `categorie ← ltm_category`, `user ← ltm_user`) + `page_url`, `referrer`. **Bugs d'origine corrigés** : champs cachés `user`/`msclkid`/UTM ajoutés au HTML (`get_params()` plantait si le paramètre était présent) et `id` ajoutés (`source/categorie/user`…) → le pont `postMessage` Hellodevis redevient fonctionnel.
- **Inchangés** : envoi autonome anti-« Oops! », validation FR + consentement, sauvegarde page de remerciement + redirection `ltm_typ`, **aucun code SMS**.
- **Tests** (jsdom + vrai jQuery, parcours Formly, `fetch` espion, endpoints de test injectés) : ✅ champs cachés remplis depuis l'URL (source `ADW_tns`, gclid, UTM, user…), 2 livraisons correctement formatées, payload normalisé vérifié (libellés, +33…), dataLayer enrichi ; sans configuration → 0 envoi, « Merci ! » OK (GTM seul).

## 9. Alignement production sur la LP de référence `assurance-consultant-conseil-v2` (2026-10-26)
Inventaire mémorisé + correspondance complète : **`docs/ANALYSE-FONCTIONNELLE-REFERENCE.md`**. Application **sans aucune modification du design, du CSS — ni même du HTML** (tout est dans `lead-handler.js` ; honeypot et champ récap créés en JS, invisibles) :
- **CRM production HelloLead** : POST enveloppe `{payload:{formId,id,data}}` vers `…/api/webflow/get_information.php`, transport `nocors` (sendBeacon → fetch `text/plain`) comme la référence, `formId = ADW_LP_ASSURANCE_TNS_PRO` (à enregistrer côté CRM).
- **Google Sheets AGV/AMR** : même Apps Script confirmé que la référence, champs plats form-urlencoded, JSON `status:"ok"` vérifié, mapping `solution`/`enjeu` (récap `autre_info_fj` ≤ 500 car.) + q1–q3.
- **Honeypot** `website` : rempli ⇒ « Merci ! » sans aucun envoi ni événement.
- **Consentement filtrant** (modèle référence) lu dans le cookie de la bannière existante `user_cookie_preferences` : analytics ⇒ UTM/LTM/`page_url`, marketing ⇒ click IDs + `user_data` ; sans consentement, `source = LP TNS PRO` et événement GTM minimal. Tracking alias complet + persistance session + purge.
- **Pont iframe Webflow** (canal `ubepro-assurance-v1`, nonce, origine `www.comparateurpro.fr`) : réception `landing-url` après consentement — **sans le proxy SMS**. Snippet parent adapté : `docs/WEBFLOW_EMBED-TNS.md`.
- **GTM** : schéma référence (`form_id`, `lead_type`, tracking consenti) en conservant les noms d'événements historiques TNS. Livraisons parallèles avec états : « Merci ! » seulement si CRM ou Sheets aboutit, sinon message d'erreur + réessai. APIs QA `window.tnsLead.preview()` / `tnsTracking.inspect()`.
- ⛔ **Confirmation téléphone par code SMS : non portée** (aucun endpoint, aucun champ `telephone_verifie` émis).
- **Tests** (jsdom + vrai jQuery, parcours Formly, beacon/fetch espions, cookie consentement réel) : 5/5 ✅ — parité complète consentie, filtrage sans consentement, honeypot, événement micro-entrepreneur, échec livraisons sans faux « Merci ! ».
- Guide de lancement mis à jour : `docs/CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md`. Livrable : `assurance-tns-pro-v2-adw-FONCTIONNEL.zip`.

## Checklist avant mise en ligne
1. Parcours complet du formulaire jusqu'à « Merci ! » (sans étape SMS, sans envoi Webflow).
2. Renseigner `crm.url` et `googleSheet.url` dans `lead-handler.js` (voir `docs/CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md`), puis tester un lead complet avec l'URL de test fournie.
3. Tag Assistant : vérification de l'événement `formulaire_lead`.
4. ~~Test OTP SMS~~ → remplacé par : tester un numéro invalide (message d'erreur) puis un numéro valide (succès direct « Merci ! »).

## Ajout — Verification du numero par SMS (2026-10-26)
A la demande metier, la verification par code SMS (API SMS Partner HelloLead, meme contrat que la LP de reference) est **reintroduite** :
- nouveau module `verification-sms.js` : mobile 06/07, envoi `envoyer_code`, verification `verifier_code` (code 6 chiffres, 10 min, usage unique), compte a rebours de renvoi 120 s, erreurs 422/404/409/410/429/502 affichees depuis le JSON ;
- l'envoi du lead est desormais **bloque** tant que le numero n'est pas verifie ; le drapeau `telephone_verifie` est transmis au CRM, a Google Sheets et a l'evenement GTM ;
- interface injectee sous le champ telephone, sans modification de `style.css` ni du design.
Details : `docs/VERIFICATION-SMS.md`. Prerequis : l'API doit autoriser l'origine publique de la LP en CORS.
