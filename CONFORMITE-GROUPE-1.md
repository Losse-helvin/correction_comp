# Conformité du Groupe 1 — `GTM-53SH7D7F` (32 pages)

> Vérification et corrections appliquées aux 32 pages du Groupe 1, conformément à l’instruction GTM fournie. 13 novembre 2026.

## Instruction appliquée

1. **Chargeur** `gtm.js` le plus haut possible dans le `<head>`, avec `GTM-53SH7D7F`.
2. **noscript** `ns.html` juste après la balise d’ouverture `<body>`.
3. **Événement `formulaire_lead`** poussé dans le `dataLayer` à la validation du formulaire.

## Résumé

| Point de contrôle | Avant | Après |
|---|---:|---:|
| Pages avec le chargeur (1 seul, dans `<head>`) | 32 | **32** |
| Pages avec le noscript (après `<body>`) | 7 | **32** |
| Pages poussant `formulaire_lead` | 31 | **32** |
| Chargeurs en double ou conteneur erroné | 0 | **0** |

**25 pages** ont reçu le noscript manquant, **1 noscript mal placé** a été déplacé, **1 page wrapper** a reçu le relais de conversion. **Aucune page n’a perdu sa fonctionnalité.**

## Corrections appliquées

### 1. noscript manquant — 25 pages

Deux situations, deux traitements :

| Situation | Nb | Traitement |
|---|---:|---|
| Conteneur Webflow `w-embed w-iframe` présent avec commentaires GTM vides | 20 | iframe `ns.html` insérée entre les commentaires |
| Aucun emplacement réservé | 5 | bloc complet inséré juste après `<body>` |

- **Emplacement Webflow restauré (20)** : `assurance/agriculteur`, `assurance/assurance-professionnelle-iard-cookie`, `assurance/multirisques`, `assurance/professionnelle-iard`, `assurance/protection-sociale-collective`, `assurance/protection-sociale-collective-v4`, `assurance/rc-pro`, `assurance-agriculteur`, `assurance-assurance-professionnelle-iard-cookie`, `assurance-consultants-societe-conseil - Copie`, `assurance-estheticienne-institut-beaute`, `assurance-estheticiennes-institut-beaute`, `assurance-estheticiennes-instituts-beaute-v1`, `assurance-multirisques`, `assurance-professionnelle-iard`, `assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw`, `assurance-protection-sociale-collective`, `assurance-protection-sociale-collective-v4`, `assurance-rc-pro`, `assurance-tns-pro-v2-adw`
- **Bloc inséré après `<body>` (5)** : `assurance-agriculteur-v2`, `assurance-iard-v2`, `assurance-tns`, `assurances-professionnelles`, `protection-sociale-collective`

### 2. noscript mal placé — 1 page

| Page | Problème | Correction |
|---|---|---|
| [`solutions-agv-amr/index.html`](solutions-agv-amr/index.html) | iframe `ns.html` à la ligne 466, loin après `<body>` | déplacée juste après `<body` |

### 3. Chargeur GTM — 3 pages

Sur `LP_reference`, `vehicules-utilitaires` et `solutions-agv-amr`, le chargeur était le dernier script du `<head>`, après le bloqueur de rendu Webflow, gtag.js et le Meta Pixel. Il a été remonté immédiatement après le bloc Consent Mode V2, premier script Google du `<head>`.

L’ordre `Consent Mode` → `GTM` est conservé : c’est une exigence du dépôt (commentaire « Elle DOIT PRÉCÉDER tout autre script Google »), couverte par un test. Placer GTM avant le Consent Mode aurait fait démarrer le conteneur sans consentement par défaut.

### 4. Événement `formulaire_lead` — page wrapper

[`assurance-estheticiennes-instituts-beaute/index.html`](assurance-estheticiennes-instituts-beaute/index.html) est une page hôte qui affiche la LP dans une iframe. Le formulaire est dans [`assurance-estheticiennes-institut-beaute`](assurance-estheticiennes-institut-beaute/index.html), donc dans **un autre document, avec son propre `dataLayer`** : l’événement poussé dans l’iframe n’atteint jamais le conteneur GTM de la page hôte, et la conversion n’était pas trackée sur cette URL.

Le pont `postMessage` existant a été étendu :

