# Rapport de modifications — `assurance-consultant-societe-conseil-v2` (version FONCTIONNELLE)
_Continuités des traitements TNS Pro / TNS / Agriculteur / Consultants, adaptée à la nature de cette LP : c'est une **page wrapper iframe** (sans formulaire propre). 2026-10-26. Domaine : https://assurance-consultant-societe-conseil-v2.lp.comparateurpro.fr_

## État d'origine constaté
Page quasi vide (2,2 Ko) qui embarque en iframe pleine page la LP hébergée `https://www.ubepro.com/assurance-consultant-conseil-v2/`. Consent Mode V2 « default denied » déjà présent dans le `<head>`, mais **aucun conteneur GTM**, **aucun pont postMessage** (l'iframe ne recevait ni consentement ni URL parente → attribution des leads perdue), `lang="en"`, et chargement inutile d'un bundle `script.js` de 1,5 Mo (celui des LP Webflow, sans rapport avec cette page). Le principe « sans SMS » ne concerne pas directement cette page (aucun formulaire), mais la LP embarquée.

## Modifications appliquées
1. **GTM ajouté** : conteneur `GTM-53SH7D7F` (le même que les autres LP) inséré **après** le Consent Mode default existant + balise `<noscript>` — le consentement par défaut est désormais consommé.
2. **Pont parent `bridge.js` (sans SMS)** : protocole `ubepro-assurance-v1` — relaie le consentement (`cookieconsent_accept/deHarbor`, `user_cookie_preferences_changed`, `setAssuranceConsent()`) et l'**URL publique complète** de la page parente (UTM, click IDs, `ltm_*`) vers l'iframe, répond aux requêtes de l'enfant, sources/origine enfant strictement vérifiées. A remplacé le bundle de 1,5 Mo.
3. `lang="fr"`. Titre, meta, canonical et iframe conservés.

## ⚠️ Points de vigilance (à trancher avant mise en production)
1. **La LP embarquée exige encore le SMS** : la version hébergée `ubepro.com/assurance-consultant-conseil-v2/` est la référence AVEC vérification par code SMS, et sans proxy SMS côté parent ses envois échoueront. Options (docs/CONFIGURATION-IFRAME.md) : faire héberger une version **sans SMS** de cette LP (recommandé, cohérent avec toutes les autres), ou pointer l'iframe vers une LP déjà sans SMS, ou réactiver le relais SMS (contraire à la consigne « sans SMS », à confirmer explicitement).
2. **Origine parent** : la LP de référence n'accepte les messages parent que depuis `https://www.comparateurpro.fr` (origine parente codée de son côté). Sur le domaine `*.lp.comparateurpro.fr`, le pont n'aura d'effet que si la LP enfant accepte aussi cette origine — à aligner lors de l'hébergement sans SMS (notre `lead-handler.js` accepte toute origine parent qui se déclare correctement).

## Tests effectués
Contrôles statiques : présence GTM + noscript, consent default avant GTM, syntaxe `bridge.js` validée (Node), `script.js` supprimé, `lang="fr"`, HTTP 200 en local. Test bout-en-bout impossible ici (dépend de la LP hébergée et des origines réelles).

## Ajout — Relais SMS active (2026-10-26)
A la demande metier, le pont parent relaie desormais la verification SMS de la LP hebergee : poignee de main avec nonce (`bridge-ready` -> `bridge-init`), reponse `landing-url` filtree par le consentement de l'enfant, et relais `sms-request` -> API SMS Partner (`envoyer_code`/`verifier_code`, URLSearchParams, JSON lu meme en erreur) -> `sms-response` (statut + data, 422/404/409/410/429/502 transmis a l'enfant). C'est le protocole exact du snippet `WEBFLOW_EMBED.md` de la reference ; l'ancien format des LP du depot reste supporte en parallele. Conditions : la LP enfant doit autoriser l'origine de ce wrapper comme parent, et l'API SMS doit autoriser cette origine en CORS (details : `docs/VERIFICATION-SMS.md`).
