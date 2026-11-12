# Verification du numero de telephone par SMS — Assurance TNS Pro

_Mise en place le 2026-10-26, sur le meme modele que la LP de reference `assurance-consultant-conseil-v2`._

## Fichiers
- `verification-sms.js` : module autonome (charge apres `lead-handler.js`). Il injecte l'interface sous le champ telephone, sans modifier `style.css` ni le design (styles embarques et limites a `.sms-verification`).
- `lead-handler.js` : bloque l'envoi du lead tant que le numero n'est pas verifie et transmet `telephone_verifie=oui/non` au CRM, a Google Sheets et a l'evenement GTM.

## Parcours utilisateur
1. Saisie d'un mobile francais (10 chiffres, commencant par 06 ou 07 ; les formats +33 / 0033 / espaces sont normalises).
2. Clic **Recevoir le code** → `POST https://mc.hellolead.pro/mon_compte/api/smspartner/envoi_code_verification.php` avec `action=envoyer_code` et `telephone=...` (corps `URLSearchParams`, jamais de JSON brut).
3. Envoi reussi → le champ code apparait ; renvoi desactive avec compte a rebours de 120 s.
4. Clic **Verifier** → `POST` avec `action=verifier_code`, `telephone`, `code` (6 chiffres, valable 10 minutes, usage unique ; un nouveau code remplace l'ancien).
5. Verification reussie → badge vert « ✓ Numéro vérifié », boutons masques ; modifier le numero reinitialise la verification.
6. L'envoi du formulaire est **bloque** tant que le numero saisi n'est pas verifie (message d'erreur en ligne, focus sur le champ telephone).

## Gestion des reponses (JSON lu meme en erreur HTTP)
| Statut | Cas | Affichage |
|---|---|---|
| 200 + statut OK | envoi / verification reussis | messages de succes ci-dessus |
| 422 | numero ou code invalide | message renvoye par l'API |
| 404 | aucun code envoye | inviter a cliquer « Recevoir le code » |
| 410 | code expire (> 10 min) | inviter a demander un nouveau code |
| 409 | code deja utilise | inviter a demander un nouveau code |
| 429 | demande trop rapide | delai restant renvoye (`retry_after`…) + compte a rebours correspondant |
| 502 | echec d'envoi SMS | « Réessayez dans un instant » |
| reseau | fetch impossible | message de connexion generique |

Le message du JSON (`message` / `error`) est toujours prioritaire sur les messages par defaut.

## Prerequis serveur (a verifier cote HelloLead)
L'API doit autoriser en **CORS** l'origine publique de cette LP (les appels partent directement du navigateur du visiteur). Si la LP est affichee dans une iframe d'un autre domaine, privilegier le relais parent (voir le dossier `assurance-consultant-societe-conseil-v2`).

## Surcharge eventuelle
Avant le chargement du module : `window.SMS_VERIFICATION_CONFIG = { apiUrl: '...', cooldown: 120 };`

## QA (console navigateur)
- `smsVerification.estVerifie()` → `true/false` ; `smsVerification.numeroVerifie()` → numero verifie.
- `lpLead.preview()` → le payload contient `telephone_verifie`.
