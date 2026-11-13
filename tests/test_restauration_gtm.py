import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from audit_fonctionnalites import Page, active_gtm

PAGES = {
    'assurance-assurance-professionnelle-iard-v2': 'GTM-WMVZJKS',
    'assurance-protection-sociale-collective-v4': 'GTM-53SH7D7F',
    'assurances-multirisques-v2': 'GTM-WMVZJKS',
    'energie-v2': 'GTM-WMVZJKS',
    'geolocalisation-v2': 'GTM-WMVZJKS',
}


PAGES_SANS_GTM = json.loads((ROOT / 'tests' / 'pages-sans-gtm.json').read_text(encoding='utf-8'))
CONTENEURS = json.loads((ROOT / 'tests' / 'gtm-conteneurs.json').read_text(encoding='utf-8'))


def html_pages():
    return sorted(p for p in ROOT.rglob('*.html')
                  if '.git' not in p.parts and 'node_modules' not in p.parts)


def gtm_state(path):
    """Conteneurs du chargeur, du noscript, et tous les ID présents dans le fichier."""
    text = path.read_text(encoding='utf-8', errors='replace')
    page = Page()
    page.feed(text)
    page.close()
    noscript = sorted({m for src in page.iframes if 'googletagmanager.com/ns.html' in src
                       for m in re.findall(r'GTM-[A-Z0-9]+', src)})
    loaders = sum(1 for s in page.scripts
                  if 'googletagmanager.com/gtm.js' in s['src'] + ' ' + s['text'])
    return {'script': active_gtm(page.scripts), 'noscript': noscript, 'loaders': loaders,
            'ids': sorted(set(re.findall(r'GTM-[A-Z0-9]+', text)))}


class RestoredGtmTests(unittest.TestCase):
    def test_identifiant_et_ordre_consentement(self):
        for site, expected in PAGES.items():
            with self.subTest(site=site):
                folder = ROOT / site
                html = (folder / 'index.html').read_text(encoding='utf-8')
                page = Page()
                page.feed(html)
                self.assertEqual(active_gtm(page.scripts), [expected])
                self.assertIn(expected, (folder / 'rapport-site.md').read_text(encoding='utf-8'))
                consent = re.search(r"gtag\(['\"]consent['\"],\s*['\"]default", html)
                loader = html.index('https://www.googletagmanager.com/gtm.js')
                self.assertIsNotNone(consent)
                self.assertLess(consent.start(), loader)
                self.assertEqual(html.count('https://www.googletagmanager.com/gtm.js'), 1)

    def test_pages_sans_gtm_sans_chargeur_ni_evenements(self):
        self.assertEqual(len(PAGES_SANS_GTM), 99)
        for site in PAGES_SANS_GTM:
            with self.subTest(site=site):
                folder = ROOT / site
                html = (folder / 'index.html').read_text(encoding='utf-8')
                page = Page()
                page.feed(html)
                self.assertEqual(active_gtm(page.scripts), [])
                self.assertNotIn('googletagmanager.com/gtm.js', html)
                self.assertNotIn('googletagmanager.com/ns.html', html)
                self.assertNotIn('GTM-', html)
                handler = folder / 'lead-handler.js'
                if handler.exists():
                    code = handler.read_text(encoding='utf-8')
                    self.assertNotIn('pushLeadEvents', code)
                    self.assertNotIn('formulaire_lead', code)
                    self.assertNotIn('formulaire_micro_entrepreneur', code)
                script_path = folder / 'script.js'
                if script_path.exists():
                    script = script_path.read_text(encoding='utf-8')
                    self.assertNotIn('cookie_preferences_updated', script)
                # Certains gabarits poussaient la conversion depuis script.js,
                # sans lead-handler.js : les deux fichiers doivent être propres.
                for name in ('script.js', 'lead-handler.js', 'verification-sms.js'):
                    module = folder / name
                    if not module.exists():
                        continue
                    code = module.read_text(encoding='utf-8')
                    for marker in ('formulaire_lead', 'formulaire_micro_entrepreneur',
                                   'pushLeadEvents', 'googletagmanager.com'):
                        self.assertNotIn(marker, code, f'{site}/{name}')


GROUPE_1 = [
    'LP_reference', 'agriculteur', 'assurance/agriculteur',
    'assurance/assurance-professionnelle-iard-cookie', 'assurance/multirisques',
    'assurance/professionnelle-iard', 'assurance/protection-sociale-collective',
    'assurance/protection-sociale-collective-v4', 'assurance/rc-pro',
    'assurance-agriculteur', 'assurance-agriculteur-v2',
    'assurance-assurance-professionnelle-iard-cookie',
    'assurance-consultant-societe-conseil-v2', 'assurance-consultants-societe-conseil',
    'assurance-consultants-societe-conseil - Copie',
    'assurance-estheticienne-institut-beaute',
    'assurance-estheticiennes-institut-beaute',
    'assurance-estheticiennes-instituts-beaute',
    'assurance-estheticiennes-instituts-beaute-v1', 'assurance-iard-v2',
    'assurance-multirisques', 'assurance-professionnelle-iard',
    'assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw',
    'assurance-protection-sociale-collective',
    'assurance-protection-sociale-collective-v4', 'assurance-rc-pro',
    'assurance-tns', 'assurance-tns-pro-v2-adw', 'assurances-professionnelles',
    'protection-sociale-collective', 'solutions-agv-amr', 'vehicules-utilitaires',
]


