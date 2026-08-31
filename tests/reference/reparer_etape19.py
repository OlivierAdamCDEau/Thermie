"""
reparer_etape19.py — ETAPE 20 : reparer des artefacts d'etape 19 que j'ai ecrases.

CE QUI S'EST PASSE
-------------------
`eprouver_temoin.py` porte `OUT = RACINE / "out" / "etape19"` EN DUR. L'etape 20
demandait de le rejouer INCHANGE, meme sceau — ce qui est la bonne exigence : un
temoin qu'on retouche entre deux epreuves ne compare plus rien. Mais rejouer un
script dont le chemin de sortie est fige le fait ECRIRE DANS L'ETAPE
PRECEDENTE, et c'est ce qui est arrive.

Quatre fichiers d'`out/etape19/` ont ete ecrases par leurs homologues d'etape
20 :
    B_populations.csv   B_synthese.csv   C_faux_negatifs.csv   C_par_point.csv

Ce qui a survecu : les quatre traces console, `C_impact.csv`, `D_bie35.csv`,
`E_mouvements.csv`, `F_aucune_pose.txt`, `REGLE_SCELLEE.txt`.

CE QUI PERMET LA REPARATION
    · `B_populations.csv` d'etape 19 avait ete COPIE avant le rejeu, dans
      `out/etape20/temoin/`. C'est le seul fichier qui ne se deduise pas ; il
      est restitue tel quel, et sa version est verifiable — 69 journees
      marquees contre 150 apres la pose.
    · Les trois autres sont des PROJECTIONS de celui-la. `eprouver_temoin.py`
      les derive par filtres et agregats ; les memes filtres, appliques au
      fichier restitue, les reconstruisent a l'identique.

LA VERIFICATION QUI REND LA REPARATION CREDIBLE
Les chiffres reconstruits sont confrontes a `99_console_epreuve.txt`, qui a
survecu et qui porte les valeurs publiees au rapport d'etape 19 : tau = 0,205 %,
186 faux negatifs, 13 artefacts sur 6 339 journees de controle. Si un seul
chiffre diverge, la reparation est refusee.

CE QUI N'EST PAS CORRIGE, ET POURQUOI
Le chemin en dur de `eprouver_temoin.py` RESTE EN L'ETAT. Le modifier romprait
son sceau, et c'est precisement ce sceau qui donne sa valeur a la comparaison
d'etape 20. Le danger est donc DECLARE plutot que corrige : rejouer ce script
ecrit dans `out/etape19/`, et il faut sauvegarder avant. La correction du chemin
appartient a la cloture, quand le sceau n'aura plus a servir.
"""
from __future__ import annotations

import shutil
import sys

import numpy as np
import pandas as pd

from _commun import RACINE, ecrire_csv, _f

E19 = RACINE / "out" / "etape19"
E20 = RACINE / "out" / "etape20"
TEMOIN20 = E20 / "temoin"
ARTEFACT, COMPATIBLE, INDETERMINABLE = "artefact", "compatible", "indeterminable"
ECRASES = ["B_populations.csv", "B_synthese.csv", "C_faux_negatifs.csv",
           "C_par_point.csv"]


def deriver(pop):
    """Les trois projections, par les memes filtres que `eprouver_temoin.py`."""
    syn = []
    for p in ["B1_les_42", "B2_controle", "B2_controle_voisine", "B3_les_27",
              "hors_appariement"]:
        s = pop[pop.population == p]
        if not len(s):
            continue
        jug = s[s.verdict != INDETERMINABLE]
        n_art = int((s.verdict == ARTEFACT).sum())
        syn.append(dict(
            population=p, n=len(s), n_jugeables=len(jug),
            n_indeterminables=int((s.verdict == INDETERMINABLE).sum()),
            n_artefact=n_art,
            pct_artefact_sur_jugeables=_f(100 * n_art / len(jug) if len(jug) else np.nan),
            exc_median_des_artefacts=_f(
                s.loc[s.verdict == ARTEFACT, "exc"].median() if n_art else np.nan)))
    fn = pop[(pop.marquee == "non") & (pop.verdict == ARTEFACT)].copy()
    pp = []
    if len(fn):
        g = (fn.groupby(["jeu", "point"])
               .agg(n_signalees=("date", "size"), exc_max=("exc", "max"),
                    exc_median=("exc", "median"), premier=("date", "min"),
                    dernier=("date", "max")).reset_index())
        tot = pop[pop.marquee == "non"].groupby(["jeu", "point"]).size()
        g["n_non_marquees"] = g.apply(
            lambda r: int(tot.get((r["jeu"], r["point"]), 0)), axis=1)
        pp = g.to_dict("records")
    return syn, fn, pp


