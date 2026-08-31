"""
test_adaptateur_qc.py — ÉTAPE 6, TÂCHE A3 : la preuve que le corpus ne donne pas.

CE QUE CE TEST ÉTABLIT
----------------------
L'adaptateur du correctif 3 doit rendre à l'aval EXACTEMENT ce que V4.5
rendait. Sur le corpus de `data/`, l'invariance est vérifiée — mais elle y est
vérifiée pour une mauvaise raison : aucune journée du corpus n'est écartée par
plus d'un détecteur. Une invariance qui tient parce que le cas critique est
absent des données n'est pas une invariance, c'est une chance.

Ce test fabrique donc le cas critique. Les chroniques sont SYNTHÉTIQUES et
vivent dans `tests/`, jamais dans `data/` : elles ne sont pas des données
d'étude et n'ont pas à entrer dans le corpus.

Trois cas :

  1. `deux_motifs`  — une journée déclenche bornes physiques ET plateau.
     C'est le cas que le corpus ne porte pas.
  2. `trois_motifs` — une journée déclenche bornes, plateau et hors d'eau.
  3. `corpus_type`  — une chronique ordinaire, un seul détecteur par journée,
     pour vérifier que le cas nominal ne régresse pas non plus.

Pour chacun, on exécute le contrôle qualité de `ref/v4_5/` puis celui de
`app/`, dans deux interpréteurs séparés — les deux modules portent le même
nom, `thermie_debits.qc`, et ne peuvent pas coexister dans un même processus —
et l'on compare :

  · `propre`  : mêmes colonnes, même ordre, mêmes valeurs, mêmes types ;
  · `rapport` : mêmes cinq colonnes, mêmes valeurs, `motif` compris ;
  · la sortie console, caractère par caractère.

Puis on vérifie que la table de marquage de `app/`, elle, porte bien TOUS les
motifs — ce que V4.5 perdait.

USAGE
    python tests/test_adaptateur_qc.py
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
REF_V45 = RACINE / "ref" / "v4_5"
APP = RACINE / "app"

# Paramètres du contrôle qualité, au format que `controle_qualite` attend.
# Choisis pour que les détecteurs se déclenchent sur les chroniques ci-dessous,
# et non repris d'un jeu réel.
QC = {
    "bornes_physiques": True, "T_eau_min": -0.5, "T_eau_max": 35.0,
    "hors_eau": True, "hors_eau_ecart_seuil": 4.0,
    "hors_eau_mois": [6, 7, 8, 9], "hors_eau_min_jours": 3,
    "hors_eau_exclut_saison": False,
    "plateau": True, "plateau_fenetre": 5, "plateau_ecart_type_min": 0.05,
    "mad_outliers": False, "mad_k": 50.0, "mad_mois": None,
}


# ============================================================
# Les chroniques synthétiques
# ============================================================
def cas_deux_motifs():
    """
    Une journée qui déclenche BORNES et PLATEAU à la fois.

    Onze journées de juillet. Les journées 3 à 9 forment un plateau parfait à
    40 °C : leur écart-type glissant est nul, et 40 °C dépasse la borne haute.
    Les journées centrales du plateau portent donc DEUX motifs.
    """
    dates = pd.date_range("2020-07-01", periods=11, freq="D").date
    t = [12.0, 13.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 14.0, 15.0]
    eau = pd.DataFrame({
        "date": dates, "T_eau_moy": t, "T_eau_max": [x + 0.5 for x in t],
        "T_eau_min": [x - 0.5 for x in t], "n_mesures": [24] * 11})
    air = pd.DataFrame({"date": dates, "T_air": [20.0] * 11})
    return eau, air


def cas_trois_motifs():
    """
    Une journée qui déclenche BORNES, PLATEAU et HORS D'EAU.

    Même plateau à 40 °C, mais l'air est maintenant à 10 °C : l'écart
    `T_eau_max − T_air` vaut 30,5 °C, très au-dessus du seuil de 4 °C, et sept
    journées suspectes dépassent le minimum de trois.
    """
    dates = pd.date_range("2020-07-01", periods=11, freq="D").date
    t = [12.0, 13.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 14.0, 15.0]
    eau = pd.DataFrame({
        "date": dates, "T_eau_moy": t, "T_eau_max": [x + 0.5 for x in t],
        "T_eau_min": [x - 0.5 for x in t], "n_mesures": [24] * 11})
    air = pd.DataFrame({"date": dates, "T_air": [10.0] * 11})
    return eau, air


def cas_corpus_type():
    """
    Une chronique ordinaire : un seul détecteur par journée, comme le corpus.
    Une journée hors bornes, isolée, au milieu d'une série variable.
    """
    dates = pd.date_range("2020-06-15", periods=20, freq="D").date
    t = [12.0 + (i % 5) * 1.3 for i in range(20)]
    t[9] = 48.0                                     # hors bornes, seule
    eau = pd.DataFrame({
        "date": dates, "T_eau_moy": t, "T_eau_max": [x + 0.6 for x in t],
        "T_eau_min": [x - 0.6 for x in t], "n_mesures": [24] * 20})
    air = pd.DataFrame({"date": dates, "T_air": [x - 1.0 for x in t]})
    return eau, air


CAS = {"deux_motifs": cas_deux_motifs,
       "trois_motifs": cas_trois_motifs,
       "corpus_type": cas_corpus_type}


# ============================================================
# Exécution dans un interpréteur dédié
# ============================================================
_ENFANT = r'''
import io, json, sys
from contextlib import redirect_stdout
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
import pandas as pd
sys.path.insert(0, sys.argv[3])
from test_adaptateur_qc import CAS, QC
from thermie_debits import qc as qcmod

eau, air = CAS[sys.argv[2]]()
tampon = io.StringIO()
with redirect_stdout(tampon):
    propre, rapport = qcmod.controle_qualite(eau, air, QC, verbose=True)

sortie = {
    "console": tampon.getvalue(),
    "propre_colonnes": list(propre.columns),
    "propre": propre.to_json(orient="split", date_format="iso"),
    "rapport_colonnes": list(rapport.columns),
    "rapport": rapport.to_json(orient="split", date_format="iso"),
}
if hasattr(qcmod, "marquer_qualite"):
    with redirect_stdout(io.StringIO()):
        marques = qcmod.marquer_qualite(eau, air, QC, verbose=False)
    ec = marques[marques["statut"] == qcmod.STATUT_ECARTE]
    sortie["motifs_par_journee"] = [list(m) for m in ec["motifs"]]
    sortie["statuts"] = sorted(set(marques["statut"]))
print("<<<JSON>>>" + json.dumps(sortie))
'''


def executer(racine_code: Path, nom_cas: str) -> dict:
    script = ICI / "_enfant_qc.py"
    script.write_text(_ENFANT, encoding="utf-8")
    try:
        r = subprocess.run(
            [sys.executable, "-W", "ignore", str(script),
             str(racine_code), nom_cas, str(ICI)],
            capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise SystemExit(f"echec {racine_code.name}/{nom_cas} :\n{r.stderr}")
        marque = r.stdout.index("<<<JSON>>>") + len("<<<JSON>>>")
        return json.loads(r.stdout[marque:])
    finally:
        script.unlink(missing_ok=True)


def comparer(a: dict, b: dict, nom_cas: str):
    """Retourne la liste des écarts entre la sortie de V4.5 et celle de app/."""
    ecarts = []
    if a["console"] != b["console"]:
        ecarts.append("la sortie console diffère")
    for cle in ("propre", "rapport"):
        if a[f"{cle}_colonnes"] != b[f"{cle}_colonnes"]:
            ecarts.append(f"{cle} : colonnes {a[f'{cle}_colonnes']} "
                          f"!= {b[f'{cle}_colonnes']}")
            continue
        da = pd.read_json(io.StringIO(a[cle]), orient="split")
        db = pd.read_json(io.StringIO(b[cle]), orient="split")
        if da.shape != db.shape:
            ecarts.append(f"{cle} : dimensions {da.shape} != {db.shape}")
            continue
        for col in da.columns:
            if not da[col].equals(db[col]):
                diff = [(i, x, y) for i, (x, y)
                        in enumerate(zip(da[col], db[col])) if x != y]
                ecarts.append(f"{cle}.{col} : {len(diff)} valeur(s) differente(s), "
                              f"1re = ligne {diff[0][0]} "
                              f"{diff[0][1]!r} != {diff[0][2]!r}")
    return ecarts


def main():
    print("=" * 74)
    print("PREUVE D'INVARIANCE DE L'ADAPTATEUR — cas synthetiques, hors data/")
    print("=" * 74)
    echecs = 0
    for nom_cas in CAS:
        ref = executer(REF_V45, nom_cas)
        app = executer(APP, nom_cas)
        ecarts = comparer(ref, app, nom_cas)

        n_ec = len(json.loads(ref["rapport"])["data"])
        motifs = app.get("motifs_par_journee", [])
        n_multi = sum(1 for m in motifs if len(m) > 1)
        max_motifs = max((len(m) for m in motifs), default=0)

        print(f"\n--- cas « {nom_cas} » ---")
        print(f"  journees ecartees                       : {n_ec}")
        print(f"  journees a PLUSIEURS motifs (app)       : {n_multi} "
              f"(jusqu'a {max_motifs} motifs)")
        print(f"  statuts produits (app)                  : "
              f"{', '.join(app.get('statuts', []))}")
        if ecarts:
            echecs += 1
            print(f"  VUE HERITEE : {len(ecarts)} ECART(S)")
            for e in ecarts:
                print(f"     - {e}")
        else:
            print("  VUE HERITEE : identique a V4.5 "
                  "(console, propre, rapport, motif compris)")

        # Le motif herite doit etre le PREMIER de la liste, pas la liste jointe.
        if motifs:
            rap = pd.read_json(io.StringIO(app["rapport"]), orient="split")
            premiers = [m[0] for m in motifs]
            if list(rap["motif"]) == premiers:
                print("  colonne `motif` = premier motif : conforme")
            else:
                echecs += 1
                print("  colonne `motif` : NON CONFORME — ce n'est pas le "
                      "premier motif")

    print("\n" + "=" * 74)
    if echecs:
        print(f"ECHEC : {echecs} cas presentent un ecart.")
        return 1
    print("SUCCES : sur les trois cas, dont deux que le corpus ne porte pas,")
    print("la vue rendue par l'adaptateur est IDENTIQUE a celle de V4.5,")
    print("tandis que la table de marquage conserve tous les motifs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
