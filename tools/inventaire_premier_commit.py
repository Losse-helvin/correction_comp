#!/usr/bin/env python3
"""Compare les dossiers de pages au premier commit et documente le travail restant."""
from pathlib import Path
import subprocess
from collections import Counter
from audit_fonctionnalites import analyse
from inventaire_formulaires import classify

ROOT = Path(__file__).resolve().parent.parent
FIRST = '5b7b2e6'
BASE = '88adabd1fac19b3fbc536460fed64f1920702808'
SPECIAL = 'assurance-estheticiennes-institut-beaute'
PARENT = 'assurance-estheticiennes-instituts-beaute'
GTM_RESTORED = {
    'assurance-agriculteur-v2', 'assurance-assurance-professionnelle-iard-v2',
    'assurance-protection-sociale-collective-v4', 'assurances-multirisques-v2',
    'energie-v2', 'geolocalisation-v2',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').splitlines()


def build():
    initial = {p.split('/')[0] for p in git('ls-tree', '-r', '--name-only', FIRST) if '/' in p}
    changed = {p.split('/')[0] for p in git('diff', '--name-only', FIRST, BASE) if '/' in p}
    rows = []
    for path in sorted(ROOT.glob('*/index.html')):
        r = analyse(path)
        name = r['site']
        history = 'Ajouté après premier commit' if name not in initial else ('Modifié après premier commit' if name in changed else 'Inchangé au premier commit')
        if name == SPECIAL:
            status = 'Capture spécifique corrigée dans cette branche ; validation réelle requise'
        elif name == PARENT:
            status = 'Page parente iframe : relais corrigé ; parcours réel à valider'
        elif r['complete']:
            if name not in changed and name in initial:
                status = f"Capture équipée dans cette branche ; formId {r['form_id']} ; validation réelle requise"
            else:
                status = 'Capture équipée précédemment ; validation réelle requise'
        elif r['phone_forms']:
            status = f"Capture téléphone à adapter ({len(r['phone_forms'])} formulaire(s))"
            if r['gtm'] == ['GTM-53SH7D7F']:
                status += '; GTM de référence installé, configuration à valider'
        elif r['iframes']:
            status = 'Iframe à examiner : ' + ', '.join(r['iframes'])
        elif not r['page'].forms:
            status = 'Aucun formulaire HTML détecté ; rôle à vérifier'
        else:
            types = sorted(set(classify(f) for f in r['page'].forms))
            status = 'Autre formulaire ou étape à qualifier : ' + ', '.join(types)
        if name in GTM_RESTORED:
            status += '; chargeur GTM d’origine rétabli uniquement — configuration et réception à vérifier'
        rows.append((name, history, status, r))
    counts = Counter(h for _, h, _, _ in rows)
    pending = [r for n, _, _, r in rows if n != SPECIAL and r['phone_forms'] and not r['complete']]
    out = [
        '# Réexamen des dossiers depuis le premier commit', '',
        f"Référence historique : premier commit `{FIRST}`, état comparé `{BASE[:7]}` (après fusion des PR précédentes). La colonne historique ne reflète pas les modifications locales en cours ; celles-ci sont décrites dans la colonne statut.", '',
        f"Sur **{len(rows)} dossiers avec `index.html`**, {counts['Inchangé au premier commit']} étaient inchangés depuis le premier commit à l’état comparé, {counts['Modifié après premier commit']} avaient été modifiés et {counts['Ajouté après premier commit']} avaient été ajoutés après celui-ci. Les dossiers techniques `tests` et `tools` ne sont pas des pages.", '',
        '**Travail effectué précédemment :** correction de `assurance-estheticiennes-institut-beaute` et de son parent iframe `assurance-estheticiennes-instituts-beaute`. La page de capture conserve son formulaire, ses questions, ses destinations et son `formId` existant `ADW_LP_ASSURANCE_CONSULTANT` ; cet identifiant atypique doit être confirmé auprès du CRM. Le code émet la conversion et montre le succès uniquement après confirmation CRM CORS ou Google Sheets, pas nécessairement les deux.', '',
        '**Six pages supplémentaires** ont uniquement récupéré leur conteneur GTM identifié dans leur rapport d’origine : `assurance-agriculteur-v2`, `assurance-assurance-professionnelle-iard-v2`, `assurance-protection-sociale-collective-v4`, `assurances-multirisques-v2`, `energie-v2` et `geolocalisation-v2`. Le Consent Mode par défaut précède le chargeur ; les tags configurés dans les conteneurs et la réception effective doivent être contrôlés. Cette intervention ne rend pas leurs formulaires conformes et ne prouve aucune livraison de lead.', '',
        f"**Pages de capture concernées : {27 - len(pending)} sur 27 adaptées selon l’inventaire statique ; {len(pending)} restent à adapter.** L’utilisateur a défini pour chaque page `ADW-` suivi du nom du dossier comme formId et les URL CRM et Google Sheets des LP de référence ; ces configurations sont renseignées dans `CONFIGURATIONS-CRM-A-COMPLETER.csv`. Les pages à formulaires multiples disposent d’une vérification SMS et d’un état de soumission par formulaire. Le chargeur `GTM-53SH7D7F` de référence a été installé sur ces 27 pages après le Consent Mode par défaut ; les tags configurés et leur déclenchement doivent être vérifiés. Cette installation ne valide ni le SMS ni le CRM, Sheets ou les conversions. Les autres pages de l’inventaire comprennent notamment des remerciements et des étapes de qualification à examiner individuellement.", '',
        'Le code corrigé retire le simulateur local de faux succès, vérifie les réponses et la fraîcheur des requêtes SMS, filtre la catégorie URL selon le consentement et rétablit GTM `GTM-53SH7D7F` d’après le rapport de conversion. Le relais iframe ne fait confiance qu’à `https://www.comparateurpro.fr` et au domaine canonique de la page parente ; son déploiement, le chemin de l’iframe, les CORS et son fonctionnement réel doivent être vérifiés sur le domaine final.', '',
        'Les tests utilisent des réponses simulées : aucune réception réelle SMS, CRM, Sheets ou GTM n’a été vérifiée. Le mode CRM `no-cors` ne confirme pas la réception et peut entraîner des doublons si Sheets échoue et que l’utilisateur réessaie. La réponse SMS JSON non vide peut encore être acceptée sans indicateur positif explicite : contrat API réel à confirmer.', '',
        '## Pages avec téléphone encore à adapter', '',
    ]
    out += [f"- `{r['site']}` ({len(r['phone_forms'])} formulaire(s) détecté(s))" for r in pending] if pending else ['Aucune parmi les 27 pages de capture ciblées. La validation en conditions réelles reste indispensable.']
    out += ['', '## Détail de tous les dossiers de pages', '',
            'L’historique est basé sur la comparaison Git du **dossier entier** ; l’analyse des formulaires et des iframes est statique et ne couvre pas les formulaires injectés dynamiquement.', '',
            '| Dossier | Historique avant ce travail | Statut et action |', '|---|---|---|']
    for name, history, status, _ in rows:
        safe = status.replace('|', r'\|').replace('\n', ' ')
        out.append(f'| [`{name}`]({name}/index.html) | {history} | {safe} |')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    output = ROOT / 'RAPPORT-PREMIER-COMMIT.md'
    output.write_text(build(), encoding='utf-8')
    print(output)
