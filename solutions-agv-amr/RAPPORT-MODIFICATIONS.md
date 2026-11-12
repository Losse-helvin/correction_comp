# Rapport de modifications — `solutions-agv-amr` (mise au standard FONCTIONNEL)
_Même principe que les LP TNS Pro / TNS / Agriculteur / Consultants, identité préservée. Particularité : cette LP **fonctionnait déjà** (gestionnaire de leads autonome intégré à `script.js`, aucun SMS) — le traitement consiste à la ramener au **même niveau de fiabilité** que les autres, sans changer son identité CRM. 2026-10-26. Domaine : https://solutions-agv-amr.lp.ubepro.fr_

## Audit de l'existant (ce qui marchait déjà)
Export Webflow converti, `lang="fr"`, GTM-53SH7D7F, wrapper `form-autonome` déjà en place. Le bloc « 5. Gestion autonome » en fin de `script.js` envoyait déjà les leads vers le CRM (`formId ADW_LP_SOLUTIONS_AGV_AMR`) et la feuille Google, avec honeypot et capture tracking. Formulaire : 2 listes déroulantes (Fonction, Type de site) + cases à cocher Solutions (AGV/AMR...), coordonnées complètes.

## Écarts corrigés par rapport au standard (référence)
1. **Faux « Merci ! »** : l'ancien code affichait la confirmation **avant** l'envoi (envois en arrière-plan non vérifiés — un CRM en panne perdait les leads en silence). Désormais : succès affiché **uniquement si CRM ou Google Sheets confirme**, sinon erreur claire et bouton réactivé.
2. **Aucune validation** avant : ajout des contrôles standard (e-mail, code postal 5 chiffres, téléphone FR 10 chiffres) avec message d'erreur en ligne.
3. **Consentement incomplet** : les UTM/click IDs partaient dans le payload **sans** le consentement correspondant. Désormais filtrés comme sur les autres LP (UTM/page ⇒ analytics ; click IDs + `user_data` ⇒ marketing), source de secours `ADW` sinon.
4. **Google Sheets non vérifiée** (mode opaque « confirmé » d'office) : passage au transport CORS avec `status:"ok"` exigé et timeout 15 s. Colonnes préservées : `solution` = solutions cochées, `site` = type de site, `enjeu` = récapitulatif.
5. **Garde multi-étapes** : envoi seulement quand le bouton final est visible (dernière étape).
6. Handler extrait du bundle vers **`lead-handler.js`** (standard du dépôt, identité inchangée : même `formId`, mêmes APIs QA `agvLead`/`ubeproLead` en alias) ; champs cachés complétés (`id`, fbclid/gbraid/wbraid/ttclid, UTM, page_url, referrer) ; pont iframe prêt.

## Image de fond du haut (hero)
L'ancien bandeau (gros plan abstrait d'un boîtier de commande AGV) est remplacé par un **visuel d'entrepôt automatisé** (`img/hero-agv-amr.jpg` : robots AMR orange transportant des palettes, superviseurs avec tablette) — dégradé sombre et mise en page conservés, preload ajouté, ancienne image supprimée.

## SEO léger (rendu inchangé)
**H1 unique** : la page en comptait 19 (défaut Webflow) ; seul le titre hero « Automatisez vos flux logistiques... » reste en H1, les 18 autres deviennent des H2 (les classes portent les tailles : aucun impact visuel). `lang`, titre et metas d'origine conservés.

## Tests (jsdom + vrai jQuery, formulaire réel)
Consentement total → CRM (`ADW_LP_SOLUTIONS_AGV_AMR`)/Sheets/GTM complets avec source campagne · sans consentement → source `ADW`, aucun click ID · honeypot → zéro envoi · livraisons KO → erreur visible, **pas de faux Merci** (le défaut corrigé est couvert par ce scénario) · syntaxes JS + HTTP 200.

## Lancement
- [ ] Aucune action CRM requise (formId inchangé, déjà en production)
- [ ] Déployer et vérifier un lead réel (CRM + feuille) + aperçu GTM
- [ ] Parcours local dans un **nouveau dossier** (cache)

## Ajout — Verification du numero par SMS (2026-10-26)
A la demande metier, la verification par code SMS (API SMS Partner HelloLead, meme contrat que la LP de reference) est **reintroduite** :
- nouveau module `verification-sms.js` : mobile 06/07, envoi `envoyer_code`, verification `verifier_code` (code 6 chiffres, 10 min, usage unique), compte a rebours de renvoi 120 s, erreurs 422/404/409/410/429/502 affichees depuis le JSON ;
- l'envoi du lead est desormais **bloque** tant que le numero n'est pas verifie ; le drapeau `telephone_verifie` est transmis au CRM, a Google Sheets et a l'evenement GTM ;
- interface injectee sous le champ telephone, sans modification de `style.css` ni du design.
Details : `docs/VERIFICATION-SMS.md`. Prerequis : l'API doit autoriser l'origine publique de la LP en CORS.
