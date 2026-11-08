"""
Статистические функции, общие для ноутбуков.

    from src.stats import num, cramers_v, share_ci

    chi2, p, dof, v, expected = cramers_v(pd.crosstab(df["a"], df["b"]))
    pct, lo, hi = share_ci(k, n)   # доля в % и 95% ДИ Уилсона
"""

import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportion_confint


def num(x, digits=0):
    """Число с пробелом между разрядами: 105 996."""
    return f"{x:,.{digits}f}".replace(",", " ")


def cramers_v(table):
    """χ² Пирсона для таблицы сопряжённости и V Крамера (сила связи)."""
    chi2, p, dof, expected = stats.chi2_contingency(table)
    n = np.asarray(table).sum()
    v = np.sqrt(chi2 / (n * (min(np.shape(table)) - 1)))
    return chi2, p, dof, v, expected


def share_ci(k, n):
    """Доля k из n в процентах и 95% доверительный интервал Уилсона."""
    lo, hi = proportion_confint(k, n, method="wilson")
    return 100 * k / n, 100 * lo, 100 * hi


def rank_by_title(titles, codes):
    """
    Рейтинг с объединением одинаковых названий под разными кодами OIICS.
    Возвращает DataFrame (индекс — ключ norm_title): title, codes, cases, pct.
    """
    import pandas as pd
    from src.labels import norm_title

    df = pd.DataFrame({"key": titles.map(norm_title), "title": titles, "code": codes})
    # для каждого ключа — самое частое написание названия
    name = (df.groupby(["key", "title"]).size().sort_values(ascending=False)
            .reset_index().drop_duplicates("key").set_index("key")["title"])
    out = df.groupby("key").agg(
        cases=("code", "size"),
        codes=("code", lambda s: ", ".join(map(str, sorted(s.unique())))),
    )
    out["title"] = name.reindex(out.index)
    out["pct"] = 100 * out["cases"] / len(df)
    return out.sort_values("cases", ascending=False)[["title", "codes", "cases", "pct"]]