def main():
    print("=" * 78)
    print("ETAPE 20 — REPARATION DES ARTEFACTS D'ETAPE 19 ECRASES")
    print("=" * 78)
    sauv = TEMOIN20 / "B_populations_etape19.csv"
    if not sauv.exists():
        print(f"ECHEC : la sauvegarde {sauv} est absente. Rien n'est repare.")
        return 2

    # --- 1. mettre a l'abri les resultats d'etape 20, qui sont dans etape19/
    TEMOIN20.mkdir(parents=True, exist_ok=True)
    for n in ECRASES:
        src = E19 / n
        if src.exists():
            shutil.copy2(src, TEMOIN20 / n)
            print(f"  etape 20 mis a l'abri : out/etape20/temoin/{n}")

    # --- 2. restituer B_populations.csv
    shutil.copy2(sauv, E19 / "B_populations.csv")
    pop = pd.read_csv(E19 / "B_populations.csv", sep=";", encoding="utf-8")
    n_marq = int((pop.marquee == "oui").sum())
    print(f"\n  B_populations.csv restitue : {len(pop)} lignes, "
          f"{n_marq} journees marquees")
    if n_marq != 69:
        print(f"  ECHEC : {n_marq} journees marquees, 69 attendues pour "
              f"l'etape 19. Rien d'autre n'est ecrit.")
        return 2

    # --- 3. rederiver les trois projections
    syn, fn, pp = deriver(pop)
    ecrire_csv(E19 / "B_synthese.csv",
               ["population", "n", "n_jugeables", "n_indeterminables",
                "n_artefact", "pct_artefact_sur_jugeables",
                "exc_median_des_artefacts"], syn, tri=["population"])
    ecrire_csv(E19 / "C_faux_negatifs.csv",
               ["jeu", "point", "date", "mois", "annee", "population", "exc",
                "dec", "T_eau_moy", "T_air", "R_ampl", "morphologie",
                "n_annees", "n_jours_ref"],
               fn.to_dict("records"), tri=["jeu", "point", "date"])
    ecrire_csv(E19 / "C_par_point.csv",
               ["jeu", "point", "n_signalees", "n_non_marquees", "exc_max",
                "exc_median", "premier", "dernier"], pp,
               tri=["n_signalees", "point"])

    # --- 4. la verification contre la console survivante
    print("\n" + "-" * 78)
    print("  VERIFICATION CONTRE 99_console_epreuve.txt, QUI A SURVECU")
    print("-" * 78)
    ctrl = [s for s in syn if s["population"] == "B2_controle"][0]
    attendus = [
        ("faux negatifs", len(fn), 186),
        ("controle : journees", ctrl["n"], 6428),
        ("controle : jugeables", ctrl["n_jugeables"], 6339),
        ("controle : artefacts", ctrl["n_artefact"], 13),
        ("B1_les_42 : artefacts",
         [s for s in syn if s["population"] == "B1_les_42"][0]["n_artefact"], 16),
        ("B3_les_27 : artefacts",
         [s for s in syn if s["population"] == "B3_les_27"][0]["n_artefact"], 19),
        ("points concernes", len(pp), 15),
    ]
    ok = True
    for lib, obtenu, attendu in attendus:
        bon = (obtenu == attendu)
        ok &= bon
        print(f"  {'OK ' if bon else 'NON'}  {lib:<28} {obtenu:>6}  "
              f"(attendu {attendu})")
    tau = 100 * ctrl["n_artefact"] / ctrl["n_jugeables"]
    print(f"  {'OK ' if abs(tau - 0.205) < 0.001 else 'NON'}  "
          f"{'tau (%)':<28} {tau:>6.3f}  (attendu 0.205)")
    print("-" * 78)
    print("  VERDICT : " + ("REPARATION FIDELE — les artefacts d'etape 19 sont "
                            "ceux qu'elle a publies"
                            if ok else "REPARATION REFUSEE — un chiffre diverge"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
