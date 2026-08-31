"""
matrice_couverture.py — ÉTAPE 1, TÂCHE C.

Construit la matrice « caractéristique × jeu » à partir de l'inventaire
(out/etape1/inventaire_corpus.csv) et des artefacts du harnais
(tests/reference/<jeu>/), puis confronte cette observation au corpus.csv
rempli de mémoire.

D6 : rien n'est comblé. Une caractéristique qu'aucun jeu n'exerce est NOMMÉE
dans la section NON COUVERT, elle n'est pas fabriquée.

Sorties :
  out/etape1/matrice_couverture.csv
  docs/etape1_ecarts_corpus.md
"""
from __future__ import annotations

import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

import pandas as pd

from _commun import ICI, RACINE, decouvrir, ecrire_csv, ecrire_texte, nom_point

OUT = RACINE / "out" / "etape1"
DOCS = RACINE / "docs"
INVENTAIRE = OUT / "inventaire_corpus.csv"

# Seuil de lacune interne : un intervalle supérieur à N fois le pas modal.
# 3 est le seuil que la version en service utilise elle-même pour couper ses
# tracés (core.inserer_lacunes / segments_valides, argument seuil_pas=3).
SEUIL_LACUNE = 3

# Certaines cases vides ne sont pas des trous du corpus : elles sont
# INATTEIGNABLES par construction du code. Les confondre avec un manque de
# couverture ferait chercher un jeu de test qui ne pourrait jamais exercer la
# branche. Motif nomme, ligne a l'appui.
INATTEIGNABLES = {
    "encodage utf-8":
        "sniff.ENCODAGES commence par utf-8-sig (sniff.py:19), qui decode "
        "aussi bien l'UTF-8 sans BOM : la branche « utf-8 » n'est jamais "
        "atteinte",
    "encodage cp1252":
        "latin-1 precede cp1252 dans sniff.ENCODAGES (sniff.py:19) et ne leve "
        "jamais : la branche cp1252 n'est jamais atteinte",
    "encodage utf-8(replace)":
        "le repli errors=replace (sniff.py:156) suppose que toute la cascade a "
        "echoue ; latin-1 ne peut pas echouer",
}


def charger_inventaire():
    return pd.read_csv(INVENTAIRE, sep=";", dtype=str, keep_default_na=False)


def charger_artefacts(jeu: str):
    d = ICI / jeu
    art = {}
    for nom in ("00_format_detecte.json", "01_colonnes_retenues.json"):
        p = d / nom
        art[nom] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    for nom in ("02_effectifs.csv", "03_journees_ecartees.csv",
                "05_anomalies.csv", "06_coefficients.csv", "07_t_norm.csv",
                "08_scores.csv"):
        p = d / nom
        art[nom] = (pd.read_csv(p, sep=";", dtype=str, keep_default_na=False)
                    if p.exists() else pd.DataFrame())
    return art


