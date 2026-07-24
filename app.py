"""
app.py — Application Streamlit pour l'analyse thermie & débits.

Interface destinée à une équipe technique : expose les vrais paramètres
(seuils QC, calcul des normales, base de débit) et les diagnostics. Repose
entièrement sur le package thermie_debits (aucune logique de calcul ici).

Lancement : streamlit run app.py
"""
import io
import tempfile
import pandas as pd
import streamlit as st

from thermie_debits.config import (AnalyseConfig, SourcesConfig, QCConfig,
                                    CONTEXTES, __version__, VERSION_DATE,
                                    VERSION_NOTES)
from thermie_debits.orchestrator import run

st.set_page_config(page_title="Thermie & Débits — HMUC Moselle",
                   page_icon="🌡️", layout="wide")


def _save_upload(uploaded):
    if uploaded is None:
        return None
    import os
    suffix = os.path.splitext(uploaded.name)[1] or ".csv"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getvalue()); tmp.close()
    return tmp.name


def _fig_download(fig, label, filename):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    st.download_button(label, buf.getvalue(), file_name=filename,
                       mime="image/png", key=filename)


# ============================================================
# SIDEBAR — Configuration
# ============================================================
st.sidebar.title("🌡️ Configuration")
st.sidebar.caption(f"version **{__version__}** · {VERSION_DATE}")
st.sidebar.caption("Si ce numéro ne correspond pas à la dernière livraison, "
                   "le déploiement n'a pas pris (voir CHANGELOG.md).")

st.sidebar.header("1. Données")
up_eau = st.sidebar.file_uploader("Sonde thermique (eau) *", type=["csv", "xls", "xlsx"])
up_air = st.sidebar.file_uploader(
    "Air — station de référence (brut) *", type=["csv", "xls", "xlsx"],
    help="Températures journalières brutes de la station Météo-France de "
         "référence, couvrant au moins 1991–2020 (et idéalement les années "
         "des mesures d'eau). L'app calcule elle-même normales et écarts. "
         "Colonnes reconnues : AAAAMMJJ + TM (RR optionnel).")

with st.sidebar.expander("📐 Calcul des normales (avancé)"):
    norm_fenetre = st.slider("Lissage des normales (± jours)", 3, 20, 10, 1)
    norm_min_ans = st.number_input("Années minimum sur 1991–2020", 5, 30, 20)
    liss_delta = st.slider(
        "Lissage de l'anomalie d'air pour la compensation (jours)", 1, 15, 7, 1,
        help="La compensation retranche m × (anomalie d'air) à la température "
             "de l'eau. Comme Tmh est une moyenne sur 7 jours et que l'eau "
             "répond à l'air avec inertie, l'anomalie est lissée sur la même "
             "fenêtre : les deux termes sont alors à la même échelle de temps. "
             "Mettre 1 pour revenir à l'anomalie journalière (série beaucoup "
             "plus bruitée).")

st.sidebar.header("2. Contexte & mode")
contexte_key = st.sidebar.selectbox(
    "Contexte piscicole", options=list(CONTEXTES.keys()),
    format_func=lambda k: CONTEXTES[k]["label"], index=1)
mode = st.sidebar.radio(
    "Mode d'analyse", options=["thermie_seule", "thermie_debits"],
    format_func=lambda m: {"thermie_seule": "Thermie seule (SGVT, sans débit)",
                           "thermie_debits": "Thermie + débits de référence"}[m],
    index=1)

up_deb = up_deb_des = None
seuil_comblement = 0.10
if mode == "thermie_debits":
    st.sidebar.caption("Débits (station hydrométrique de rattachement)")
    up_deb = st.sidebar.file_uploader("Débit influencé *", type=["csv"])
    up_deb_des = st.sidebar.file_uploader("Débit désinfluencé (optionnel)", type=["csv"])
    seuil_comblement = st.sidebar.slider(
        "Seuil comblement désinfluencé (écart médian max)", 0.0, 0.30, 0.10, 0.01,
        help="Sous ce seuil, les trous du désinfluencé sont comblés par "
             "l'influencé. Au-dessus, bascule en base influencée.")
    with st.sidebar.expander("🎚️ Déclenchement du volet stress (avancé)"):
        st.caption("Le volet létal déclenche toujours Q_thermie_bio. Le volet "
                   "stress chronique n'est retenu que si le stress est matériel "
                   "ET réellement piloté par le débit.")
        stress_plancher = st.slider("Plancher de matérialité (% jours stressés)",
                                    0.0, 40.0, 10.0, 1.0,
                                    help="En deçà, le milieu ne révèle pas de "
                                         "vulnérabilité chronique : volet écarté.")
        stress_r2 = st.slider("R² minimal de la relation débit↔température",
                              0.0, 0.60, 0.10, 0.01,
                              help="La corrélation doit aussi être négative "
                                   "(l'eau chauffe quand le débit baisse).")
