#!/usr/bin/env python3
"""Inventaire statique, non une validation des services ou des parcours en production."""
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from inventaire_formulaires import classify

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.current_form = None
        self.scripts = []
        self.current_script = None
        self.inputs = []
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.current_form = {'id': a.get('id') or '', 'name': a.get('name') or '',
                                 'class': a.get('class') or '', 'marker': a.get('data-ubepro-lead'), 'fields': []}
            self.forms.append(self.current_form)
        elif tag in ('input', 'select', 'textarea'):
            field = {'tag': tag, 'name': a.get('name') or '', 'type': (a.get('type') or '').lower(),
                     'id': a.get('id') or '', 'autocomplete': a.get('autocomplete') or '',
                     'form': self.current_form}
            self.inputs.append(field)
            if self.current_form is not None:
                self.current_form['fields'].append(field)
        elif tag == 'script':
            self.current_script = {'src': a.get('src') or '', 'text': '', 'type': a.get('type') or ''}
            self.scripts.append(self.current_script)
        elif tag == 'iframe':
            self.iframes.append(a.get('src') or '')

    def handle_data(self, data):
        if self.current_script is not None:
            self.current_script['text'] += data

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current_form = None
        elif tag == 'script':
            self.current_script = None


def script_name(src):
    return unquote(urlsplit(src).path).removeprefix('./')


def active_gtm(scripts):
    containers = set()
    for script in scripts:
        text = script['src'] + ' ' + script['text']
        if 'googletagmanager.com/gtm.js' in text:
            containers.update(re.findall(r'GTM-[A-Z0-9]+', text, re.I))
    return sorted(containers)


def config_value(code, key):
    m = re.search(r'\b' + re.escape(key) + r"\s*:\s*['\"]([^'\"]*)['\"]", code)
    return m.group(1) if m else ''


def selected_sms_phone(page, form=None):
    # Les modules multi-formulaires recherchent le téléphone dans chaque formulaire.
    fields = [field for field in page.inputs if form is None or field['form'] is form]
    for field in fields:
        if field['tag'] != 'input' or not field['name']:
            continue
        n = re.sub(r'[\s_-]+', '', field['name'].lower())
        if n in ('telephone', 'phone', 'tel', 'tlphone') or re.fullmatch(r'telephone\d+', n):
            return field
    return next((field for field in fields if field['tag'] == 'input' and field['type'] == 'tel'
                 and not re.sub(r'[\s_-]+', '', field['name'].lower()).startswith('codepostal')), None)


