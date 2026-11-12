#!/usr/bin/env python3
"""
Révision du 10/11/2026 — deux changements de fond :

  1. TRACKING ET GTM SANS CONSENTEMENT
     - Consent Mode V2 : les 5 signaux passent de `denied` à `granted` par défaut.
     - lead-handler.js : capture et transmission du tracking sans condition de
       consentement. Les click IDs (gclid, fbclid…) qui étaient réservés au
       consentement marketing sont désormais capturés comme les UTM.

     ⚠️ Ceci supprime le blocage avant consentement. C'est un choix explicite du
        métier. Le bandeau cookies et le Consent Mode restent en place (l'utilisateur
        peut toujours refuser APRÈS coup via `gtag('consent','update')`).

  2. SUPPRESSION DES VALEURS PAR DÉFAUT
     Le repli `ADW` / code catégorie de la révision précédente est retiré :
     si l'URL n'apporte rien, le champ reste VIDE.

Usage :
    python3 tools/revision_tracking.py            # simulation
    python3 tools/revision_tracking.py --apply    # applique
    python3 tools/revision_tracking.py --rollback # annule la dernière application
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / '.revision-backup'

# ---------------------------------------------------------------- HTML / GTM
CONSENT_BLOCKS = [
    # variante majoritaire (134 pages)
    (re.compile(r"gtag\('consent',\s*'default',\s*\{.*?\}\);", re.S),
     """gtag('consent', 'default', {
        'ad_storage': 'granted',
        'analytics_storage': 'granted',
        'ad_user_data': 'granted',
        'ad_personalization': 'granted',
        'security_storage': 'granted',
        'wait_for_update': 500
    });"""),
    # variante compacte (1 page)
    (re.compile(r"gtag\('consent',\s*'default',\s*\{.*?\}\);", re.S),
     """gtag('consent', 'default', {
        analytics_storage: 'granted', ad_storage: 'granted',
        ad_user_data: 'granted', ad_personalization: 'granted',
        functionality_storage: 'granted', security_storage: 'granted',
        wait_for_update: 500
      });"""),
]

GTM_LOADER = re.compile(r"<script>\(function\(w,d,s,l,i\)\{.*?\}\)\(window,document,'script','dataLayer','(GTM-[A-Z0-9]+)'\);</script>", re.S)
GTM_LOADER_TMPL = """<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','__ID__');</script>"""
GTM_NOSCRIPT_TMPL = """<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=__ID__" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>"""
GTM_DEFAUT = 'GTM-53SH7D7F'

# ---------------------------------------------------------------- lead-handler
TRACKING_BLOCK = """  /* ---- Constantes de routage (brief optimisation) ----
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

TRACKING_BLOCK_NEW = """  /* ---- Collecte du tracking : SANS CONDITION DE CONSENTEMENT (révision 10/11/2026)
     Le tracking URL (utm_*, ltm_*, click IDs) et son envoi au CRM / Google Sheets /
     GTM s'exécutent désormais quel que soit l'état du consentement. Aucune valeur
     par défaut : si l'URL n'apporte rien, le champ reste vide. */