else:
    stress_plancher, stress_r2 = 10.0, 0.10

st.sidebar.header("3. Métadonnées")
nom_ce = st.sidebar.text_input("Nom du cours d'eau", "Cours d'eau")
loc_sonde = st.sidebar.text_input("Localisation de la sonde", "")
nom_station = st.sidebar.text_input("Station hydrométrique de référence", "")

# --- QC avancé ---
with st.sidebar.expander("⚙️ Contrôle qualité (avancé)"):
    qc = QCConfig()
    qc.bornes_physiques = st.checkbox("Bornes physiques", qc.bornes_physiques)
    c1, c2 = st.columns(2)
    qc.t_eau_min = c1.number_input("T_eau min (°C)", value=qc.t_eau_min, step=0.5)
    qc.t_eau_max = c2.number_input("T_eau max (°C)", value=qc.t_eau_max, step=0.5)
    qc.hors_eau = st.checkbox("Détection sonde hors d'eau", qc.hors_eau)
    qc.hors_eau_ecart_seuil = st.slider("Écart hors d'eau seuil (°C)", 1.0, 10.0,
                                        qc.hors_eau_ecart_seuil, 0.5)
    qc.hors_eau_min_jours = st.number_input("Jours suspects min",
                                            value=qc.hors_eau_min_jours, step=1)
    qc.hors_eau_exclut_saison = st.checkbox("Exclure la saison JJAS entière",
                                            qc.hors_eau_exclut_saison)
    qc.plateau = st.checkbox("Détection plateau (sonde bloquée)", qc.plateau)
    qc.mad_outliers = st.checkbox("Outliers MAD", qc.mad_outliers)
    qc.mad_k = st.slider("Seuil MAD (k × MAD)", 10.0, 100.0, qc.mad_k, 5.0)

with st.sidebar.expander("🐟 Paramètres de reproduction (lecture)"):
    _MOIS = {1: "janv", 2: "févr", 3: "mars", 4: "avr", 5: "mai", 6: "juin",
             7: "juil", 8: "août", 9: "sept", 10: "oct", 11: "nov", 12: "déc"}
    for esp, pr in CONTEXTES[contexte_key].get("fraie", {}).items():
        froid = "bloquant" if pr.get("froid_bloquant") else "ralentissant"
        st.markdown(f"**{esp}** · froid {froid}")
        for ph in pr.get("phases", []):
            mois = "-".join(_MOIS[m] for m in ph["mois"])
            crit = " ★" if ph.get("critique") else ""
            st.text(f"  {ph['cle']}{crit} · {mois}\n"
                    f"    optimum {ph['opt'][0]:.0f}–{ph['opt'][1]:.0f}°C, "
                    f"élargie {ph['elargie'][0]:.0f}–{ph['elargie'][1]:.0f}°C")
        if pr.get("src"):
            st.caption(pr["src"])
    st.caption("★ phase critique · au-delà de la fenêtre élargie : létalité "
               "(côté chaud) ou échec reproducteur (côté froid, espèces à "
               "ponte printanière/estivale).")

faire_clim = st.sidebar.checkbox("Inclure le volet climatique (bonus)", False)

