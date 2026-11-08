"""
sniff.py — Détection robuste de format tabulaire (package thermie_debits).

Gère CSV (auto-détection séparateur/encodage) ET Excel (.xls/.xlsx), avec :
  - choix de la feuille (Excel multi-feuilles) ;
  - détection d'une ligne d'en-tête décalée (l'en-tête n'est pas toujours
    la 1re ligne — ex. sondes qui préfixent des métadonnées) ;
  - proposition de mapping de colonnes (date / valeur) par vocabulaire.

Utilisé par les loaders sonde et air, et exposé à l'app pour un mapping
manuel corrigeable.
"""
from __future__ import annotations
import io
import csv
import pandas as pd


ENCODAGES = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
SEPARATEURS = [";", ",", "\t", "|"]

MOTS_DATE = ["date", "heure", "time", "timestamp", "horodat", "jour", "aaaammjj",
             "aaaa", "datetime", "cet", "cest", "gmt",
             "dtanatemp", "dtprel", "dt_", "dtana", "hranatemp", "hrprel"]
MOTS_TEMP = ["temp", "°c", "degr", "tw", "t_eau", "teau", "water", "eau",
             "valeur", "value", "tm", "t (", "t(", ", °c", "temp,",
             "rsanatemp", "rsana", "resultat", "résultat"]
# Noms de colonne trop courts pour une recherche par sous-chaîne (« t » se
# trouve partout) : ils ne sont reconnus que s'ils constituent le nom ENTIER.
# « T » est la colonne de température du format d'échange DCE des chroniques
# thermiques (onglet « chronique de température »).
NOMS_TEMP_EXACTS = ["t", "t°", "t°c", "t (°c)", "t(°c)"]


def _norm(s):
    s = str(s).lower()
    for a, b in [("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o")]:
        s = s.replace(a, b)
    return s


def _detecter_separateur(lignes, n_test=40):
    """
    Détecte le séparateur d'un CSV par cohérence tabulaire, plutôt que par
    l'heuristique fragile de csv.Sniffer (qui se fait piéger quand un
    séparateur candidat apparaît dans un nom de colonne ou une valeur —
    ex. en-tête « Date Heure, GMT +0200 » avec un vrai séparateur « ; »).

    Pour chaque candidat, on découpe les lignes non vides et on retient
    celui qui donne le plus grand nombre de colnnes RÉGULIER (même compte sur
    la majorité des lignes) et > 1. À égalité de régularité, on privilégie
    le séparateur produisant le plus de colonnes.
    """
    ech = [l for l in lignes[:n_test] if l.strip()]
    if not ech:
        return ";"
    meilleur, meilleur_score = ";", (-1, -1)
    for sep in SEPARATEURS:
        comptes = [l.count(sep) + 1 for l in ech]  # nb de champs par ligne
        if max(comptes) < 2:
            continue  # ce séparateur ne découpe rien
        # nombre de colonnes le plus fréquent (mode) et sa régularité
        from collections import Counter
        c = Counter(comptes)
        ncol_mode, freq = c.most_common(1)[0]
        if ncol_mode < 2:
            continue
        regularite = freq / len(comptes)        # part des lignes cohérentes
        # score : d'abord la régularité, puis le nb de colonnes
        score = (round(regularite, 3), ncol_mode)
        if score > meilleur_score:
            meilleur_score, meilleur = score, sep
    return meilleur


def est_excel(nom):
    """Détecte un fichier Excel d'après son extension."""
    n = str(nom).lower()
    return n.endswith(".xls") or n.endswith(".xlsx") or n.endswith(".xlsm")


def lister_feuilles(source, nom=""):
    """Retourne la liste des feuilles d'un Excel (vide si CSV)."""
    if not est_excel(nom):
        return []
    engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
    buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    try:
        return pd.ExcelFile(buf, engine=engine).sheet_names
    except Exception:
        try:
            return pd.ExcelFile(buf).sheet_names
        except Exception:
            return []


def _detecter_ligne_entete(df_brut, max_scan=15):
    """
    Trouve la ligne qui ressemble le plus à un en-tête : celle qui contient
    le plus de cellules correspondant au vocabulaire date/température.
    Retourne l'indice de ligne (0 si rien de mieux trouvé).
    """
    best_row, best_score = 0, 0
    for i in range(min(max_scan, len(df_brut))):
        cells = [_norm(v) for v in df_brut.iloc[i].tolist()]
        score = sum(1 for c in cells
                    if any(m in c for m in MOTS_DATE + MOTS_TEMP))
        # bonus : une ligne d'en-tête a peu de valeurs numériques pures
        n_num = sum(1 for c in cells
                    if c.replace(".", "").replace(",", "").replace("-", "").isdigit())
        if score > best_score and n_num <= len(cells) / 2:
            best_score, best_row = score, i
    return best_row


N_LIGNES_EVAL_FEUILLE = 300


