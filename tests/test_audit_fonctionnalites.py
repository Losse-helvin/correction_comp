import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from audit_fonctionnalites import Page, active_gtm, selected_sms_phone


class AuditParserTests(unittest.TestCase):
    def test_gtm_dans_commentaire_ignore(self):
        page = Page()
        page.feed('<!-- <script src="https://www.googletagmanager.com/gtm.js?id=GTM-FAUX"></script> -->')
        self.assertEqual(active_gtm(page.scripts), [])

    def test_gtm_actif_detecte(self):
        page = Page()
        page.feed('<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>')
        self.assertEqual(active_gtm(page.scripts), ['GTM-ABC123'])

    def test_selection_telephone_ignore_les_selects(self):
        page = Page()
        page.feed('<select name="telephone"></select><form data-ubepro-lead="1"><input name="telephone_1"></form>')
        self.assertIs(selected_sms_phone(page)['form'], page.forms[0])

    def test_repli_telephone_de_type_tel(self):
        page = Page()
        page.feed('<form><input name="portable" type="tel"></form>')
        self.assertEqual(selected_sms_phone(page)['name'], 'portable')

    def test_selection_independante_par_formulaire(self):
        page = Page()
        page.feed('<form><input name="telephone"></form><form><input name="code_postal" type="tel"><input name="telephone-2"></form>')
        self.assertEqual(selected_sms_phone(page, page.forms[0])['name'], 'telephone')
        self.assertEqual(selected_sms_phone(page, page.forms[1])['name'], 'telephone-2')

    def test_repli_n_utilise_pas_le_code_postal(self):
        page = Page()
        page.feed('<form><input name="code_postal" type="tel"></form>')
        self.assertIsNone(selected_sms_phone(page, page.forms[0]))


if __name__ == '__main__':
    unittest.main()