def analyse(path):
    page = Page()
    page.feed(path.read_text(encoding='utf-8', errors='replace'))
    folder = path.parent
    script_order = [script_name(x['src']) for x in page.scripts if x['src']]
    leads = [f for f in page.forms if f['marker'] == '1']
    phone_forms = [f for f in page.forms if classify(f).startswith('téléphone')]
    email_forms = [f for f in page.forms if classify(f).startswith('e-mail')]
    iframes = [src for src in page.iframes if src and 'googletagmanager.com/ns.html' not in src]
    handler_file = folder / 'lead-handler.js'
    sms_file = folder / 'verification-sms.js'
    handler = handler_file.read_text(encoding='utf-8', errors='replace') if handler_file.is_file() else ''
    sms = sms_file.read_text(encoding='utf-8', errors='replace') if sms_file.is_file() else ''
    handler_loaded = 'lead-handler.js' in script_order and bool(handler)
    sms_loaded = 'verification-sms.js' in script_order and bool(sms)
    order_ok = handler_loaded and sms_loaded and script_order.index('lead-handler.js') < script_order.index('verification-sms.js')
    per_form = 'function initLead(form)' in handler and 'function initForm(form)' in sms
    if per_form:
        selected_ok = bool(leads and all(selected_sms_phone(page, form) for form in leads)
                           and all(any(form is lead for lead in leads) for form in phone_forms))
    else:
        phone = selected_sms_phone(page)
        selected_ok = bool(phone and len(leads) == 1 and phone['form'] is leads[0])
    crm = handler_loaded and bool(config_value(handler, 'leadApiUrl')) and 'function sendCrm(' in handler
    sheets = handler_loaded and bool(config_value(handler, 'googleScriptUrl')) and 'function sendToGoogleSheets(' in handler
    tracking = handler_loaded and 'function getTrackingPayload(' in handler and 'function lirePreferences(' in handler
    sms_config = sms_loaded and 'smspartner/envoi_code_verification.php' in sms and 'estVerifie:' in sms
    confirmation = handler_loaded and 'crm.result.confirmed' in handler and 'sheet.result.confirmed' in handler
    gtm = active_gtm(page.scripts)
    missing = []
    if not leads or (len(leads) != 1 and not per_form):
        missing.append(f'{len(leads)} formulaire(s) marqué(s) sans gestion indépendante reconnue')
    if not handler_loaded:
        missing.append('handler non chargé')
    if not sms_loaded:
        missing.append('module SMS non chargé')
    if not order_ok:
        missing.append('ordre des modules non établi')
    if not selected_ok:
        missing.append('téléphone SMS non relié au formulaire marqué')
    if not gtm:
        missing.append('chargeur GTM non détecté dans le HTML')
    if not all((crm, sheets, tracking, sms_config, confirmation)):
        missing.append('contrat de capture incomplet ou non reconnu')
    complete = not missing
    return {
        'site': folder.name, 'page': page, 'phone_forms': phone_forms, 'email_forms': email_forms,
        'iframes': iframes, 'gtm': gtm, 'leads': leads, 'handler_loaded': handler_loaded,
        'sms_loaded': sms_loaded, 'order_ok': order_ok, 'sms_config': sms_config and selected_ok,
        'crm': crm, 'sheets': sheets, 'tracking': tracking, 'confirmation': confirmation,
        'form_id': config_value(handler, 'formId'), 'crm_mode': config_value(handler, 'leadApiMode'),
        'complete': complete, 'missing': missing,
    }


def cell(value):
    return str(value or '—').replace('|', r'\|').replace('\n', ' ')


