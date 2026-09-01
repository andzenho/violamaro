#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sheets_sync.py — синхронизация контент-плана из репозитория в Google-таблицу
«Виола // Рабочее пространство».

Направление: РЕПОЗИТОРИЙ → ТАБЛИЦА (источник правды — репозиторий).
Пишет ТОЛЬКО в две колонки каждой вкладки КП:
    «Тема / идея»  — идея поста и его цель
    «Текст поста»  (или «Суть») — итоговый текст
Больше ничего не трогает: ни разметку, ни формулы, ни объединённые ячейки,
ни строки. Строки в таблице не добавляются и не удаляются — заполняются
только уже существующие по дате.

ВНИМАНИЕ: это единственный скрипт проекта с внешними зависимостями
(google-api-python-client, google-auth). Причина — писать в Google Sheets
без внешней библиотеки нельзя (нужна подпись RS256, её нет в стандартной
библиотеке). Установка:
    python3 -m pip install -r skripty/requirements-sheets.txt

Доступ (сервис-аккаунт), делается один раз — см. kontent/kp/README.md:
    1. Google Cloud → создать сервис-аккаунт, включить Google Sheets API.
    2. Скачать JSON-ключ, положить в skripty/.google-creds.json (в .gitignore).
    3. Расшарить таблицу на email сервис-аккаунта (доступ «Редактор»).

Запуск:
    python3 skripty/sheets_sync.py --list-tabs   # какие вкладки видит, где КП
    python3 skripty/sheets_sync.py               # сухой прогон: что изменится
    python3 skripty/sheets_sync.py --apply       # записать изменения в таблицу
"""

import os
import re
import sys

# ----------------------------------------------------------------------
# Настройки. Правь здесь.
# ----------------------------------------------------------------------

# ID таблицы (из ссылки .../spreadsheets/d/<ID>/edit). Можно переопределить
# переменной окружения VIOLA_SHEET_ID.
SPREADSHEET_ID = os.environ.get(
    "VIOLA_SHEET_ID",
    "1f3kxO_BWc3NBGO1k9PoUIjzbCdvIZITB5PjiZ4DmuCQ",
)

# Путь к JSON-ключу сервис-аккаунта. Переопределяется VIOLA_SHEETS_CREDS.
KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS_PATH = os.environ.get(
    "VIOLA_SHEETS_CREDS",
    os.path.join(KOREN, "skripty", ".google-creds.json"),
)

# Папка с источником контент-плана.
KP_DIR = os.path.join(KOREN, "kontent", "kp")

# Как в шапке таблицы называются нужные колонки (сравнение без учёта
# регистра и лишних пробелов).
COL_DATE = "дата"
COL_THEME = "тема / идея"
COL_TEXT_VARIANTS = ("текст поста", "суть")  # у разных вкладок по-разному
COL_FORMAT = "формат"  # необязательная колонка; пишем, только если есть в шапке

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ----------------------------------------------------------------------
# Утилиты
# ----------------------------------------------------------------------

def norm(s):
    """Нормализовать заголовок ячейки для сравнения."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def col_letter(idx):
    """0 -> A, 1 -> B, ... (для адресов A1)."""
    s = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        s = chr(65 + rem) + s
    return s


def parse_date(s):
    """'07.08.2026' -> (2026, 8, 7). None, если не дата."""
    m = re.match(r"^\s*(\d{2})\.(\d{2})\.(\d{4})\s*$", s or "")
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (y, mo, d)


def a1_quote(title):
    """Экранировать имя листа для A1-нотации."""
    return "'" + title.replace("'", "''") + "'"


# ----------------------------------------------------------------------
# Чтение источника из репозитория
# ----------------------------------------------------------------------

def parse_post_file(path):
    """
    Разобрать файл поста. Формат:
        тема: <идея и цель, одна строка>
        статус: <необязательно>
        ---
        <текст поста, многострочный>
    Возвращает dict {'тема': str, 'текст': str}. 'текст' может быть пустым
    (для дней, где пока есть только идея без текста).
    """
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    sep = "\n---\n"
    if sep in raw:
        head, body = raw.split(sep, 1)
    elif raw.rstrip().endswith("---"):
        head, body = raw.rstrip()[:-3], ""
    else:
        head, body = raw, ""

    tema = ""
    fmt = ""
    status = ""
    for line in head.splitlines():
        m = re.match(r"^([A-Za-zА-Яа-яЁё ]+?)\s*:\s*(.*)$", line)
        if not m:
            continue
        key = norm(m.group(1))
        if key == "тема":
            tema = m.group(2).strip()
        elif key == "формат":
            fmt = m.group(2).strip()
        elif key == "статус":
            status = m.group(2).strip().lower()
        # прочие поля читаем, но в таблицу не пишем.

    return {
        "тема": tema,
        "формат": fmt,
        "текст": body.strip("\n"),
        "статус": norm(status),
    }