# ============================================================
# Caractéristiques
# ============================================================
def caracteristiques(inv: pd.DataFrame, jeux):
    """
    Retourne un OrderedDict {famille: {caracteristique: {jeu: valeur}}}.
    Une valeur vide signifie « non exercé par ce jeu ».
    """
    noms = [j["jeu"] for j in jeux]
    M = OrderedDict()

    def poser(famille, carac, jeu, valeur):
        M.setdefault(famille, OrderedDict()).setdefault(
            carac, {n: "" for n in noms})[jeu] = valeur

    def compter(famille, carac, sous_inv, etiquette=lambda r: "oui"):
        for jeu in noms:
            sel = sous_inv[sous_inv.jeu == jeu]
            if len(sel):
                poser(famille, carac, jeu, f"{len(sel)} fichier(s)")
            else:
                poser(famille, carac, jeu, "")

    fichiers = inv[inv.role.isin(["eau", "air", "debit"])]

    # --- Séparateur ---
    LISIBLE = {"';'": "point-virgule", "','": "virgule", "'\t'": "tabulation",
               "'|'": "barre verticale", "n/a": "sans objet (fichier Excel)"}
    for sep in sorted(set(fichiers.separateur) - {""}):
        # Le libelle ne doit pas contenir le separateur du CSV produit.
        lbl = LISIBLE.get(sep, sep.replace(";", "point-virgule"))
        compter("separateur", f"separateur : {lbl}",
                fichiers[fichiers.separateur == sep])
    poser_absent(M, noms, "separateur",
                 "separateur : virgule detecte par sniff (hors parseur debit)")
    poser_absent(M, noms, "separateur", "separateur : tabulation")
    poser_absent(M, noms, "separateur", "separateur : barre verticale")

    # --- Encodage ---
    for enc in sorted(set(fichiers.encodage) - {"", "n/a"}):
        compter("encodage", f"encodage {enc}", fichiers[fichiers.encodage == enc])
    for enc in ("utf-8", "cp1252", "utf-8(replace)"):
        if enc not in set(fichiers.encodage):
            poser_absent(M, noms, "encodage", f"encodage {enc}")
    for bom in sorted(set(fichiers.bom) - {"", "n/a"}):
        compter("encodage", f"BOM : {bom}", fichiers[fichiers.bom == bom])
    for fdl, lbl in (("CRLF", "fins de ligne CRLF"), ("LF", "fins de ligne LF seul")):
        sel = fichiers[fichiers.fins_de_ligne.str.startswith(fdl)
                       if fdl == "LF" else
                       fichiers.fins_de_ligne.str.contains("CRLF")]
        compter("encodage", lbl, sel)

    # --- Format de fichier ---
    compter("format", "fichier CSV", fichiers[fichiers.extension == ".csv"])
    compter("format", "fichier Excel", fichiers[fichiers.extension == ".xlsx"])
    poser_absent(M, noms, "format", "fichier Excel ancien (.xls, moteur xlrd)")
    poser_absent(M, noms, "format", "fichier Excel a macros (.xlsm)")
    multi = fichiers[pd.to_numeric(fichiers.n_feuilles, errors="coerce").fillna(0) > 1]
    compter("format", "classeur Excel multi-feuilles", multi)
    decale = fichiers[pd.to_numeric(fichiers.ligne_entete_detectee,
                                    errors="coerce").fillna(0) > 0]
    compter("format", "ligne d'en-tete decalee (hdr > 0)", decale)
    compter("format", "chronique d'air au format Excel",
            fichiers[(fichiers.role == "air") & (fichiers.extension == ".xlsx")])

    # --- Colonnes ---
    ch = fichiers[fichiers.colonne_heure_separee.str.contains("RECOMPOSEE")]
    compter("colonnes", "colonne d'heure separee, RECOMPOSEE par V4.5", ch)
    cnr = fichiers[fichiers.colonne_heure_separee.str.contains("NON recomposee")]
    compter("colonnes", "colonne d'heure separee detectee mais NON recomposee", cnr)
    # Colonne d'heure presente dans le fichier mais hors de la regle startswith.
    def _heure_perdue(r):
        if r.role != "eau" or r.colonne_heure_separee != "non":
            return False
        retenue = str(r.colonne_date_retenue_v45).lower()
        for col in str(r.entetes).split(" | "):
            c = col.strip().lower()
            if not c or c == retenue:
                continue
            if ("heure" in c or "hour" in c or c.startswith("h_")
                    or c.endswith("_heure")):
                return True
        return False
    perdue = fichiers[fichiers.apply(_heure_perdue, axis=1)]
    compter("colonnes", "colonne d'heure presente mais NON reconnue (regle "
                        "startswith de io_data.py:79)", perdue)
    compter("colonnes", "en-tetes contenant le separateur de colonnes",
            fichiers[fichiers.entetes.str.contains(",")])
    compter("colonnes", "en-tetes vides / fantomes (colonne sans nom)",
            fichiers[fichiers.entetes.str.contains(" | nan", regex=False)])
    compter("colonnes", "deux colonnes de temperature (unites differentes)",
            fichiers[fichiers.entetes.str.contains(r"°F|, .F", regex=True)])
    compter("colonnes", "vocabulaire SANDRE (DtAnaTemp / RsAnaTemp)",
            fichiers[fichiers.entetes.str.contains("AnaTemp")])
    compter("colonnes", "valeurs entourees de guillemets",
            inv[inv.fichier.isin(_avec_guillemets(inv))])

    # --- Decimales ---
    compter("decimales", "virgule decimale",
            fichiers[fichiers.separateur_decimal.str.contains("virgule")])
    compter("decimales", "point decimal",
            fichiers[fichiers.separateur_decimal.str.contains("point")])
    compter("decimales", "valeur deja numerique (Excel, sans forme textuelle)",
            fichiers[fichiers.separateur_decimal.str.contains("deja numerique")])
    compter("decimales", "virgule decimale dans la chronique d'air",
            fichiers[(fichiers.role == "air")
                     & fichiers.separateur_decimal.str.contains("virgule")])

    # --- Formats de date ---
    tous_formats = set()
    for s in fichiers.formats_date:
        for morceau in s.split("++")[0].split(" | "):
            m = re.match(r"^(.*?) x\d+$", morceau.strip())
            if m:
                # Les valeurs non reconnues sont regroupees sous un seul
                # libelle : chacune porte un exemple different, ce qui ferait
                # autant de lignes que de valeurs distinctes.
                lbl = ("valeur non reconnue par les motifs de l'inventaire"
                       if m.group(1).startswith("non reconnu") else m.group(1))
                tous_formats.add(lbl)
    for fmt in sorted(tous_formats):
        motif = ("non reconnu" if fmt.startswith("valeur non reconnue")
                 else re.escape(fmt))
        sel = fichiers[fichiers.formats_date.str.contains(motif, regex=True)]
        compter("date", f"format de date : {fmt}", sel)
    for absent in ("YYYY-MM-DD (sans heure)", "DD/MM/YYYY HH:MM (sans secondes)",
                   "date en anglais (Jan, Feb...)", "serie Excel numerique brute",
                   "horodatage avec fuseau explicite (+02:00) dans la valeur"):
        poser_absent(M, noms, "date", f"format de date : {absent}")

    # --- Pas de mesure ---
    for role, lbl in (("eau", "eau"), ("air", "air"), ("debit", "debit")):
        sel = fichiers[fichiers.role == role]
        for pas in sorted(set(sel.pas_modal_s) - {""}, key=lambda x: int(x)):
            compter("pas", f"pas modal {pas} s ({_h(pas)}) — {lbl}",
                    sel[sel.pas_modal_s == pas])
    irr = fichiers[(fichiers.pas_median_s != "") &
                   (fichiers.pas_median_s != fichiers.pas_modal_s)]
    compter("pas", "pas irregulier (median != modal)", irr)
    # Un pas MODAL unique masque les changements de cadence en cours de
    # chronique : la couverture se lit sur les intervalles reellement presents.
    for sec, lbl in ((900, "15 min"), (1800, "30 min"), (7200, "2 h"),
                     (21600, "6 h"), (86400, "1 j")):
        sel = fichiers[fichiers.apply(
            lambda r: _present(r.get("pas_observes", ""), sec), axis=1)]
        compter("pas", f"intervalle de {lbl} ({sec} s) reellement present "
                       f"(>= 5 occurrences)", sel)
    poser_absent(M, noms, "pas",
                 "chronique d'eau livree deja agregee au jour par la source "
                 "(et non par perte de la colonne d'heure)")

    # --- Contenu air ---
    for marque in ("TM", "TN", "TX", "RR"):
        compter("air", f"colonne {marque} presente dans le fichier d'air",
                fichiers[(fichiers.role == "air")
                         & (fichiers[f"presence_{marque}"] == "oui")])
    poser_absent(M, noms, "air", "fichier d'air SANS TN ni TX")
    poser_absent(M, noms, "air", "export Meteo-France MULTI-stations "
                                 "(stations_air non vide)")

    # --- Debit ---
    compter("debit", "chronique de debit fournie", fichiers[fichiers.role == "debit"])
    for jeu in noms:
        j = next(x for x in jeux if x["jeu"] == jeu)
        poser("debit", "debit desinfluence fourni", jeu, "")
    poser_absent(M, noms, "debit", "debit desinfluence fourni")
    poser_absent(M, noms, "debit", "normales pre-calculees (EcartNormales.csv) "
                                   "fournies — branche fichier_normales")

    return M, noms