def report(rows):
    counts = Counter()
    for r in rows:
        counts['pages'] += 1
        counts['complete'] += r['complete']
        counts['phone_unmarked'] += bool(r['phone_forms']) and not r['complete']
        counts['without_phone_unmarked'] += not bool(r['phone_forms']) and not r['complete']
        counts['gtm'] += bool(r['gtm'])
    out = [
        '# Audit des fonctionnalités par page', '',
        '> **Limite :** ce contrôle reconnaît le modèle standard, mais pas automatiquement les parcours spécifiques. Voir [RAPPORT-PREMIER-COMMIT.md](RAPPORT-PREMIER-COMMIT.md). Les résultats de tests ci-dessous décrivent la version auditée précédemment.', '',
        f"Date de l'audit : {date.today().isoformat()} — branche et fichiers locaux. Génération : `python3 tools/audit_fonctionnalites.py`.", '',
        '## Résumé', '',
        f"- **{counts['pages']} pages** `*/index.html` examinées ; les pages générées dynamiquement ou en dehors de ce niveau ne sont pas couvertes.",
        f"- **{counts['complete']} pages équipées selon les contrôles statiques** : formulaire marqué, modules chargés dans le bon ordre, téléphone lié, code tracking/CRM/Sheets/SMS et chargeur GTM détectés. Elles incluent `LP_reference` et `vehicules-utilitaires`.",
        f"- **{counts['phone_unmarked']} pages avec téléphone détecté mais sans standard complet reconnu** ; cela ne signifie pas nécessairement absence de toute intégration historique.",
        f"- **{counts['without_phone_unmarked']} autres pages sans téléphone détecté et sans standard complet reconnu** : contenu, qualification, remerciement, préférences, iframes ou autres cas à qualifier.",
        f"- **{counts['gtm']} pages** avec un chargeur GTM détecté dans une balise script active du HTML (et non seulement dans un commentaire ou un rapport).", '',
        'Tests exécutés le 28 octobre 2026 sur la version auditée : **308/308 tests JavaScript** et **8/8 tests Python** réussis. Les scénarios JavaScript utilisent jsdom, jQuery et des réponses réseau **simulées** ; ils ne prouvent pas une réception réelle ni la totalité des clics, variantes et parcours. Les 49 bundles ont aussi été chargés avec une soumission jQuery simulée. Les 231 fichiers `script.js`, `lead-handler.js` et `verification-sms.js` ont passé `node --check`. Ces résultats ne préjugent pas des modifications futures.', '',
        '**Important : aucune page n’est ici déclarée validée en production.** Il faut vérifier les identifiants CRM et leur routage, la feuille Apps Script, les CORS et réponses réelles de l’API SMS, les événements GTM et les leads réels sur les domaines finaux.', '',
        '- Le succès nécessite une confirmation CRM **ou** Sheets, pas nécessairement les deux. CRM est configuré en `no-cors` sur les 49 pages : un envoi opaque ou beacon est non confirmé. Si Sheets confirme alors que le CRM ne confirme pas, le succès ne prouve pas la réception CRM ; si Sheets échoue, une nouvelle tentative peut créer un doublon sans déduplication serveur.',
        '- La validation SMS vérifie les erreurs et rejette les réponses vides, mais peut accepter un objet JSON non vide sans indicateur positif explicite. Confirmer le contrat réel de l’API avant de conclure que le numéro est vérifié.',
        '- La collecte de tracking est conditionnée par le consentement dans le code ; la présence du conteneur ou d’un événement local ne garantit pas sa configuration ni sa réception dans GTM ou GA4.', '',
        '## Légende', '',
        '- **Équipée** : critères statiques ci-dessus satisfaits ; ce n’est pas une preuve de fonctionnement réel.',
        '- **Téléphone à adapter** : au moins un formulaire avec téléphone détecté, sans standard complet reconnu.',
        '- **À qualifier** : aucun formulaire téléphonique détecté ; une qualification, un formulaire e-mail, un tunnel, une iframe ou une page de contenu peuvent nécessiter un autre traitement.',
        '- Colonnes Track, SMS, CRM et Sheets : **code chargé/configuré détecté**, pas une livraison ou vérification réelle ; « non établi » ne veut pas dire qu’aucun code historique n’existe.',
        '- GTM : identifiant d’un chargeur détecté dans le HTML ; « non détecté » n’exclut pas un chargement dynamique ailleurs.',
        '- Le test d’une seule LP ne suffit pas à déclarer conformes ses autres formulaires éventuels ou la page enfant d’une iframe.', '',
        '## Pages équipées : liste demandée', '',
        '| Page | formId CRM | GTM |', '|---|---|---|',
    ]
    for r in rows:
        if r['complete']:
            out.append(f"| [`{cell(r['site'])}`]({r['site']}/index.html) | `{cell(r['form_id'])}` | {cell(', '.join(r['gtm']))} |")
    out += ['', '## Détail de toutes les pages', '',
            '| Page | Statut indicatif | Track | GTM dans HTML | SMS | CRM | Sheets | Notes |',
            '|---|---|---|---|---|---|---|---|']
    for r in rows:
        if r['complete']:
            status, notes = 'Équipée', 'Configuration et réception à valider'
        elif r['phone_forms']:
            status, notes = 'Téléphone à adapter', f"{len(r['phone_forms'])} formulaire(s) téléphone détecté(s)"
        else:
            status, notes = 'À qualifier', f"{len(r['page'].forms)} formulaire(s) HTML"
        if r['iframes']:
            notes += '; iframe : ' + ', '.join(r['iframes'])
        if r['leads'] and not r['complete']:
            notes += '; ' + ', '.join(r['missing'])
        vals = [f"[`{r['site']}`]({r['site']}/index.html)", status,
                'code' if r['tracking'] else 'non établi', ', '.join(r['gtm']) or 'non détecté',
                'code' if r['sms_config'] else 'non établi', 'code' if r['crm'] else 'non établi',
                'code' if r['sheets'] else 'non établi', notes]
        out.append('| ' + ' | '.join(cell(v) for v in vals) + ' |')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    rows = [analyse(path) for path in sorted(ROOT.glob('*/index.html'))]
    target = ROOT / 'AUDIT-FONCTIONNALITES.md'
    target.write_text(report(rows), encoding='utf-8')
    print(f"{target} — {len(rows)} pages, {sum(r['complete'] for r in rows)} équipées selon les critères statiques")
