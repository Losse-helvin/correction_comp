# Rapport de modifications — `assurance-tns` (version FONCTIONNELLE)
_Application du traitement complet de la LP Assurance TNS Pro (elle-même alignée sur la référence `assurance-consultant-conseil-v2`), **sans écraser l'identité de cette LP** : design éditorial bleu nuit, contenus et questions d'origine conservés. 2026-10-26. Domaine cible : https://assurance-tns.lp.comparateurpro.fr_

## État d'origine constaté
Export Webflow converti (lp2site) : formulaire multistep 10 étapes (mêmes questions que la TNS Pro), GTM-53SH7D7F. Défauts : envoi du formulaire vers `webflow.com` (échec « Oops! » hors Webflow), code SMS Axialys mort mais présent (+ blocage associé), tracking limité et bugué (`get_params()` plantait sur les champs absents `user`/`msclkid`, pont `postMessage` par `id` inopérant), `lang="en"`, **9 balises H1**, image `hero-background.jpg` (salon de beauté) **orpheline** — le hero de cette LP est un aplat bleu nuit (`.header-tns`), l'image n'était affichée nulle part.

## Modifications appliquées
1. **Image / hero** : le design bleu nuit est conservé tel quel (aucune photo forcée, contrairement à la TNS Pro dont le fond photo était hors sujet). Fichier orphelin `img/hero-background.jpg` supprimé (−143 Ko, récupérable via Git) et ligne `background-image` de la règle CSS morte retirée (zéro impact visuel).
2. **SMS supprimé** : retrait du système Axialys mort de `script.js` (handlers, champs code, masque, blocage `verification_champ`). Aucun endpoint SMS, récupération du contact simple. (Cette LP n'avait pas le système smspartner actif.)
3. **Soumission autonome** : wrapper `w-form` → `form-autonome` (marge compensée, design inchangé) + nouveau **`lead-handler.js`** séparé qui intercepte l'envoi simulé jQuery de Formly **et** les envois natifs — fini le « Oops! », le parcours aboutit au « Merci ! » d'origine.
4. **Production leads (parité référence)** : CRM prod HelloLead (enveloppe `{payload:{formId,id,data}}`, transport `nocors`), Google Sheets AGV/AMR (champs plats, `status:"ok"` vérifié, `solution`/`enjeu`), honeypot anti-spam, livraisons parallèles avec états réels (pas de faux « Merci ! »), APIs QA `tnsLead.preview()` / `tnsTracking.inspect()`.
   - **Identité propre** : `formId = ADW_LP_ASSURANCE_TNS` (à enregistrer côté CRM), source de secours `LP TNS`, `form_name = Assurance-TNS-Form`.
5. **Tracking URL + consentement** : capture complète (utm_*, ltm_*, gclid/gbraid/wbraid, fbclid, msclkid, ttclid, alias partenaire, hash), persistance session, **filtrage par le consentement** de la bannière existante (analytics ⇒ UTM/page, marketing ⇒ click IDs + `user_data`), champs cachés complétés avec `id` (répare `get_params()` et le pont Hellodevis).
6. **GTM** : événement `formulaire_lead` / `formulaire_micro_entrepreneur` enrichi (schéma référence : `form_id`, `lead_type`, tracking consenti). Pont iframe `landing-url` prêt (voir `docs/WEBFLOW_EMBED-TNS.md`), sans proxy SMS.
7. **SEO léger (design inchangé)** : `lang="fr"` ; un seul H1 (titre hero) — les 8 autres titres passent en `h2` **à classes identiques** (`.h1-iard-v2` porte déjà taille/marges : rendu inchangé). Titre et meta description d'origine conservés (déjà corrects).

## Documentation (dossier `docs/`)
- `ANALYSE-FONCTIONNELLE-REFERENCE.md` — inventaire de la LP de référence + correspondance d'application.
- `CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md` — guide de lancement (formId CRM, tests, GTM).
- `WEBFLOW_EMBED-TNS.md` — snippet parent si la LP est iframée. `Code.gs` — feuille Sheets dédiée (option).

## Tests effectués (jsdom + vrai jQuery, parcours Formly simulé)
Consentement total + URL trackée → CRM/Sheets/GTM complets (`ADW_LP_ASSURANCE_TNS`, source `ADW_tns`) · sans consentement → données filtrées, source `LP TNS` · honeypot → zéro envoi · micro-entrepreneur → bon événement · livraisons KO → erreur claire, pas de faux « Merci ! ». Syntaxes JS validées, serveur local HTTP 200.

## Checklist de lancement
- [ ] Enregistrer `ADW_LP_ASSURANCE_TNS` côté CRM + lead réel visible (CRM + feuille)
- [ ] Aperçu GTM (événements + variables, consentement accepté)
- [ ] Parcours complet en local dans un **nouveau dossier** (cache navigateur)
- [ ] Si iframe : embed + `publicLandingPath` dans `lead-handler.js`

## Ajout — Verification du numero par SMS (2026-10-26)
A la demande metier, la verification par code SMS (API SMS Partner HelloLead, meme contrat que la LP de reference) est **reintroduite** :
- nouveau module `verification-sms.js` : mobile 06/07, envoi `envoyer_code`, verification `verifier_code` (code 6 chiffres, 10 min, usage unique), compte a rebours de renvoi 120 s, erreurs 422/404/409/410/429/502 affichees depuis le JSON ;
- l'envoi du lead est desormais **bloque** tant que le numero n'est pas verifie ; le drapeau `telephone_verifie` est transmis au CRM, a Google Sheets et a l'evenement GTM ;
- interface injectee sous le champ telephone, sans modification de `style.css` ni du design.
Details : `docs/VERIFICATION-SMS.md`. Prerequis : l'API doit autoriser l'origine publique de la LP en CORS.