def poser_absent(M, noms, famille, carac):
    M.setdefault(famille, OrderedDict()).setdefault(
        carac, {n: "" for n in noms})


def _present(pas_observes, secondes, mini=5):
    """L'intervalle `secondes` figure-t-il vraiment dans la chronique ?"""
    for morceau in str(pas_observes).split(" | "):
        m = re.match(r"^(\d+)s x(\d+)$", morceau.strip())
        if m and int(m.group(1)) == secondes and int(m.group(2)) >= mini:
            return True
    return False


def _h(secondes):
    s = int(secondes)
    if s % 86400 == 0:
        return f"{s // 86400} j"
    if s % 3600 == 0:
        return f"{s // 3600} h"
    if s % 60 == 0:
        return f"{s // 60} min"
    return f"{s} s"


def _avec_guillemets(inv):
    """Fichiers dont les valeurs sont entourees de guillemets, releve sur les
    extraits bruts deja produits."""
    src = DOCS / "etape1_extraits_bruts.md"
    if not src.exists():
        return []
    txt = src.read_text(encoding="utf-8")
    out = []
    for bloc in txt.split("## `")[1:]:
        nom = bloc.split("`", 1)[0]
        corps = bloc.split("```")[1] if "```" in bloc else ""
        lignes = [l for l in corps.splitlines() if l.strip()][1:4]
        if lignes and all(l.lstrip().startswith('"') for l in lignes):
            out.append(nom)
    return out