def evaluer_feuilles(source, nom=""):
    """
    Évalue chaque feuille d'un classeur comme candidate à porter la chronique.

    Pour chaque feuille : détection de l'en-tête et des colonnes date /
    valeur sur ses N_LIGNES_EVAL_FEUILLE premières lignes, puis compte des
    lignes qui portent À LA FOIS une date et une valeur numérique. Retourne
    une liste de dicts {feuille, col_date, col_valeur, n_lignes_exploitables},
    dans l'ordre du classeur. Une feuille illisible est rendue avec
    n_lignes_exploitables = 0 et sa cause dans `erreur` — jamais omise.

    Motif : les classeurs au format d'échange DCE placent les métadonnées de
    pose en première feuille et la chronique en seconde. Retenir la première
    feuille par défaut lisait les métadonnées comme une chronique.
    """
    feuilles = lister_feuilles(source, nom)
    engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
    out = []
    for sh in feuilles:
        buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
        try:
            brut = pd.read_excel(buf, sheet_name=sh, header=None, engine=engine,
                                 nrows=N_LIGNES_EVAL_FEUILLE)
        except Exception as e:                       # noqa: BLE001 — tracé
            out.append(dict(feuille=sh, col_date=None, col_valeur=None,
                            n_lignes_exploitables=0, erreur=str(e)))
            continue
        if brut.empty:
            out.append(dict(feuille=sh, col_date=None, col_valeur=None,
                            n_lignes_exploitables=0, erreur="feuille vide"))
            continue
        hdr = _detecter_ligne_entete(brut)
        df = brut.iloc[hdr + 1:].copy()
        df.columns = [str(c).strip() for c in brut.iloc[hdr].tolist()]
        df = df.dropna(how="all")
        cd, cv = deviner_colonnes(df)
        n_ok = 0
        if cd is not None and cv is not None:
            val = pd.to_numeric(
                df[cv].astype(str).str.replace(",", ".").str.replace(" ", ""),
                errors="coerce")
            n_ok = int((df[cd].notna() & val.notna()).sum())
        out.append(dict(feuille=sh, col_date=cd, col_valeur=cv,
                        n_lignes_exploitables=n_ok, erreur=None))
    return out


def detecter_feuille(source, nom=""):
    """
    Nom de la feuille qui porte le plus de lignes exploitables (date ET valeur
    numérique). À égalité — y compris si aucune n'en porte —, la première
    feuille du classeur, ce qui reproduit l'ancien comportement.
    """
    ev = evaluer_feuilles(source, nom)
    if not ev:
        return 0
    meilleure = max(ev, key=lambda e: e["n_lignes_exploitables"])
    if meilleure["n_lignes_exploitables"] == ev[0]["n_lignes_exploitables"]:
        return ev[0]["feuille"]
    return meilleure["feuille"]


def lire_brut(source, nom="", n_lignes=None, feuille=None, ligne_entete=None):
    """
    Lit un CSV ou Excel en auto-détectant le format.

    source : chemin de fichier OU bytes (upload Streamlit).
    nom    : nom du fichier (pour détecter l'extension). Si source est un
             chemin, nom est déduit automatiquement.
    feuille : nom de feuille Excel (défaut : la feuille qui porte le plus de
              lignes date + valeur, cf. `detecter_feuille` ; la 1re feuille
              si aucune ne se distingue).
    ligne_entete : indice de la ligne d'en-tête (défaut : auto-détection).

    Retourne (df, meta) où meta décrit le format détecté.
    """
    if not nom and isinstance(source, str):
        nom = source

    # ---- Excel ----
    if est_excel(nom):
        engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
        buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
        feuilles = lister_feuilles(source, nom)
        if feuille in feuilles:
            sh = feuille
        elif len(feuilles) > 1:
            sh = detecter_feuille(source, nom)
        else:
            sh = feuilles[0] if feuilles else 0
        # lire brut sans header pour trouver la ligne d'en-tête
        brut = pd.read_excel(buf, sheet_name=sh, header=None, engine=engine)
        hdr = ligne_entete if ligne_entete is not None else _detecter_ligne_entete(brut)
        df = brut.iloc[hdr + 1:].copy()
        df.columns = [str(c).strip() for c in brut.iloc[hdr].tolist()]
        df = df.reset_index(drop=True).dropna(how="all")
        if n_lignes:
            df = df.head(n_lignes)
        return df, {"format": "excel", "engine": engine, "feuille": sh,
                    "feuilles": feuilles, "ligne_entete": hdr}

    # ---- CSV ----
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        with open(source, "rb") as f:
            raw = f.read()
    texte = None; enc_ok = None
    for enc in ENCODAGES:
        try:
            texte = raw.decode(enc); enc_ok = enc; break
        except (UnicodeDecodeError, LookupError):
            continue
    if texte is None:
        texte = raw.decode("utf-8", errors="replace"); enc_ok = "utf-8(replace)"

    lignes = texte.splitlines()
    sep_ok = _detecter_separateur(lignes)

    # détection ligne d'en-tête pour CSV aussi (rare mais possible)
    # Lecture bornée à la source quand n_lignes est fourni (aperçu) : évite de
    # matérialiser en mémoire un fichier volumineux (ex. export Météo-France
    # multi-stations de ~100 Mo) juste pour montrer 3 lignes. On lit un petit
    # surplus pour absorber une éventuelle ligne d'en-tête décalée.
    nrows = (n_lignes + 30) if n_lignes else None
    brut = pd.read_csv(io.StringIO(texte), sep=sep_ok, engine="python",
                       header=None, nrows=nrows)
    hdr = ligne_entete if ligne_entete is not None else _detecter_ligne_entete(brut)
    df = brut.iloc[hdr + 1:].copy()
    df.columns = [str(c).lstrip("\ufeff").strip() for c in brut.iloc[hdr].tolist()]
    df = df.reset_index(drop=True).dropna(how="all")
    if n_lignes:
        df = df.head(n_lignes)
    return df, {"format": "csv", "encodage": enc_ok, "separateur": sep_ok,
                "ligne_entete": hdr}


