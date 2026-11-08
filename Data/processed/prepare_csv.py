"""
Разбивает УЖЕ ЗАГРУЖЕННЫЕ в память DataFrame'ы `osha` и `naics_titles`
на 6 CSV-файлов, готовых для загрузки в таблицы PostgreSQL.

По умолчанию все CSV сохраняются в ту же папку, где лежит сам этот
скрипт (SCRIPT_DIR) — можно переопределить через параметр out_dir.

Использование в ноутбуке/скрипте:

    from prepare_csv import build_lookup_csvs, build_naics_lookup_csv, check_naics_coverage

    check_naics_coverage(osha, naics_titles)         # QC, необязательно
    build_naics_lookup_csv(naics_titles)             # -> naics_lookup.csv
    build_lookup_csvs(osha)                          # -> остальные 5 CSV
"""

import pandas as pd
from pathlib import Path


# Папка, где лежит сам скрипт — CSV по умолчанию сохраняются сюда же
SCRIPT_DIR = Path(__file__).resolve().parent


def check_naics_coverage(df: pd.DataFrame, naics_titles: pd.DataFrame,
                          code_col_osha: str = "Primary NAICS",
                          code_col_naics: str = "Code") -> None:
    """
    QC-проверка: есть ли в osha['Primary NAICS'] коды, которых нет
    в справочнике naics_titles. Ничего не пишет в CSV — только печатает
    отчёт, чтобы вы заранее знали о "дырах" в расшифровке.

    Если название колонки с кодом в naics_titles называется не 'Code' —
    поправьте code_col_naics (после skiprows=2 проверьте
    naics_titles.columns, обычно там что-то вроде '2022 NAICS Code').
    """
    osha_codes = set(df[code_col_osha].astype(str).str.strip())
    naics_codes = set(naics_titles[code_col_naics].astype(str).str.strip())

    missing = osha_codes - naics_codes
    if missing:
        print(f"[!] {len(missing)} кодов NAICS из osha отсутствуют в справочнике:")
        print(sorted(missing)[:20], "...(показаны первые 20)" if len(missing) > 20 else "")
    else:
        print("[OK] Все коды Primary NAICS найдены в naics_titles.")


def build_naics_lookup_csv(naics_titles: pd.DataFrame, out_dir: str = None,
                            code_col: str = "Code", title_col: str = "Title") -> None:
    """
    Строит naics_lookup.csv (code, title) из справочника 2022 NAICS Structure.

    ВАЖНО: проверьте реальные названия колонок в вашем naics_titles —
    после skiprows=2 и str.strip() сделайте
        print(naics_titles.columns.tolist())
    и подставьте точные имена в code_col / title_col. В файле census.gov
    это обычно что-то вроде '2022 NAICS US Code' и '2022 NAICS US Title'.
    """
    out = Path(out_dir) if out_dir else SCRIPT_DIR

    naics_lookup = (
        naics_titles[[code_col, title_col]]
        .rename(columns={code_col: "code", title_col: "title"})
        .dropna(subset=["code"])
        .drop_duplicates(subset=["code"])
    )
    naics_lookup["code"] = naics_lookup["code"].astype(str).str.strip()

    naics_lookup.to_csv(out / "naics_lookup.csv", index=False)
    print(f"naics_lookup.csv сохранён в {out.resolve()} ({len(naics_lookup)} строк)")


def build_lookup_csvs(df: pd.DataFrame, out_dir: str = None) -> None:
    out = Path(out_dir) if out_dir else SCRIPT_DIR
    out.mkdir(parents=True, exist_ok=True)

    # ---------- 1. nature_lookup ----------
    nature = (
        df[["Nature", "NatureTitle"]]
        .drop_duplicates()
        .rename(columns={"Nature": "code", "NatureTitle": "title"})
    )
    nature.to_csv(out / "nature_lookup.csv", index=False)

    # ---------- 2. body_part_lookup ----------
    body_part = (
        df[["Part of Body", "Part of Body Title"]]
        .drop_duplicates()
        .rename(columns={"Part of Body": "code", "Part of Body Title": "title"})
    )
    body_part.to_csv(out / "body_part_lookup.csv", index=False)

    # ---------- 3. event_lookup ----------
    event = (
        df[["Event", "EventTitle"]]
        .drop_duplicates()
        .rename(columns={"Event": "code", "EventTitle": "title"})
    )
    event.to_csv(out / "event_lookup.csv", index=False)

    # ---------- 4. source_lookup (объединяем Source и Secondary Source) ----------
    src_primary = df[["Source", "SourceTitle"]].rename(
        columns={"Source": "code", "SourceTitle": "title"}
    )
    src_secondary = df[["Secondary Source", "Secondary Source Title"]].rename(
        columns={"Secondary Source": "code", "Secondary Source Title": "title"}
    )
    source_lookup = (
        pd.concat([src_primary, src_secondary], ignore_index=True)
        .drop_duplicates()
    )
    source_lookup.to_csv(out / "source_lookup.csv", index=False)

    # ---------- 5. injuries (битовая маска severity) ----------
    def build_severity(row):
        code = 0
        if row["Hospitalized"] == 1:
            code |= 4
        if row["Amputation"] == 1:
            code |= 2
        if row["Loss of Eye"] == 1:
            code |= 1
        return code

    injuries = pd.DataFrame({
        "id": df["ID"],
        "event_date": pd.to_datetime(df["EventDate"]).dt.date,
        "city": df["City"],
        "state": df["State"],
        "naics_code": df["Primary NAICS"],
        "final_narrative": df["Final Narrative"],
        "severity_code": df.apply(build_severity, axis=1),
        "nature_code": df["Nature"],
        "part_of_body_code": df["Part of Body"],
        "event_code": df["Event"],
        "source_code": df["Source"],
        "secondary_source_code": df["Secondary Source"],
    })
    injuries.to_csv(out / "injuries.csv", index=False)

    print(f"5 CSV файлов сохранены в {out.resolve()}")
    print("Порядок загрузки в PostgreSQL: naics_lookup, nature_lookup, "
          "body_part_lookup, event_lookup, source_lookup, затем injuries")