# ============================================================
# Caractéristiques déduites du harnais
# ============================================================
def caracteristiques_harnais(M, noms, jeux):
    for j in jeux:
        jeu = j["jeu"]
        art = charger_artefacts(jeu)
        eff = art["02_effectifs.csv"]
        ecart = art["03_journees_ecartees.csv"]
        coef = art["06_coefficients.csv"]
        sc = art["08_scores.csv"]
        anom = art["05_anomalies.csv"]

        n_points = len(j["points"])
        M.setdefault("harnais", OrderedDict())
        _p(M, noms, "nombre de points du jeu", jeu, str(n_points))

        # Points dont la chaine echoue (D7)
        fmt = art["00_format_detecte.json"]
        echecs = [f["point"] for f in fmt if f.get("statut") == "ECHEC"]
        _p(M, noms, "point(s) sur lesquels V4.5 echoue (D7)", jeu,
           f"{len(echecs)} : {', '.join(echecs)}" if echecs else "")

        # Points sans donnee exploitable en sortie
        sans = set(echecs)          # un echec ne produit aucun indicateur
        if len(eff):
            tot = eff[eff.annee == "-1"]
            vides = tot[pd.to_numeric(tot.journees_retenues_apres_fusion,
                                      errors="coerce").fillna(0) == 0]
            sans |= set(vides.point)
        _p(M, noms, "point(s) sans aucun indicateur exploitable "
                    "(echec de chaine ou zero journee retenue)", jeu,
           f"{len(sans)}/{n_points} : {', '.join(sorted(sans))}" if sans else "")

        # Lacunes internes de la chronique retenue
        if len(anom):
            n_lac, pire = 0, 0
            for pt, sub in anom.groupby("point"):
                d = pd.to_datetime(sub["date"]).sort_values()
                trous = d.diff().dt.days.dropna()
                lac = trous[trous > SEUIL_LACUNE]
                n_lac += int((lac > 1).sum())
                pire = max(pire, int(trous.max()) if len(trous) else 0)
            _p(M, noms, f"lacunes internes > {SEUIL_LACUNE} j dans la serie "
                        f"retenue", jeu,
               f"{n_lac} lacune(s), la plus longue {pire} j" if n_lac else "")
        else:
            _p(M, noms, f"lacunes internes > {SEUIL_LACUNE} j dans la serie "
                        f"retenue", jeu, "")

        # Journees ecartees dont le motif n'est pas recuperable
        if len(ecart):
            nr = ecart[ecart.motif == "NON_RECUPERABLE"]
            _p(M, noms, "journees ecartees a motif NON_RECUPERABLE", jeu,
               f"{len(nr)} journee(s)" if len(nr) else "")
            for etape in sorted(set(ecart.etape)):
                n = int((ecart.etape == etape).sum())
                _p(M, noms, f"journees ecartees a l'etape « {etape} »", jeu,
                   f"{n} journee(s)")
            motifs = sorted({m.split("(")[0].split("—")[0].strip()
                             for m in ecart[ecart.etape == "controle_qualite"].motif})
            for m in motifs:
                n = int(ecart[(ecart.etape == "controle_qualite")
                              & ecart.motif.str.startswith(m)].shape[0])
                _p(M, noms, f"motif QC exerce : « {m} »", jeu, f"{n} journee(s)")
        else:
            _p(M, noms, "journees ecartees a motif NON_RECUPERABLE", jeu, "")

        # Repli du m saisonnier
        if len(coef):
            ms = coef[coef.grandeur == "m_saisonnier_fraie"]
            rep = ms[ms.diagnostic.str.contains("estival_repli")]
            _p(M, noms, "repli du m saisonnier sur le m estival "
                        "(core.py:250 ou 258)", jeu,
               f"{len(rep)} / {len(ms)} appel(s)" if len(ms) else "")
            nrm = coef[coef.grandeur == "normales"]
            sous = nrm[nrm.diagnostic.str.contains("Fiabilite reduite|Fiabilité réduite")]
            _p(M, noms, "normales calculees sur moins de 20 annees de reference",
               jeu, f"{len(sous)} / {len(nrm)} point(s)" if len(nrm) else "")
        # Deux definitions de T normalisee reellement produites
        tn = art["07_t_norm.csv"]
        if len(tn):
            g = sorted({x.split("[")[0] for x in tn.grandeur})
            _p(M, noms, "series de temperature normalisee produites", jeu,
               ", ".join(g))
        # Doublons d'horodatage (releve d'inventaire, repris ici par jeu)
        # Chevauchement de series sur un meme point
        codes = [nom_point(p) for p in j["points"]]
        base = [re.sub(r"__NA$|_regroup$", "", c) for c in codes]
        dbl = sorted({c for c in base if base.count(c) > 1})
        _p(M, noms, "chevauchement de series sur un meme point "
                    "(plusieurs fichiers pour un meme code)", jeu,
           ", ".join(dbl) if dbl else "")
    return M