"""

GATING_REPLACEMENTS = [
    # fonctions de consentement : neutralisées sans les supprimer (le bandeau reste)
    ("  function analyticsGranted() { return preferences.analytics === true; }\n"
     "  function marketingGranted() { return preferences.marketing === true; }\n"
     "  function trackingGranted() { return analyticsGranted() || marketingGranted(); }\n"
     "  function trackingKeyGranted(key) {\n"
     "    return CLICK_IDS.indexOf(key) !== -1 ? marketingGranted() : analyticsGranted();\n"
     "  }",
     "  /* Révision 10/11/2026 : le tracking et le Consent Mode se déclenchent SANS\n"
     "     consentement. Les préférences restent lues (pour l'affichage et pour un refus\n"
     "     a posteriori) mais ne conditionnent plus ni la collecte ni la transmission. */\n"
     "  function analyticsGranted() { return true; }\n"
     "  function marketingGranted() { return true; }\n"
     "  function trackingGranted() { return true; }\n"
     "  function trackingKeyGranted() { return true; }"),
]


def backup(path: Path) -> None:
    rel = path.relative_to(ROOT)
    dest = BACKUP / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(path, dest)


def patch_html(path: Path) -> tuple[str, list[str]]:
    t = path.read_text(encoding='utf-8')
    notes = []
    orig = t

    # 1. Consent Mode : denied -> granted
    m = re.search(r"gtag\('consent',\s*'default',\s*\{.*?\}\);", t, re.S)
    if m and "'denied'" in m.group(0):
        bloc = m.group(0)
        nouveau = (CONSENT_BLOCKS[1][1] if 'analytics_storage:' in bloc and "'denied'" not in bloc.split('analytics_storage')[0]
                   else CONSENT_BLOCKS[0][1])
        t = t.replace(bloc, nouveau, 1)
        notes.append('consent-default -> granted')

    # 2. GTM : ajout du conteneur s'il est absent
    if 'googletagmanager.com/gtm.js' not in t:
        anchor = None
        m2 = re.search(r"gtag\('consent',\s*'default',\s*\{.*?\}\);", t, re.S)
        if m2:
            anchor = m2.end()
        if anchor:
            # fermeture du <script> contenant le consent default
            fin = t.find('</script>', anchor)
            if fin != -1:
                fin += len('</script>')
                inject = ('\n  <!-- Google Tag Manager (révision 10/11/2026 : chargeur ajouté) -->\n  '
                          + GTM_LOADER_TMPL.replace('__ID__', GTM_DEFAUT))
                t = t[:fin] + inject + t[fin:]
                # noscript après <body>
                if 'googletagmanager.com/ns.html' not in t:
                    body = re.search(r'<body[^>]*>', t)
                    if body:
                        t = t[:body.end()] + '\n  ' + GTM_NOSCRIPT_TMPL.replace('__ID__', GTM_DEFAUT) + t[body.end():]
                notes.append('GTM ajouté ' + GTM_DEFAUT)

    return (t, notes) if t != orig else (orig, [])


def patch_handler(path: Path) -> tuple[str, list[str]]:
    t = path.read_text(encoding='utf-8')
    orig = t
    notes = []

    # 1. bloc de constantes : neutralisé (valeurs par défaut supprimées)
    if TRACKING_BLOCK in t:
        t = t.replace(TRACKING_BLOCK, TRACKING_BLOCK_NEW, 1)
        notes.append('valeurs par défaut supprimées')

    # 2. gating du consentement neutralisé
    for avant, apres in GATING_REPLACEMENTS:
        if avant in t:
            t = t.replace(avant, apres, 1)
            notes.append('consentement neutralisé')

    # 3. repli dans getTrackingPayload : supprimé
    ligne = ("      if (!result[def.key] && TRACKING_DEFAULTS[def.key]) "
             "result[def.key] = TRACKING_DEFAULTS[def.key];\n")
    if ligne in t:
        t = t.replace(ligne, '', 1)
        notes.append('repli supprimé')

    # 4. bloc ROUTING_KEYS.forEach : supprimé
    bloc = ("    /* Constantes de routage : toujours transmises, indépendamment du consentement\n"
            "       (constantes de campagne, pas données de navigation personnelles). */\n"
            "    ROUTING_KEYS.forEach(function (key) {\n"
            "      if (!data[key] && tracking[key]) data[key] = tracking[key];\n"
            "    });\n")
    if bloc in t:
        t = t.replace(bloc, '', 1)
        notes.append('bloc ROUTING_KEYS retiré')

    # 5. data.categorie : plus de code par défaut
    t = t.replace(
        "data.categorie = getCurrentUrlCategory() || textValue('categorie') || tracking.categorie ||\n"
        "      initialCategory || CONFIG.categorieCode;",
        "data.categorie = getCurrentUrlCategory() || textValue('categorie') || tracking.categorie ||\n"
        "      initialCategory || '';")
    t = re.sub(r"\n *if \(!data\.categorie\) data\.categorie = CONFIG\.categorieCode;", "", t)
    t = re.sub(r"\n *data\.categorie = data\.categorie \|\| CONFIG\.categorieCode;", "", t)

    return (t, notes) if t != orig else (orig, [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--rollback', action='store_true')
    args = ap.parse_args()

    if args.rollback:
        if not BACKUP.exists():
            print('Aucune sauvegarde.')
            return 1
        n = 0
        for f in BACKUP.rglob('*'):
            if f.is_file():
                rel = f.relative_to(BACKUP)
                (ROOT / rel).write_bytes(f.read_bytes())
                n += 1
        print(f'{n} fichiers restaurés depuis {BACKUP.relative_to(ROOT)}')
        return 0

    journal = {'date': datetime.now().isoformat(timespec='seconds'), 'fichiers': {}}
    n_html = n_js = 0

    for f in sorted(list(ROOT.glob('*/index.html'))):
        out, notes = patch_html(f)
        if notes:
            n_html += 1
            journal['fichiers'][str(f.relative_to(ROOT))] = notes
            if args.apply:
                backup(f)
                f.write_text(out, encoding='utf-8')

    handlers = sorted(list(ROOT.glob('*/lead-handler.js')) + list(ROOT.glob('*/*/lead-handler.js')))
    for f in handlers:
        out, notes = patch_handler(f)
        if notes:
            n_js += 1
            journal['fichiers'][str(f.relative_to(ROOT))] = notes
            if args.apply:
                backup(f)
                f.write_text(out, encoding='utf-8')

    print(f'HTML modifiés : {n_html} · handlers modifiés : {n_js}'
          + ('' if args.apply else ' (simulation — relancer avec --apply)'))
    if args.apply:
        j = ROOT / 'ANALYSE' / 'data' / 'journal-revision-tracking.json'
        j.parent.mkdir(parents=True, exist_ok=True)
        j.write_text(json.dumps(journal, ensure_ascii=False, indent=1), encoding='utf-8')
        print('→', j.relative_to(ROOT))
        print('Annulation possible : --rollback')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
