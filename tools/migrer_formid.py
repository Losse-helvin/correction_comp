#!/usr/bin/env python3
"""
Migration des identifiants CRM (`formId`) + catégories (cf. categories_codes_sms.xlsx)
sur l'ensemble des landing pages du dépôt.

DEUX CHANTIERS, un seul passage idempotent :

  1. `formId` : suppression du préfixe « ADW_LP_ », remplacé par un identifiant court,
     lisible et unique (TNS, COLLECTIVE, IARD_AGRI, AGV_1, AGV_2, ...).
     Le caractère « ADW » est déjà porté par le champ `source` (défaut = ADW) :
     le répéter dans le formId est redondant.

  2. `categorie` : injection d'un code catégorie par défaut (table categories_codes_sms.xlsx)
     utilisé quand l'URL n'apporte aucune catégorie (campagne mal configurée, trafic direct,
     paramètres perdus). Le code vient de `CONFIG.categorieCode`.

  3. `source` : défaut unifié à `ADW` (au lieu de « LP TNS », « SOURCE PAR DEFAUT »...).

Usage :
    python3 tools/migrer_formid.py            # simulation (aucune écriture)
    python3 tools/migrer_formid.py --apply    # applique
    python3 tools/migrer_formid.py --registre # écrit ANALYSE/data/registre-formid.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# REGISTRE CANONIQUE
# dossier -> (formId, code_categorie, libelle_categorie)
# Le formId est court, en MAJUSCULES, sans préfixe ADW ni LP.
# Le code catégorie vient de categories_codes_sms.xlsx (colonne « Code »).
# ---------------------------------------------------------------------------
REGISTRE: dict[str, tuple[str, int, str]] = {
    # --- Référence / véhicules de société ---
    'LP_reference':                                          ('VEH_SOC', 138, 'Véhicules Professionnels'),
    'vehicules-utilitaires':                                 ('VEH_UTIL', 178, 'Véhicules Utilitaires'),
    'vehicules-de-societe-hd':                               ('VEH_SOC_HD', 227, 'Véhicules RCS'),

    # --- Assurance : IARD / pro (code 117) ---
    'assurance-professionnelle-iard':                        ('IARD', 117, 'Sécurité De Locaux'),
    'assurance/professionnelle-iard':                        ('IARD_2', 117, 'Sécurité De Locaux'),
    'assurance-assurance-professionnelle-iard-cookie':       ('IARD_COOKIE', 117, 'Sécurité De Locaux'),
    'assurance/assurance-professionnelle-iard-cookie':       ('IARD_COOKIE_2', 117, 'Sécurité De Locaux'),
    'assurance-assurance-professionnelle-iard-v2':           ('IARD_V2', 117, 'Sécurité De Locaux'),
    'assurance-iard-v2':                                     ('IARD_3', 117, 'Sécurité De Locaux'),
    'assurance-marchandise':                                 ('MARCHANDISE', 117, 'Sécurité De Locaux'),
    'assurance-rc-pro':                                      ('RC_PRO', 117, 'Sécurité De Locaux'),
    'assurance/rc-pro':                                      ('RC_PRO_2', 117, 'Sécurité De Locaux'),
    'rc-pro-consultant-conseil-adw':                         ('RC_PRO_CONSEIL', 117, 'Sécurité De Locaux'),
    'assurance-commerce':                                    ('COMMERCE', 117, 'Sécurité De Locaux'),
    'assurance-consultants-societe-conseil':                 ('IARD_CONSEIL', 117, 'Sécurité De Locaux'),
    'assurance-consultants-societe-conseil - Copie':         ('IARD_CONSEIL_COPIE', 117, 'Sécurité De Locaux'),
    'assurance-test-telephone':                              ('TEST_TEL', 117, 'Sécurité De Locaux'),
    'securite-professionnels':                               ('SECURITE', 117, 'Sécurité De Locaux'),
    'assurance-estheticienne-institut-beaute':               ('ESTHETICIENNE', 117, 'Sécurité De Locaux'),
    'assurance-estheticiennes-instituts-beaute-v1':          ('ESTHETICIENNE_V1', 117, 'Sécurité De Locaux'),
    'assurances-professionnelles':                           ('ASSURANCES_PRO', 462, 'Assurances'),

    # --- Assurance : TNS / prévoyance / collective (code 462) ---
    'assurance-tns':                                         ('TNS', 462, 'Assurances'),
    'assurance-professionnelle-tns-v2':                      ('TNS_V2', 462, 'Assurances'),
    'assurance-tns-pro-v2-adw':                              ('TNS_PRO', 462, 'Assurances'),
    'assurance-professionnelle-tns-v2/assurance-tns-pro-v2-adw': ('TNS_PRO_2', 462, 'Assurances'),
    'protection-sociale-collective':                         ('COLLECTIVE', 462, 'Assurances'),
    'assurance-protection-sociale-collective':               ('COLLECTIVE_2', 462, 'Assurances'),
    'assurance/protection-sociale-collective':               ('COLLECTIVE_3', 462, 'Assurances'),
    'assurance-protection-sociale-collective-v4':            ('COLLECTIVE_V4', 462, 'Assurances'),
    'assurance/protection-sociale-collective-v4':            ('COLLECTIVE_V4_2', 462, 'Assurances'),
    'tns-prevoyance-v2':                                     ('TNS_PREVOYANCE', 462, 'Assurances'),
    'tns-prevoyance-v2-adw-test':                            ('TNS_PREV_TEST', 462, 'Assurances'),
    'complementaire-retraite-tns-v2':                        ('RETRAITE_TNS', 462, 'Assurances'),

    # --- Assurance agricole (code 117) ---
    'agriculteur':                                           ('IARD_AGRI', 117, 'Sécurité De Locaux'),
    'assurance-agriculteur':                                 ('IARD_AGRI_2', 117, 'Sécurité De Locaux'),
    'assurance/agriculteur':                                 ('IARD_AGRI_3', 117, 'Sécurité De Locaux'),
    'assurance-agriculteur-v2':                              ('IARD_AGRI_V2', 117, 'Sécurité De Locaux'),

    # --- Multirisques (code 117) ---
    'assurance-multirisques':                                ('MULTIRISQUE', 117, 'Sécurité De Locaux'),
    'assurance/multirisques':                                ('MULTIRISQUE_2', 117, 'Sécurité De Locaux'),
    'assurances-multirisques-v2':                            ('MULTIRISQUE_V2', 117, 'Sécurité De Locaux'),

    # --- Manutention (112) / AGV (800) ---
    'still-manutention':                                     ('MANUTENTION', 112, 'Manutention'),
    'solutions-agv-amr':                                     ('AGV_1', 800, 'Manutention Automatisée - AGV'),
    'solutions-industrielles-cles-en-main':                  ('AGV_2', 800, 'Manutention Automatisée - AGV'),
    'solutions-cles':                                        ('AGV_3', 800, 'Manutention Automatisée - AGV'),

    # --- Rayonnage (173) ---
    'gamme-de-rayonnage-actiflip-hd':                        ('RAYONNAGE_HD', 173, 'Rayonnage'),
    'gamme-de-rayonnage-actiflip-v4':                        ('RAYONNAGE_V4', 173, 'Rayonnage'),

    # --- Géolocalisation (127) ---
    'geolocalisation':                                       ('GEOLOC', 127, 'Géolocalisation'),
    'geolocalisation-v2':                                    ('GEOLOC_V2', 127, 'Géolocalisation'),
    'geolocalisation-de-flotte':                             ('GEOLOC_FLOTTE', 127, 'Géolocalisation'),
    'suivi-de-vehicules':                                    ('SUIVI_VEH', 127, 'Géolocalisation'),

    # --- Énergie (192) / Photovoltaïque (135) / PAC (207) ---
    'energie':                                               ('ENERGIE', 192, "Fournisseurs D'énergie"),
    'energie-v2':                                            ('ENERGIE_V2', 192, "Fournisseurs D'énergie"),
    'primagaz':                                              ('PRIMAGAZ', 192, "Fournisseurs D'énergie"),
    'primagaz-v2':                                           ('PRIMAGAZ_V2', 192, "Fournisseurs D'énergie"),
    'primagaz-obtenez-votre-gaz-propane-a-prix-fixe':        ('PRIMAGAZ_PROPANE', 192, "Fournisseurs D'énergie"),
    'panneaux-photovoltaiques-energie-solaire':              ('PHOTOVOLTAIQUE', 135, 'Panneaux Photovoltaïques'),
    'panneaux-photovoltaiques-panneaux-photovoltaique-valider': ('PHOTOVOLTAIQUE_V2', 135, 'Panneaux Photovoltaïques'),
    'form-panneaux-photovoltaiques':                         ('PHOTOVOLTAIQUE_FORM', 135, 'Panneaux Photovoltaïques'),
    'intuis':                                                ('POMPE_CHALEUR', 207, 'Pompes à Chaleur'),

    # --- Télécom (159) ---
    'acces-internet-et-telephonie-pro':                      ('TELECOM', 159, 'Accès Internet Et Téléphonie Pro'),
    'acces-internet-et-telephonie-pro-v2':                   ('TELECOM_V2', 159, 'Accès Internet Et Téléphonie Pro'),
    'paritel':                                               ('PARITEL', 159, 'Accès Internet Et Téléphonie Pro'),
    'paritel-vous-rembourse':                                ('PARITEL_REMBOURS', 159, 'Accès Internet Et Téléphonie Pro'),
    'paritel-vous-rembourse-v2':                             ('PARITEL_REMBOURS_V2', 159, 'Accès Internet Et Téléphonie Pro'),

    # --- Ticket restaurant / cadeaux (215) et carburant (122) ---
    'ticket-restaurant':                                     ('TICKET_RESTO', 215, 'Titres Resto Cartes Cadeau'),
    'ticket-restaurant-':                                    ('TICKET_RESTO_VARIANTE', 215, 'Titres Resto Cartes Cadeau'),
    'ticket-restaurant-v2':                                  ('TICKET_RESTO_V2', 215, 'Titres Resto Cartes Cadeau'),
    'ticket-restaurant-septembre':                           ('TICKET_RESTO_SEPT', 215, 'Titres Resto Cartes Cadeau'),
    'ticket-restaurant-septembre-btp':                       ('TICKET_RESTO_SEPT_BTP', 215, 'Titres Resto Cartes Cadeau'),
    'edenred-ticket-restaurant-juillet-v1':                  ('EDENRED_RESTO', 215, 'Titres Resto Cartes Cadeau'),
    'edenred-kadeos':                                        ('KADEOS', 215, 'Titres Resto Cartes Cadeau'),
    'celebrez-le-noel-des-salaries-avec-kadeos':             ('KADEOS_NOEL', 215, 'Titres Resto Cartes Cadeau'),
    'une-rentree-sous-le-signe-du-pouvoir-d-achat':          ('POUVOIR_ACHAT', 215, 'Titres Resto Cartes Cadeau'),
    'too-good-to-go':                                        ('TOO_GOOD_TO_GO', 215, 'Titres Resto Cartes Cadeau'),
    'cartes-carburant':                                      ('CARBURANT', 122, 'Carte Carburant Badge Télépéage'),

    # --- Encaissement (125) / Sage (200) / Canal (145) ---
    'typ-formulaires-typ-caisses-enregistreuse':             ('ENCAISSEMENT', 125, "Solutions D'encaissement"),
    'sage-gestion-de-la-paie-hd':                            ('SAGE_PAIE', 200, 'Sage'),
    'sage-gestion-de-la-paie-hd-v4':                         ('SAGE_PAIE_V4', 200, 'Sage'),
    'canal':                                                 ('CANAL', 145, 'Offres Canal Pro'),

    # --- Nettoyage (134) ---
    'nettoyage-locaux-professionnels':                       ('NETTOYAGE', 134, 'Nettoyage De Locaux Professionnels'),

    # --- Véhicules : marques et modèles (138 / codes dédiés) ---
    'automobile':                                            ('AUTO', 138, 'Véhicules Professionnels'),
    'alfaromeo-tonale':                                      ('AUTO_ALFA', 138, 'Véhicules Professionnels'),
    'ayvens-france':                                         ('AYVENS', 138, 'Véhicules Professionnels'),
    'dacia-jogger':                                          ('AUTO_DACIA', 138, 'Véhicules Professionnels'),
    'ecomobility':                                           ('ECOMOBILITY', 138, 'Véhicules Professionnels'),
    'fiat-pro':                                              ('FIAT_PRO', 213, 'Fiat Professional'),
    'hyundai-kona-electric-nouvelle-generation':             ('AUTO_HYUNDAI', 138, 'Véhicules Professionnels'),
    'hyundai-tucson':                                        ('AUTO_HYUNDAI_TUCSON', 138, 'Véhicules Professionnels'),
    'lexus-lbx':                                             ('LEXUS', 224, 'Lexus'),
    'lexus-lbx-2':                                           ('LEXUS_2', 224, 'Lexus'),
    'mercedes-benz-mercedes-benz-evito':                     ('MERCEDES_EVITO', 138, 'Véhicules Professionnels'),
    'mercedes-benz-nouvel-ecitan-fourgon':                   ('MERCEDES_ECITAN', 138, 'Véhicules Professionnels'),
    'mercedes-benz-sprinter':                                ('MERCEDES_SPRINTER', 138, 'Véhicules Professionnels'),
    'mitsubishi-fuso':                                       ('FUSO', 221, 'Fuso'),
    'nissan-ariya':                                          ('NISSAN_ARIYA', 138, 'Véhicules Professionnels'),
    'nissan-juke':                                           ('NISSAN_JUKE', 138, 'Véhicules Professionnels'),
    'renault-capture':                                       ('AUTO_RENAULT', 138, 'Véhicules Professionnels'),
    'toyota-gamme-hybride':                                  ('AUTO_TOYOTA', 138, 'Véhicules Professionnels'),
    'voiture-nouveau-range-rover':                           ('RANGE_ROVER', 138, 'Véhicules Professionnels'),
    'voiture-range-rover':                                   ('RANGE_ROVER_2', 138, 'Véhicules Professionnels'),
    'volvo':                                                 ('VOLVO', 138, 'Véhicules Professionnels'),

    # --- Divers / génériques (400 Typ Multicatégories) ---
    'formulaire':                                            ('FORM_GENERIQUE', 400, 'Typ Multicatégories'),
    'formulaire-globale':                                    ('FORM_GLOBAL', 400, 'Typ Multicatégories'),
    'form-vehicules-utilitaires':                            ('FORM_VEH_UTIL', 178, 'Véhicules Utilitaires'),
    'sauvie-defibrillateurs-en-entreprise':                  ('DEFIBRILLATEUR', 400, 'Typ Multicatégories'),
    'typ-formulaires-form-typ-vehicules':                    ('TYP_VEHICULES', 400, 'Typ Multicatégories'),
    'typ-formulaires-typ-energie-form':                      ('TYP_ENERGIE', 400, 'Typ Multicatégories'),
    'typ-formulaires-typ-panneaux-form':                     ('TYP_PANNEAUX', 400, 'Typ Multicatégories'),
    'typ-formulaires-typ-secu-form':                         ('TYP_SECURITE', 400, 'Typ Multicatégories'),
    'typ-formulaires-typ-log-entreprise':                    ('TYP_LOGICIEL', 400, 'Typ Multicatégories'),
}


def handlers() -> list[Path]:
    return sorted(list(ROOT.glob('*/lead-handler.js')) + list(ROOT.glob('*/*/lead-handler.js')))


def patch(text: str, form_id: str, code: int) -> str:
    """Applique les transformations. Idempotent : relancer ne change rien."""
    # 1. formId (toute forme : ADW_LP_X, ADW-x...)
    text = re.sub(r"(formId:\s*)'[^']*'", lambda m: f"{m.group(1)}'{form_id}'", text, count=1)

    # 2. code catégorie par défaut : ajouté juste après la ligne formId si absent
    if 'categorieCode:' not in text:
        text = re.sub(
            r"(formId:\s*'[^']*',[^\n]*\n)",
            lambda m: m.group(1) + f"  categorieCode: '{code}',               // défaut (categories_codes_sms.xlsx)\n",
            text, count=1)

    # 3. source par défaut = ADW
    text = re.sub(r"source:\s*'[^']*',(\s*//[^\n]*)?",
                  "source: 'ADW',                // défaut : canal ADW (cf. brief optimisation)",
                  text, count=1)

    # 4. bloc de constantes de routage (avant TRACKING_DEFS), une seule fois
    if 'var ROUTING_KEYS' not in text:
        text = text.replace('  var TRACKING_DEFS = [',
                            ROUTING_BLOCK.rstrip('\n') + '\n\n  var TRACKING_DEFS = [', 1)

    # 5. repli dans getTrackingPayload, une seule fois
    if 'TRACKING_DEFAULTS[def.key]) result[def.key]' not in text:
        text = text.replace(
            "result[def.key] = trackingKeyGranted(def.key) ? cleanParam(trackingValues[def.key] || '') : '';",
            "result[def.key] = trackingKeyGranted(def.key) ? cleanParam(trackingValues[def.key] || '') : '';\n"
            "      if (!result[def.key] && TRACKING_DEFAULTS[def.key]) result[def.key] = TRACKING_DEFAULTS[def.key];",
            1)

    # 6. categorie : la chaîne de repli finit toujours sur le code par défaut
    text = re.sub(
        r"data\.categorie = analyticsGranted\(\)\n\s*\? \(getCurrentUrlCategory\(\) \|\| textValue\('categorie'\) \|\| tracking\.categorie \|\| ''\)\n\s*: initialCategory;",
        "data.categorie = getCurrentUrlCategory() || textValue('categorie') || tracking.categorie ||\n"
        "      initialCategory || CONFIG.categorieCode;", text)
    variante = "data.categorie = getCurrentUrlCategory() || textValue('categorie') || tracking.categorie || '';"
    if variante in text and 'if (!data.categorie) data.categorie = CONFIG.categorieCode;' not in text:
        text = text.replace(variante,
            variante + "\n    if (!data.categorie) data.categorie = CONFIG.categorieCode;")
    if 'CONFIG.categorieCode' not in text.split('data.coordonnee')[0].split('data.categorie')[-1]:
        text = text.replace(
            "    data.coordonnee = textValue('coordonnee') || '1';",
            "    data.categorie = data.categorie || CONFIG.categorieCode;\n"
            "    data.coordonnee = textValue('coordonnee') || '1';", 1)

    # 7. les 6 constantes de routage partent TOUJOURS (indépendamment du consentement)
    if 'ROUTING_KEYS.forEach' not in text:
        text = text.replace(
            "    if (marketingGranted()) {\n      CLICK_IDS.forEach(function (key) {\n        if (tracking[key]) data[key] = tracking[key];\n      });\n    }\n    return data;",
            "    if (marketingGranted()) {\n      CLICK_IDS.forEach(function (key) {\n        if (tracking[key]) data[key] = tracking[key];\n      });\n    }\n"
            "    /* Constantes de routage : toujours transmises, ind\u00e9pendamment du consentement\n"
            "       (constantes de campagne, pas donn\u00e9es de navigation personnelles). */\n"
            "    ROUTING_KEYS.forEach(function (key) {\n"
            "      if (!data[key] && tracking[key]) data[key] = tracking[key];\n"
            "    });\n    return data;", 1)
    return text


ROUTING_BLOCK = """
  /* ---- Constantes de routage (brief optimisation) ----
     Si l'URL n'apporte rien (campagne mal configurée, trafic direct, paramètres
     perdus), le lead doit QUAND MÊME porter une source, une catégorie et les
     variantes utm/ltm correspondantes. Ce sont des constantes de campagne,
     pas des données de navigation : elles sont donc transmises indépendamment
     du consentement analytics. Aucun click ID, aucune donnée personnelle. */
  var ROUTING_KEYS = ['source', 'categorie', 'utm_source', 'utm_category', 'ltm_source', 'ltm_category'];
  var TRACKING_DEFAULTS = {
    source: 'ADW',
    categorie: CONFIG.categorieCode,
    utm_source: 'ADW',
    utm_category: CONFIG.categorieCode,
    ltm_source: 'ADW',
    ltm_category: CONFIG.categorieCode
  };
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--registre', action='store_true')
    args = ap.parse_args()

    files = handlers()
    manquants = [str(f.parent.relative_to(ROOT)) for f in files if str(f.parent.relative_to(ROOT)) not in REGISTRE]
    if manquants:
        print('⚠ Dossiers absents du registre :')
        for m in manquants:
            print('   ', m)
    dups: dict[str, list[str]] = {}
    for d, (fid, _c, _l) in REGISTRE.items():
        dups.setdefault(fid, []).append(d)
    collisions = {k: v for k, v in dups.items() if len(v) > 1}
    if collisions:
        print('⚠ formId en collision dans le registre :')
        for k, v in collisions.items():
            print('   ', k, '→', v)

    changes = 0
    for f in files:
        rel = str(f.parent.relative_to(ROOT))
        if rel not in REGISTRE:
            continue
        form_id, code, _lib = REGISTRE[rel]
        src = f.read_text(encoding='utf-8')
        out = patch(src, form_id, code)
        # injection du bloc TRACKING_DEFAULTS juste avant TRACKING_DEFS
        if 'TRACKING_DEFAULTS = {' not in out:
            out = out.replace('  var TRACKING_DEFS = [', TRACKING_DEFAULTS_BLOCK.strip('\n') + '\n\n  var TRACKING_DEFS = [', 1)
        if out != src:
            changes += 1
            if args.apply:
                f.write_text(out, encoding='utf-8')

    print(f'{len(files)} handlers examinés · {changes} modifiés'
          + ('' if args.apply else ' (simulation — relancer avec --apply)'))

    if args.registre:
        out = ROOT / 'ANALYSE' / 'data' / 'registre-formid.json'
        out.write_text(json.dumps(
            {d: {'formId': v[0], 'categorie': v[1], 'libelle': v[2]} for d, v in sorted(REGISTRE.items())},
            ensure_ascii=False, indent=1), encoding='utf-8')
        print('→', out.relative_to(ROOT))
        # copie consommée par les tests (contrat formId)
        copy = ROOT / 'tests' / 'registre-formid.json'
        copy.write_text(out.read_text(encoding='utf-8'), encoding='utf-8')
        print('→', copy.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
