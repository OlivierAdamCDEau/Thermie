"""
print_style.py — Normes de restitution graphique (package thermie_debits).

Toutes les figures de l'app sont destinées à être copiées dans un document
Word, soit en pleine largeur portrait (16 cm — page A4, marges 2,5 cm), soit
en pleine largeur paysage (24,7 cm). Une fois collée à cette largeur, aucun
texte de la figure ne doit descendre sous 8 pt sur le papier.

Comme Word redimensionne l'image en conservant les proportions, la taille de
police "sur le papier" dépend du rapport (largeur cible / largeur native de
la figure en pouces) — indépendant du DPI. Ce module calcule donc, pour
chaque figure, la taille de police minimale à utiliser dans matplotlib pour
que le pire des deux formats (portrait, plus étroit et donc plus exigeant)
reste lisible.
"""
from __future__ import annotations
import matplotlib.text

PORTRAIT_CM = 16.0
LANDSCAPE_CM = 24.7
MIN_PT = 8.0
_CM_PER_IN = 2.54

# Plafond de sécurité : au-delà, on considère que la figure est trop large
# pour tenir un format portrait plein cadre et on préconise plutôt un collage
# à largeur réduite (auquel cas la contrainte est desserrée). Évite un
# gonflement de police disproportionné sur les figures très larges.
FONT_FLOOR_CAP = 15.0


def min_fontsize_for_print(fig_width_in, target_cm=PORTRAIT_CM, min_pt=MIN_PT):
    """Taille de police mpl minimale pour garantir `min_pt` une fois la figure
    redimensionnée à `target_cm` de large dans Word."""
    target_in = target_cm / _CM_PER_IN
    if fig_width_in <= 0:
        return min_pt
    scale = target_in / fig_width_in
    if scale >= 1:
        return min_pt
    return min_pt / scale


def enforce_min_fontsize(fig, cap=FONT_FLOOR_CAP, target_cm=PORTRAIT_CM):
    """
    Relève toutes les tailles de police de la figure sous le plancher calculé
    pour le format portrait (le plus contraignant), sans jamais les réduire.
    Plafonné à `cap` pt pour rester lisible même sur les figures très larges.
    """
    w_in = fig.get_size_inches()[0]
    floor = min(min_fontsize_for_print(w_in, target_cm=target_cm), cap)
    for txt in fig.findobj(matplotlib.text.Text):
        try:
            cur = txt.get_fontsize()
            if cur is not None and cur < floor:
                txt.set_fontsize(floor)
        except Exception:
            pass
    return fig


def style_legend(leg, alpha=0.62):
    """Fond translucide (les courbes restent visibles à travers) + cadre
    discret, pour qu'une légende ne masque jamais complètement une courbe."""
    if leg is None:
        return leg
    frame = leg.get_frame()
    frame.set_alpha(alpha)
    frame.set_facecolor("white")
    frame.set_edgecolor("#BFC9CA")
    frame.set_linewidth(0.8)
    return leg


def table_fontsize(fig_width_in, target_cm=PORTRAIT_CM, cap=FONT_FLOOR_CAP):
    """Taille de police à utiliser directement dans un tableau matplotlib,
    calculée en amont (plutôt que corrigée après coup), pour que le calcul
    du retour à la ligne (wrap_rows) soit cohérent avec le rendu final."""
    return min(min_fontsize_for_print(fig_width_in, target_cm=target_cm), cap)


def wrap_rows(rows, col_chars):
    """
    Pré-découpe chaque cellule d'un tableau (liste de listes de chaînes) sur
    plusieurs lignes, pour qu'aucune ligne de texte ne dépasse la largeur de
    sa colonne — évite la troncature silencieuse d'un ax.table() matplotlib,
    qui n'effectue lui-même aucun retour à la ligne automatique.

    col_chars : nombre de caractères par colonne (None = colonne non wrappée,
    par ex. une colonne de puce ou de valeur courte).
    Retourne (rows_wrappees, nb_lignes_par_ligne) — ce second élément sert à
    recalculer la hauteur de chaque ligne du tableau proportionnellement à
    son nombre de lignes de texte.
    """
    import textwrap
    new_rows, line_counts = [], []
    for row in rows:
        wrapped, maxlines = [], 1
        for cell, w in zip(row, col_chars):
            if not isinstance(cell, str) or not w:
                wrapped.append(cell); continue
            lines = textwrap.wrap(cell, width=w, break_long_words=False) or [""]
            wrapped.append("\n".join(lines))
            maxlines = max(maxlines, len(lines))
        new_rows.append(wrapped)
        line_counts.append(maxlines)
    return new_rows, line_counts


def apply_row_heights(tbl, line_counts, has_header=True):
    """Redimensionne chaque ligne d'un tableau matplotlib proportionnellement
    à son nombre de lignes de texte (après wrap_rows), pour que les cellules
    à retour à la ligne restent lisibles sans chevaucher la ligne suivante."""
    offset = 1 if has_header else 0
    total_units = offset + sum(line_counts)
    unit_h = 1.0 / total_units
    for (row, col), cell in tbl.get_celld().items():
        if row == 0 and has_header:
            cell.set_height(unit_h)
        else:
            idx = row - offset
            if 0 <= idx < len(line_counts):
                cell.set_height(unit_h * line_counts[idx])


def make_print_ready(fig, target_cm=PORTRAIT_CM, cap=FONT_FLOOR_CAP):
    """
    Produit une COPIE indépendante de la figure (par sérialisation) avec le
    plancher de lisibilité à l'impression appliqué. L'original — utilisé
    pour l'affichage à l'écran — n'est pas modifié : ses proportions restent
    celles voulues par l'auteur de la figure, pensées pour un rendu d'écran
    plutôt que pour un collage à pleine largeur dans un document.

    Les tableaux matplotlib de ce module pré-calculent leur retour à la ligne
    en anticipant CETTE police agrandie (voir wrap_rows / table_fontsize) :
    le texte tient donc exactement une fois la police effectivement relevée
    ici, sans repasser par un nouveau calcul de découpe.
    """
    import pickle
    copie = pickle.loads(pickle.dumps(fig))
    enforce_min_fontsize(copie, cap=cap, target_cm=target_cm)
    return copie


def col_width_chars(width_frac, fig_width_in, fontsize_pt, avg_char_ratio=0.56):
    """
    Nombre de caractères qui tiennent dans une colonne de tableau, à partir
    de sa largeur en fraction de l'axe et de la largeur réelle de la figure.
    `avg_char_ratio` est une estimation prudente de la largeur moyenne d'un
    caractère (police sans-serif, majuscules et gras inclus) — mieux vaut
    replier une ligne de trop que la voir déborder silencieusement.
    """
    width_pt = width_frac * fig_width_in * 72
    return max(6, int(width_pt / (fontsize_pt * avg_char_ratio)))
