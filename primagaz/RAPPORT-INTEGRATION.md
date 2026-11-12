# Intégration de `primagaz`

Formulaire simple et design d’origine conservés ; identité CRM demandée : `ADW-primagaz`. Le CRM, Google Sheets et SMS utilisent les mêmes URL que les LP déjà adaptées. Le GTM existant reste inchangé. Le simulateur local a été retiré et les champs obligatoires gardent leur validation native.

L’envoi est soumis à la vérification SMS et le succès attend une confirmation applicative CRM **ou** Sheets. La réception des deux n’est pas garantie : CRM est en `no-cors` par défaut. Vérifier l’existence et le routage du formId, les CORS et les services réels avant déploiement ; les tests sont simulés.
