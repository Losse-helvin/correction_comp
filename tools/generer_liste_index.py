#!/usr/bin/env python3
"""Liste « index -> URL -> form_id » dans le format demande par l'utilisateur :

    1-assurance-consultants-societe-conseil --- https://comparateurpro.fr/assurance-consultants-societe-conseil/-------h23751036083219c

Regle d'URL : un domaine unique, chemin = chemin du dossier dans le depot.
  <dossier>/index.html          -> https://comparateurpro.fr/<dossier>/
  <dossier>/<sous>/index.html   -> https://comparateurpro.fr/<dossier>/<sous>/

Sources : le depot lui-meme (146 index.html), le formId etant releve dans le code
(lead-handler.js puis data-form-id) et confronte au registre.

Sorties :
  LISTE-INDEX-FORMID.txt  la liste, un index par ligne, format exact demande
  ANALYSE/data/liste-index-formid.csv  meme contenu, une colonne par champ

Usage : python3 tools/generer_liste_index.py
"""
import csv
import io
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOMAINE = "https://comparateurpro.fr"
SORTIE_TXT = RACINE / "LISTE-INDEX-FORMID.txt"
SORTIE_CSV = RACINE / "ANALYSE" / "data" / "liste-index-formid.csv"

RX_ID = re.compile(r"formId:\s*'([^']+)'")
RX_DATA = re.compile(r'data-form-id="([^"]+)"')
RX_CANON = re.compile(r'<link\s+rel="canonical"\s+href="([^"]*)"')
RX_LOC = re.compile(r"<loc>([^<]+)</loc>")


def slug(chemin):
    """Chemin de dossier -> segment d'URL propre (espaces et majuscules interdits)."""
    s = chemin.replace(" ", "-").replace("_", "-")
    s = re.sub(r"-{2,}", "-", s).lower()
    # pas de strip('-') : le dossier « ticket-restaurant- » doit rester distinct de « ticket-restaurant »
    return s


def collecte():
    reg = json.loads((RACINE / "ANALYSE" / "data" / "registre-formid.json").read_text("utf-8"))
    pages = sorted(list(RACINE.glob("*/index.html"))) + sorted(list(RACINE.glob("*/*/index.html")))
    lignes = []
    for page in pages:
        dossier = page.parent.relative_to(RACINE).as_posix()
        html = page.read_text(encoding="utf-8", errors="ignore")

        cable = ""
        handler = page.parent / "lead-handler.js"
        if handler.exists():
            m = RX_ID.search(handler.read_text(encoding="utf-8", errors="ignore"))
            cable = m.group(1) if m else ""
        if not cable:
            m = RX_DATA.search(html)
            cable = m.group(1) if m else ""

        canon = RX_CANON.search(html)
        sitemap = page.parent / "sitemap.xml"
        loc = RX_LOC.search(sitemap.read_text(encoding="utf-8", errors="ignore")) if sitemap.exists() else None
        lignes.append(
            {
                "dossier": dossier,
                "url": f"{DOMAINE}/{slug(dossier)}/",
                "form_id": reg.get(dossier, {}).get("formId", ""),
                "cable": cable,
                "canonical": canon.group(1) if canon else "",
                "sitemap": loc.group(1) if loc else "",
                "sitemap_ok": (loc is not None and page.parent.name in loc.group(1)),
            }
        )
    lignes.sort(key=lambda l: l["url"])
    return lignes


def main():
    lignes = collecte()

    # --- la liste, au format demande ---
    buf = io.StringIO()
    buf.write("LISTE DES INDEX — URL ET form_id\n")
    buf.write(f"{len(lignes)} index.html, un par ligne.\n")
    buf.write("Format : numero-dossier --- URL-------form_id\n")
    buf.write("=" * 78 + "\n\n")
    for i, l in enumerate(lignes, 1):
        buf.write(f"{i}-{l['dossier']} --- {l['url']}-------{l['form_id']}\n")
    SORTIE_TXT.write_text(buf.getvalue(), encoding="utf-8")

    # --- version tabulaire ---
    SORTIE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["n", "dossier", "url", "form_id", "form_id_cable", "canonical", "sitemap"])
        for i, l in enumerate(lignes, 1):
            w.writerow([i, l["dossier"], l["url"], l["form_id"], l["cable"], l["canonical"], l["sitemap"]])

    # --- controles ---
    ids = [l["form_id"] for l in lignes]
    sans_id = [l["form_id"] for l in ids if not l]
    non_cables = [l for l in lignes if not l["cable"]]
    divergents = [l for l in lignes if l["cable"] and l["cable"] != l["form_id"]]
    canon_lp = [l for l in lignes if ".lp.comparateurpro.fr" in l["canonical"]]
    sm_bad = [l for l in lignes if l["sitemap"] and not l["sitemap_ok"]]
    sm_absent = [l for l in lignes if not l["sitemap"]]

    print(f"index.html trouvés      : {len(lignes)}")
    print(f"form_id renseignés      : {len(ids) - len(sans_id)}")
    print(f"form_id uniques         : {len(set(i for i in ids if i))}")
    print(f"form_id non câblés      : {len(non_cables)}")
    print(f"divergences registre    : {len(divergents)}")
    print(f"canonical en .lp.…      : {len(canon_lp)}/{len(lignes)}")
    print(f"sitemap incohérent      : {len(sm_bad)} {[l['dossier'] for l in sm_bad]}")
    print(f"sitemap absent          : {len(sm_absent)} {[l['dossier'] for l in sm_absent]}")
    print(f"URL distinctes          : {len({l['url'] for l in lignes})}")
    print(f"\nécrit : {SORTIE_TXT.relative_to(RACINE)}")
    print(f"écrit : {SORTIE_CSV.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