# --- Mapping manuel colonnes / feuille Excel ---
eau_cd = eau_ct = air_cd = air_ct = None
eau_feuille = air_feuille = None
eau_ligne_ent = air_ligne_ent = None
with st.sidebar.expander("🔧 Format & colonnes (CSV / Excel)"):
    st.caption("Auto-détection du séparateur, de l'encodage, de la feuille "
               "Excel et de la ligne d'en-tête. Corriger ici si besoin.")
    from thermie_debits.sniff import lire_brut, deviner_colonnes, lister_feuilles, est_excel

    if up_eau is not None:
        try:
            st.markdown("**Sonde (eau)**")
            _feuilles = lister_feuilles(up_eau.getvalue(), up_eau.name)
            if _feuilles:
                eau_feuille = st.selectbox("Feuille Excel (sonde)", _feuilles, key="eauf")
            _dfp, _meta = lire_brut(up_eau.getvalue(), nom=up_eau.name, feuille=eau_feuille)
            fmt = _meta.get("format")
            info = (f"CSV — sép. {_meta.get('separateur')!r}, enc. {_meta.get('encodage')}"
                    if fmt == "csv" else f"Excel — feuille « {_meta.get('feuille')} »")
            st.caption(f"{info} · en-tête détecté ligne {_meta.get('ligne_entete')}")
            eau_ligne_ent = st.number_input("Ligne d'en-tête (sonde)", 0, 30,
                                            int(_meta.get("ligne_entete", 0)), key="eaul")
            if eau_ligne_ent != _meta.get("ligne_entete"):
                _dfp, _meta = lire_brut(up_eau.getvalue(), nom=up_eau.name,
                                        feuille=eau_feuille, ligne_entete=eau_ligne_ent)
            _cd, _ct = deviner_colonnes(_dfp)
            cols = ["auto"] + list(_dfp.columns)
            s1 = st.selectbox("Colonne date", cols,
                              index=cols.index(_cd) if _cd in cols else 0, key="eaucd")
            s2 = st.selectbox("Colonne température", cols,
                              index=cols.index(_ct) if _ct in cols else 0, key="eauct")
            eau_cd = None if s1 == "auto" else s1
            eau_ct = None if s2 == "auto" else s2
            st.dataframe(_dfp.head(3), use_container_width=True)
        except Exception as e:
            st.warning(f"Aperçu sonde indisponible : {e}")

    if up_air is not None:
        try:
            st.markdown("**Air (référence)**")
            _feuillesa = lister_feuilles(up_air.getvalue(), up_air.name)
            if _feuillesa:
                air_feuille = st.selectbox("Feuille Excel (air)", _feuillesa, key="airf")
            _dfa, _ma = lire_brut(up_air.getvalue(), nom=up_air.name, feuille=air_feuille)
            air_ligne_ent = int(_ma.get("ligne_entete", 0))
            colsa = ["auto"] + list(_dfa.columns)
            _adc = next((c for c in _dfa.columns if c.upper() == "AAAAMMJJ"), "auto")
            _atc = next((c for c in _dfa.columns if c.upper() == "TM"), "auto")
            a1 = st.selectbox("Colonne date (air)", colsa,
                              index=colsa.index(_adc) if _adc in colsa else 0, key="aircd")
            a2 = st.selectbox("Colonne température (air)", colsa,
                              index=colsa.index(_atc) if _atc in colsa else 0, key="airct")
            air_cd = None if a1 == "auto" else a1
            air_ct = None if a2 == "auto" else a2
        except Exception as e:
            st.warning(f"Aperçu air indisponible : {e}")

lancer = st.sidebar.button("▶️  Lancer l'analyse", type="primary",
                           use_container_width=True)


# ============================================================
# ZONE PRINCIPALE
# ============================================================
st.title("Analyse thermie & débits de référence")
st.caption(f"HMUC Moselle — approche thermique (note méthodologique Point 2) · application v{__version__} ({VERSION_DATE})")
with st.expander("ℹ️ Contenu de cette version"):
    st.markdown(f"**v{__version__}** — {VERSION_NOTES}")


def _inputs_ok():
    if not (up_eau and up_air):
        return False, "Fournissez au minimum : sonde eau et air (station de référence)."
    if mode == "thermie_debits" and not up_deb:
        return False, "Mode thermie+débits : fournissez le débit influencé "\
                      "(ou passez en mode thermie seule)."
    return True, ""


