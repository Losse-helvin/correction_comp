import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from audit_fonctionnalites import Page, active_gtm

PAGES = {
    'assurance-agriculteur-v2': 'GTM-53SH7D7F',
    'assurance-assurance-professionnelle-iard-v2': 'GTM-WMVZJKS',
    'assurance-protection-sociale-collective-v4': 'GTM-53SH7D7F',
    'assurances-multirisques-v2': 'GTM-WMVZJKS',
    'energie-v2': 'GTM-WMVZJKS',
    'geolocalisation-v2': 'GTM-WMVZJKS',
}


REFERENCE_PAGES = [
    'alfaromeo-tonale', 'assurance-test-telephone', 'assurances-professionnelles',
    'ayvens-france', 'cartes-carburant', 'dacia-jogger', 'edenred-kadeos',
    'formulaire-globale', 'gamme-de-rayonnage-actiflip-hd', 'gamme-de-rayonnage-actiflip-v4',
    'intuis', 'lexus-lbx', 'lexus-lbx-2', 'mitsubishi-fuso', 'paritel',
    'paritel-vous-rembourse', 'primagaz', 'primagaz-obtenez-votre-gaz-propane-a-prix-fixe',
    'rc-pro-consultant-conseil-adw', 'renault-capture', 'sage-gestion-de-la-paie-hd',
    'sauvie-defibrillateurs-en-entreprise', 'toyota-gamme-hybride', 'typ-formulaires-typ-secu-form',
    'voiture-nouveau-range-rover', 'voiture-range-rover', 'volvo',
]


class RestoredGtmTests(unittest.TestCase):
    def test_conteneur_reference_des_formulaires_restants(self):
        self.assertEqual(len(REFERENCE_PAGES), 27)
        for site in REFERENCE_PAGES:
            with self.subTest(site=site):
                folder = ROOT / site
                html = (folder / 'index.html').read_text(encoding='utf-8')
                page = Page()
                page.feed(html)
                self.assertEqual(active_gtm(page.scripts), ['GTM-53SH7D7F'])
                consent = re.search(r"gtag\(['\"]consent['\"],\s*['\"]default", html)
                self.assertIsNotNone(consent)
                self.assertLess(consent.start(), html.index('https://www.googletagmanager.com/gtm.js'))
                self.assertEqual(html.count('https://www.googletagmanager.com/gtm.js'), 1)


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


if __name__ == '__main__':
    unittest.main()
