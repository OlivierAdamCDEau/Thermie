"""
app.py — Application Streamlit pour l'analyse thermie & débits.

Interface destinée à une équipe technique : expose les vrais paramètres
(seuils QC, fenêtres de fraie, base de débit) et les diagnostics. Repose
entièrement sur le package thermie_debits (aucune logique de calcul ici).

Lancement : streamlit run app.py
"""
import tempfile
from pathlib import Path
import streamlit as st

from thermie_debits.config import (AnalyseConfig, SourcesConfig, QCConfig,
                                    CONTEXTES)
from thermie_debits.orchestrator import run

st.set_page_config(page_title="Thermie & Débits — HMUC Moselle",
                   page_icon="🌡️", layout="wide")


# ============================================================
# Utilitaires
# ============================================================
def _save_upload(uploaded, suffix=".csv"):
    """Écrit un fichier uploadé en temporaire et retourne son chemin."""
    if uploaded is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getvalue())
    tmp.close()
    return tmp.name


def _fig_download(fig, label, filename):
    """Bouton de téléchargement PNG d'une figure matplotlib."""
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    st.download_button(label, buf.getvalue(), file_name=filename,
                       mime="image/png", key=filename)


# ============================================================
# SIDEBAR — Configuration
# ============================================================
st.sidebar.title("🌡️ Configuration")

st.sidebar.header("1. Données")
up_eau  = st.sidebar.file_uploader("Sonde thermique (eau) *", type=["csv"])
up_air  = st.sidebar.file_uploader(
    "Air — station de référence (brut) *", type=["csv"],
    help="Températures journalières brutes de la station Météo-France de "
         "référence, couvrant au moins 1991–2020 (et idéalement les années "
         "des mesures d'eau). L'app calcule elle-même les normales et les "
         "écarts. Colonnes reconnues : AAAAMMJJ + TM (RR optionnel).")

with st.sidebar.expander("📐 Calcul des normales (avancé)"):
    norm_fenetre = st.slider("Lissage des normales (± jours)", 3, 20, 10, 1,
                             help="Fenêtre glissante circulaire pour lisser la "
                                  "normale de chaque jour calendaire.")
    norm_min_ans = st.number_input("Années minimum sur 1991–2020", 5, 30, 20,
                                   help="En deçà, un avertissement est émis "
                                        "(normales moins fiables).")

st.sidebar.header("2. Contexte & mode")
contexte_key = st.sidebar.selectbox(
    "Contexte piscicole",
    options=list(CONTEXTES.keys()),
    format_func=lambda k: CONTEXTES[k]["label"], index=1)

mode = st.sidebar.radio(
    "Mode d'analyse",
    options=["thermie_seule", "thermie_debits"],
    format_func=lambda m: {"thermie_seule": "Thermie seule (SGVT, sans débit)",
                           "thermie_debits": "Thermie + débits de référence"}[m],
    index=1)

up_deb = up_deb_des = None
seuil_comblement = 0.10
if mode == "thermie_debits":
    st.sidebar.caption("Débits (station hydrométrique)")
    up_deb = st.sidebar.file_uploader("Débit influencé *", type=["csv"])
    up_deb_des = st.sidebar.file_uploader("Débit désinfluencé (optionnel)",
                                          type=["csv"])
    seuil_comblement = st.sidebar.slider(
        "Seuil comblement désinfluencé (écart médian max)",
        0.0, 0.30, 0.10, 0.01,
        help="Sous ce seuil, les trous du désinfluencé sont comblés par "
             "l'influencé. Au-dessus, bascule en base influencée.")

st.sidebar.header("3. Métadonnées")
nom_ce = st.sidebar.text_input("Nom du cours d'eau", "Cours d'eau")
loc_sonde = st.sidebar.text_input("Localisation de la sonde", "")

# --- Paramètres avancés QC ---
with st.sidebar.expander("⚙️ Contrôle qualité (avancé)"):
    qc = QCConfig()
    qc.bornes_physiques = st.checkbox("Bornes physiques", qc.bornes_physiques)
    c1, c2 = st.columns(2)
    qc.t_eau_min = c1.number_input("T_eau min (°C)", value=qc.t_eau_min, step=0.5)
    qc.t_eau_max = c2.number_input("T_eau max (°C)", value=qc.t_eau_max, step=0.5)
    qc.hors_eau = st.checkbox("Détection sonde hors d'eau", qc.hors_eau)
    qc.hors_eau_ecart_seuil = st.slider("Écart hors d'eau seuil (°C)", 1.0, 10.0,
                                        qc.hors_eau_ecart_seuil, 0.5)
    qc.hors_eau_min_jours = st.number_input("Jours suspects min", value=qc.hors_eau_min_jours, step=1)
    qc.hors_eau_exclut_saison = st.checkbox("Exclure la saison JJAS entière",
                                            qc.hors_eau_exclut_saison)
    qc.plateau = st.checkbox("Détection plateau (sonde bloquée)", qc.plateau)
    qc.mad_outliers = st.checkbox("Outliers MAD", qc.mad_outliers)
    qc.mad_k = st.slider("Seuil MAD (k × MAD)", 10.0, 100.0, qc.mad_k, 5.0)

