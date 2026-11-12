#!/usr/bin/env python3
"""Supprime toute trace de « donnee par defaut » dans les LP (demande du 11/11).

Principes :
  - la donnee par defaut reste VIDE : si l'URL n'apporte rien, le champ est vide ;
  - un champ cache qui porte une valeur en dur est vidé ;
  - aucun repli de code ne doit réinjecter une source ou une catégorie inventée.

Ce que fait --apply :
  1. index.html : value="…" des champs caches nommes source / categorie -> value=""
  2. index.html : attribut data-source="…" -> data-source=""
  3. lead-handler.js : suppression de la cle categorieCode des 87 handlers
  4. lead-handler.js : plus de suffixe fabrique ' TYP' dans localStorage
  5. lead-handler.js : initialCategory / textValue('categorie') ne servent plus de
     repli pour la categorie envoyee au CRM
  6. script.js : la valeur litterale 'SOURCE PAR DEFAUT' n'est plus reintroduite

Sauvegardes dans .sauvegarde-defauts/ (exclu de Git). --rollback restaure.

Usage :
  python3 tools/supprimer_defauts.py             # simulation (n'ecrit rien)
  python3 tools/supprimer_defauts.py --apply
  python3 tools/supprimer_defauts.py --rollback
"""
import json
import re
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SAUVEGARDE = RACINE / ".sauvegarde-defauts"
JOURNAL = RACINE / "ANALYSE" / "data" / "journal-suppression-defauts.json"

EXCLUS = {"node_modules", ".git", ".sauvegarde-defauts", ".revision-backup", "tests", "ANALYSE", "tools"}

CHAMPS = ("source", "categorie")


def pages_html():
    for p in sorted(RACINE.rglob("index.html")):
        if any(part in EXCLUS for part in p.relative_to(RACINE).parts):
            continue
        yield p


def handlers():
    for p in sorted(RACINE.rglob("lead-handler.js")):
        if any(part in EXCLUS for part in p.relative_to(RACINE).parts):
            continue
        yield p


# --- regles ------------------------------------------------------------------
def nettoie_html(txt):
    """Vide les valeurs en dur des champs de tracking. Retourne (texte, actions)."""
    actions = []

    def vide_input(m):
        tag = m.group(0)
        nom = re.search(r'name="([^"]*)"', tag)
        val = re.search(r'value="([^"]*)"', tag)
        if not nom or not val or nom.group(1) not in CHAMPS:
            return tag
        if val.group(1).strip() == "":
            return tag
        actions.append(f"champ cache {nom.group(1)} : {val.group(1)!r} -> vide")
        nouveau = tag[: val.start(1)] + "" + tag[val.end(1):]
        return nouveau

    txt = re.sub(r"<input\b[^>]*>", vide_input, txt, flags=re.I)

    def vide_attribut(m):
        actions.append(f"attribut {m.group(1)} : {m.group(2)!r} -> vide")
        return f'{m.group(1)}={m.group(3)}=""'

    txt = re.sub(r'(data-(?:source|categorie))=(["\'])([^"\']*)\2', vide_attribut, txt)
    return txt, actions


def nettoie_handler(txt):
    actions = []

    # 3. cle categoriedCode
    m = re.search(r"\n\s*categorieCode:\s*'[^']*',\s*(//[^\n]*)?", txt)
    if m:
        actions.append("categorieCode supprime")
        txt = txt[: m.start()] + txt[m.end():]

    # 4. suffixe fabrique
    if "' TYP'" in txt:
        txt = txt.replace("localStorage.setItem('source', (data.source || '') + ' TYP');",
                          "localStorage.setItem('source', (data.source || ''));")
        txt = txt.replace("localStorage.setItem('source', data.source + ' TYP');",
                          "localStorage.setItem('source', (data.source || ''));")
        actions.append("suffixe ' TYP' retire")

    # 5. plus de repli sur la categorie presente dans la page ou dans l'URL
    ancien = ("    data.categorie = getCurrentUrlCategory() || textValue('categorie') || tracking.categorie ||\n"
              "      initialCategory || '';")
    if ancien in txt:
        txt = txt.replace(ancien,
                          "    data.categorie = getCurrentUrlCategory() || tracking.categorie || '';")
        actions.append("repli initialCategory / textValue('categorie') retire de la categorie")

    # 6. plus de valeur litterale de remplacement dans la source
    if "'SOURCE PAR DEFAUT'" in txt:
        txt = txt.replace("(k === 'source' && input.value === 'SOURCE PAR DEFAUT')", "false")
        txt = txt.replace("if (input.value === '' || false) input.value = t[k];",
                          "if (input.value === '') input.value = t[k];")
        actions.append("valeur litterale 'SOURCE PAR DEFAUT' neutralisee")

    # 7. la variable de repli de categorie n'a plus d'usage : on la retire
    if "initialCategory" in txt:
        txt = txt.replace(
            "  // Conserver la catégorie métier initiale, sans reprendre une campagne non consentie.\n", ""
        )
        txt = txt.replace(
            "  var initialCategory = categoryField ? String(categoryField.defaultValue || '').trim() : '';\n", ""
        )
        txt = txt.replace(
            "  var initialCategory = categoryField ? String(categoryField.value || '').trim() : '';\n", ""
        )
        if "initialCategory" not in txt:
            actions.append("variable initialCategory (repli de categorie) supprimee")
        else:
            actions.append("ATTENTION : initialCategory encore utilise, non supprime")

    # 8. liste des cles a remplir : plus de cas particulier pour la source
    txt = txt.replace("if (input.value === '' || false) input.value = t[k];",
                      "if (input.value === '') input.value = t[k];")
    return txt, actions


