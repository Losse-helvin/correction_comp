import unittest
from tools.inventaire_formulaires import PageParser, classify, normalise


class InventoryTests(unittest.TestCase):
    def form(self, html):
        parser = PageParser()
        parser.feed(html)
        return parser.forms[0]

    def test_phone_alias_and_postal_code(self):
        self.assertEqual(classify(self.form('<form><input name="T-l-phone"></form>')), 'téléphone détecté / à vérifier')
        self.assertEqual(classify(self.form('<form><input type="tel" name="code_postal"></form>')), 'sans coordonnées détectées / à qualifier')

    def test_cookies_not_lead(self):
        self.assertEqual(classify(self.form('<form><input id="analytics-toggle"><input type="email"></form>')), 'préférences cookies')

    def test_normalization_and_email(self):
        self.assertEqual(normalise('Téléphone-2'), 'telephone2')
        self.assertEqual(classify(self.form('<form><input type="email" name="mail"></form>')), 'e-mail sans téléphone détecté / à vérifier')

    def test_iframe_recorded_without_becoming_form(self):
        parser = PageParser()
        parser.feed('<iframe src="https://example.org"></iframe>')
        self.assertEqual(parser.iframes, ['https://example.org'])
        self.assertEqual(parser.forms, [])

if __name__ == '__main__':
    unittest.main()
