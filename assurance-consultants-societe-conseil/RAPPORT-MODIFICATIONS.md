# Rapport de modifications — `assurance-consultants-societe-conseil` (version FONCTIONNELLE)
_Application du traitement complet des LP Assurance TNS Pro / Assurance TNS (alignées sur la référence `assurance-consultant-conseil-v2`), **sans écraser l'identité de cette LP** : design, contenus et questions d'origine conservés. 2026-10-26. Domaine cible : https://assurance-consultants-societe-conseil.lp.comparateurpro.fr_

## État d'origine constaté
Export Webflow converti (lp2site), GTM-53SH7D7F. Clone fonctionnel de la LP TNS Pro (memes questions protection sociale), titre hero sans balise H1, image de fond salon de beaute hors sujet (meme fichier que l'ancien defaut TNS Pro) remplacee par un visuel consultants dedie (img/hero-consultants.jpg). Défauts communs corrigés : envoi du formulaire vers `webflow.com` (échec « Oops! » hors Webflow), systèmes SMS présents dans le bundle, tracking limité et bugué (`get_params()` plantait sur les champs absents, pont `postMessage` par `id` inopérant), `lang="en"`.

## Modifications appliquées
1. **SMS supprimé** : retrait intégral des systèmes de vérification par code de `script.js` (Axialys mort + smspartner actif le cas échéant, masque, blocages). Aucun endpoint SMS, récupération du contact simple.
2. **Soumission autonome** : wrapper `w-form` → `form-autonome` (marge compensée, design inchangé) + nouveau **`lead-handler.js`** (générique : réponses construites par scan des questions du formulaire) qui intercepte l'envoi simulé jQuery de Formly **et** les envois natifs — fini le « Oops! », aboutissement au « Merci ! » d'origine.
3. **Production leads (parité référence)** : CRM prod HelloLead (enveloppe `{payload:{formId,id,data}}`, transport `nocors`), Google Sheets AGV/AMR (champs plats, `status:"ok"` vérifié, `solution`/`enjeu`), honeypot anti-spam, livraisons parallèles avec états réels, APIs QA `lpLead.preview()` / `lpTracking.inspect()`.
   - **Identité propre** : `formId = ADW_LP_ASSURANCE_CONSULTANTS_SOCIETE_CONSEIL` (à enregistrer côté CRM), source de secours `LP CONSULTANTS SOCIETE CONSEIL`, `form_name = Assurance-Consultants-Societe-Conseil-Form`.
4. **Tracking URL + consentement** : capture complète (utm_*, ltm_*, click IDs, alias, hash), persistance session, **filtrage par le consentement** de la bannière existante (analytics ⇒ UTM/page, marketing ⇒ click IDs + `user_data`), champs cachés complétés avec `id`.
5. **GTM** : événement `formulaire_lead` / `formulaire_micro_entrepreneur` enrichi (schéma référence). Pont iframe `landing-url` prêt, sans proxy SMS.
6. **SEO léger (rendu inchangé)** : `lang="fr"`, H1 hero créé sur le titre principal, preload de l'image hero. Titre et meta d'origine conservés.

## Documentation (dossier `docs/`)
`ANALYSE-FONCTIONNELLE-REFERENCE.md` (inventaire référence), `CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md` (lancement), `WEBFLOW_EMBED-TNS.md` (snippet parent si iframe), `Code.gs` (feuille dédiée, option).

## Tests effectués (jsdom + vrai jQuery, parcours Formly simulé)
Consentement total + URL trackée → CRM/Sheets/GTM complets (identité vérifiée) · sans consentement → données filtrées, source de secours · honeypot → zéro envoi · micro-entrepreneur → bon événement · livraisons KO → erreur claire, pas de faux « Merci ! ». Syntaxes JS validées, serveur local HTTP 200.

## Checklist de lancement
- [ ] Enregistrer `ADW_LP_ASSURANCE_CONSULTANTS_SOCIETE_CONSEIL` côté CRM + lead réel visible (CRM + feuille)
- [ ] Aperçu GTM (événements + variables, consentement accepté)
- [ ] Parcours complet en local dans un **nouveau dossier** (cache navigateur)
- [ ] Si iframe : embed + `publicLandingPath` dans `lead-handler.js`

## Ajout — Verification du numero par SMS (2026-10-26)
A la demande metier, la verification par code SMS (API SMS Partner HelloLead, meme contrat que la LP de reference) est **reintroduite** :
- nouveau module `verification-sms.js` : mobile 06/07, envoi `envoyer_code`, verification `verifier_code` (code 6 chiffres, 10 min, usage unique), compte a rebours de renvoi 120 s, erreurs 422/404/409/410/429/502 affichees depuis le JSON ;
- l'envoi du lead est desormais **bloque** tant que le numero n'est pas verifie ; le drapeau `telephone_verifie` est transmis au CRM, a Google Sheets et a l'evenement GTM ;
- interface injectee sous le champ telephone, sans modification de `style.css` ni du design.
Details : `docs/VERIFICATION-SMS.md`. Prerequis : l'API doit autoriser l'origine publique de la LP en CORS.
