# Configuration — page wrapper `assurance-consultant-societe-conseil-v2`

## Structure
- `index.html` : Consent Mode V2 (default denied) + GTM-53SH7D7F + iframe pleine page vers la LP hébergée.
- `bridge.js` : pont parent double protocole — consentement/URL publique **et relais SMS** (voir `VERIFICATION-SMS.md`).
- `style.css` : contient la règle `.lp-assurance-frame` (plein écran) — conservée telle quelle.

## Vérification SMS
La LP hébergée dans l'iframe exige la vérification du numéro par SMS : le pont relaye désormais ses demandes (`envoyer_code` / `verifier_code`) vers l'API SMS Partner et lui renvoie statut + JSON (même en erreur). Détail et prérequis (origine parent acceptée par l'enfant, CORS de l'API, liste `allowedParents`, HTTPS) : `VERIFICATION-SMS.md`.

## Changer la LP embarquée
Éditer l'attribut `src` de l'iframe dans `index.html`. Les LP traitées du dépôt (avec `verification-sms.js`) appellent l'API directement — le relais reste inactif mais inoffensif pour elles. Après changement de domaine cible, rien à modifier dans `bridge.js` : l'origine enfant est calculée depuis le `src`.

## GTM
Conteneur `GTM-53SH7D7F` partagé avec les autres LP. Les conversions proviennent de l'iframe (dataLayer de la LP enfant) — à mesurer via le mode Aperçu sur le domaine de la LP enfant, pas sur ce wrapper.
