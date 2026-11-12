/*************************************************************
 * Code.gs — Réception des leads "Assurance TNS Pro" dans Google Sheets
 * -------------------------------------------------------------
 * INSTALLATION (2 minutes, voir docs/CONFIGURATION-CRM-GOOGLE-SHEET-GTM.md) :
 * 1. Créez un Google Sheet (ex. "Leads Assurance TNS")
 * 2. Menu Extensions > Apps Script, effacez tout, collez ce code
 * 3. (Optionnel) Renseignez EMAIL_NOTIFICATION ci-dessous
 * 4. Déployer > Nouveau déploiement > Application Web
 *    - Exécuter en tant que : Moi
 *    - Qui a accès : Tout le monde
 * 5. Copiez l'URL (.../exec) dans lead-handler.js : googleSheet.url
 *************************************************************/

var SHEET_NAME = 'Leads';
var EMAIL_NOTIFICATION = ''; // ex : 'vous@exemple.fr' (vide = pas d'email)

// Ordre des colonnes (clés envoyées par lead-handler.js)
var CLES = ['date', 'nom', 'prenom', 'email', 'telephone', 'telephone_e164', 'societe',
  'code_postal', 'type_contrat', 'regime', 'auto_entrepreneur', 'nb_salaries',
  'assurances_pro', 'nb_vehicules', 'assureur_actuel', 'societe_existante',
  'consentement', 'source', 'categorie', 'user', 'utm_source', 'utm_medium',
  'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid',
  'fbclid', 'msclkid', 'ttclid', 'page', 'referrer', 'formulaire'];

var ENTETES = ['Date', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Tél. E.164', 'Société',
  'Code postal', 'Type de contrat', 'Régime', 'Auto-entrepreneur', 'Nb salariés',
  'Assurances pro', 'Nb véhicules', 'Assureur actuel', 'Société existante',
  'Consentement', 'Source', 'Catégorie', 'User', 'UTM Source', 'UTM Medium',
  'UTM Campaign', 'UTM Term', 'UTM Content', 'GCLID', 'GBRAID', 'WBRAID',
  'FBCLID', 'MSCLKID', 'TTCLID', 'Page', 'Referrer', 'Formulaire'];

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var data = {};
    if (e && e.postData && e.postData.contents) {
      try { data = JSON.parse(e.postData.contents); } catch (err) { data = e.parameter || {}; }
    } else if (e && e.parameter) {
      data = e.parameter;
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sh.getLastRow() === 0) {
      sh.appendRow(ENTETES);
      sh.setFrozenRows(1);
    }
    var row = CLES.map(function (k) { return nettoyer(data[k]); });
    sh.appendRow(row);

    if (EMAIL_NOTIFICATION) {
      var sujet = 'Nouveau lead Assurance TNS — ' + (data.nom || '') + ' ' + (data.prenom || '');
      var corps = CLES.map(function (k, i) { return ENTETES[i] + ' : ' + (data[k] || ''); }).join('\n');
      MailApp.sendEmail(EMAIL_NOTIFICATION, sujet, corps);
    }
    return repondre({ success: true });
  } catch (err) {
    return repondre({ success: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return ContentService.createTextOutput('OK — endpoint leads Assurance TNS actif. Utilisez POST.');
}

// Anti-injection de formules Sheets (=, +, -, @, |, % en début de cellule)
function nettoyer(v) {
  if (v === null || v === undefined) return '';
  v = String(v);
  return /^[=+\-@|%]/.test(v) ? "'" + v : v;
}

function repondre(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