if lancer:
    ok, msg = _inputs_ok()
    if not ok:
        st.error(msg); st.stop()
    src = SourcesConfig(
        fichier_eau=_save_upload(up_eau), fichier_air=_save_upload(up_air),
        fichier_normales=None,
        fichier_debit=_save_upload(up_deb) if up_deb else None,
        fichier_debit_desinf=_save_upload(up_deb_des) if up_deb_des else None,
        eau_col_date=eau_cd, eau_col_temp=eau_ct,
        air_col_date=air_cd, air_col_temp=air_ct,
        eau_nom_fichier=up_eau.name if up_eau else "",
        eau_feuille=eau_feuille, eau_ligne_entete=eau_ligne_ent,
        air_nom_fichier=up_air.name if up_air else "",
        air_feuille=air_feuille, air_ligne_entete=air_ligne_ent,
        nom_cours_eau=nom_ce, localisation_sonde=loc_sonde,
        nom_station_debit=nom_station)
    cfg = AnalyseConfig(sources=src, qc=qc, contexte_piscicole=contexte_key,
                        mode=mode, faire_volet_climatique=faire_clim,
                        seuil_comblement_desinf=seuil_comblement,
                        normales_fenetre_lissage=norm_fenetre,
                        normales_min_annees=norm_min_ans,
                        normalisation_lissage_delta=liss_delta,
                        stress_plancher_pct=stress_plancher,
                        stress_corr_r2_min=stress_r2, output_dir=None)
    with st.spinner("Analyse en cours..."):
        try:
            res = run(cfg, verbose=False)
        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
            st.stop()
    st.session_state["res"] = res


res = st.session_state.get("res")
if res is None:
    st.info("Configurez l'analyse dans le panneau de gauche puis cliquez sur "
            "**Lancer l'analyse**.")
    st.stop()

ctx = res.contexte
sg = res.sgvt

# --- Bandeau ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("SGVT", f"{sg['sgvt']:.2f} / 10", sg["interp"])
c2.metric("Composantes SGVT", f"{sg['composantes']}")
c3.metric("Contexte", res.config.contexte_piscicole)
c4.metric("Base débit", res.base_debit)

for av in res.avertissements:
    st.warning(av)
if res.config.avec_debits:
    st.caption(f"ℹ️ {res.entete_base_debit}")
dn = res.diag_normales
if dn.get("n_annees_ref") is not None:
    st.caption(f"📐 Normales 1991–2020 : {dn['n_annees_ref']} année(s), "
               f"lissage ±{dn['fenetre_lissage']}j · air couvre "
               f"{dn['periode_totale'][0]}–{dn['periode_totale'][1]}")
elif dn.get("source"):
    st.caption(f"📐 Normales : {dn['source']}")

# --- Onglets ---
noms = ["📊 Synthèse", "🧹 QC", "📈 Sensibilité", "🌡️ Vulnérabilité", "🐟 Fraie",
        "📉 Indicateurs"]
if res.config.avec_debits:
    noms.append("🔗 Relation Q–T°")
    noms.append("💧 Débits")
if res.figures_climatiques:
    noms.append("🌍 Climatique")
ong = st.tabs(noms)

with ong[0]:
    # --- Cadre de lecture : que permet de conclure l'approche thermique ? ---
    mat = getattr(res, "matrice", None)
    if mat:
        st.subheader("Que permet de conclure l'approche thermique ?")
        boite = {1: st.error, 2: st.warning, 3: st.success, 4: st.info}
        boite.get(mat["case"], st.info)(
            f"**{mat['libelle']}** — {mat['conduite']}")
        c1, c2 = st.columns(2)
        c1.metric("Problème thermique",
                  "avéré" if mat["probleme"] else "non constaté",
                  mat["motif_probleme"], delta_color="off")
        c2.metric("Levier débit",
                  "opérant" if mat["levier"] else "non opérant",
                  mat["motif_levier"], delta_color="off")
        if res.figures.get("matrice") is not None:
            st.pyplot(res.figures["matrice"])
            _fig_download(res.figures["matrice"], "⬇️ PNG matrice",
                          "Matrice_Diagnostic.png")
        st.divider()

    if res.figures.get("synthese") is not None:
        st.pyplot(res.figures["synthese"])
        _fig_download(res.figures["synthese"], "⬇️ PNG synthèse", "Synthese_SGVT.png")
    if res.figures.get("chronique") is not None:
        st.subheader("Chronique thermique")
        st.pyplot(res.figures["chronique"])