def load_tab_source(folder):
    """
    Прочитать папку одной вкладки: точное имя вкладки из _tab.txt и посты.
    Возвращает (tab_title, posts_by_date) где posts_by_date — dict
    (y,mo,d) -> [post, ...] в порядке имён файлов.
    """
    tab_file = os.path.join(folder, "_tab.txt")
    if not os.path.isfile(tab_file):
        return None, None
    with open(tab_file, encoding="utf-8") as f:
        tab_title = f.readline().strip()
    if not tab_title:
        return None, None

    posts_by_date = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
        if not m:
            continue
        key = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        post = parse_post_file(os.path.join(folder, name))
        posts_by_date.setdefault(key, []).append(post)
    return tab_title, posts_by_date


def load_all_sources():
    """Все вкладки из kontent/kp/: {tab_title: posts_by_date}."""
    sources = {}
    if not os.path.isdir(KP_DIR):
        return sources
    for name in sorted(os.listdir(KP_DIR)):
        folder = os.path.join(KP_DIR, name)
        if not os.path.isdir(folder):
            continue
        title, posts = load_tab_source(folder)
        if title:
            sources[title] = posts
    return sources


# ----------------------------------------------------------------------
# Работа с таблицей
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

    # Ключ можно передать тремя способами (по приоритету):
    #  1) VIOLA_SHEETS_CREDS_B64 — JSON, закодированный в base64. РЕКОМЕНДУЕТСЯ
    #     для переменных окружения: только буквы/цифры, .env ничего не ломает;
    #  2) VIOLA_SHEETS_CREDS_JSON — сам JSON строкой (может пострадать от
    #     обработки спецсимволов в некоторых .env);
    #  3) файл по пути CREDS_PATH (по умолчанию skripty/.google-creds.json).
    import json
    info = None
    creds_b64 = os.environ.get("VIOLA_SHEETS_CREDS_B64")
    creds_json = os.environ.get("VIOLA_SHEETS_CREDS_JSON")
    if creds_b64:
        import base64
        info = json.loads(base64.b64decode(creds_b64))
    elif creds_json:
        info = json.loads(creds_json)

    if info is not None:
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
    elif os.path.isfile(CREDS_PATH):
        creds = service_account.Credentials.from_service_account_file(
            CREDS_PATH, scopes=SCOPES
        )
    else:
        sys.exit(
            "Нет ключа сервис-аккаунта.\n"
            "Задай VIOLA_SHEETS_CREDS_B64 (JSON в base64) или "
            "VIOLA_SHEETS_CREDS_JSON (сам JSON), либо положи файл: %s\n"
            "Инструкция — kontent/kp/README.md." % CREDS_PATH
        )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_sheet_grid(svc, title):
    """Прочитать верх листа. Возвращает список строк (список списков)."""
    rng = "%s!A1:H1000" % a1_quote(title)
    resp = (
        svc.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=rng, valueRenderOption="FORMATTED_VALUE")
        .execute()
    )
    return resp.get("values", [])


def analyze_kp(rows):
    """
    Найти в листе шапку КП и разметку колонок/дат.
    Возвращает dict с ключами header_row (0-based), col_date, col_theme,
    col_text, dates ({(y,mo,d): [row_number_1based, ...]}) — или None,
    если это не вкладка КП.
    """
    header_idx = None
    for i, row in enumerate(rows):
        cells = [norm(c) for c in row]
        if COL_THEME in cells and COL_DATE in cells:
            header_idx = i
            break
    if header_idx is None:
        return None

    header = [norm(c) for c in rows[header_idx]]
    col_date = header.index(COL_DATE)
    col_theme = header.index(COL_THEME)
    col_text = None
    for variant in COL_TEXT_VARIANTS:
        if variant in header:
            col_text = header.index(variant)
            break
    if col_text is None:
        return None
    col_format = header.index(COL_FORMAT) if COL_FORMAT in header else None

    dates = {}
    for r in range(header_idx + 1, len(rows)):
        row = rows[r]
        cell = row[col_date] if col_date < len(row) else ""
        key = parse_date(cell)
        if key is None:
            continue
        dates.setdefault(key, []).append(r + 1)  # 1-based номер строки
    return {
        "header_row": header_idx,
        "col_date": col_date,
        "col_theme": col_theme,
        "col_text": col_text,
        "col_format": col_format,
        "dates": dates,
        "rows": rows,
    }


def cell_current(rows, row_1based, col_idx):
    """Текущее значение ячейки из уже прочитанной сетки."""
    r = row_1based - 1
    if r < len(rows) and col_idx < len(rows[r]):
        return rows[r][col_idx]
    return ""


