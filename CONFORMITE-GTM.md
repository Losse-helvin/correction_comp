# Conformité GTM — correspondance, vérification et corrections

> Source : `GTM_PAR_GROUPE.md` (fourni). Vérification et corrections appliquées au dépôt `correction_comp` — 13 novembre 2026.

## Résumé

| Indicateur | Avant | Après |
|---|---:|---:|
| Pages HTML du dépôt | 152 | 152 |
| Pages avec GTM | 122 | **114** |
| Pages sans GTM | 30 | **38** |
| Conteneur `GTM-53SH7D7F` | 107 | **100** |
| Conteneur `GTM-WMVZJKS` | 15 | **14** |
| Pages avec plusieurs conteneurs | 0 | **0** |

Les trois règles demandées sont satisfaites et couvertes par des tests automatisés.

## Règle 1 — un seul conteneur par page

**Vérification :** les 152 fichiers HTML ont été analysés (chargeur `gtm.js`, iframe `noscript`, identifiants présents).

- Aucune page n’utilisait deux conteneurs différents, ni deux chargeurs.
- Aucun `noscript` ne pointait vers un conteneur différent de celui du script.
- **1 seule correction de conteneur a été nécessaire** : `vehicules-utilitaires`, passé de `GTM-WMVZJKS` à `GTM-53SH7D7F` (chargeur + noscript), car cette page est absente du document — voir règle 3.

| Page | Avant | Après | Motif |
|---|---|---|---|
| [`vehicules-utilitaires/index.html`](vehicules-utilitaires/index.html) | `GTM-WMVZJKS` | `GTM-53SH7D7F` | Absente du document → conteneur par défaut |

Les **14 pages du groupe `GTM-WMVZJKS`** listées comme « complet » conservent ce conteneur, conformément au document.

## Règle 2 — suppression GTM sur les installations partielles

Le document marque **8 pages** comme partielles : 3 « script seul ⚠️ » et 5 « noscript seul ❌ ». GTM y a été entièrement retiré.

| # | Page du document | Marque | Dossier du dépôt | Chargeur retiré | noscript retiré | Événements lead retirés | Push cookies retiré |
|---:|---|---|---|---|---|---|---|
| 1 | `assurance-agriculteur-v2.html` | script seul ⚠️ | [`assurance-agriculteur-v2/index.html`](assurance-agriculteur-v2/index.html) | Oui | — | — | Oui |
| 2 | `assurance-iard-v2.html` | script seul ⚠️ | [`assurance-iard-v2/index.html`](assurance-iard-v2/index.html) | Oui | — | Oui | Oui |
| 3 | `assurance-tns.html` | script seul ⚠️ | [`assurance-tns/index.html`](assurance-tns/index.html) | Oui | — | Oui | Oui |
| 4 | `remerciement-carte-cadeau.html` | noscript seul ❌ | [`remerciement-carte-cadeau/index.html`](remerciement-carte-cadeau/index.html) | Oui | Oui | — | Oui |
| 5 | `remerciement-panneaux-solaire.html` | noscript seul ❌ | [`remerciement-panneaux-solaire/index.html`](remerciement-panneaux-solaire/index.html) | Oui | Oui | — | Oui |
| 6 | `remerciement-ticket-restaurant-v2.html` | noscript seul ❌ | [`remerciement-ticket-restaurant-v2/index.html`](remerciement-ticket-restaurant-v2/index.html) | Oui | Oui | — | Oui |
| 7 | `remerciement-ticket-restaurant.html` | noscript seul ❌ | [`remerciement-ticket-restaurant/index.html`](remerciement-ticket-restaurant/index.html) | Oui | Oui | — | Oui |
| 8 | `remerciements-panneaux-solaires.html` | noscript seul ❌ | [`remerciements-panneaux-solaires/index.html`](remerciements-panneaux-solaires/index.html) | Oui | Oui | — | Oui |

Éléments supprimés sur ces pages :

