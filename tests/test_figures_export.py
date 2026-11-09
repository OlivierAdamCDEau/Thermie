"""
Tests de l'export des figures (v4.7) — autonomes, sans corpus.

Lancement : python -m pytest tests/test_figures_export.py
"""
import itertools

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text
import pytest

from thermie_debits.config import SourcesConfig
from thermie_debits.print_style import (FORMATS_FIGURE, figure_en_octets,
                                        make_print_ready, mise_en_page)


def _figure_legende_dessous():
    """Cas qui chevauchait : légende sous l'axe + étiquette d'axe, petites
    polices d'écran que l'export relève."""
    fig, ax = plt.subplots(figsize=(10.5, 5.4), layout="constrained")
    for i in range(6):
        ax.plot([0, 1], [i, i + 1], label=f"Série numéro {i} au libellé long")
    ax.set_xlabel("Date", fontsize=11)
    fig.legend(*ax.get_legend_handles_labels(), fontsize=8.5,
               loc="outside lower center", ncol=3)
    return fig


def _chevauchements(fig, a, b):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    return a.get_window_extent(r).overlaps(b.get_window_extent(r))


def test_svg_valide_et_vectoriel():
    fig = _figure_legende_dessous()
    svg = figure_en_octets(fig, "svg")
    assert svg.lstrip().startswith(b"<?xml")
    assert b"<svg" in svg[:2000]
    plt.close(fig)


def test_png_valide():
    fig = _figure_legende_dessous()
    assert figure_en_octets(fig, "png")[:8] == b"\x89PNG\r\n\x1a\n"
    plt.close(fig)


def test_format_inconnu_refuse():
    fig = _figure_legende_dessous()
    with pytest.raises(ValueError, match="non pris en charge"):
        figure_en_octets(fig, "pdf")
    plt.close(fig)
    assert set(FORMATS_FIGURE) == {"png", "svg"}


def test_mise_en_page_conservee_par_la_copie_impression():
    """Le moteur doit survivre à la copie : c'est lui qui recalcule les
    marges APRÈS le relèvement des polices."""
    fig, ax = plt.subplots()
    mise_en_page(fig, "tight")
    copie = make_print_ready(fig)
    assert copie.get_layout_engine() is not None
    plt.close(fig)


def test_legende_dessous_ne_chevauche_pas_l_etiquette_apres_relevement():
    fig = _figure_legende_dessous()
    copie = make_print_ready(fig)
    ax = copie.axes[0]
    leg = copie.legends[0]
    assert ax.xaxis.label.get_fontsize() >= 11
    assert not _chevauchements(copie, leg, ax.xaxis.label)
    plt.close(fig)


def test_tight_layout_ponctuel_chevauchait():
    """Témoin : l'ancien montage (légende ancrée à l'axe + tight_layout
    ponctuel) chevauche bien l'étiquette une fois les polices relevées —
    c'est le défaut corrigé."""
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    for i in range(6):
        ax.plot([0, 1], [i, i + 1], label=f"Série numéro {i} au libellé long")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["Aug 2023", "Feb 2024", "Aug 2024", "Feb 2025",
                        "Aug 2025"], rotation=30)
    # Montage d'origine de la chronique (figures.py, v4.6).
    ax.legend(fontsize=8.5, loc="upper center",
              bbox_to_anchor=(0.5, -0.24), ncol=3)
    plt.tight_layout()
    copie = make_print_ready(fig)
    a = copie.axes[0]
    assert _chevauchements(copie, a.get_legend(), a.xaxis.label)
    plt.close(fig)


# ---- Titre des figures --------------------------------------------------
@pytest.mark.parametrize("ce, pt, attendu", [
    ("La Valserine", "VAL_993", "La Valserine · VAL_993"),
    ("La Valserine", "", "La Valserine"),
    ("La Valserine", "La Valserine", "La Valserine"),
    ("", "VAL_993", "VAL_993"),
])
def test_titre_figures(ce, pt, attendu):
    src = SourcesConfig(nom_cours_eau=ce, localisation_sonde=pt)
    assert src.titre_figures == attendu
