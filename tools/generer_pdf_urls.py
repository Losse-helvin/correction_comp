#!/usr/bin/env python3
"""Genere le PDF « URL de chaque LP + form_id » (demande du 10/11).

Source de verite : les fichiers du depot.
  - ANALYSE/data/registre-formid.json  : 146 formId (dossier -> formId)
  - ANALYSE/data/url-formid.json       : 146 URL (dossier -> url, dossier, titre)
  - <dossier>/lead-handler.js          : verifie que le formId est bien celui cable
  - <dossier>/index.html               : verifie la presence du <form> et de la canonical

Sortie : URL-formid-LP.pdf (racine du depot)

Usage :
  python3 tools/generer_pdf_urls.py            # genere le PDF
  python3 tools/generer_pdf_urls.py --verifier # controle seulement, sans PDF
"""
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle, KeepTogether)

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "ANALYSE" / "data"
SORTIE = RACINE / "URL-formid-LP.pdf"

FORMAT_ID = re.compile(r"^[a-z]\d{14}[a-z]$")

# --- polices ---------------------------------------------------------------
FONTES = Path("/usr/share/fonts/truetype/dejavu")
if (FONTES / "DejaVuSans.ttf").exists():
    pdfmetrics.registerFont(TTFont("Sans", str(FONTES / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("Sans-Bold", str(FONTES / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Mono", str(FONTES / "DejaVuSansMono.ttf")))
    pdfmetrics.registerFontFamily(
        "Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold"
    )
    P, PB, PM = "Sans", "Sans-Bold", "Mono"
else:  # repli : polices de base, accents limites
    P, PB, PM = "Helvetica", "Helvetica-Bold", "Courier"

BLEU = colors.HexColor("#1F3A5F")
BLEU_CLAIR = colors.HexColor("#E8EEF6")
GRIS = colors.HexColor("#5A6472")
ROUGE = colors.HexColor("#B3261E")
VERT = colors.HexColor("#1E6B3A")
AMBRE = colors.HexColor("#8A5A00")


# --- collecte --------------------------------------------------------------
def charger():
    reg = json.loads((DONNEES / "registre-formid.json").read_text(encoding="utf-8"))
    inv = json.loads((DONNEES / "url-formid.json").read_text(encoding="utf-8"))
    par_dossier = {x["dossier"]: x for x in inv}
    lignes = []
    for dossier in sorted(reg, key=lambda d: (par_dossier.get(d, {}).get("url") or "zzz" + d)):
        meta = reg[dossier]
        info = par_dossier.get(dossier, {})
        lignes.append(
            {
                "dossier": dossier,
                "form_id": meta["formId"],
                "url": info.get("url", ""),
                "titre": info.get("titre", ""),
                "categorie": meta.get("categorie"),
            }
        )
    return lignes


def verifier(lignes):
    """Controles reels sur le depot. Retourne (controles, statut_par_dossier)."""
    rx_handler = re.compile(r"formId:\s*'([^']+)'")
    rx_data = re.compile(r'data-form-id="([^"]+)"')
    rx_canon = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"')

    ids = [l["form_id"] for l in lignes]
    doublons = sorted({i for i in ids if ids.count(i) > 1})
    hors_format = [l["dossier"] for l in lignes if not FORMAT_ID.match(l["form_id"])]
    sans_url = [l["dossier"] for l in lignes if not l["url"]]

    etats = {}
    for l in lignes:
        dossier = RACINE / l["dossier"]
        handler = dossier / "lead-handler.js"
        index = dossier / "index.html"
        html = index.read_text(encoding="utf-8", errors="ignore") if index.exists() else ""

        cable = ""
        if handler.exists():
            m = rx_handler.search(handler.read_text(encoding="utf-8", errors="ignore"))
            cable = m.group(1) if m else ""
            if cable == l["form_id"]:
                where = "lead-handler.js"
            elif not cable:
                where = "handler sans formId"
            else:
                where = "DIVERGENT"
        elif rx_data.search(html):
            m = rx_data.search(html)
            cable = m.group(1)
            where = "index.html (data-form-id)" if cable == l["form_id"] else "DIVERGENT"
        else:
            where = None  # aucun formId dans le dossier

        canon = rx_canon.search(html)
        canon = canon.group(1) if canon else ""
        l["canonical"] = canon
        l["cable"] = where
        l["a_formulaire"] = bool(re.search(r"<form\b", html, re.I))
        l["url_ok"] = bool(canon) and canon.rstrip("/") == l["url"].rstrip("/") and bool(l["url"])
        l["sous_dossier"] = "/" in l["dossier"]
        # etat du Consent Mode et du module mobile, pour reperer les pages oubliees
        l["consent"] = ("denied" if re.search(r"ad_storage['\"]?\s*:\s*['\"]denied", html)
                        else "granted" if re.search(r"ad_storage['\"]?\s*:\s*['\"]granted", html) else "—")
        l["mobile_ux"] = (dossier / "mobile-ux.js").exists()

        if not l["url"]:
            etats[l["dossier"]] = "URL absente"
        elif where is None:
            etats[l["dossier"]] = "ID non cable"
        elif where == "DIVERGENT":
            etats[l["dossier"]] = "Divergence"
        else:
            etats[l["dossier"]] = "OK"

    controles = {
        "total": len(lignes),
        "uniques": len(set(ids)),
        "doublons": doublons,
        "hors_format": hors_format,
        "sans_url": sans_url,
        "non_cables": [l["dossier"] for l in lignes if l["cable"] is None],
        "cables_ok": sum(1 for l in lignes if l["cable"] not in (None, "DIVERGENT", "handler sans formId")),
        "avec_formulaire": sum(1 for l in lignes if l["a_formulaire"]),
        "canonical_ok": sum(1 for l in lignes if l["url_ok"]),
        "denied": [l["dossier"] for l in lignes if l["consent"] == "denied"],
        "sans_mobile_ux": [l["dossier"] for l in lignes if l["mobile_ux"] is False],
    }

    # URL publiques partagees par plusieurs dossiers (copies ou doublons a arbitrer)
    par_url = {}
    for l in lignes:
        if l["url"]:
            par_url.setdefault(l["url"].rstrip("/"), []).append(l)
    controles["urls_doublons"] = {u: ls for u, ls in par_url.items() if len(ls) > 1}
    controles["urls_distinctes"] = len(par_url)
    return controles, etats


# --- styles ----------------------------------------------------------------
ss = getSampleStyleSheet()
S = {
    "titre": ParagraphStyle("titre", fontName=PB, fontSize=22, leading=27, textColor=BLEU, spaceAfter=4),
    "sous": ParagraphStyle("sous", fontName=P, fontSize=10.5, leading=15, textColor=GRIS),
    "h1": ParagraphStyle("h1", fontName=PB, fontSize=13, leading=17, textColor=BLEU,
                         spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName=PB, fontSize=10, leading=14, textColor=BLEU,
                         spaceBefore=8, spaceAfter=3),
    "corps": ParagraphStyle("corps", fontName=P, fontSize=9.5, leading=14),
    "petit": ParagraphStyle("petit", fontName=P, fontSize=8, leading=11, textColor=GRIS),
    "cell": ParagraphStyle("cell", fontName=P, fontSize=7.4, leading=9.2),
    "cellmono": ParagraphStyle("cellmono", fontName=PM, fontSize=7.6, leading=9.2),
    "cellhead": ParagraphStyle("cellhead", fontName=PB, fontSize=7.6, leading=9.4,
                               textColor=colors.white),
    "cellheadc": ParagraphStyle("cellheadc", fontName=PB, fontSize=7.6, leading=9.4,
                                textColor=colors.white, alignment=TA_CENTER),
    "legende": ParagraphStyle("legende", fontName=P, fontSize=8.2, leading=11.5, textColor=GRIS),
}


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def url_affichage(url, dossier):
    if url:
        return esc(url)
    return f'<font color="#B3261E">(à définir)</font> <font color="#5A6472" size="6.5">dossier /{esc(dossier)}</font>'


# --- document --------------------------------------------------------------
def construit(chemin, lignes, controles, etats):
    doc = BaseDocTemplate(
        str(chemin), pagesize=A4,
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=16 * mm, bottomMargin=15 * mm,
        title="URL et form_id de chaque landing page",
        author="Comparateurpro", subject="Inventaire URL -> form_id",
    )
    cadre = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="corps")

    def pied(canvas, d):
        canvas.saveState()
        canvas.setFont(P, 7.5)
        canvas.setFillColor(GRIS)
        canvas.drawString(doc.leftMargin, 10 * mm, "Comparateurpro — inventaire URL / form_id, 10 novembre 2026")
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"page {canvas.getPageNumber()}")
        canvas.setStrokeColor(colors.HexColor("#D5DBE5"))
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 13 * mm, A4[0] - doc.rightMargin, 13 * mm)
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="std", frames=[cadre], onPage=pied)])
    story = []

    # --- page 1 : couverture ---
    story.append(Paragraph("URL de chaque landing page", S["titre"]))
    story.append(Paragraph("et son <b>form_id</b> — inventaire complet, vérifié sur le dépôt", S["sous"]))
    story.append(Spacer(1, 10))

    tableau_intro = [
        ["Périmètre", f"{controles['total']} landing pages du dépôt"],
        ["Source", "registre-formid.json + url-formid.json + lead-handler.js de chaque dossier"],
        ["Date de génération", "10 novembre 2026"],
    ]
    t = Table(tableau_intro, colWidths=[38 * mm, 140 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), PB), ("FONTNAME", (1, 0), (1, -1), P),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6), ("TEXTCOLOR", (0, 0), (0, -1), BLEU),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # synthèse de vérification
    story.append(Paragraph("Ce que dit la vérification", S["h1"]))
    ok_id = controles["uniques"] == controles["total"] and not controles["hors_format"]
    lignes_synth = [
        (VERT, f"<b>{controles['total']} form_id</b> recensés, <b>{controles['uniques']} uniques</b>, "
               f"{'tous conformes' if not controles['hors_format'] else str(len(controles['hors_format'])) + ' hors format'} "
               f"au format <font face='{PM}'>[a-z]14 chiffres[a-z]</font>."),
        (VERT if controles["cables_ok"] else AMBRE,
         f"<b>{controles['cables_ok']}/{controles['total']}</b> form_id sont réellement câblés dans la page "
         f"(lead-handler.js ou data-form-id) et identiques au registre."),
        (AMBRE if controles["non_cables"] else VERT,
         f"<b>{len(controles['non_cables'])}</b> pages n'ont aucun form_id câblé dans leur code : "
         f"l'identifiant existe au registre mais n'est envoyé par aucun formulaire."),
        (AMBRE if controles["sans_url"] else VERT,
         f"<b>{len(controles['sans_url'])}</b> pages n'ont pas d'URL publique identifiable "
         f"(ni canonical, ni domaine propre) : signalées « à définir » dans la liste."),
        (ROUGE if controles["urls_doublons"] else VERT,
         f"<b>{len(controles['urls_doublons'])}</b> adresses publiques sont portées par plusieurs dossiers : "
         f"sur {controles['total']} lignes, cela ne fait que <b>{controles['urls_distinctes']}</b> URL "
         f"réellement distinctes."),
        (VERT if controles["canonical_ok"] == controles["total"] - len(controles["sans_url"]) else AMBRE,
         f"<b>{controles['canonical_ok']}</b> URL sur {controles['total'] - len(controles['sans_url'])} "
         f"vérifiées contre la balise canonical de la page : identiques."),
        (GRIS, f"<b>{controles['avec_formulaire']}</b> pages contiennent un <font face='{PM}'>&lt;form&gt;</font> ; "
               f"les autres sont des pages de remerciement, de contenu ou des gabarits."),
    ]
    for couleur, texte in lignes_synth:
        p = Paragraph(f'<font color="{couleur.hexval()}">■</font>&nbsp; {texte}', S["corps"])
        story.append(p)
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Forme des URL : chaque page est publiée sur le sous-domaine "
        "<font face='Mono'>&lt;dossier&gt;.lp.comparateurpro.fr</font>, ce qui correspond exactement à la "
        "balise canonical de la page — c'est donc l'adresse de référence, et non la forme courte "
        "<font face='Mono'>comparateur.fr/…</font>.", S["legende"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Les 146 lignes de la liste ci-après reprennent l'inventaire sans rien masquer : une page sans "
        "form_id câblé apparaît avec la mention correspondante, une page sans URL avec « à définir ». "
        "Les points à traiter sont regroupés en fin de document.", S["legende"]))

    story.append(PageBreak())

    # --- liste complète ---
    story.append(Paragraph("Liste complète — URL et form_id", S["h1"]))
    story.append(Paragraph(
        f"{controles['total']} lignes, ordre alphabétique d'URL. Colonne « Câblé » : "
        "emplacement où le form_id est réellement présent dans le code de la page.", S["petit"]))
    story.append(Spacer(1, 6))

    largeurs = [9 * mm, 74 * mm, 40 * mm, 26 * mm, 29 * mm]
    entete = [
        Paragraph("#", S["cellheadc"]),
        Paragraph("URL de la landing page", S["cellhead"]),
        Paragraph("form_id", S["cellhead"]),
        Paragraph("Dossier", S["cellhead"]),
        Paragraph("Câblé", S["cellhead"]),
    ]
    data = [entete]
    for i, l in enumerate(lignes, 1):
        cable = l["cable"]
        if cable is None:
            v = '<font color="#B3261E">non câblé</font>'
        elif cable == "DIVERGENT":
            v = '<font color="#B3261E">divergent</font>'
        elif cable == "handler sans formId":
            v = '<font color="#8A5A00">handler vide</font>'
        else:
            v = '<font color="#1E6B3A">oui</font>'
        data.append([
            Paragraph(str(i), S["cell"]),
            Paragraph(url_affichage(l["url"], l["dossier"]), S["cell"]),
            Paragraph(esc(l["form_id"]), S["cellmono"]),
            Paragraph(esc(l["dossier"]), S["cell"]),
            Paragraph(v, S["cell"]),
        ])

    t = Table(data, colWidths=largeurs, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DBE5")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BLEU),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5F7FA")))
    t.setStyle(TableStyle(style))
    story.append(t)

    story.append(PageBreak())

    # --- points a traiter ---
    story.append(Paragraph("Points à traiter", S["h1"]))

    sans_url = [l for l in lignes if not l["url"]]
    non_cables = [l for l in lignes if l["cable"] is None]
    divergents = [l for l in lignes if l["cable"] == "DIVERGENT"]

    story.append(Paragraph(f"A. {len(sans_url)} pages sans URL publique identifiable", S["h2"]))
    story.append(Paragraph(
        "Ces dossiers n'ont ni balise canonical ni domaine propre dans le code. L'URL de mise en "
        "ligne doit être fournie pour les référencer : sans elle, le form_id existe mais ne peut "
        "être rattaché à aucune adresse de campagne.", S["petit"]))
    story.append(Spacer(1, 4))

    if sans_url:
        rows = [[Paragraph("Dossier", S["cellhead"]), Paragraph("Titre", S["cellhead"]),
                 Paragraph("form_id", S["cellhead"]), Paragraph("Formulaire dans la page", S["cellhead"])]]
        for l in sans_url:
            rows.append([
                Paragraph(esc(l["dossier"]), S["cell"]),
                Paragraph(esc(l["titre"]), S["cell"]),
                Paragraph(esc(l["form_id"]), S["cellmono"]),
                Paragraph("oui" if l["a_formulaire"] else "non", S["cell"]),
            ])
        t = Table(rows, colWidths=[62 * mm, 45 * mm, 40 * mm, 31 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DBE5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t)

    # A bis : une meme URL publiee par plusieurs dossiers
    dbl = controles["urls_doublons"]
    story.append(Paragraph(
        f"A bis. {len(dbl)} adresses publiques portées par plusieurs dossiers", S["h2"]))
    story.append(Paragraph(
        f"Les {controles['total']} lignes de l'inventaire ne correspondent qu'à "
        f"<b>{controles['urls_distinctes']}</b> URL réellement distinctes. Dans les cas ci-dessous, "
        f"deux dossiers — parfois un dossier et sa copie rangée dans un sous-dossier — déclarent la même "
        f"adresse publique avec <b>deux form_id différents</b>. Un seul des deux peut être servi en ligne : "
        f"le second est du code mort, ou une copie à archiver. Cela doit être tranché avant la bascule CRM, "
        f"sinon un même emplacement de campagne peut router vers deux identifiants.", S["petit"]))
    story.append(Spacer(1, 4))
    if dbl:
        rows = [[Paragraph("URL publique", S["cellhead"]), Paragraph("Dossier", S["cellhead"]),
                 Paragraph("form_id", S["cellhead"]), Paragraph("État sur le disque", S["cellhead"])]]
        for url, groupe in sorted(dbl.items()):
            for j, l in enumerate(groupe):
                ds = []
                if l["sous_dossier"]:
                    ds.append("sous-dossier")
                ds.append("handler" if l["cable"] not in (None, "DIVERGENT", "handler sans formId") else "sans form_id")
                if l["consent"] == "denied":
                    ds.append("consentement denied")
                if not l["mobile_ux"]:
                    ds.append("mobile-ux absent")
                rows.append([
                    Paragraph(esc(url) if j == 0 else "", S["cell"]),
                    Paragraph(esc(l["dossier"]), S["cell"]),
                    Paragraph(esc(l["form_id"]), S["cellmono"]),
                    Paragraph(", ".join(ds), S["cell"]),
                ])
        t = Table(rows, colWidths=[56 * mm, 47 * mm, 33 * mm, 42 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DBE5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"B. {len(non_cables)} pages dont le form_id n'est câblé nulle part", S["h2"]))
    story.append(Paragraph(
        "Cas de figure, par ordre de gravité : <b>leads perdus</b> si la page contient un formulaire "
        "actif mais aucun code n'envoie de form_id ; <b>informationnel</b> si la page n'a pas de "
        "formulaire (remerciement, contenu, gabarit). Seules les pages de la première catégorie "
        "demandent une action.", S["petit"]))
    story.append(Spacer(1, 4))

    avec_form = [l for l in non_cables if l["a_formulaire"]]
    sans_form = [l for l in non_cables if not l["a_formulaire"]]

    for titre, groupe, couleur in (
        (f"B1. {len(avec_form)} pages avec formulaire mais sans form_id envoyé — action requise",
         avec_form, ROUGE),
        (f"B2. {len(sans_form)} pages sans formulaire (remerciement, contenu, gabarit) — aucun lead attendu",
         sans_form, GRIS),
    ):
        story.append(Paragraph(f'<font color="{couleur.hexval()}">{esc(titre)}</font>', S["h2"]))
        if not groupe:
            story.append(Paragraph("aucune", S["petit"]))
            continue
        rows = [[Paragraph("Dossier", S["cellhead"]), Paragraph("URL", S["cellhead"]),
                 Paragraph("form_id au registre", S["cellhead"])]]
        for l in groupe:
            rows.append([
                Paragraph(esc(l["dossier"]), S["cell"]),
                Paragraph(url_affichage(l["url"], l["dossier"]), S["cell"]),
                Paragraph(esc(l["form_id"]), S["cellmono"]),
            ])
        t = Table(rows, colWidths=[62 * mm, 74 * mm, 42 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DBE5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    if divergents:
        story.append(Paragraph(f"C. {len(divergents)} pages divergentes", S["h2"]))
        for l in divergents:
            story.append(Paragraph(f"{esc(l['dossier'])} — registre {l['form_id']}, code {l['cable']}", S["petit"]))

    # D : pages reste(e)s hors du train de revision du 10/11
    denied = [l for l in lignes if l["consent"] == "denied"]
    story.append(Paragraph(
        f"D. {len(denied)} pages encore en Consent Mode « denied »", S["h2"]))
    story.append(Paragraph(
        "La révision du 10/11 a basculé 135 pages en <font face='Mono'>granted</font>. Les pages "
        "ci-dessous y ont échappé : ce sont précisément les copies rangées dans un sous-dossier "
        "<font face='Mono'>assurance/</font>, que le script de révision ne balayait qu'à un niveau de "
        "profondeur. Si l'une d'elles est en ligne, le tracking n'y remonte pas comme ailleurs.", S["petit"]))
    story.append(Spacer(1, 4))
    if denied:
        rows = [[Paragraph("Dossier", S["cellhead"]), Paragraph("URL", S["cellhead"]),
                 Paragraph("form_id", S["cellhead"])]]
        for l in denied:
            rows.append([
                Paragraph(esc(l["dossier"]), S["cell"]),
                Paragraph(url_affichage(l["url"], l["dossier"]), S["cell"]),
                Paragraph(esc(l["form_id"]), S["cellmono"]),
            ])
        t = Table(rows, colWidths=[62 * mm, 74 * mm, 42 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BLEU),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DBE5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.append(t)

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Rappel : les form_id sont des clés de routage HelloLead. Tout identifiant absent du CRM "
        "provoque la perte du lead, qu'il soit ou non câblé dans la page.", S["legende"]))

    doc.build(story)


def main():
    lignes = charger()
    controles, etats = verifier(lignes)

    print(f"lignes                 : {controles['total']}")
    print(f"form_id uniques        : {controles['uniques']}")
    print(f"hors format            : {len(controles['hors_format'])}")
    print(f"doublons               : {len(controles['doublons'])}")
    print(f"cablés et conformes    : {controles['cables_ok']}")
    print(f"non câblés             : {len(controles['non_cables'])}")
    print(f"sans URL               : {len(controles['sans_url'])} {controles['sans_url']}")
    print(f"canonical == URL       : {controles['canonical_ok']}")
    print(f"URL distinctes         : {controles['urls_distinctes']} "
          f"({len(controles['urls_doublons'])} adresses partagées)")
    print(f"encore en denied       : {len(controles['denied'])} {controles['denied']}")
    print(f"sans mobile-ux         : {len(controles['sans_mobile_ux'])}")

    if "--verifier" in sys.argv:
        return 0

    construit(SORTIE, lignes, controles, etats)
    print(f"\nPDF écrit : {SORTIE} ({SORTIE.stat().st_size / 1024:.0f} Ko)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
