# Intégration de `gamme-de-rayonnage-actiflip-v4`

Formulaire et contenu existants conservés ; identifiant CRM demandé `ADW-gamme-de-rayonnage-actiflip-v4` et URL CRM / Google Sheets de référence. Le simulateur local et l’ancien script SMS concurrent ont été retirés. Le conteneur GTM de référence reste à valider.

Les cinq branches principales sont testées en navigation simulée. Trois étapes vides et un bouton de soumission prématuré ont été corrigés. Le parcours d’origine ne demande que le téléphone et le consentement : aucune autre coordonnée n’est inventée. Les réponses conservent libellés et valeurs HTML originales.

L’envoi nécessite un mobile vérifié. Le succès et l’événement GTM ne sont émis qu’après confirmation CRM CORS **ou** Google Sheets (pas nécessairement les deux). Les tests utilisent des services simulés : vérifier l’enregistrement du formId, le contrat et la réception SMS, le stockage des champs supplémentaires dans Sheets, les CORS et les tags GTM en conditions réelles avant publication. Une tentative CRM opaque peut aboutir malgré un échec Sheets et créer un doublon en cas de nouvel essai.
