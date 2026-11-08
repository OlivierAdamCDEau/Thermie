"""
Tests de la lecture v4.7 — autonomes : ils fabriquent leurs propres fichiers
et ne réclament ni le corpus ni les références figées de tests/reference/.

Lancement : python -m pytest tests/test_lecture_multi.py
"""
import io

import pandas as pd
import pytest

from thermie_debits import io_data, sniff


def _classeur_dce(n_heures=72, avec_pose=True):
    """Classeur au format d'échange DCE : métadonnées de pose en 1re feuille,
    chronique en 2de, date et heure séparées, température en colonne « T »."""
    t0 = pd.Timestamp("2025-07-01 00:00")
    dt = [t0 + pd.Timedelta(hours=h) for h in range(n_heures)]
    chron = pd.DataFrame({
        "CODE_STA_SANDRE": "06000000", "COD_STA_METIER": "RIV_100",
        "NOM_STA_METIER": "RIV_100", "COD_SONDE": "123",
        "DATE": [d.strftime("%d/%m/%Y") for d in dt],
        "HEURE": [d.strftime("%H:%M:%S") for d in dt],
        "REF_HORAIRE": "UTC+2",
        "T": [15.0 + (h % 24) / 10 for h in range(n_heures)],
        "chmes_validation": "Validé"})
    pose = pd.DataFrame({
        "CODE_STA_SANDRE": ["06000000"], "COD_STA_METIER": ["RIV_100"],
        "RIV_NOM": ["La Rivière"], "NOM_STA_METIER": ["RIV_100"],
        "DATE_POSE": ["2025-03-20"], "T_POSE": [9.5]})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        if avec_pose:
            pose.to_excel(w, sheet_name="Pose_relève", index=False)
        chron.to_excel(w, sheet_name="chronique de température", index=False)
    return buf.getvalue()


def _meteo_france(tmp_path, stations):
    """Export quotidien Météo-France (« ; », AAAAMMJJ, TM, TNTXM)."""
    lignes = ["NUM_POSTE;NOM_USUEL;LAT;LON;ALTI;AAAAMMJJ;RR;TN;TX;TM;TNTXM"]
    for code, tm, tntxm in stations:
        for d in pd.date_range("1995-01-01", "1995-01-10"):
            lignes.append(f"{code};ST;46;5;500;{d:%Y%m%d};0.0;1.0;9.0;"
                          f"{tm};{tntxm}")
    p = tmp_path / "meteo.csv"
    p.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return str(p)


# ---- Détection de la feuille ---------------------------------------------
def test_feuille_chronique_detectee_et_non_la_premiere():
    b = _classeur_dce()
    assert sniff.detecter_feuille(b, "x.xlsx") == "chronique de température"
    df, meta = sniff.lire_brut(b, nom="x.xlsx", n_lignes=10)
    assert meta["feuille"] == "chronique de température"


def test_feuille_explicite_prime_sur_la_detection():
    b = _classeur_dce()
    _df, meta = sniff.lire_brut(b, nom="x.xlsx", feuille="Pose_relève")
    assert meta["feuille"] == "Pose_relève"


def test_feuille_unique_inchangee():
    b = _classeur_dce(avec_pose=False)
    assert sniff.detecter_feuille(b, "x.xlsx") == "chronique de température"


def test_aucune_feuille_exploitable_rend_la_premiere():
    """Cas limite : rien ne se distingue → ancien comportement."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame({"a": [1]}).to_excel(w, sheet_name="A", index=False)
        pd.DataFrame({"b": [2]}).to_excel(w, sheet_name="B", index=False)
    assert sniff.detecter_feuille(buf.getvalue(), "x.xlsx") == "A"


# ---- Colonne « T » --------------------------------------------------------
def test_colonne_T_reconnue_comme_temperature():
    df = pd.DataFrame({"DATE": ["01/07/2025"], "T": [15.2],
                       "chmes_validation": ["Validé"]})
    assert sniff.deviner_colonnes(df) == ("DATE", "T")


def test_lettre_t_dans_un_nom_non_reconnue():
    """« t » n'est reconnu que comme nom ENTIER, pas comme sous-chaîne."""
    df = pd.DataFrame({"DATE": ["01/07/2025"], "STATUT": [1.0]})
    assert sniff.deviner_colonnes(df)[1] is None