def _p(M, noms, carac, jeu, valeur):
    M.setdefault("harnais", OrderedDict()).setdefault(
        carac, {n: "" for n in noms})[jeu] = valeur


# ============================================================
# Écriture
# ============================================================
def ecrire_matrice(M, noms, chemin: Path):
    colonnes = (["famille", "caracteristique"] + noms
                + ["couverture", "nature_du_trou"])
    lignes = []
    for famille, caracs in M.items():
        for carac, par_jeu in caracs.items():
            n = sum(1 for v in par_jeu.values() if v)
            lignes.append(dict(
                famille=famille, caracteristique=carac,
                **{k: v for k, v in par_jeu.items()},
                couverture=("NON COUVERT" if n == 0
                            else f"{n}/{len(noms)} jeu(x)"),
                nature_du_trou=(
                    "" if n else INATTEIGNABLES.get(
                        carac, "non exerce par le corpus"))))
    ecrire_csv(chemin, colonnes, lignes, tri=["famille", "caracteristique"])
    return lignes


# ============================================================
# Confrontation à corpus.csv
# ============================================================
def confronter(inv: pd.DataFrame, jeux, lignes_matrice):
    """
    Trois colonnes déclaré / observé / écart, une ligne par champ de
    corpus.csv et par jeu, plus les champs que corpus.csv ne prévoit pas mais
    que l'inventaire impose de dire.

    Le statut distingue quatre situations, parce que les confondre rendrait le
    tableau illisible :
      conforme   la déclaration et l'observation disent la même chose ;
      precise    la déclaration disait « à vérifier » / « inconnu » —
                 l'inventaire la renseigne, ce n'est pas une erreur ;
      ECART      la déclaration et l'observation se contredisent ;
      libre      champ en texte libre, non comparable terme à terme ; on lui
                 oppose ce que l'inventaire a trouvé, sans verdict.
    """
    corpus = pd.read_csv(RACINE / "data" / "corpus.csv", sep=";", dtype=str,
                         keep_default_na=False)
    corpus.columns = [c.lstrip("\ufeff") for c in corpus.columns]
    out = []

    def add(jeu, champ, declare, observe, statut):
        out.append(dict(jeu=jeu, champ=champ, declare=declare,
                        observe=observe, statut=statut))

    def verdict(declare, observe):
        if _incertain(declare):
            return "precise"
        return "conforme" if _egal(declare, observe) else "ECART"

    declares = set(corpus.jeu)
    observes = {j["jeu"] for j in jeux}
    for jeu in sorted(declares - observes):
        add(jeu, "existence du jeu", "declare dans corpus.csv",
            "ABSENT de data/ (ou sans dossier eau/)", "ECART")
    for jeu in sorted(observes - declares):
        add(jeu, "existence du jeu", "NON declare dans corpus.csv",
            "present dans data/", "ECART")

    for j in jeux:
        jeu = j["jeu"]
        ligne = corpus[corpus.jeu == jeu]
        if not len(ligne):
            continue
        r = ligne.iloc[0]
        sel = inv[inv.jeu == jeu]
        eaux = sel[sel.role == "eau"]
        airs = sel[sel.role == "air"]
        debits = sel[sel.role == "debit"]

        add(jeu, "n_points", r["n_points"], str(len(eaux)),
            verdict(r["n_points"], str(len(eaux))))

        exts = sorted({e.lstrip(".") for e in eaux.extension})
        feuilles = sorted({f for s_ in eaux.feuilles
                           for f in s_.split(" | ") if f and f != "n/a"})
        obs_fmt = ", ".join(exts) + (f" ; feuille(s) : {', '.join(feuilles)}"
                                     if feuilles else "")
        add(jeu, "format_eau", r["format_eau"], obs_fmt,
            verdict(r["format_eau"], obs_fmt))

        tn = sorted(set(airs.presence_TN)) or ["aucun fichier air"]
        tx = sorted(set(airs.presence_TX)) or ["aucun fichier air"]
        obs_air = ("oui" if tn == ["oui"] and tx == ["oui"]
                   else f"TN={'/'.join(tn)} ; TX={'/'.join(tx)}")
        add(jeu, "air_tn_tx", r["air_tn_tx"], obs_air,
            verdict(r["air_tn_tx"], obs_air))

        # ÉTAPE 2, C5 — requalification.
        # `pas_eau` porte la MÊME phrase sur les six lignes de corpus.csv :
        # c'est une declaration de portee CORPUS, recopiee par jeu, et non six
        # declarations par jeu. La confronter jeu par jeu a une distribution
        # d'intervalles fabrique cinq ecarts a partir d'un seul enonce. Elle
        # est donc evaluee une fois, au niveau du corpus (voir plus bas), et
        # marquee "portee corpus" sur chaque ligne de jeu.
        add(jeu, "pas_eau", r["pas_eau"], _decrire_pas(eaux), "portee corpus")

        obs_deb = "oui" if len(debits) else "non"
        add(jeu, "debit", r["debit"], obs_deb, verdict(r["debit"], obs_deb))

        add(jeu, "particularite", r["particularite"], _traits(eaux, airs),
            "libre")

        # --- Champs que corpus.csv ne prevoit pas ---
        add(jeu, "[hors corpus.csv] fichiers d'air", "non prevu",
            f"{len(airs)} : "
            + ", ".join(sorted(Path(f).name for f in airs.fichier)), "libre")
        add(jeu, "[hors corpus.csv] debit desinfluence", "non prevu",
            "aucun : le dossier debit/ ne porte qu'un fichier"
            if len(debits) <= 1 else f"{len(debits)} fichiers de debit", "libre")

    # --- La declaration `pas_eau`, evaluee UNE FOIS au niveau du corpus ---
    pas_uniques = set(corpus["pas_eau"])
    eaux_tout = inv[inv.role == "eau"]
    presents = _intervalles(eaux_tout)
    if len(pas_uniques) == 1:
        decl = next(iter(pas_uniques))
        obs = ("intervalles reellement presents dans le corpus (>= 5 "
               "occurrences) : "
               + ", ".join(_h(str(x)) for x in sorted(presents)))
        infra = sorted(x for x in presents if x < 86400)
        verdict = ("conforme" if (900 in presents and 1800 in presents
                                  and 3600 in presents) else "ECART")
        add("[corpus entier]", "pas_eau (declaration unique, recopiee sur les "
                               "six lignes)", decl, obs, verdict)
        add("[corpus entier]", "pas_eau — ou se trouvent les periodes a 15 et "
                               "30 min", "non precise",
            _ou_sont(inv, {900, 1800}), "libre")
    return out


