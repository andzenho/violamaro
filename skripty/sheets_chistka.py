# -*- coding: utf-8 -*-
"""
Чистка контент-плана в Google-таблице: удаляет строки с датами, которых
не должно быть.

Зачем. Автозаполнение Google Sheets умеет протянуть строку вниз и наплодить
даты вперёд на сотни лет: во вкладке «КП Кабинет предзаписи» так появились
184 строки с годами от 2027 до 2210, и в каждой продублировалась тема
последнего заполненного дня. Скрипт синхронизации такие строки видит как
обычные и молча в них пишет.

Что удаляет: строки, где дата разобралась, но год не 2026 (или год из
--god). Ничего другого не трогает — ни разметку, ни формулы, ни строки
без даты, ни строки с датами нужного года, даже пустые.

Запуск:
    python3 skripty/sheets_chistka.py            # сухой прогон
    python3 skripty/sheets_chistka.py --apply    # удалить
    python3 skripty/sheets_chistka.py --god 2026 # какой год считать своим
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_sync as S


def sheet_ids(svc):
    meta = svc.spreadsheets().get(spreadsheetId=S.SPREADSHEET_ID).execute()
    return {sh["properties"]["title"]: sh["properties"]["sheetId"]
            for sh in meta.get("sheets", [])}


def main():
    apply = "--apply" in sys.argv
    god = 2026
    if "--god" in sys.argv:
        god = int(sys.argv[sys.argv.index("--god") + 1])

    svc = S.build_service()
    ids = sheet_ids(svc)
    requests = []
    total = 0

    for title, sheet_id in ids.items():
        rows = S.read_sheet_grid(svc, title)
        kp = S.analyze_kp(rows)
        if not kp:
            continue
        bad = []
        for key, row_nums in kp["dates"].items():
            if key[0] != god:
                bad.extend(row_nums)
        if not bad:
            continue
        bad.sort()
        total += len(bad)
        print("%s: лишних строк %d (строки %d-%d, годы %s)" % (
            title, len(bad), bad[0], bad[-1],
            ", ".join(str(y) for y in sorted({k[0] for k in kp["dates"] if k[0] != god})[:5]) + "…"))
        # удаляем снизу вверх, чтобы номера не съезжали
        for r in sorted(bad, reverse=True):
            requests.append({"deleteDimension": {"range": {
                "sheetId": sheet_id, "dimension": "ROWS",
                "startIndex": r - 1, "endIndex": r}}})

    if not requests:
        print("Лишних строк нет.")
        return
    print("\nВсего к удалению: %d строк." % total)
    if not apply:
        print("Это сухой прогон. Чтобы удалить — запусти с --apply.")
        return
    svc.spreadsheets().batchUpdate(
        spreadsheetId=S.SPREADSHEET_ID, body={"requests": requests}).execute()
    print("Удалено: %d строк." % total)


if __name__ == "__main__":
    main()