def deviner_colonnes(df, mots_valeur=MOTS_TEMP):
    """Propose (col_date, col_valeur) par vocabulaire. None si non trouvé.

    Pour la valeur, on ne prend pas le premier nom qui matche le vocabulaire
    (des libellés comme « CdStationMesureEauxSurface » contiennent « eau »
    sans être des températures) : on classe les candidats par plausibilité
    numérique, puis par cohérence physique (médiane dans une plage de
    température crédible), et on retient le meilleur.
    """
    cols = list(df.columns)
    col_date = next((c for c in cols
                     if any(m in _norm(c) for m in MOTS_DATE)), None)
    candidates = [c for c in cols
                  if (any(m in _norm(c) for m in mots_valeur)
                      or _norm(c).strip() in NOMS_TEMP_EXACTS)
                  and c != col_date]

    def _score(c):
        serie = pd.to_numeric(
            df[c].astype(str).str.replace(",", ".").str.replace(" ", ""),
            errors="coerce")
        frac = float(serie.notna().mean())
        med = serie.median()
        # bonus si la médiane tombe dans une plage de température crédible
        plausible = 1 if (pd.notna(med) and -30 <= med <= 50) else 0
        # malus pour les colonnes de code/identifiant (souvent de grands entiers)
        idlike = 1 if (pd.notna(med) and abs(med) >= 1000) else 0
        return (plausible, frac, -idlike)

    col_val = None
    if candidates:
        ranked = sorted(candidates, key=_score, reverse=True)
        col_val = ranked[0]
    return col_date, col_val


# Colonnes d'identification reconnues dans les classeurs (format d'échange DCE
# des chroniques thermiques et voisins). Ordre = priorité.
COLS_COURS_EAU = ["RIV_NOM", "MILIEU", "COURS_EAU", "NOM_COURS_EAU"]
COLS_POINT = ["NOM_STA_METIER", "COD_STA_METIER", "CODERHJ", "NOM_STATION",
              "CODE_STA_SANDRE"]


def identifier_sonde(source, nom=""):
    """
    Cherche, dans toutes les feuilles d'un classeur, le nom du cours d'eau et
    l'identifiant du point de mesure (colonnes COLS_COURS_EAU / COLS_POINT,
    insensibles à la casse). Retourne {cours_eau, point} ; une clé vaut None
    si rien n'a été trouvé — c'est alors à l'opérateur de la saisir. CSV : on
    ne cherche rien, les deux clés valent None.

    Ne sert qu'à PRÉ-REMPLIR le tableau de rapprochement : la valeur reste
    modifiable à l'écran et n'entre dans aucun calcul.
    """
    trouve = {"cours_eau": None, "point": None}
    for sh in lister_feuilles(source, nom):
        buf = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
        engine = "xlrd" if str(nom).lower().endswith(".xls") else "openpyxl"
        try:
            brut = pd.read_excel(buf, sheet_name=sh, header=None, engine=engine,
                                 nrows=20)
        except Exception:                            # noqa: BLE001
            continue        # feuille illisible : evaluer_feuilles le trace déjà
        if brut.empty:
            continue
        hdr = _detecter_ligne_entete(brut)
        entetes = {str(c).strip().upper(): j
                   for j, c in enumerate(brut.iloc[hdr].tolist())}
        corps = brut.iloc[hdr + 1:]
        for cle, cols in (("cours_eau", COLS_COURS_EAU), ("point", COLS_POINT)):
            if trouve[cle] is not None:
                continue
            for c in cols:
                if c in entetes:
                    v = corps.iloc[:, entetes[c]].dropna().astype(str).str.strip()
                    v = v[v != ""]
                    if len(v):
                        trouve[cle] = v.iloc[0]
                        break
    return trouve
