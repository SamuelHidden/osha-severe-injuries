"""
Общий стиль графиков и подписи на двух языках (русский / английский).

Использование:

    from src.viz import tr, save_fig, set_style, LANGS

    set_style()
    for lang in LANGS:
        fig, ax = plt.subplots()
        ax.bar(...)
        ax.set_title(tr("Случаи по годам", "Cases by year", lang))
        save_fig(fig, "04_cases_by_year", lang)   # -> figures/ru/... и figures/en/...
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
FIGURES_DIR = ANALYSIS_DIR / "figures"
TABLES_DIR = ANALYSIS_DIR / "tables"

LANGS = ("ru", "en")


def tr(ru: str, en: str, lang: str) -> str:
    """Возвращает подпись на нужном языке."""
    return ru if lang == "ru" else en


def set_style() -> None:
    """Единый стиль для всех графиков работы."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "DejaVu Sans",  # есть кириллица
        "axes.titleweight": "bold",
    })


def save_fig(fig, name: str, lang: str, formats: tuple[str, ...] = ("png", "svg")) -> None:
    """Сохраняет график в figures/<lang>/<name>.<fmt>."""
    out = FIGURES_DIR / lang
    out.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        fig.savefig(out / f"{name}.{fmt}")


# Основной цвет (одна серия) и акцент — как в ноутбуке 01
MAIN = "#4c72b0"
ACCENT = "#c0392b"

# Категориальная палитра для нескольких серий (проверена на различимость при дальтонизме);
# цвета назначаются по порядку и не перебираются по кругу — больше 8 серий не рисуем
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]


def finish(fig, name: str, lang: str) -> None:
    """Сохраняет график; русскую версию показывает в ноутбуке, английскую только сохраняет."""
    save_fig(fig, name, lang)
    if lang == "ru":
        plt.show()
    plt.close(fig)


def wrap(text: str, width: int = 42) -> str:
    """Переносит длинную подпись оси на несколько строк."""
    import textwrap
    return "\n".join(textwrap.wrap(str(text), width)) or str(text)


def barh_ranked(ax, labels, values, notes=None, color=MAIN, width: int = 42):
    """
    Горизонтальные столбцы: первый элемент списка — сверху.
    notes — подписи у концов столбцов, color — один цвет или список цветов.
    """
    labels, values = list(labels), list(values)
    y = range(len(values))[::-1]
    colors = color if isinstance(color, str) else list(color)
    bars = ax.barh(list(y), values, color=colors)
    ax.set_yticks(list(y), [wrap(t, width) for t in labels])
    if notes is not None:
        ax.bar_label(bars, labels=list(notes), padding=3, fontsize=9)
    ax.margins(x=0.12)
    ax.grid(axis="y", visible=False)
    return bars
