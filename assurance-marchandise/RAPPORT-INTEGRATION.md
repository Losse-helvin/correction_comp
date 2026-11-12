# Intégration de assurance-marchandise

Formulaire, contenus et identité conservés. L'ancien SMS concurrent et le simulateur local des appels ont été retirés de ce dossier. Les modules `lead-handler.js` et `verification-sms.js` assurent la capture et le SMS ; le succès attend une confirmation applicative.

- Identité CRM : `ADW_LP_ASSURANCE_MARCHANDISE` (à confirmer/enregistrer côté CRM).
- Source de secours : `LP ASSURANCE MARCHANDISE`.
- GTM : `GTM-WMVZJKS` (conteneur retrouvé dans le rapport existant, sinon référence).
- Vérifier la feuille Google et les origines CORS, puis tester un SMS et un lead réels sur le domaine final. Un transport CRM `no-cors` est non confirmé : un nouvel essai après échec de la feuille peut créer un doublon si le CRM ne déduplique pas.

Tests simulés : `npm ci --prefix tests && npm test --prefix tests`. Les mocks ne prouvent pas la livraison réelle.
