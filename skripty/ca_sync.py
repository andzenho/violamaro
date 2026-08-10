#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ca_sync.py — синхронизация анализа ЦА из репозитория в Google-таблицу
«Виола / ЦА и продукты».

Направление: РЕПОЗИТОРИЙ → ТАБЛИЦА (источник правды — репозиторий).
Источник: analitika/ca-data.json (генерируется из книги; правится как текст,
диффается в git). Каждый лист источника пишется в одноимённую вкладку таблицы.

Что скрипт делает:
  - создаёт недостающие вкладки;
  - пишет значения ячеек (заголовок + строки) в диапазон своих колонок;
  - НЕ трогает форматирование, твои дополнительные колонки справа и любые
    вкладки, которых нет в источнике. Правки контента делаем в репозитории,
    оформление — руками в таблице, оно переживает синхронизацию.

ВНИМАНИЕ: как и sheets_sync.py, требует внешних библиотек (google-api-python-
client, google-auth) — писать в Google Sheets без них нельзя.
    python3 -m pip install -r skripty/requirements-sheets.txt

Доступ (сервис-аккаунт), один раз:
  1. Тот же ключ, что для sheets_sync (VIOLA_SHEETS_CREDS_JSON или
     skripty/.google-creds.json).
  2. Расшарить таблицу ЦА на email сервис-аккаунта, доступ «Редактор».

Запуск:
    python3 skripty/ca_sync.py --list-tabs   # какие вкладки уже есть в таблице
    python3 skripty/ca_sync.py               # сухой прогон: что изменится
    python3 skripty/ca_sync.py --apply       # записать изменения
"""

import json
import os
import sys

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(KOREN, "analitika", "ca-data.json")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CREDS_PATH = os.environ.get(
    "VIOLA_SHEETS_CREDS",
    os.path.join(KOREN, "skripty", ".google-creds.json"),
)


# ----------------------------------------------------------------------
# Источник
# ----------------------------------------------------------------------

def load_source():
    with open(SOURCE, encoding="utf-8") as f:
        data = json.load(f)
    sheet_id = os.environ.get("VIOLA_CA_SHEET_ID") or data.get("spreadsheet_id_default")
    if not sheet_id:
        sys.exit("Не задан ID таблицы: VIOLA_CA_SHEET_ID или spreadsheet_id_default в ca-data.json")
    return sheet_id, data.get("sheets", [])


def col_letter(idx):
    """0 -> A, 1 -> B, ..."""
    s = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        s = chr(65 + rem) + s
    return s


def a1_quote(title):
    return "'" + title.replace("'", "''") + "'"


def rectangular(rows):
    """Дополнить строки до общей ширины пустыми ячейками."""
    width = max((len(r) for r in rows), default=0)
    return [list(r) + [""] * (width - len(r)) for r in rows], width


# ----------------------------------------------------------------------
# Google Sheets
# ----------------------------------------------------------------------

def build_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit(
            "Нет библиотек google-api-python-client / google-auth.\n"
            "Установи: python3 -m pip install -r skripty/requirements-sheets.txt"
        )
    creds_json = os.environ.get("VIOLA_SHEETS_CREDS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    elif os.path.isfile(CREDS_PATH):
        creds = service_account.Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    else:
        sys.exit(
            "Нет ключа сервис-аккаунта.\n"
            "Задай VIOLA_SHEETS_CREDS_JSON (содержимое JSON) или положи файл: %s\n"
            "И не забудь расшарить таблицу ЦА на email сервис-аккаунта (Редактор)." % CREDS_PATH
        )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def existing_tabs(svc, sheet_id):
    meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return {s["properties"]["title"] for s in meta["sheets"]}, meta


def read_range(svc, sheet_id, title, last_col, last_row):
    rng = "%s!A1:%s%d" % (a1_quote(title), col_letter(last_col - 1), last_row)
    resp = (
        svc.spreadsheets().values()
        .get(spreadsheetId=sheet_id, range=rng, valueRenderOption="FORMATTED_VALUE")
        .execute()
    )
    return resp.get("values", [])


def cell(grid, r, c):
    return grid[r][c] if r < len(grid) and c < len(grid[r]) else ""


def create_tabs(svc, sheet_id, titles):
    requests = [{"addSheet": {"properties": {"title": t}}} for t in titles]
    svc.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests}
    ).execute()


# ----------------------------------------------------------------------
# Синхронизация
# ----------------------------------------------------------------------

def run(apply):
    sheet_id, sheets = load_source()
    if not sheets:
        print("В источнике нет листов (%s)." % SOURCE)
        return

    svc = build_service()
    present, _ = existing_tabs(svc, sheet_id)

    to_create = [s["title"] for s in sheets if s["title"] not in present]
    if to_create:
        print("Нет вкладок в таблице: %s" % ", ".join(to_create))
        if apply:
            create_tabs(svc, sheet_id, to_create)
            print("  → созданы.")
        else:
            print("  → будут созданы при --apply.")

    total_changes = 0
    write_data = []

    for s in sheets:
        title = s["title"]
        grid, width = rectangular(s["rows"])
        nrows = len(grid)
        if nrows == 0:
            continue

        # текущее состояние (только если вкладка уже есть)
        current = []
        if title in present:
            current = read_range(svc, sheet_id, title, width, nrows)

        changed = 0
        for r in range(nrows):
            for c in range(width):
                if str(cell(grid, r, c)) != str(cell(current, r, c)):
                    changed += 1
        if changed:
            total_changes += changed
            print("  [%s] изменится ячеек: %d (%d×%d)" % (title, changed, nrows, width))
            rng = "%s!A1:%s%d" % (a1_quote(title), col_letter(width - 1), nrows)
            write_data.append({"range": rng, "values": grid})
        else:
            print("  [%s] без изменений" % title)

    if total_changes == 0 and not to_create:
        print("Таблица уже совпадает с источником.")
        return

    if not apply:
        print("\nСухой прогон. Чтобы записать — запусти с --apply.")
        return

    if write_data:
        resp = svc.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={"valueInputOption": "RAW", "data": write_data},
        ).execute()
        print("\nЗаписано ячеек: %s" % resp.get("totalUpdatedCells", 0))
    print("Готово. Форматирование и твои доп-колонки не тронуты.")


def cmd_list_tabs():
    sheet_id, _ = load_source()
    svc = build_service()
    present, meta = existing_tabs(svc, sheet_id)
    print("Таблица «%s» (%s):" % (meta.get("properties", {}).get("title", ""), sheet_id))
    for t in sorted(present):
        print("  - %s" % t)


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return
    if "--list-tabs" in args:
        cmd_list_tabs()
        return
    run(apply="--apply" in args)


if __name__ == "__main__":
    main()