with ong[1]:
    st.subheader("Contrôle qualité — artefacts écartés")
    rq = res.rapport_qc
    if rq is not None and len(rq):
        st.write(f"**{len(rq)} enregistrement(s) écarté(s)**")
        if res.figures.get("qc") is not None:
            st.pyplot(res.figures["qc"])
        st.dataframe(rq, use_container_width=True, height=260)
        st.download_button("⬇️ Rapport QC (CSV)",
                           rq.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           "rapport_qualite.csv", "text/csv")
    else:
        st.success("Aucun artefact détecté.")

with ong[2]:
    s = res.sensibilite
    c1, c2, c3 = st.columns(3)
    c1.metric("Pente m", f"{s['m']:.3f}", s["sens_cat"])
    c2.metric("R²", f"{s['r2']:.3f}", s["r2_cat"])
    c3.metric("Robustesse |ρ−r|", f"{s['robustesse']:.4f}", s["rob_cat"])
    if res.figures.get("sensibilite") is not None:
        st.pyplot(res.figures["sensibilite"])

with ong[3]:
    v = res.vulnerabilite
    c1, c2 = st.columns(2)
    c1.metric(f"Stress chronique (>{v['seuil_chr']}°C)", f"{v['pct_chr']:.1f}%", v["cat_chr"])
    c2.metric(f"Létalité aiguë (>{v['seuil_aigu']}°C)", f"{v['n_aigu']} j", v["cat_aigu"])
    if res.figures.get("vulnerabilite") is not None:
        st.pyplot(res.figures["vulnerabilite"])

with ong[4]:
    fr = res.fraie
    if fr is None:
        st.info("Pas de composante fraie pour ce contexte.")
    elif not fr.get("disponible"):
        st.warning("Composante fraie non évaluée (chronique lacunaire sur les "
                   "mois centraux). Le SGVT est calculé sur 3 composantes.")
    else:
        st.metric("P_fraie", fr["P_fraie"],
                  f"repère : {fr['espece_limitante']} ({fr.get('n_annees','?')} an)")
    if fr:
        st.caption("Trois phases successives — **pré-frai**, **ponte**, "
                   "**incubation** — aux tolérances thermiques distinctes. Pour "
                   "chacune : optimum strict (aucune pénalité), tolérance "
                   "élargie (pénalité intermédiaire), au-delà = létalité ou "
                   "échec reproducteur (pénalité forte). Calculs sur "
                   "**températures normalisées**.")

        # --- Synthèse par espèce ---
        rows = []
        for si in fr.get("sous_indicateurs", []):
            ev = si.get("evalue")
            rows.append({
                "Espèce": si["espece"],
                "Statut": "évalué" if ev else "non évalué",
                "% optimum": f"{si['pct_optimum']:.0f}" if ev else "—",
                "% élargie": f"{si['pct_elargie']:.0f}" if ev else "—",
                "% létal": f"{si['pct_letal']:.0f}" if ev else "—",
                "Sévérité moy.": f"{si['sev_moy']:.2f}" if ev else "—",
                "Froid": ("bloquant" if si.get("froid_bloquant") else
                          "ralentissant") if ev else "—",
                "Catégorie": si.get("cat", si.get("motif", "—"))})
        st.dataframe(rows, use_container_width=True)

        # --- Détail par phase ---
        st.markdown("**Détail par phase de reproduction**")
        rows_ph = []
        for si in fr.get("sous_indicateurs", []):
            for ph in si.get("phases", []):
                if not ph.get("n"):
                    rows_ph.append({"Espèce": si["espece"], "Phase": ph["nom"],
                                    "Fenêtre °C": "—", "n (jours)": 0,
                                    "% optimum": "—", "% élargie": "—",
                                    "% létal": "—", "Couverture": "aucune donnée"})
                    continue
                rows_ph.append({
                    "Espèce": si["espece"],
                    "Phase": ph["nom"] + (" ★" if ph.get("critique") else ""),
                    "Fenêtre °C": f"{ph['opt'][0]:.0f}–{ph['opt'][1]:.0f} "
                                  f"(élargie {ph['elargie'][0]:.0f}–{ph['elargie'][1]:.0f})",
                    "n (jours)": ph["n"],
                    "% optimum": f"{ph['pct_optimum']:.0f}",
                    "% élargie": f"{ph['pct_elargie']:.0f}",
                    "% létal": f"{ph['pct_letal']:.0f}",
                    "Couverture": ("mois central couvert" if ph.get("evaluee")
                                   else "mois central lacunaire")})
        st.dataframe(rows_ph, use_container_width=True)
        st.caption("★ phase critique : au moins une doit être couverte pour que "
                   "le sous-indicateur soit évalué. En pré-frai, une eau trop "
                   "froide décale le frai sans le compromettre — la pénalité y "
                   "reste intermédiaire.")

        # --- Températures brutes (information) ---
        rows_brut = [{"Espèce": si["espece"],
                      "% optimum (brut)": f"{si['pct_optimum_brut']:.0f}",
                      "% élargie (brut)": f"{si['pct_elargie_brut']:.0f}",
                      "% létal (brut)": f"{si['pct_letal_brut']:.0f}"}
                     for si in fr.get("sous_indicateurs", []) if si.get("evalue")]
        if rows_brut:
            with st.expander("🌡️ Températures brutes non compensées (information)"):
                st.caption("Ces valeurs n'entrent pas dans le score. Elles "
                           "montrent ce qu'ont réellement subi les stades "
                           "précoces sur la période observée, sans "
                           "normalisation climatique.")
                st.dataframe(rows_brut, use_container_width=True)

        # --- Références bibliographiques ---
        srcs = {si["espece"]: si.get("src", "") for si in
                fr.get("sous_indicateurs", []) if si.get("src")}
        if srcs:
            with st.expander("📚 Références bibliographiques des seuils"):
                for e, src in srcs.items():
                    st.markdown(f"**{e.capitalize()}** — {src}")
    if res.figures.get("fraie") is not None:
        st.pyplot(res.figures["fraie"])