def _ou_sont(inv, secondes):
    """Quels fichiers portent ces intervalles, et en quelle quantite."""
    import re as _re
    out = []
    for _, r in inv[inv.role == "eau"].iterrows():
        for morceau in str(r.get("pas_observes", "")).split(" | "):
            m = _re.match(r"^(\d+)s x(\d+)$", morceau.strip())
            if m and int(m.group(1)) in secondes and int(m.group(2)) >= 5:
                out.append(f"{r.fichier.split('/')[-1]} : "
                           f"{_h(m.group(1))} x{m.group(2)}")
    return " ; ".join(out) or "aucun"


def _incertain(v):
    n = re.sub(r"\s+", " ", str(v).strip().lower())
    return n in ("a verifier", "à vérifier", "a verifier.", "inconnu",
                 "inconnue", "?", "")


def _intervalles(eaux, mini=5):
    """Intervalles réellement présents (au moins `mini` occurrences)."""
    presents = set()
    if "pas_observes" not in eaux.columns:
        return presents
    for s_ in eaux.pas_observes:
        for morceau in str(s_).split(" | "):
            m = re.match(r"^(\d+)s x(\d+)$", morceau.strip())
            if m and int(m.group(2)) >= mini:
                presents.add(int(m.group(1)))
    return presents


def _decrire_pas(eaux):
    """
    Ce que V4.5 LIT, et non ce que la source porte. La distinction compte : sur
    BLE3-0, la source est strictement horaire (2 951 intervalles de 3 600 s
    dans la colonne `chmes_heure`) mais V4.5 ne reconnait pas cette colonne
    (io_data.py:79-82) et date les 2 952 mesures a minuit, ce qui rend la
    chronique journaliere A LA LECTURE.
    """
    modaux = sorted({_h(p) for p in eaux.pas_modal_s if p})
    presents = _intervalles(eaux)
    lst = ", ".join(_h(str(x)) for x in sorted(presents)) if presents else "—"
    txt = (f"tel que V4.5 le lit — pas modal : "
           f"{', '.join(modaux) or 'indetermine'} ; intervalles presents "
           f"(>= 5 occurrences) : {lst}")
    perdus = [r.fichier.split("/")[-1] for _, r in eaux.iterrows()
              if r.colonne_heure_separee == "non"
              and any(("heure" in c.strip().lower() or "hour" in c.strip().lower())
                      and c.strip().lower() != str(r.colonne_date_retenue_v45).lower()
                      for c in str(r.entetes).split(" | "))]
    if perdus:
        txt += (f" — ATTENTION : {', '.join(perdus)} porte une colonne d'heure "
                f"que V4.5 ne reconnait pas ; la source y est infra-journaliere, "
                f"la lecture non")
    return txt