- chargeur `googletagmanager.com/gtm.js` et commentaires GTM associés ;
- iframe de secours `googletagmanager.com/ns.html` et son conteneur `w-embed` devenu vide ;
- fonction `pushLeadEvents()` et son appel dans `lead-handler.js` (`assurance-iard-v2`, `assurance-tns`) ;
- push dataLayer `cookie_preferences_updated` dans `script.js` ;
- **ancien événement de conversion poussé depuis `script.js`** (`formulaire_lead`, `formulaire_micro_entrepreneur`, `formulaire_lead_societe_en_cours_creation`) sur `assurance-agriculteur-v2`, `assurance-iard-v2` et `assurance-tns` : ce code historique vit dans `script.js`, pas dans `lead-handler.js`, et aurait été manqué en ne nettoyant que le handler ;
- ligne « GTM » des rapports `rapport-site.md`, désormais à `absent`.

Conservés : formulaires, CRM, Google Sheets, vérification SMS, Consent Mode `gtag` et bandeau cookies. Le `e.preventDefault()` du gestionnaire `.form-ass` a été maintenu à l’identique pour ne pas modifier le comportement du formulaire.

## Règle 3 — pages avec GTM absentes du document

**79 pages** du dépôt utilisent GTM sans figurer dans `GTM_PAR_GROUPE.md`. Elles doivent toutes utiliser `GTM-53SH7D7F`.

- Après vérification, une seule était en écart : `vehicules-utilitaires` (corrigée ci-dessus).
- Les autres étaient déjà sur `GTM-53SH7D7F` : aucune modification nécessaire.

## Correspondance complète des 33 entrées du document

Correspondance établie via le champ **Page source** des fichiers `rapport-site.md`. Plusieurs entrées correspondent à plusieurs dossiers du dépôt (copies rangées à la racine et en sous-dossier) : elles sont traitées identiquement.