# Indicateurs
if "📉 Indicateurs" in noms and res.indicateurs is not None:
    with ong[noms.index("📉 Indicateurs")]:
        st.subheader("Indicateurs thermiques — bruts et compensés")
        st.caption("Compensé = ramené aux conditions normales (écart aux "
                   "normales 1991–2020 retiré). Amplitude nycthémérale = "
                   "écart Tmax−Tmin journalier (variation jour/nuit).")
        table = res.indicateurs["table_mensuelle"]
        st.dataframe(table, use_container_width=True, height=380)
        st.download_button(
            "⬇️ Indicateurs (CSV)",
            table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "indicateurs_thermiques.csv", "text/csv")

        st.subheader("Corrélations")
        cors = res.indicateurs["correlations"]
        n_ok = len([c for c in cors.values() if c.get("n", 0) >= 5])
        if n_ok == 0:
            st.info("Corrélations indisponibles (données insuffisantes ou "
                    "débit/air manquant).")
        else:
            if res.figures.get("correlations") is not None:
                st.pyplot(res.figures["correlations"])
                _fig_download(res.figures["correlations"],
                              "⬇️ PNG corrélations", "Correlations.png")
            # Récapitulatif chiffré des R²
            recap = [{"Corrélation": c["ylabel"] + " ~ " + c["xlabel"],
                      "R²": round(c["r2"], 3), "Pente": round(c["pente"], 3),
                      "n": c["n"]}
                     for c in cors.values() if c.get("n", 0) >= 5]
            st.dataframe(recap, use_container_width=True)