def plan_updates(title, kp, posts_by_date):
    """
    Сопоставить посты со строками и собрать список изменений.
    Возвращает (updates, warnings). updates — список dict для batchUpdate,
    каждый с доп. полями для показа диффа.
    """
    updates = []
    warnings = []
    rows = kp["rows"]

    for date_key in sorted(posts_by_date):
        # Снятые посты строк не занимают: то, что решено не выпускать,
        # в витрине не показываем, а освободившиеся строки чистим ниже.
        posts = [p for p in posts_by_date[date_key] if p.get("статус") != "снят"]
        row_nums = kp["dates"].get(date_key, [])
        ds = "%02d.%02d.%04d" % (date_key[2], date_key[1], date_key[0])

        if not row_nums:
            warnings.append(
                "  [%s] дата %s есть в репозитории, но строки с такой датой "
                "нет в таблице — пропускаю (строки не добавляю)." % (title, ds)
            )
            continue
        if len(posts) > len(row_nums):
            warnings.append(
                "  [%s] дата %s: постов %d, а строк в таблице %d — лишние "
                "пропущены. Добавь строки в таблице вручную." % (title, ds, len(posts), len(row_nums))
            )

        # Строки, оставшиеся без поста (все посты дня сняты либо их стало
        # меньше), очищаем — иначе в таблице висит снятый текст.
        for row_num in row_nums[len(posts):]:
            cols = [(kp["col_theme"], ""), (kp["col_text"], "")]
            if kp.get("col_format") is not None:
                cols.append((kp["col_format"], ""))
            for col_idx, value in cols:
                old = cell_current(rows, row_num, col_idx)
                if not (old or ""):
                    continue
                addr = "%s!%s%d" % (a1_quote(title), col_letter(col_idx), row_num)
                updates.append({"range": addr, "values": [[value]],
                                "_old": old, "_new": value, "_date": ds})

        for post, row_num in zip(posts, row_nums):
            cols = [
                (kp["col_theme"], post.get("тема", "")),
                (kp["col_text"], post.get("текст", "")),
            ]
            # 'Формат' — если колонка есть в шапке и поле задано; у снятого
            # поста поле пустое и колонка тоже очищается.
            if kp.get("col_format") is not None and (
                post.get("формат") or post.get("статус") == "снят"
            ):
                cols.append((kp["col_format"], post.get("формат", "")))
            for col_idx, value in cols:
                old = cell_current(rows, row_num, col_idx)
                if (old or "") == (value or ""):
                    continue
                addr = "%s!%s%d" % (a1_quote(title), col_letter(col_idx), row_num)
                updates.append(
                    {
                        "range": addr,
                        "values": [[value]],
                        "_old": old,
                        "_new": value,
                        "_date": ds,
                    }
                )
    return updates, warnings


def short(s, n=60):
    s = (s or "").replace("\n", " ⏎ ")
    return s if len(s) <= n else s[: n - 1] + "…"


# ----------------------------------------------------------------------
# Команды
# ----------------------------------------------------------------------

def cmd_list_tabs(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    print("Вкладки таблицы «%s»:" % meta.get("properties", {}).get("title", ""))
    for s in meta["sheets"]:
        title = s["properties"]["title"]
        rows = read_sheet_grid(svc, title)
        kp = analyze_kp(rows)
        mark = "КП" if kp else "  "
        extra = ""
        if kp:
            n = len(kp["dates"])
            text_col = col_letter(kp["col_text"])
            extra = " — дат: %d, колонка текста: %s" % (n, text_col)
        print("  [%s] %s%s" % (mark, title, extra))


def run_sync(svc, apply):
    sources = load_all_sources()
    if not sources:
        print("В %s нет вкладок-источников (папок с _tab.txt). Нечего писать." % KP_DIR)
        return

    meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_titles = {s["properties"]["title"] for s in meta["sheets"]}

    all_updates = []
    all_warnings = []

    for title, posts_by_date in sources.items():
        if title not in sheet_titles:
            all_warnings.append(
                "  Вкладка «%s» есть в репозитории, но не найдена в таблице "
                "(проверь _tab.txt)." % title
            )
            continue
        rows = read_sheet_grid(svc, title)
        kp = analyze_kp(rows)
        if not kp:
            all_warnings.append(
                "  Вкладка «%s» найдена, но это не похоже на КП "
                "(нет колонок «Дата» и «Тема / идея»)." % title
            )
            continue
        updates, warnings = plan_updates(title, kp, posts_by_date)
        all_updates.extend(updates)
        all_warnings.extend(warnings)

    # Показать план.
    if all_updates:
        print("Изменения (%d ячеек):" % len(all_updates))
        for u in all_updates:
            print("  %s  [%s]" % (u["range"], u["_date"]))
            print("      было:  %s" % short(u["_old"]))
            print("      стало: %s" % short(u["_new"]))
    else:
        print("Изменений нет — таблица уже совпадает с репозиторием.")

    if all_warnings:
        print("\nПредупреждения:")
        for w in all_warnings:
            print(w)

    if not all_updates:
        return

    if not apply:
        print("\nЭто сухой прогон. Чтобы записать — запусти с --apply.")
        return

    body = {
        "valueInputOption": "RAW",  # писать как есть, без интерпретации формул/дат
        "data": [{"range": u["range"], "values": u["values"]} for u in all_updates],
    }
    resp = svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body=body
    ).execute()
    print("\nЗаписано ячеек: %s" % resp.get("totalUpdatedCells", 0))


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return
    svc = build_service()
    if "--list-tabs" in args:
        cmd_list_tabs(svc)
        return
    run_sync(svc, apply="--apply" in args)


if __name__ == "__main__":
    main()
