"""
Сборка данных для дашбордов отчёта.

Читает итоговые таблицы из Analysis/tables (их создают ноутбуки анализа)
и записывает Report/assets/data.js, который подключают HTML-дашборды.
Долю пальцев рук считает по Data/processed/DataBaseFiles так же, как ноутбук 01.
Дашборды: части тела (01), источники (02), отрасли (03, 09), сезоны (04), типы травм (06, 10).

Запуск из корня репозитория или из папки Report:

    python3 Report/build.py
"""

import csv
import json
from datetime import date
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "Analysis" / "tables"
DB_FILES = ROOT / "Data" / "processed" / "DataBaseFiles"
OUT = Path(__file__).resolve().parent / "assets" / "data.js"

TOP_N = 15


def read(name: str) -> list[dict]:
    with open(TABLES / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def division(codes: str) -> str:
    """Раздел OIICS — первая цифра кода; у объединённых названий все коды из одного раздела."""
    return codes.split(",")[0].strip()[0]


def body_parts() -> dict:
    divisions = [
        {
            "code": r["division"],
            "ru": r["name_ru"],
            "en": r["name_en"],
            "cases": int(r["cases"]),
            "pct": float(r["pct_of_all"]),
        }
        for r in read("01_2_body_divisions.csv")
    ]
    total = sum(d["cases"] for d in divisions)

    top = [
        {
            "rank": int(r[""]),
            "ru": r["body_part_ru"],
            "en": r["body_part"],
            "codes": r["codes"],
            "cases": int(r["cases"]),
            "pct": float(r["pct_of_all"]),
            "division": division(r["codes"]),
        }
        for r in read("01_1_top_body_parts.csv")
    ]

    amputation = {
        r["division"]: float(r["pct"])
        for r in read("01_3_severity_by_division.csv")
        if r["outcome"] == "amputation"
    }

    return {
        "total": total,
        "divisions": divisions,
        "top": top,
        "topN": TOP_N,
        "fingers": fingers(total),
        "amputationPct": amputation,
    }


def fingers(total: int) -> dict:
    """Все коды частей тела со словом finger в названии — как в ноутбуке 01_body_parts."""
    with open(DB_FILES / "body_part_lookup.csv", encoding="utf-8-sig", newline="") as f:
        codes = {r["code"] for r in csv.DictReader(f) if "finger" in r["title"].lower()}
    with open(DB_FILES / "injuries.csv", encoding="utf-8-sig", newline="") as f:
        cases = sum(r["part_of_body_code"] in codes for r in csv.DictReader(f))
    return {"cases": cases, "pct": round(100 * cases / total, 2)}


def sources(total: int) -> dict:
    def ranked(name: str, ru_col: str) -> list[dict]:
        return [
            {
                "rank": int(r[""]),
                "ru": r[ru_col],
                "en": r["title"],
                "codes": r["codes"],
                "cases": int(r["cases"]),
                "pct": float(r["pct"]),
                "division": division(r["codes"]),
            }
            for r in read(name)
        ]

    divisions = [
        {
            "code": r[""],
            "ru": r["name_ru"],
            "en": r["name_en"],
            "source": int(r["as_source"]),
            "secondary": int(r["as_secondary"]),
            "pctSource": float(r["pct_source"]),
            "pctSecondary": float(r["pct_secondary"]),
        }
        for r in read("02_4_source_divisions.csv")
    ]
    secondary_total = sum(d["secondary"] for d in divisions)

    by_year = read("02_7_source_groups_by_year.csv")
    groups = [c for c in by_year[0] if c != "year"]
    years = [int(r["year"]) for r in by_year]

    # Доля группы за весь период: годовые доли, взвешенные числом случаев в году
    cases_by_year = {int(r["year"]): int(r["cases"]) for r in read("04_1_cases_by_year.csv")}
    period_pct = {
        g: round(sum(float(r[g]) * cases_by_year[int(r["year"])] for r in by_year) / total, 2)
        for g in groups
    }

    secondary_share = {r["title"]: float(r["secondary_share"]) for r in read("02_5_total_mentions.csv")}
    filled_by_year = {int(r["year"]): float(r["real"]) for r in read("02_3_secondary_status_by_year.csv")}

    return {
        "top": ranked("02_1_top_sources.csv", "source_ru"),
        "secondary": ranked("02_2_top_secondary_sources.csv", "secondary_ru"),
        "secondaryTotal": secondary_total,
        "secondaryFilledPct": round(100 * secondary_total / total, 2),
        "secondaryFilledByYear": filled_by_year,
        "divisions": divisions,
        "groupsByYear": {
            "years": years,
            "partialYear": max(years),
            "series": [{"name": g, "values": [float(r[g]) for r in by_year]} for g in groups],
            "periodPct": period_pct,
        },
        "secondaryShare": secondary_share,
    }


def num(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def industries() -> dict:
    sectors = [
        {"code": r["sector"], "ru": r["sector_ru"], "en": r["sector_en"], "cases": int(r["cases"]), "pct": float(r["pct"])}
        for r in read("03_1_sectors.csv")
    ]
    subsectors = [
        {"code": r["subsector"], "ru": r["title_ru"], "en": r["title"], "sector": r["sector_ru"],
         "cases": int(r["cases"]), "pct": float(r["pct"])}
        for r in read("03_2_top_subsectors.csv")
    ]
    severity = [
        {"code": r["sector"], "ru": r["sector_ru"], "en": r["sector_en"], "cases": int(r["cases"]),
         "amputation": float(r["pct_amputation"]), "ampLow": float(r["amp_ci_low"]), "ampHigh": float(r["amp_ci_high"]),
         "hospitalized": float(r["pct_hospitalized"])}
        for r in read("03_4_severity_by_sector.csv")
    ]
    change = [
        {"code": r["sector"], "ru": r["sector_ru"], "start": int(float(r["cases_start"])), "end": int(float(r["cases_end"])),
         "perMonthStart": float(r["per_month_start"]), "perMonthEnd": float(r["per_month_end"]),
         "pct": float(r["pct_change"]), "low": float(r["ci_low"]), "high": float(r["ci_high"]), "verdict": r["verdict"]}
        for r in read("09_5_sector_change.csv")
    ]

    # Все отрасли вместе: случаи в месяц 2024–2025 против 2015–2016, как в ноутбуке 09
    years = {int(r["year"]): r for r in read("04_1_cases_by_year.csv")}
    per_month = lambda ys: sum(int(years[y]["cases"]) for y in ys) / sum(int(years[y]["months"]) for y in ys)
    total_change = 100 * (per_month((2024, 2025)) / per_month((2015, 2016)) - 1)

    # Доля ампутаций по всем случаям — из сводки по сезонам (там есть число ампутаций)
    seasons = read("04_6_seasons.csv")
    amputation_all = 100 * sum(int(r["amputations"]) for r in seasons) / sum(int(r["cases"]) for r in seasons)

    return {
        "sectors": sectors,
        "subsectors": subsectors,
        "severity": severity,
        "change": change,
        "totalChange": round(total_change, 2),
        "amputationAll": round(amputation_all, 2),
    }


def seasonality() -> dict:
    monthly = [
        {"month": int(r["month"]), "perDay": float(r["mean"]), "ci": float(r["ci"]), "season": r["season"],
         "index": float(r["seasonal_index"])}
        for r in read("04_5_monthly_profile.csv")
    ]
    seasons = [
        {"key": r["season"], "ru": r["season_ru"], "cases": int(r["cases"]), "days": int(r["days"]),
         "perDay": float(r["per_day"]), "vsMean": float(r["vs_mean_pct"]),
         "amputation": float(r["pct_amputation"]), "hospitalized": float(r["pct_hospitalized"])}
        for r in read("04_6_seasons.csv")
    ]
    weekdays = [
        {"day": int(r["weekday"]), "ru": r["weekday_ru"], "cases": int(r["cases"]), "days": int(r["days"]),
         "perDay": float(r["per_day"]), "amputation": float(r["pct_amputation"])}
        for r in read("04_9_weekdays.csv")
    ]
    heat = read("04_3_cases_per_day_month_year.csv")
    year_cols = [c for c in heat[0] if c.strip()]
    causes = [
        {"key": r[""], "ru": r["cause_ru"], "cases": int(r["cases"]), "peak": r["peak_month"],
         "peakIndex": float(r["peak_index"]), "low": r["low_month"], "lowIndex": float(r["low_index"]),
         "summer": float(r["summer_share"]), "winter": float(r["winter_share"])}
        for r in read("04_8_seasonal_causes.csv")
    ]
    cause_index = read("04_8_seasonal_causes_index.csv")
    return {
        "monthly": monthly,
        "seasons": seasons,
        "weekdays": weekdays,
        "perDayAll": round(sum(s["cases"] for s in seasons) / sum(s["days"] for s in seasons), 2),
        "monthYear": {
            "years": [int(y) for y in year_cols],
            "months": [r[""] for r in heat],
            "values": [[num(r[y]) for y in year_cols] for r in heat],
        },
        "causes": causes,
        "causeIndex": {c["ru"]: [float(r[c["ru"]]) for r in cause_index] for c in causes},
    }


def nature() -> dict:
    categories = [
        {"ru": r["category_ru"], "en": r["category_en"], "cases": int(r["cases"]), "pct": float(r["pct_of_all"]),
         "hospitalized": float(r["pct_hospitalized"]), "amputation": float(r["pct_amputation"])}
        for r in read("06_2_nature_categories.csv")
    ]
    top = [
        {"rank": int(r[""]), "ru": r["nature_ru"], "en": r["title"], "codes": r["codes"],
         "cases": int(r["cases"]), "pct": float(r["pct"])}
        for r in read("06_1_top_nature.csv")
    ]

    months = [str(m) for m in range(1, 13)]
    matrix = lambda name: {r["category"]: [float(r[m]) for m in months] for r in read(name)}
    share_rows = read("10_1_category_month_share.csv")
    leaders = [
        {"month": int(r["month"]), "ru": r["month_ru"], "cases": int(r["cases"]),
         "leader": r["leader"], "leaderPct": float(r["leader_pct"]),
         "characteristic": r["characteristic"] or None, "index": num(r["char_index"]),
         "also": r["also"] or None}
        for r in read("10_3_month_leaders.csv")
    ]
    peaks = [
        {"ru": r["category_ru"], "en": r["category_en"], "cases": int(r["cases"]),
         "peak": r["peak_month_ru"], "peakIndex": float(r["peak_index"]),
         "low": r["low_month_ru"], "lowIndex": float(r["low_index"]),
         "summer": float(r["summer_share"]), "winter": float(r["winter_share"])}
        for r in read("10_2_category_peaks.csv")
    ]
    robust = read("10_4_robustness.csv")
    return {
        "categories": categories,
        "top": top,
        "research": {
            "order": [r["category"] for r in share_rows],
            "share": matrix("10_1_category_month_share.csv"),
            "shareAll": {r["category"]: float(r["all_months"]) for r in share_rows},
            "index": matrix("10_3_category_month_index.csv"),
            "resid": matrix("10_3_category_month_resid.csv"),
            "rateIndex": matrix("10_2_category_rate_index.csv"),
            # Порог Бонферрони для остатка — как в ноутбуке 10: 12 категорий × 12 месяцев
            "crit": round(NormalDist().inv_cdf(1 - 0.05 / 2 / (len(share_rows) * 12)), 3),
            "leaders": leaders,
            "peaks": peaks,
            "robustSame": sum(r["same"] == "True" for r in robust),
        },
    }


def main() -> None:
    body = body_parts()
    data = {
        "meta": {
            "total": body["total"],
            "period": "январь 2015 – ноябрь 2025",
            "built": date.today().isoformat(),
        },
        "body": body,
        "sources": sources(body["total"]),
        "industries": industries(),
        "seasons": seasonality(),
        "nature": nature(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "// Сгенерировано Report/build.py из Analysis/tables — не редактировать вручную.\n"
        f"window.REPORT_DATA = {json.dumps(data, ensure_ascii=False, indent=1)};\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT.relative_to(ROOT)} · {body['total']:,} случаев".replace(",", " "))


if __name__ == "__main__":
    main()
