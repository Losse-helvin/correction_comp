# Restauration GTM — 7 pages

> Dépôt `correction_comp` — 13 novembre 2026. Demande : ajouter la fonctionnalité `GTM-53SH7D7F` aux pages listées.

## Résumé

| Indicateur | Avant | Après |
|---|---:|---:|
| Pages avec `GTM-53SH7D7F` (dépôt, 152 fichiers) | 26 | **32** |
| Pages sans GTM | 112 | **106** |
| Pages avec `GTM-WMVZJKS` | 14 | 14 |

**6 pages** sans GTM ont été restaurées à leur état d’origine (chargeur, noscript le cas échéant, événements). **1 page** avait déjà la fonctionnalité : aucune modification.

## Pages restaurées (6)

| Page | Installation restaurée | Éléments restaurés |
|---|---|---|
| [`assurance-agriculteur-v2/index.html`](assurance-agriculteur-v2/index.html) | script seul | chargeur, ancien événement `formulaire_lead` dans `script.js`, push cookies |
| [`assurance-consultant-societe-conseil-v2/index.html`](assurance-consultant-societe-conseil-v2/index.html) | complet (script + noscript) | chargeur, noscript, push cookies |
| [`assurance-estheticiennes-instituts-beaute/index.html`](assurance-estheticiennes-instituts-beaute/index.html) | complet (script + noscript) | chargeur, noscript, push cookies |
| [`assurance-iard-v2/index.html`](assurance-iard-v2/index.html) | script seul | chargeur, `pushLeadEvents()` dans `lead-handler.js`, ancien événement dans `script.js`, push cookies |
| [`assurance-tns/index.html`](assurance-tns/index.html) | script seul | chargeur, `pushLeadEvents()` dans `lead-handler.js`, ancien événement dans `script.js`, push cookies |
| [`assurances-professionnelles/index.html`](assurances-professionnelles/index.html) | script seul | chargeur, `pushLeadEvents()` dans `lead-handler.js`, push cookies |

Restauration par `git checkout` depuis les commits précédant les suppressions (`0d603f4` pour les 3 pages « script seul », `7baf16b` pour les 3 pages de la liste des 74) : le code restauré est identique à l’original.

## Page déjà conforme (1)

- [`assurance-tns-pro-v2-adw/index.html`](assurance-tns-pro-v2-adw/index.html) : utilisait déjà `GTM-53SH7D7F` (script seul, chargeur + `pushLeadEvents()` + push cookies). Aucune modification.

## Vérifications automatisées

- `python -B -m unittest discover -s tests -p 'test*.py'` : **17 tests réussis**.
- `node --check` : syntaxe valide sur les 9 fichiers JS restaurés.
- Suite JavaScript : **361 succès / 7 échecs**, soit exactement les 7 échecs préexistants sur `assurance-consultants-societe-conseil` (page non modifiée). Aucune régression.
- Équilibre des balises `<script>` vérifié sur les 7 pages.

### Tests mis à jour

- `tests/pages-sans-gtm.json` : **105 → 99 dossiers** (retrait des 6 pages restaurées).
- `tests/test_restauration_gtm.py` : compteur 105 → 99.

## Limite

Analyse statique du code source : elle confirme la présence du conteneur et des événements, pas le déclenchement réel des balises en production.