def _verdict_pas(declare, eaux):
    """
    La déclaration affirme deux choses : un pas infra-journalier, et quelques
    périodes à 15 et 30 min. Les deux sont vérifiées séparément.
    """
    if _incertain(declare):
        return "precise"
    d = str(declare).lower()
    presents = _intervalles(eaux)
    infra = any(p < 86400 for p in presents)
    if ("infra" in d) != infra:
        return "ECART"
    for sec, mot in ((900, "15"), (1800, "30")):
        if mot in d and sec not in presents:
            return "ECART"
    if "86400" in set(eaux.pas_modal_s) and "journalier" == d.strip():
        return "conforme"
    if "86400" in set(eaux.pas_modal_s):
        return "ECART"       # au moins un fichier est de fait journalier
    return "conforme"


def _traits(eaux, airs):
    traits = []
    n_rec = sum(1 for c in eaux.colonne_heure_separee if "RECOMPOSEE" in c)
    if n_rec:
        traits.append(f"{n_rec} fichier(s) a colonne d'heure separee, recomposee")
    if any("NON recomposee" in c for c in eaux.colonne_heure_separee):
        traits.append("colonne d'heure detectee mais non recomposee "
                      "(la date porte deja une heure)")
    n_sans = sum(1 for c in eaux.colonne_heure_separee if c == "non")
    if n_sans:
        traits.append(f"{n_sans} fichier(s) sans colonne d'heure reconnue")
    if any("virgule" in s_ for s_ in eaux.separateur_decimal):
        traits.append("virgule decimale")
    nf = pd.to_numeric(eaux.n_feuilles, errors="coerce").fillna(0)
    if (nf > 1).any():
        traits.append("classeur multi-feuilles")
    nd = pd.to_numeric(eaux.doublons_horodatage, errors="coerce").fillna(0)
    if (nd > 0).any():
        traits.append(f"{int(nd.sum())} horodatage(s) en double")
    encs = sorted({e for e in eaux.encodage if e and e != "n/a"})
    if encs:
        traits.append("encodage " + "/".join(encs))
    if any("AnaTemp" in e for e in eaux.entetes):
        traits.append("vocabulaire SANDRE")
    if any("\u00b0F" in e for e in eaux.entetes):
        traits.append("colonne en Fahrenheit a cote du Celsius")
    if any("virgule" in s_ for s_ in airs.separateur_decimal):
        traits.append("virgule decimale dans la chronique d'air")
    return " ; ".join(traits) or "aucun trait releve"


MOTS_VIDES = {"feuille", "feuilles", "les", "des", "une", "the", "avec",
              "dans", "sur", "pour", "par", "aux", "que", "qui", "est"}