class GroupeUnTests(unittest.TestCase):
    """Instruction GTM : chargeur dans <head>, noscript juste après <body>,
    et evenement formulaire_lead a la validation du formulaire."""

    def test_chargeur_dans_le_head_et_noscript_apres_body(self):
        self.assertEqual(len(GROUPE_1), 32)
        for site in GROUPE_1:
            with self.subTest(site=site):
                html = (ROOT / site / 'index.html').read_text(encoding='utf-8')
                state = gtm_state(ROOT / site / 'index.html')
                self.assertEqual(state['script'], ['GTM-53SH7D7F'])
                self.assertEqual(state['noscript'], ['GTM-53SH7D7F'])
                self.assertEqual(state['loaders'], 1)
                bas = html.lower()
                self.assertLess(bas.index('googletagmanager.com/gtm.js'), bas.index('</head>'),
                                'chargeur hors du <head>')
                self.assertGreater(bas.index('ns.html'), bas.index('<body'),
                                   'noscript avant <body>')

    def test_evenement_formulaire_lead_present(self):
        for site in GROUPE_1:
            with self.subTest(site=site):
                dossier = ROOT / site
                sources = [dossier / 'index.html']
                sources += [p for p in dossier.rglob('*.js') if 'node_modules' not in p.parts]
                pousse = any('formulaire_lead' in p.read_text(encoding='utf-8', errors='replace')
                             for p in sources if p.is_file())
                self.assertTrue(pousse, 'aucun formulaire_lead pousse')

    def test_wrapper_estheticiennes_relaie_la_conversion(self):
        parent = (ROOT / 'assurance-estheticiennes-instituts-beaute' / 'script.js').read_text(encoding='utf-8')
        enfant = (ROOT / 'assurance-estheticiennes-institut-beaute' / 'script.js').read_text(encoding='utf-8')
        self.assertIn("'lead-submitted'", parent)
        self.assertIn("event: 'formulaire_lead'", parent)
        self.assertIn("parentBridgePost({ type: 'lead-submitted' })", enfant)


class ContainerPolicyTests(unittest.TestCase):
    """Règles du fichier GTM_PAR_GROUPE.md : un seul conteneur par page,
    GTM-WMVZJKS réservé aux pages listées, GTM-53SH7D7F partout ailleurs."""

    def test_un_seul_conteneur_par_page(self):
        for path in html_pages():
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                state = gtm_state(path)
                self.assertLessEqual(len(state['ids']), 1, 'plusieurs conteneurs sur la même page')
                self.assertLessEqual(state['loaders'], 1, 'plusieurs chargeurs GTM')
                self.assertEqual(state['script'], state['ids'], 'ID présent hors chargeur')
                if state['noscript']:
                    self.assertEqual(state['noscript'], state['script'],
                                     'le noscript ne pointe pas vers le conteneur du script')

    def test_conteneur_conforme_au_groupe(self):
        attendu = set(CONTENEURS['GTM-WMVZJKS'])
        for path in html_pages():
            state = gtm_state(path)
            if not state['ids']:
                continue
            site = path.parent.relative_to(ROOT).as_posix()
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                cible = 'GTM-WMVZJKS' if site in attendu else CONTENEURS['defaut']
                self.assertEqual(state['script'], [cible])

    def test_groupe_wmvzjks_est_intact(self):
        self.assertEqual(len(CONTENEURS['GTM-WMVZJKS']), 14)
        for site in CONTENEURS['GTM-WMVZJKS']:
            with self.subTest(site=site):
                state = gtm_state(ROOT / site / 'index.html')
                self.assertEqual(state['script'], ['GTM-WMVZJKS'])

    def test_balises_script_equilibrees(self):
        """Retirer un chargeur GTM ne doit pas emporter une balise </script>
        voisine : certains gabarits la placent sur la même ligne que le
        commentaire GTM, ce qui casse tout le HTML qui suit."""
        for path in html_pages():
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding='utf-8', errors='replace')
                ouvrantes = len(re.findall(r'<script[\s>]', text))
                fermantes = len(re.findall(r'</script>', text))
                self.assertEqual(ouvrantes, fermantes)

    def test_vehicules_utilitaires_aligne_sur_le_conteneur_par_defaut(self):
        # Absente du document : elle doit utiliser le conteneur par défaut.
        state = gtm_state(ROOT / 'vehicules-utilitaires' / 'index.html')
        self.assertEqual(state['script'], ['GTM-53SH7D7F'])
        self.assertEqual(state['noscript'], ['GTM-53SH7D7F'])


if __name__ == '__main__':
    unittest.main()