# Relation débit ↔ température (test préalable)
if "🔗 Relation Q–T°" in noms:
    with ong[noms.index("🔗 Relation Q–T°")]:
        rel = res.relation_debit_temp
        st.subheader("Le débit module-t-il la température de l'eau ?")
        st.caption("Postulat fondateur de l'approche « débits thermiques » : "
                   "si le débit ne pilote pas la température, agir sur le débit "
                   "n'améliorera pas la situation thermique. Ce test est "
                   "**informatif** — il n'interrompt aucun calcul, mais qualifie "
                   "la portée des débits obtenus.")
        if not rel or not rel.get("disponible"):
            st.info(rel.get("message", "Test non réalisable.") if rel
                    else "Test non réalisable.")
        else:
            couleurs = {"etablie": st.success, "faible": st.warning,
                        "absente": st.warning, "inversee": st.error}
            couleurs.get(rel["verdict"], st.info)(
                f"**{rel['libelle']}** — {rel['commentaire']}")

            st.markdown("**Corrélations par gamme de débit**")
            st.caption("La corrélation *brute* inclut l'effet structurel du "
                       "régime d'étiage ; la corrélation *partielle* isole le "
                       "rôle propre du débit, à température d'air égale.")
            lignes = []
            for l in rel["lignes"]:
                lignes.append({
                    "Gamme de débit": l["gamme"],
                    "n (jours)": l["n"],
                    "r brute": f"{l['r_brute']:+.3f}" if l["r_brute"] == l["r_brute"] else "—",
                    "R² brute": f"{l['r2_brute']:.3f}" if l["r2_brute"] == l["r2_brute"] else "—",
                    "r partielle": f"{l['r_partielle']:+.3f}" if l["r_partielle"] == l["r_partielle"] else "—",
                    "R² partielle": f"{l['r2_partielle']:.3f}" if l["r2_partielle"] == l["r2_partielle"] else "—",
                    "Concluante": "oui" if l["concluante"] else "non"})
            st.dataframe(lignes, use_container_width=True)

            # Lecture automatique de la tendance par gamme (effet de seuil)
            r2s = [l["r2_partielle"] for l in rel["lignes"]
                   if l["r2_partielle"] == l["r2_partielle"]]
            if len(r2s) == 3:
                if r2s[2] > r2s[0] * 1.15:
                    st.info("📈 La relation **se renforce vers les bas débits** "
                            "malgré la réduction de la gamme : signature d'un "
                            "effet de seuil, l'inertie thermique se perdant "
                            "surtout en étiage prononcé.")
                elif r2s[2] < r2s[0] * 0.6:
                    st.info("📉 La relation **s'affaiblit vers les bas débits**. "
                            "Une part est attribuable à la réduction de variance, "
                            "mais cela peut aussi signaler que l'effet observé "
                            "sur toute la gamme relève surtout de la covariation "
                            "saisonnière.")

            _m = getattr(res, "matrice", None)
            if _m:
                st.caption(
                    f"↳ Croisé avec le diagnostic de vulnérabilité, cela place "
                    f"la station en **« {_m['libelle']} »** "
                    f"(voir la matrice en tête de l'onglet Synthèse).")
            st.caption("Ces corrélations sont la **source unique** du projet : "
                       "le verrou du volet stress chronique (onglet Débits) "
                       "consomme exactement les mêmes valeurs.")

            if res.figures.get("relation_debit_temp") is not None:
                st.pyplot(res.figures["relation_debit_temp"])
                _fig_download(res.figures["relation_debit_temp"],
                              "⬇️ PNG relation Q–T°", "Relation_Q_T.png")

            st.download_button(
                "⬇️ Corrélations (CSV)",
                pd.DataFrame(lignes).to_csv(index=False, sep=";",
                                            decimal=",").encode("utf-8-sig"),
                "relation_debit_temperature.csv", "text/csv")

