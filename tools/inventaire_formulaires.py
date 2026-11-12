#!/usr/bin/env python3
"""Inventaire statique indicatif des formulaires des pages exportées.

L'identification des formulaires métier doit être confirmée manuellement :
les champs dynamiques, les scripts et les iframes ne sont pas analysés.
"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent.parent


def normalise(value):
    value = unicodedata.normalize('NFKD', value or '')
    return re.sub(r'[^a-z0-9]', '', value.encode('ascii', 'ignore').decode().lower())


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.form = None
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.form = {'id': attrs.get('id') or '', 'name': attrs.get('name') or '',
                         'class': attrs.get('class') or '', 'fields': []}
            self.forms.append(self.form)
        elif tag == 'iframe':
            self.iframes.append(attrs.get('src') or '')
        elif self.form is not None and tag in ('input', 'select', 'textarea'):
            self.form['fields'].append({'name': attrs.get('name') or '',
                                        'type': (attrs.get('type') or '').lower(),
                                        'id': attrs.get('id') or '',
                                        'autocomplete': attrs.get('autocomplete') or ''})

    def handle_endtag(self, tag):
        if tag == 'form':
            self.form = None


def classify(form):
    fields = form['fields']
    names = [normalise(f['name']) for f in fields if f['type'] != 'hidden']
    ids = [normalise(f['id']) for f in fields]
    classes = form['class'].lower().split()
    if any(x in ids for x in ('essentialstoggle', 'analyticstoggle', 'marketingtoggle')):
        return 'préférences cookies'
    if any(x.startswith('w-commerce') for x in classes):
        return 'commerce / à vérifier'
    phone = any(n.startswith(('telephone', 'phone', 'mobile', 'tlphone')) for n in names)
    phone |= any(f['type'] == 'tel' and not normalise(f['name']).startswith(('codepostal', 'postal', 'zip')) for f in fields)
    email = any(n.startswith(('mail', 'email', 'courriel')) for n in names)
    email |= any(f['type'] == 'email' for f in fields)
    if phone:
        return 'téléphone détecté / à vérifier'
    if email:
        return 'e-mail sans téléphone détecté / à vérifier'
    return 'sans coordonnées détectées / à qualifier'


def cell(value):
    return (value or '—').replace('|', r'\|').replace('\n', ' ')


def build_report(root=ROOT):
    pages = sorted(root.glob('*/index.html'))
    rows, counts = [], Counter()
    for path in pages:
        parser = PageParser()
        parser.feed(path.read_text(encoding='utf-8', errors='replace'))
        counts['pages'] += 1
        counts['pages_forms'] += bool(parser.forms)
        counts['forms'] += len(parser.forms)
        counts['pages_iframe'] += bool(parser.iframes)
        for form in parser.forms:
            kind = classify(form)
            counts[kind] += 1
            names = list(dict.fromkeys(f['name'] for f in form['fields'] if f['name']))
            rows.append((path.parent.name, form['id'] or form['name'], kind, ', '.join(names)))
    out = ['# Inventaire statique des formulaires', '',
           'Généré par `python3 tools/inventaire_formulaires.py`. Détection indicative : '
           'elle ne vérifie ni les formulaires injectés en JavaScript, ni les contenus des iframes, '
           'ni le chemin de soumission, le consentement ou les destinations réelles.', '',
           f"- Pages `*/index.html` : **{counts['pages']}**",
           f"- Pages avec au moins un formulaire HTML : **{counts['pages_forms']}**",
           f"- Formulaires HTML : **{counts['forms']}**",
           f"- Pages avec iframe : **{counts['pages_iframe']}**", '']
    for kind in ('téléphone détecté / à vérifier', 'e-mail sans téléphone détecté / à vérifier',
                 'préférences cookies', 'commerce / à vérifier', 'sans coordonnées détectées / à qualifier'):
        out.append(f'- {kind} : **{counts[kind]}**')
    out += ['', 'Un téléphone détecté ne signifie pas nécessairement un formulaire de lead. '
            'Un formulaire sans téléphone peut être une étape de qualification ; ne pas le neutraliser automatiquement.', '',
            '| Page | ID ou nom du formulaire | Classement indicatif | Noms de champs HTML |',
            '|---|---|---|---|']
    out += ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows]
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    target = ROOT / 'INVENTAIRE-FORMULAIRES.md'
    target.write_text(build_report(), encoding='utf-8')
    print(target)