- [`assurance-estheticiennes-institut-beaute/script.js`](assurance-estheticiennes-institut-beaute/script.js) : après le push `formulaire_lead`, envoi de `{ type: 'lead-submitted' }` au parent via `parentBridgePost()`, déjà protégé par le nonce et l’origine autorisée ;
- [`assurance-estheticiennes-instituts-beaute/script.js`](assurance-estheticiennes-instituts-beaute/script.js) : réception du message et push de `{ event: 'formulaire_lead' }` dans le `dataLayer` de la page hôte.

Aucun autre comportement du pont (consentement, URL de campagne, relais SMS) n’est modifié.

## Pages du Groupe 1 — état final

Les **32 pages** réunissent les trois points de l’instruction :

| # | Page | Chargeur | noscript | `formulaire_lead` |
|---:|---|:--:|:--:|---|
| 1 | `LP_reference` | ✔ | ✔ | `lead-handler.js` |
| 2 | `agriculteur` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 3 | `assurance/agriculteur` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 4 | `assurance/assurance-professionnelle-iard-cookie` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 5 | `assurance/multirisques` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 6 | `assurance/professionnelle-iard` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 7 | `assurance/protection-sociale-collective` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 8 | `assurance/protection-sociale-collective-v4` | ✔ | ✔ | `script.js` |
| 9 | `assurance/rc-pro` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 10 | `assurance-agriculteur` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 11 | `assurance-agriculteur-v2` | ✔ | ✔ | `script.js` |
| 12 | `assurance-assurance-professionnelle-iard-cookie` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 13 | `assurance-consultant-societe-conseil-v2` | ✔ | ✔ | `js/main.js` |
| 14 | `assurance-consultants-societe-conseil` | ✔ | ✔ | `lead-handler.js` |
| 15 | `assurance-consultants-societe-conseil - Copie` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 16 | `assurance-estheticienne-institut-beaute` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 17 | `assurance-estheticiennes-institut-beaute` | ✔ | ✔ | `script.js` |
| 18 | `assurance-estheticiennes-instituts-beaute` | ✔ | ✔ | relais iframe (nouveau) |
| 19 | `assurance-estheticiennes-instituts-beaute-v1` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 20 | `assurance-iard-v2` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 21 | `assurance-multirisques` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 22 | `assurance-professionnelle-iard` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 23 | `assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 24 | `assurance-protection-sociale-collective` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 25 | `assurance-protection-sociale-collective-v4` | ✔ | ✔ | `script.js` |
| 26 | `assurance-rc-pro` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 27 | `assurance-tns` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 28 | `assurance-tns-pro-v2-adw` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 29 | `assurances-professionnelles` | ✔ | ✔ | `lead-handler.js` |
| 30 | `protection-sociale-collective` | ✔ | ✔ | `lead-handler.js` + `script.js` |
| 31 | `solutions-agv-amr` | ✔ | ✔ | `lead-handler.js` |
| 32 | `vehicules-utilitaires` | ✔ | ✔ | `lead-handler.js` + `script.js` |

## Vérifications automatisées

- **32/32 pages** : chargeur unique dans le `<head>`, noscript unique après `<body>`, conteneur `GTM-53SH7D7F`, balises `<script>` équilibrées — `test_chargeur_dans_le_head_et_noscript_apres_body`.
- **32/32 pages** : un `formulaire_lead` est poussé — `test_evenement_formulaire_lead_present`.
- **Wrapper** : relais de conversion présent des deux côtés — `test_wrapper_estheticiennes_relaie_la_conversion`, plus 4 tests JSDOM dans `tests/relais-conversion-iframe.test.cjs` (dont un contrôle de nonce et un contrôle d’origine).
- Tests Python : **20 réussis**.
- Suite JavaScript : **365 succès / 7 échecs**, soit exactement les 7 échecs préexistants sur `assurance-consultants-societe-conseil` (comportement SMS/CRM, sans lien avec GTM). Aucune régression.
- Équilibre des balises `<script>` vérifié sur les **152 fichiers HTML** du dépôt.

## Périmètre

- Seuls les fichiers du Groupe 1 sont modifiés ; les 14 pages `GTM-WMVZJKS` et les 106 pages sans GTM sont inchangées.
- Consent Mode, bannière cookies, CRM, Google Sheets et SMS : inchangés.
- Analyse statique du code source : elle confirme la présence et la position des balises et des appels, pas le déclenchement réel en production. Le conteneur `GTM-53SH7D7F` doit avoir une balise déclenchée sur l’événement `formulaire_lead` pour que la conversion remonte.