# Débits
if res.config.avec_debits and "💧 Débits" in noms:
    with ong[noms.index("💧 Débits")]:
        ds = res.debits_sorties
        # Réserve méthodologique si la relation débit–température n'est pas établie
        _rel = res.relation_debit_temp
        if _rel and _rel.get("disponible") and _rel.get("verdict") != "etablie":
            _f = {"faible": st.warning, "absente": st.warning,
                  "inversee": st.error}.get(_rel["verdict"], st.info)
            _f(f"⚠️ **Réserve méthodologique — {_rel['libelle'].lower()}.** "
               f"{_rel['commentaire']} Les débits ci-dessous restent calculés, "
               f"mais leur portée opérationnelle doit être appréciée à la "
               f"lumière de ce constat (voir l'onglet « Relation Q–T° »).")

        st.subheader("Débits de référence — station de rattachement")
        if res.config.sources.nom_station_debit:
            st.caption(f"Station : {res.config.sources.nom_station_debit}")

        def _afficher_debit(cle, titre, principal=True):
            d = ds.get(cle, {})
            if not d or d.get("valeur") is None:
                st.info(f"{titre} : non applicable.")
                return
            val = d["valeur"]
            pnd_des = d.get("pnda_desinf")
            pnd_inf = d.get("pnda_inf")
            st.markdown(f"**{titre}**")
            col1, col2 = st.columns([2, 1])
            # Priorité désinfluencé
            if pnd_des is not None:
                col1.metric(f"{val:.3f} m³/s", f"PNDA désinfluencé : {pnd_des:.0f}%",
                            help="Valeur brute (base de calcul) et sa probabilité "
                                 "de non-dépassement sur la courbe désinfluencée.")
                if pnd_inf is not None:
                    col2.caption(f"↳ pour information (influencé) :\n"
                                 f"PNDA influencé = {pnd_inf:.0f}%")
            else:
                # Désinfluencé absent → influencé en principal
                col1.metric(f"{val:.3f} m³/s",
                            f"PNDA influencé : {pnd_inf:.0f}%" if pnd_inf is not None else "—")
                col2.caption("↳ désinfluencé non fourni")

        _afficher_debit("q_thermie_bio", "Q_thermie_bio — résultat principal")
        st.divider()
        _afficher_debit("q_thermie_fonc", "Q_thermie_fonc — information complémentaire")

        # Diagnostic du volet stress (déclenché ou écarté, et pourquoi)
        di = res.debits_inflexion or {}
        dstr = di.get("diag_stress")
        if dstr:
            st.divider()
            st.subheader("Volet stress chronique — diagnostic de déclenchement")
            c1, c2, c3 = st.columns(3)
            c1.metric("Stress estival global",
                      f"{dstr['pct_stress_global']:.1f} %",
                      f"plancher {dstr['plancher']:.0f} %",
                      delta_color="off")
            rp = dstr.get("r_partielle")
            rb = dstr.get("r_qt")
            c2.metric("Corrélation débit ↔ T° (à air égal)",
                      f"{rp:+.2f}" if (rp is not None and rp == rp) else "—",
                      f"R² = {dstr['r2_partielle']:.2f}"
                      if dstr.get("r2_partielle") == dstr.get("r2_partielle") else "—",
                      delta_color="off",
                      help="Corrélation partielle : effet du débit sur la "
                           "température de l'eau à forçage atmosphérique égal. "
                           "Robuste même sur une seule saison.")
            c3.metric("Volet stress",
                      "retenu" if dstr["stress_actif"] else "écarté")
            def _f(v):
                return f"{v:+.2f}" if (v is not None and v == v) else "n.d."
            st.caption(
                f"Corrélation brute = {_f(rb)} "
                f"(R²={dstr.get('r2_qt', float('nan')):.2f}, "
                f"{'concluante' if dstr.get('causal_brut') else 'non concluante'}) · "
                f"partielle à air égal = {_f(rp)} "
                f"(R²={dstr.get('r2_partielle', float('nan')):.2f}, "
                f"{'concluante' if dstr.get('causal_partielle') else 'non concluante'}). "
                f"Le verrou s'ouvre si l'une des deux est concluante.")
            if dstr["stress_actif"]:
                st.success("Les deux conditions sont réunies (stress matériel et "
                           "réellement piloté par le débit) : le volet stress "
                           "contribue à Q_thermie_bio.")
            else:
                st.info(f"Volet stress écarté — {dstr['raison']}. "
                        f"Q_thermie_bio repose sur le seul volet létal "
                        f"(ou devient non applicable). Agir sur le débit ne "
                        f"réduirait pas significativement le stress observé.")

        st.divider()
        for k, t in [("debits_vuln", "Q_thermie_bio — vulnérabilité vs débit"),
                     ("debits_inflexion", "Q_thermie_fonc — inflexion thermique"),
                     ("debits_classes", "Débits classés (PNDA)")]:
            if res.figures.get(k) is not None:
                st.subheader(t)
                st.pyplot(res.figures[k])

# Climatique
if res.figures_climatiques and "🌍 Climatique" in noms:
    with ong[noms.index("🌍 Climatique")]:
        st.caption("Volet descriptif sur données brutes (contexte observé réel).")
        for f in res.figures_climatiques:
            st.pyplot(f)
