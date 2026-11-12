# Mise en production — CRM, Google Sheets, GTM (version FONCTIONNELLE)
_LP `assurance-consultants-societe-conseil-pro-v2-adw` alignée sur la LP de référence `assurance-consultant-conseil-v2`. Détail fonctionnel : `docs/ANALYSE-FONCTIONNELLE-REFERENCE.md`. Aucune confirmation par code SMS._

## État : déjà configuré (endpoints de production de la référence)
Tout se règle dans **`TNS_CONFIG`** en tête de `lead-handler.js` :

| Réglage | Valeur actuelle |
|---|---|
| CRM (`leadApiUrl`) | `https://mc.hellolead.pro/mon_compte/api/webflow/get_information.php` |
| Transport CRM (`leadApiMode`) | `nocors` (sendBeacon/fetch `text/plain` — le CRM ne renvoie pas d'en-tête CORS ; `cors` possible si l'API évolue) |
| `formId` | `ADW_LP_ASSURANCE_CONSULTANTS_SOCIETE_CONSEIL` → **à confirmer/enregistrer côté CRM** (même convention que `ADW_LP_ASSURANCE_CONSULTANT`) |
| Google Sheets (`googleScriptUrl`) | Apps Script partagé **AGV/AMR** confirmé sur la référence (…`/exec`) |
| `source` de secours | `LP CONSULTANTS SOCIETE CONSEIL` (si aucune source de campagne consentie) |
| `publicLandingPath` | `''` → à renseigner si la LP passe en iframe (voir `docs/WEBFLOW_EMBED-TNS.md`) |

Chaque lead part **en parallèle** vers le CRM (enveloppe `{payload:{formId,id,data}}`) et vers Sheets (champs plats, schéma AGV/AMR : `solution`, `enjeu` = récapitulatif complet ≤ 500 car., q1–q3). Le « Merci ! » s'affiche si **au moins une** livraison aboutit ; sinon message d'erreur clair + nouvel essai possible. ⚠️ Un `sendBeacon` accepté ne **confirme pas** l'insertion CRM (transport non vérifiable, comme sur la référence) — contrôlez la réception réelle côté CRM lors du test de lancement.

> Le fichier `docs/Code.gs` reste fourni pour créer **votre propre** feuille si besoin (autre mapping 34 colonnes). La config par défaut utilise le script AGV/AMR partagé, pas celui-là.

## GTM (GTM-53SH7D7F, déjà sur la page)
Événements poussés à la validation finale : `formulaire_lead` (ou `formulaire_micro_entrepreneur` si auto-entrepreneur = Oui) avec `form_id`, `lead_type` (`standard`/`micro_entrepreneur`), et — **uniquement selon le consentement cookies de la bannière** — `page_url`, `categorie`, `lead_source`, `utm_*`/`ltm_*` (analytics), click IDs + `user_data` conversions améliorées (marketing).
- Déclencheurs : événement personnalisé regex `formulaire_(lead|micro_entrepreneur)` ou les deux événements.
- GA4 : mapper vers `generate_lead`. Google Ads : conversion + variable « données fournies par l'utilisateur » → `user_data`.
- Vérifier en Aperçu GTM / Tag Assistant avec un consentement « tout accepter ».

## Tracking URL (automatique)
`utm_source/medium/campaign/term/content/id`, `ltm_source/category/typ/user`, `gclid`, `gbraid`, `wbraid`, `fbclid`, `msclkid`, `ttclid`, `source`, `categorie`, `user` — capturés (query + hash), gardés en session, **filtrés par le consentement** (analytics : UTM/LTM/page ; marketing : click IDs). `source` CRM = `ltm_source` en priorité.
**URL de test** (après avoir cliqué « Accepter » sur la bannière cookies) :
```
https://assurance-consultants-societe-conseil.lp.comparateurpro.fr/?utm_source=google&utm_medium=cpc&utm_campaign=test_tns&gclid=TEST123&ltm_source=ADW_tns&ltm_user=42
```
→ lead attendu avec Source `ADW_tns`, campagne `test_tns`, GCLID `TEST123`, user `42`.

## Contrôles QA intégrés (console navigateur)
- `tnsLead.preview()` → enveloppe CRM complète qui serait envoyée
- `tnsLead.googleSheetPreview()` → champs plats Sheets
- `tnsTracking.inspect()` → tracking retenu (après filtrage consentement)
- `TNS_CONFIG.debug = true` (via `window.TNS_CONFIG_OVERRIDE = {debug:true}` avant le chargement) → logs `[tns lead]`

## Checklist de lancement
- [ ] `formId` TNS confirmé/enregistré côté CRM + **lead réel de test visible dans le CRM**
- [ ] Lead de test visible dans la feuille AGV/AMR (colonnes `solution`/`enjeu` correctes, pas de troncature abusive)
- [ ] Aperçu GTM : événements + variables reçus (consentement accepté), conversions OK
- [ ] Test sans consentement : lead transmis **sans** UTM/click IDs, source = `LP CONSULTANTS SOCIETE CONSEIL`
- [ ] Honeypot : champ invisible `website` bien vide pour les humains
- [ ] Si iframe Webflow : embed remplacé (`docs/WEBFLOW_EMBED-TNS.md`) + `publicLandingPath` renseigné + campagne publique reçue après consentement
- [ ] Parcours complet jusqu'à « Merci ! » (+ redirection `ltm_typ` si utilisée)