def test_lecture_dce_complete_sans_mapping():
    """Date + heure séparées, colonne T : 3 journées complètes de 24 h."""
    daily, marques = io_data.marquer_lecture(_classeur_dce(), nom="x.xlsx")
    assert len(daily) == 3
    assert (daily["n_mesures"] == 24).all()
    assert len(marques) == 0


def test_identifier_sonde_dce():
    ident = sniff.identifier_sonde(_classeur_dce(), "x.xlsx")
    assert ident == {"cours_eau": "La Rivière", "point": "RIV_100"}


# ---- Air de référence ------------------------------------------------------
def test_air_station_sans_TM_message_explicite(tmp_path):
    """Régression « cannot convert float NaN to integer »."""
    p = _meteo_france(tmp_path, [("001", "", "5.0"), ("002", "4.0", "4.5")])
    with pytest.raises(ValueError, match="aucune valeur de « TM »"):
        io_data.charger_air_brut(p, station_code="001")


def test_normales_air_vide_message_explicite():
    vide = pd.DataFrame(columns=["date", "T_air"])
    with pytest.raises(ValueError, match="Air de référence vide"):
        io_data.calculer_normales_ecarts(vide, verbose=False)


def test_colonne_air_choisie_est_appliquee(tmp_path):
    """La colonne choisie à l'écran (TNTXM) était ignorée sur ce format."""
    p = _meteo_france(tmp_path, [("001", "", "5.0"), ("002", "4.0", "4.5")])
    a = io_data.charger_air_brut(p, station_code="001", col_temp="TNTXM")
    assert len(a) == 10 and (a["T_air"] == 5.0).all()
    assert a.attrs["colonne_temperature"] == "TNTXM"


def test_colonne_air_par_defaut_reste_TM(tmp_path):
    p = _meteo_france(tmp_path, [("001", "", "5.0"), ("002", "4.0", "4.5")])
    a = io_data.charger_air_brut(p)                  # station la mieux couverte
    assert a.attrs["station"]["code"] == "002"
    assert (a["T_air"] == 4.0).all()


# ---- Codes de poste et zéro initial -----------------------------------------
def test_code_poste_sans_zero_initial_trouve_le_poste(tmp_path):
    """Régression v4.7 en ligne : la liste des postes rendait 1014002, le
    fichier porte 01014002 → aucune ligne retenue, « air vide »."""
    p = _meteo_france(tmp_path, [("01014002", "4.0", "4.5"),
                                 ("01014001", "", "5.0")])
    a = io_data.charger_air_brut(p, station_code="1014002")
    assert len(a) == 10 and (a["T_air"] == 4.0).all()


def test_fichier_sans_zero_initial_trouve_le_poste(tmp_path):
    """Sens inverse : fichier repassé par Excel (1014002), code 01014002."""
    p = _meteo_france(tmp_path, [("1014002", "4.0", "4.5"),
                                 ("1014001", "", "5.0")])
    a = io_data.charger_air_brut(p, station_code="01014002")
    assert len(a) == 10


def test_stations_air_conserve_le_zero_initial(tmp_path):
    p = _meteo_france(tmp_path, [("01014002", "4.0", "4.5"),
                                 ("01014001", "", "5.0")])
    codes = [s["code"] for s in io_data.stations_air(p)]
    assert codes == ["01014002", "01014001"]


def test_poste_introuvable_message_distinct(tmp_path):
    p = _meteo_france(tmp_path, [("01014002", "4.0", "4.5"),
                                 ("01014001", "", "5.0")])
    with pytest.raises(ValueError, match="introuvable"):
        io_data.charger_air_brut(p, station_code="99999999",
                                 nom_fichier="ARBENT.csv")