| # | Page du document | Groupe | Installation | Dossier(s) du dépôt | Action |
|---:|---|---|---|---|---|
| 1 | `assurance/agriculteur.html` | `GTM-53SH7D7F` | complet | [`agriculteur/index.html`](agriculteur/index.html)<br>[`assurance/agriculteur/index.html`](assurance/agriculteur/index.html)<br>[`assurance-agriculteur/index.html`](assurance-agriculteur/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 2 | `assurance/assurance-professionnelle-iard-cookie.html` | `GTM-53SH7D7F` | complet | [`assurance/assurance-professionnelle-iard-cookie/index.html`](assurance/assurance-professionnelle-iard-cookie/index.html)<br>[`assurance-assurance-professionnelle-iard-cookie/index.html`](assurance-assurance-professionnelle-iard-cookie/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 3 | `assurance/multirisques.html` | `GTM-53SH7D7F` | complet | [`assurance/multirisques/index.html`](assurance/multirisques/index.html)<br>[`assurance-multirisques/index.html`](assurance-multirisques/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 4 | `assurance/professionnelle-iard.html` | `GTM-53SH7D7F` | complet | [`assurance/professionnelle-iard/index.html`](assurance/professionnelle-iard/index.html)<br>[`assurance-professionnelle-iard/index.html`](assurance-professionnelle-iard/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 5 | `assurance/protection-sociale-collective-v4.html` | `GTM-53SH7D7F` | complet | [`assurance/protection-sociale-collective-v4/index.html`](assurance/protection-sociale-collective-v4/index.html)<br>[`assurance-protection-sociale-collective-v4/index.html`](assurance-protection-sociale-collective-v4/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 6 | `assurance/protection-sociale-collective.html` | `GTM-53SH7D7F` | complet | [`assurance/protection-sociale-collective/index.html`](assurance/protection-sociale-collective/index.html)<br>[`assurance-protection-sociale-collective/index.html`](assurance-protection-sociale-collective/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 7 | `assurance/rc-pro.html` | `GTM-53SH7D7F` | complet | [`assurance/rc-pro/index.html`](assurance/rc-pro/index.html)<br>[`assurance-rc-pro/index.html`](assurance-rc-pro/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 8 | `assurance-agriculteur-v2.html` | `GTM-53SH7D7F` | script seul ⚠️ | [`assurance-agriculteur-v2/index.html`](assurance-agriculteur-v2/index.html) | GTM supprimé (règle 2) |
| 9 | `assurance-consultants-societe-conseil.html` | `GTM-53SH7D7F` | complet | [`assurance-consultants-societe-conseil/index.html`](assurance-consultants-societe-conseil/index.html)<br>[`assurance-consultants-societe-conseil - Copie/index.html`](assurance-consultants-societe-conseil%20-%20Copie/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 10 | `assurance-estheticienne-institut-beaute.html` | `GTM-53SH7D7F` | complet | [`assurance-estheticienne-institut-beaute/index.html`](assurance-estheticienne-institut-beaute/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 11 | `assurance-estheticiennes-instituts-beaute-v1.html` | `GTM-53SH7D7F` | complet | [`assurance-estheticiennes-instituts-beaute-v1/index.html`](assurance-estheticiennes-instituts-beaute-v1/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 12 | `assurance-iard-v2.html` | `GTM-53SH7D7F` | script seul ⚠️ | [`assurance-iard-v2/index.html`](assurance-iard-v2/index.html) | GTM supprimé (règle 2) |
| 13 | `assurance-tns-pro-v2-adw.html` | `GTM-53SH7D7F` | complet | [`assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw/index.html`](assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw/index.html)<br>[`assurance-tns-pro-v2-adw/index.html`](assurance-tns-pro-v2-adw/index.html) | Conteneur `GTM-53SH7D7F` vérifié, conforme |
| 14 | `assurance-tns.html` | `GTM-53SH7D7F` | script seul ⚠️ | [`assurance-tns/index.html`](assurance-tns/index.html) | GTM supprimé (règle 2) |
| 15 | `assurance/assurance-professionnelle-iard-v2.html` | `GTM-WMVZJKS` | complet | [`assurance-assurance-professionnelle-iard-v2/index.html`](assurance-assurance-professionnelle-iard-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 16 | `assurance-commerce.html` | `GTM-WMVZJKS` | complet | [`assurance-commerce/index.html`](assurance-commerce/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 17 | `assurance-marchandise.html` | `GTM-WMVZJKS` | complet | [`assurance-marchandise/index.html`](assurance-marchandise/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 18 | `assurance-professionnelle-tns-v2.html` | `GTM-WMVZJKS` | complet | [`assurance-professionnelle-tns-v2/index.html`](assurance-professionnelle-tns-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 19 | `assurances-multirisques-v2.html` | `GTM-WMVZJKS` | complet | [`assurances-multirisques-v2/index.html`](assurances-multirisques-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 20 | `complementaire-retraite-tns-v2.html` | `GTM-WMVZJKS` | complet | [`complementaire-retraite-tns-v2/index.html`](complementaire-retraite-tns-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 21 | `energie-v2.html` | `GTM-WMVZJKS` | complet | [`energie-v2/index.html`](energie-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 22 | `energie.html` | `GTM-WMVZJKS` | complet | [`energie/index.html`](energie/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 23 | `geolocalisation-v2.html` | `GTM-WMVZJKS` | complet | [`geolocalisation-v2/index.html`](geolocalisation-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 24 | `geolocalisation.html` | `GTM-WMVZJKS` | complet | [`geolocalisation/index.html`](geolocalisation/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 25 | `panneaux-photovoltaiques-energie-solaire.html` | `GTM-WMVZJKS` | complet | [`panneaux-photovoltaiques-energie-solaire/index.html`](panneaux-photovoltaiques-energie-solaire/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 26 | `remerciement-carte-cadeau.html` | `GTM-WMVZJKS` | noscript seul ❌ | [`remerciement-carte-cadeau/index.html`](remerciement-carte-cadeau/index.html) | GTM supprimé (règle 2) |
| 27 | `remerciement-panneaux-solaire.html` | `GTM-WMVZJKS` | noscript seul ❌ | [`remerciement-panneaux-solaire/index.html`](remerciement-panneaux-solaire/index.html) | GTM supprimé (règle 2) |
| 28 | `remerciement-ticket-restaurant-v2.html` | `GTM-WMVZJKS` | noscript seul ❌ | [`remerciement-ticket-restaurant-v2/index.html`](remerciement-ticket-restaurant-v2/index.html) | GTM supprimé (règle 2) |
| 29 | `remerciement-ticket-restaurant.html` | `GTM-WMVZJKS` | noscript seul ❌ | [`remerciement-ticket-restaurant/index.html`](remerciement-ticket-restaurant/index.html) | GTM supprimé (règle 2) |
| 30 | `remerciements-panneaux-solaires.html` | `GTM-WMVZJKS` | noscript seul ❌ | [`remerciements-panneaux-solaires/index.html`](remerciements-panneaux-solaires/index.html) | GTM supprimé (règle 2) |
| 31 | `securite-professionnels.html` | `GTM-WMVZJKS` | complet | [`securite-professionnels/index.html`](securite-professionnels/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 32 | `tns-prevoyance-v2-adw-test.html` | `GTM-WMVZJKS` | complet | [`tns-prevoyance-v2-adw-test/index.html`](tns-prevoyance-v2-adw-test/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |
| 33 | `tns-prevoyance-v2.html` | `GTM-WMVZJKS` | complet | [`tns-prevoyance-v2/index.html`](tns-prevoyance-v2/index.html) | Conteneur `GTM-WMVZJKS` vérifié, conforme |

Ces 33 entrées couvrent **43 dossiers** du dépôt (copies incluses), dont **35** conservent GTM.

## Point de vigilance : « complet » dans le document ≠ « complet » dans le dépôt

Le document classe « complet (script + noscript) » des pages qui, dans ce dépôt, n’ont **que le chargeur script** : c’est le cas de **33 dossiers** conservés. Leur conteneur est correct et unique (règle 1), mais le secours `noscript` est absent.

Ces pages n’ont **pas** été supprimées : la règle 2 s’applique aux marques du document, et elles y sont notées « complet ». Aucun `noscript` n’a été ajouté non plus, ce n’était pas demandé. À trancher si vous souhaitez aligner l’installation réelle sur le document.

## Vérifications automatisées

Nouveaux contrôles dans `tests/test_restauration_gtm.py` :

- `test_un_seul_conteneur_par_page` : un seul identifiant et un seul chargeur par page, `noscript` cohérent avec le script ;
- `test_conteneur_conforme_au_groupe` : `GTM-WMVZJKS` réservé aux 14 pages listées, `GTM-53SH7D7F` partout ailleurs ;
- `test_groupe_wmvzjks_est_intact` : les 14 pages du groupe conservent leur conteneur ;
- `test_balises_script_equilibrees` : aucune balise `</script>` emportée par la suppression ;
- `test_pages_sans_gtm_sans_chargeur_ni_evenements` : étendu à **29 pages**, contrôle aussi `script.js` et `verification-sms.js`.

Fichiers de référence ajoutés : `tests/gtm-conteneurs.json` (politique de conteneurs) et `tests/pages-sans-gtm.json` (29 pages).

### Résultats

- `python -B -m unittest discover -s tests -p 'test*.py'` : **18 tests réussis**.
- `node --check` : syntaxe valide sur tous les modules JavaScript modifiés.
- Suite JavaScript : **361 succès / 7 échecs**, soit exactement les 7 échecs préexistants sur `assurance-consultants-societe-conseil` (page non modifiée). Aucune régression introduite.
- Structure HTML vérifiée : nombre de formulaires inchangé sur toutes les pages modifiées.

### Correction trouvée par les tests

Sur `assurance-tns/index.html`, la balise `</script>` du bloc Consent Mode était sur la même ligne que le commentaire GTM. Une suppression par ligne l’emportait et cassait le HTML (10 tests en échec). La balise a été restaurée et un test de garde a été ajouté.

## Limite

Analyse statique du code source : elle confirme la présence et l’unicité du conteneur, pas le déclenchement réel des balises en production.
