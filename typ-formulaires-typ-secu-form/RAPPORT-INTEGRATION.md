# Intégration de `typ-formulaires-typ-secu-form`

Formulaire et contenu existants conservés ; identifiant CRM demandé `ADW-typ-formulaires-typ-secu-form` et URL CRM / Google Sheets de référence. Le simulateur local et l’ancien script SMS concurrent ont été retirés. Le conteneur GTM de référence reste à valider.

Ancien panneau SMS conservé mais masqué ; le nouveau contrôle ne partage pas les six champs `code_1`. Le consentement reste obligatoire.

L’envoi nécessite un mobile vérifié. Le succès et l’événement GTM ne sont émis qu’après confirmation CRM CORS **ou** Google Sheets (pas nécessairement les deux). Les tests utilisent des services simulés : vérifier l’enregistrement du formId, le contrat et la réception SMS, le stockage des champs supplémentaires dans Sheets, les CORS et les tags GTM en conditions réelles avant publication. Une tentative CRM opaque peut aboutir malgré un échec Sheets et créer un doublon en cas de nouvel essai.