def nettoie_script(txt):
    actions = []
    if "SOURCE PAR DEFAUT" in txt:
        n = txt.count("SOURCE PAR DEFAUT")
        txt = txt.replace("'SOURCE PAR DEFAUT'", "''").replace('"SOURCE PAR DEFAUT"', '""')
        # cas restant : affectation directe de la valeur a un champ
        txt = txt.replace("SOURCE PAR DEFAUT", "")
        actions.append(f"script.js : {n} occurrence(s) de 'SOURCE PAR DEFAUT' supprimee(s)")

    # 9. plus de suffixe fabrique ' TYP' sur la source memorisee
    if "' TYP'" in txt or '" TYP"' in txt:
        n = txt.count("+' TYP'") + txt.count('+" TYP"') + txt.count(" + ' TYP'")
        txt = re.sub(r"\s*\+\s*' TYP'", "", txt)
        txt = re.sub(r'\s*\+\s*" TYP"', "", txt)
        txt = txt.replace("' TYP'", "").replace('" TYP"', "")
        actions.append(f"script.js : suffixe ' TYP' retire ({n} occurrence(s))")

    # 10. repli sur la categorie en dur de la page (script.js autonome)
    for motif, remplacement, libelle in (
        ("      categoryField.value = category || initialCategory;",
         "      categoryField.value = category || '';",
         "categorie : repli sur la valeur en dur retire"),
        ("  var initialCategory = categoryField ? String(categoryField.defaultValue || '').trim() : '';\n",
         "",
         "variable initialCategory supprimee"),
        ("      : initialCategory;", "      : '';", "repli initialCategory retire du CRM"),
    ):
        if motif in txt:
            txt = txt.replace(motif, remplacement)
            actions.append(libelle)
    return txt, actions


def traiter(apply=False):
    journal = {}
    total = {"html": 0, "handlers": 0, "scripts": 0, "actions": 0}

    cibles = [(p, nettoie_html) for p in pages_html()]
    cibles += [(p, nettoie_handler) for p in handlers()]
    cibles += [(p, nettoie_script) for p in sorted(RACINE.rglob("script.js"))
               if not any(part in EXCLUS for part in p.relative_to(RACINE).parts)]

    for chemin, fonction in cibles:
        origine = chemin.read_text(encoding="utf-8", errors="ignore")
        texte, actions = fonction(origine)
        if texte == origine:
            continue
        rel = chemin.relative_to(RACINE).as_posix()
        journal[rel] = actions
        total["actions"] += len(actions)
        total["html" if fonction is nettoie_html else "handlers" if fonction is nettoie_handler else "scripts"] += 1
        print(f"{rel}")
        for a in actions:
            print(f"    - {a}")
        if apply:
            dest = SAUVEGARDE / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(chemin, dest)
            chemin.write_text(texte, encoding="utf-8")

    print("\n--- bilan ---")
    print(f"pages HTML modifiees : {total['html']} actions")
    print(f"handlers modifies    : {total['handlers']}")
    print(f"script.js modifies   : {total['scripts']}")
    print(f"actions au total     : {total['actions']}")
    print("simulation" if not apply else "applique")
    if apply:
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        JOURNAL.write_text(json.dumps(journal, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"journal : {JOURNAL.relative_to(RACINE)}")
    return total


def rollback():
    if not SAUVEGARDE.exists():
        print("aucune sauvegarde : rien a restaurer")
        return
    n = 0
    for sauvegarde in sorted(SAUVEGARDE.rglob("*")):
        if not sauvegarde.is_file():
            continue
        rel = sauvegarde.relative_to(SAUVEGARDE)
        shutil.copy2(sauvegarde, RACINE / rel)
        n += 1
    print(f"{n} fichier(s) restaure(s) depuis {SAUVEGARDE.name}/")


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        rollback()
    else:
        traiter(apply="--apply" in sys.argv)