with st.sidebar.expander("🐟 Paramètres fraie (lecture)"):
    st.caption("Fenêtres et seuils par espèce du contexte sélectionné :")
    for esp, pr in CONTEXTES[contexte_key].get("fraie", {}).items():
        mois = "-".join(map(str, pr["fenetre"]))
        st.text(f"{esp}\n  fenêtre {mois} (central {pr['mois_central']})\n"
                f"  optimum {pr['opt'][0]}–{pr['opt'][1]}°C, rés. {pr['res']}°C")

faire_clim = st.sidebar.checkbox("Inclure le volet climatique (bonus)", False)

# --- Mapping manuel des colonnes (si auto-détection à corriger) ---
eau_cd = eau_ct = air_cd = air_ct = None
with st.sidebar.expander("🔧 Mapping colonnes (si détection erronée)"):
    st.caption("Laisser sur « auto » sauf si le chargement échoue ou détecte "
               "les mauvaises colonnes.")
    if up_eau is not None:
        try:
            from thermie_debits.sniff import lire_brut, deviner_colonnes
            _dfp, _meta = lire_brut(up_eau.getvalue())
            _cd, _ct = deviner_colonnes(_dfp)
            st.text(f"Sonde — sép. détecté : {_meta['separateur']!r}")
            cols = ["auto"] + list(_dfp.columns)
            sel_cd = st.selectbox("Sonde : colonne date",
                                  cols, index=cols.index(_cd) if _cd in cols else 0)
            sel_ct = st.selectbox("Sonde : colonne température",
                                  cols, index=cols.index(_ct) if _ct in cols else 0)
            eau_cd = None if sel_cd == "auto" else sel_cd
            eau_ct = None if sel_ct == "auto" else sel_ct
            st.dataframe(_dfp.head(3), use_container_width=True)
        except Exception as e:
            st.warning(f"Aperçu sonde indisponible : {e}")
    if up_air is not None:
        try:
            from thermie_debits.sniff import lire_brut
            _dfa, _metaa = lire_brut(up_air.getvalue())
            st.text(f"Air — sép. détecté : {_metaa['separateur']!r}")
            colsa = ["auto"] + list(_dfa.columns)
            _adc = next((c for c in _dfa.columns if c.upper() == "AAAAMMJJ"), "auto")
            _atc = next((c for c in _dfa.columns if c.upper() == "TM"), "auto")
            sa_cd = st.selectbox("Air : colonne date", colsa,
                                 index=colsa.index(_adc) if _adc in colsa else 0)
            sa_ct = st.selectbox("Air : colonne température", colsa,
                                 index=colsa.index(_atc) if _atc in colsa else 0)
            air_cd = None if sa_cd == "auto" else sa_cd
            air_ct = None if sa_ct == "auto" else sa_ct
        except Exception as e:
            st.warning(f"Aperçu air indisponible : {e}")

lancer = st.sidebar.button("▶️  Lancer l'analyse", type="primary",
                           use_container_width=True)


# ============================================================
# ZONE PRINCIPALE
# ============================================================
st.title("Analyse thermie & débits de référence")
st.caption("HMUC Moselle — approche thermique (note méthodologique Point 2)")

# Validation des entrées requises
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
        st.error(msg)
        st.stop()

    # Construire la config
    src = SourcesConfig(
        fichier_eau=_save_upload(up_eau), fichier_air=_save_upload(up_air),
        fichier_normales=None,   # calcul auto des normales depuis l'air brut
        fichier_debit=_save_upload(up_deb) if up_deb else None,
        fichier_debit_desinf=_save_upload(up_deb_des) if up_deb_des else None,
        eau_col_date=eau_cd, eau_col_temp=eau_ct,
        air_col_date=air_cd, air_col_temp=air_ct,
        nom_cours_eau=nom_ce, localisation_sonde=loc_sonde)
    cfg = AnalyseConfig(sources=src, qc=qc, contexte_piscicole=contexte_key,
                        mode=mode, faire_volet_climatique=faire_clim,
                        seuil_comblement_desinf=seuil_comblement,
                        normales_fenetre_lissage=norm_fenetre,
                        normales_min_annees=norm_min_ans,
                        output_dir=None)

    with st.spinner("Analyse en cours..."):
        try:
            res = run(cfg, verbose=False)
        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
            st.exception(e)
            st.stop()
    st.session_state["res"] = res


# ============================================================
# AFFICHAGE DES RÉSULTATS
# ============================================================
res = st.session_state.get("res")
if res is None:
    st.info("Configurez l'analyse dans le panneau de gauche puis cliquez sur "
            "**Lancer l'analyse**.")
    st.stop()