def _egal(a, b):
    """
    Egalite par jeu de mots significatifs, et non par chaine exacte : « xlsx
    (feuille ValInstantanees) » et « xlsx ; feuille(s) : ValInstantanees »
    disent la meme chose. Un mot significatif present d'un seul cote fait
    l'ecart.
    """
    import unicodedata

    def mots(v):
        t = unicodedata.normalize("NFKD", str(v).lower())
        t = "".join(c for c in t if not unicodedata.combining(c))
        bruts = re.split(r"[^a-z0-9]+", t)
        return {m for m in bruts if len(m) >= 3 and m not in MOTS_VIDES}

    na, nb = str(a).strip().lower(), str(b).strip().lower()
    if na == nb:
        return True
    if na.isdigit() and nb.isdigit():
        return int(na) == int(nb)
    return mots(a) == mots(b)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inv = charger_inventaire()
    jeux = decouvrir()
    M, noms = caracteristiques(inv, jeux)
    M = caracteristiques_harnais(M, noms, jeux)
    lignes = ecrire_matrice(M, noms, OUT / "matrice_couverture.csv")
    non_couvert = [l for l in lignes if l["couverture"] == "NON COUVERT"]

    ecarts = confronter(inv, jeux, lignes)
    n_ecarts = sum(1 for e in ecarts if e["statut"] == "ECART")
    n_precise = sum(1 for e in ecarts if e["statut"] == "precise")
    n_libre = sum(1 for e in ecarts if e["statut"] == "libre")

    # --- docs/etape1_ecarts_corpus.md ---
    txt = ["# Étape 1 — corpus déclaré, corpus observé", "",
           "`data/corpus.csv` est rempli **de mémoire, sans ouvrir les "
           "fichiers** : c'est sa consigne. Ce document lui oppose ce que "
           "l'inventaire et le harnais ont trouvé. Il ne corrige pas "
           "`corpus.csv`.", "",
           f"{len(ecarts)} confrontation(s) : **{n_ecarts} écart(s)**, "
           f"{n_precise} champ(s) déclaré(s) « à vérifier » que l'inventaire "
           f"renseigne, {n_libre} champ(s) en texte libre non comparables "
           f"terme à terme.", "",
           "Un champ déclaré « à vérifier » n'est pas un écart : la consigne "
           "de `corpus.csv` autorise explicitement cette réponse. Il est "
           "marqué *précisé*.", "",
           "**Requalification de l'étape 2 (C5).** La colonne `pas_eau` porte "
           "la *même phrase* sur les six lignes de `corpus.csv` : c'est une "
           "déclaration de portée **corpus**, recopiée par jeu, et non six "
           "déclarations distinctes. L'opposer jeu par jeu à une distribution "
           "d'intervalles fabriquait cinq écarts à partir d'un seul énoncé. "
           "Elle est désormais marquée *portée corpus* sur chaque ligne de jeu "
           "et évaluée **une fois**, en fin de tableau.", "",
           "Second point de la requalification : la colonne « observé » de "
           "`pas_eau` dit ce que **V4.5 lit**, pas ce que la source porte. Sur "
           "`BLE3-0`, la source est strictement horaire — 2 951 intervalles de "
           "3 600 s dans `chmes_heure` — et c'est V4.5 qui la rend journalière "
           "en ne reconnaissant pas cette colonne (`io_data.py:79-82`). "
           "L'écart n'est donc pas entre la mémoire et la source, mais entre "
           "la source et sa lecture.", "",
           "## Déclaré / observé / statut", "",
           "| Jeu | Champ | Déclaré | Observé | Statut |",
           "|---|---|---|---|---|"]
    ETIQ = {"ECART": "**ÉCART**", "conforme": "conforme",
            "precise": "précisé", "libre": "texte libre",
            "portee corpus": "portée corpus — évalué une fois, plus bas"}
    for e in ecarts:
        txt.append("| {} | `{}` | {} | {} | {} |".format(
            e["jeu"], e["champ"], _md(e["declare"]), _md(e["observe"]),
            ETIQ.get(e["statut"], e["statut"])))
    txt += ["", "## Les écarts, un par un", ""]
    if not n_ecarts:
        txt.append("Aucun écart au sens strict.")
    for i, e in enumerate([x for x in ecarts if x["statut"] == "ECART"], 1):
        txt += [f"**É{i} — {e['jeu']} · `{e['champ']}`**", "",
                f"- déclaré : {_md(e['declare'])}",
                f"- observé : {_md(e['observe'])}", ""]

    txt += ["", "## Caractéristiques NON COUVERTES", "",
            "Ce que l'outil sait lire mais qu'aucun jeu du corpus n'exerce. "
            "Elles sont **nommées, pas comblées** (D6) : fabriquer un jeu de "
            "test pour les couvrir reviendrait à tester l'idée qu'on se fait "
            "du format, pas le format.", "",
            "Deux natures de vide sont distinguées : celui qu'aucun jeu "
            "n'exerce, et celui qu'**aucun jeu ne pourrait exercer** parce que "
            "le code ne peut pas y arriver.", "",
            "| Famille | Caractéristique | Nature |", "|---|---|---|"]
    for l in non_couvert:
        nat = l["nature_du_trou"]
        nat = ("non exercé par le corpus" if nat == "non exerce par le corpus"
               else f"**inatteignable par construction** — {nat}")
        txt.append(f"| {l['famille']} | {l['caracteristique']} | {nat} |")
    txt.append("")
    ecrire_texte(DOCS / "etape1_ecarts_corpus.md", "\n".join(txt) + "\n")

    print(f"matrice_couverture.csv : {len(lignes)} caracteristiques, "
          f"{len(non_couvert)} NON COUVERT")
    print(f"etape1_ecarts_corpus.md : {n_ecarts} ecart(s) sur {len(ecarts)}")


def _md(s):
    return str(s).replace("|", "\\|").replace("\n", " ") or "—"


if __name__ == "__main__":
    main()
