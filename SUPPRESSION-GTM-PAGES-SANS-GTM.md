# Suppression GTM — pages identifiées « sans GTM »

> 13 novembre 2026 — dépôt `correction_comp`.

## Périmètre

Cibles : les **21 sous-pages retrouvées** de la liste fournie, identifiées dans `CORRESPONDANCE-PAGES-LISTE.md` et listées dans `tests/pages-sans-gtm.json`.

Les **7 entrées absentes** du dépôt ne peuvent pas être modifiées :

- `nicolas/ayvens.html`
- `nicolas/form-test.html`
- `nicolas/formly.html`
- `temlpate-webflow/comparateur-2.html`
- `temlpate-webflow/comparateur-3.html`
- `temlpate-webflow/comparateur-4.html`
- `webflow/template-1.html`

Les pages `mentions-legales` et `politique-de-confidentialite-donnees-personnelles` étaient déjà sans GTM ; elles n’ont pas été modifiées.

## Éléments supprimés sur chaque cible

- Chargeur JavaScript Google Tag Manager `googletagmanager.com/gtm.js` et commentaire GTM associé lorsque présent.
- Fallback `<noscript>` `googletagmanager.com/ns.html` lorsque présent.
- Fonction `pushLeadEvents()` et son appel dans `lead-handler.js` lorsque présent : événements `formulaire_lead` / `formulaire_micro_entrepreneur`.
- Push dataLayer `cookie_preferences_updated` dans `script.js`.

Conservés : formulaire, CRM, Google Sheets, vérification SMS, Consent Mode/gtag et bandeau cookies. Le Consent Mode n’est pas un conteneur GTM ; il a été conservé pour ne pas casser la gestion des préférences.

## Pages nettoyées — 21

Dans le tableau, « Oui » signifie que l’élément était présent avant intervention et a été retiré.

| Page | Chargeur GTM | Fallback noscript | Événements lead GTM | Push cookies GTM |
|---|---|---|---|---|
| [`alfaromeo-tonale-remerciement/index.html`](alfaromeo-tonale-remerciement/index.html) | Oui | Oui | Non | Oui |
| [`alfaromeo-tonale/index.html`](alfaromeo-tonale/index.html) | Oui | Non | Oui | Oui |
| [`lexus-lbx-2/index.html`](lexus-lbx-2/index.html) | Oui | Non | Oui | Oui |
| [`mercedes-benz-mercedes-benz-evito/index.html`](mercedes-benz-mercedes-benz-evito/index.html) | Oui | Non | Oui | Oui |
| [`mercedes-benz-nouvel-ecitan-fourgon/index.html`](mercedes-benz-nouvel-ecitan-fourgon/index.html) | Oui | Non | Oui | Oui |
| [`mercedes-benz-sprinter/index.html`](mercedes-benz-sprinter/index.html) | Oui | Non | Oui | Oui |
| [`panneaux-photovoltaiques-panneaux-photovoltaique-valider/index.html`](panneaux-photovoltaiques-panneaux-photovoltaique-valider/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-caisses-thank-you-page/index.html`](typ-formulaires-caisses-thank-you-page/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-energie-thank-you-page/index.html`](typ-formulaires-energie-thank-you-page/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-form-typ-vehicules/index.html`](typ-formulaires-form-typ-vehicules/index.html) | Oui | Non | Oui | Oui |
| [`typ-formulaires-panneaux-photovoltaiques/index.html`](typ-formulaires-panneaux-photovoltaiques/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-panneaux-thank-you-page/index.html`](typ-formulaires-panneaux-thank-you-page/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-securite-thank-you-page/index.html`](typ-formulaires-securite-thank-you-page/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-typ-caisses-enregistreuse/index.html`](typ-formulaires-typ-caisses-enregistreuse/index.html) | Oui | Non | Oui | Oui |
| [`typ-formulaires-typ-energie-form/index.html`](typ-formulaires-typ-energie-form/index.html) | Oui | Non | Oui | Oui |
| [`typ-formulaires-typ-log-entreprise/index.html`](typ-formulaires-typ-log-entreprise/index.html) | Oui | Oui | Non | Oui |
| [`typ-formulaires-typ-panneaux-form/index.html`](typ-formulaires-typ-panneaux-form/index.html) | Oui | Non | Oui | Oui |
| [`typ-formulaires-typ-secu-form/index.html`](typ-formulaires-typ-secu-form/index.html) | Oui | Non | Oui | Oui |
| [`typ-formulaires-vehicules-thank-you-page/index.html`](typ-formulaires-vehicules-thank-you-page/index.html) | Oui | Oui | Non | Oui |
| [`voiture-nouveau-range-rover/index.html`](voiture-nouveau-range-rover/index.html) | Oui | Non | Oui | Oui |
| [`voiture-range-rover/index.html`](voiture-range-rover/index.html) | Oui | Non | Oui | Oui |

## Vérification

Contrôle automatisé ajouté : `tests/test_restauration_gtm.py::test_pages_sans_gtm_sans_chargeur_ni_evenements`.

Il vérifie pour les 21 cibles :

- aucun chargeur GTM actif dans le HTML ;
- aucune URL `googletagmanager.com/gtm.js` ou `ns.html` ;
- aucun identifiant `GTM-` dans le HTML ;
- aucun `pushLeadEvents`, `formulaire_lead` ou `formulaire_micro_entrepreneur` dans `lead-handler.js` lorsque présent ;
- aucun `cookie_preferences_updated` dans `script.js`.

Des mentions textuelles du mot GTM peuvent subsister dans des commentaires ou dans une garde neutre anti-scripts externes ; elles ne chargent pas de conteneur GTM et n’émettent pas d’événement GTM.

Résultats :

- `python -B -m unittest discover -s tests -p 'test*.py' -v` : **13 tests Python réussis**.
- `node --check` : syntaxe JavaScript valide pour les fichiers ciblés modifiés.
- Suite JavaScript : les parcours ciblés passent. La suite complète remonte 7 échecs préexistants sur `assurance-consultants-societe-conseil`, page non modifiée par ce changement.