ctx = res.contexte
sg = res.sgvt

# --- Bandeau de traçabilité ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("SGVT", f"{sg['sgvt']:.2f} / 10", sg["interp"])
c2.metric("Composantes SGVT", f"{sg['composantes']}")
c3.metric("Contexte", res.config.contexte_piscicole)
c4.metric("Base débit", res.base_debit)

# Avertissements (bascule débit, normales, etc.)
for av in res.avertissements:
    st.warning(av)
if res.config.avec_debits:
    st.caption(f"ℹ️ {res.entete_base_debit}")
# Traçabilité des normales
dn = res.diag_normales
if dn.get("n_annees_ref") is not None:
    st.caption(f"📐 Normales 1991–2020 : {dn['n_annees_ref']} année(s), "
               f"lissage ±{dn['fenetre_lissage']}j · air couvre "
               f"{dn['periode_totale'][0]}–{dn['periode_totale'][1]}")
elif dn.get("source"):
    st.caption(f"📐 Normales : {dn['source']}")

# --- Onglets ---
noms_onglets = ["📊 Synthèse", "🧹 QC", "📈 Sensibilité", "🌡️ Vulnérabilité",
                "🐟 Fraie"]
if res.config.avec_debits:
    noms_onglets.append("💧 Débits")
if res.figures_climatiques:
    noms_onglets.append("🌍 Climatique")
onglets = st.tabs(noms_onglets)

# Synthèse
with onglets[0]:
    if res.figures.get("synthese") is not None:
        st.pyplot(res.figures["synthese"])
        _fig_download(res.figures["synthese"], "⬇️ PNG synthèse", "Synthese_SGVT.png")
    st.subheader("Chronique thermique")
    if res.figures.get("chronique") is not None:
        st.pyplot(res.figures["chronique"])

# QC
with onglets[1]:
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

# Sensibilité
with onglets[2]:
    s = res.sensibilite
    c1, c2, c3 = st.columns(3)
    c1.metric("Pente m", f"{s['m']:.3f}", s["sens_cat"])
    c2.metric("R²", f"{s['r2']:.3f}", s["r2_cat"])
    c3.metric("Robustesse |ρ−r|", f"{s['robustesse']:.4f}", s["rob_cat"])
    if res.figures.get("sensibilite") is not None:
        st.pyplot(res.figures["sensibilite"])

# Vulnérabilité
with onglets[3]:
    v = res.vulnerabilite
    c1, c2 = st.columns(2)
    c1.metric(f"Stress chronique (>{v['seuil_chr']}°C)", f"{v['pct_chr']:.1f}%", v["cat_chr"])
    c2.metric(f"Létalité aiguë (>{v['seuil_aigu']}°C)", f"{v['n_aigu']} j", v["cat_aigu"])
    if res.figures.get("vulnerabilite") is not None:
        st.pyplot(res.figures["vulnerabilite"])

# Fraie
with onglets[4]:
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
        st.write("**Détail des sous-indicateurs :**")
        rows = []
        for si in fr.get("sous_indicateurs", []):
            rows.append(dict(
                Espèce=si["espece"],
                Statut="évalué" if si.get("evalue") else "non évalué",
                **{"% hors optimum": f"{si['pct']:.1f}" if si.get("evalue") else "—"},
                **{"Mois central (j)": si.get("n_central", "—")},
                **{"Années": si.get("n_annees", "—")},
                Catégorie=si.get("cat", "—")))
        st.dataframe(rows, use_container_width=True)
    if res.figures.get("fraie") is not None:
        st.pyplot(res.figures["fraie"])

# Débits
if res.config.avec_debits and "💧 Débits" in noms_onglets:
    idx = noms_onglets.index("💧 Débits")
    with onglets[idx]:
        cst = res.debits_reference
        if cst:
            c1, c2 = st.columns(2)
            qb = cst.get("q_thermie_bio")
            c1.metric("Q_thermie_bio (principal)",
                      f"{qb:.3f} m³/s" if qb else "non applicable")
            c2.metric("Q_thermie_fonc (appoint)",
                      f"{cst['q_thermie_fonc']:.3f} m³/s")
        else:
            st.info("Débits de référence non déterminés (rupture non validée "
                    "ou Q*_vuln non détecté).")
        for k, titre in [("debits_vuln", "Q_thermie_bio — vulnérabilité"),
                         ("debits_inflexion", "Q_thermie_fonc — inflexion"),
                         ("debits_classes", "Débits classés (PNDA)")]:
            if res.figures.get(k) is not None:
                st.subheader(titre)
                st.pyplot(res.figures[k])

# Climatique
if res.figures_climatiques and "🌍 Climatique" in noms_onglets:
    idx = noms_onglets.index("🌍 Climatique")
    with onglets[idx]:
        st.caption("Volet descriptif sur données brutes (contexte observé réel).")
        for f in res.figures_climatiques:
            st.pyplot(f)
