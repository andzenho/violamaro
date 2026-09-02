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
Добавление строк (--dobavit). Скрипт синхронизации строк не создаёт,
и каждый раз, когда в плане появляется новый день или второй пост на день,
строку приходится заводить руками. Протяжка за уголок в Google Sheets
наращивает год (04.09.2026 → 04.09.2027), поэтому так делать нельзя.
Режим --dobavit вставляет недостающие строки сам: копией строки-соседа,
чтобы разметка и формулы сохранились, и ставит нужную дату с днём недели.

Запуск:
    python3 skripty/sheets_chistka.py --dobavit          # сухой прогон
    python3 skripty/sheets_chistka.py --dobavit --apply  # вставить
"""
import sys, os, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheets_sync as S


def sheet_ids(svc):
    meta = svc.spreadsheets().get(spreadsheetId=S.SPREADSHEET_ID).execute()
    return {sh["properties"]["title"]: sh["properties"]["sheetId"]
            for sh in meta.get("sheets", [])}


DNI = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def nuzhnye_stroki():
    """Сколько строк нужно каждой дате по репозиторию: {вкладка: {дата: n}}."""
    need = {}
    for title, posts_by_date in S.load_all_sources().items():
        for key, posts in posts_by_date.items():
            live = [p for p in posts if p.get("статус") != "снят"]
            if live:
                need.setdefault(title, {})[key] = len(live)
    return need


def dobavit(svc, ids, apply):
    """
    Вставить недостающие строки и проставить в них дату с днём недели.

    В два прохода. Сначала вставки: батч применяется целиком, и адреса
    ячеек внутри одного батча посчитать нельзя — после каждой вставки
    номера строк ниже съезжают. Поэтому даты пишем вторым проходом, уже
    по свежему чтению листа: пустые строки сопоставляются с недостающими
    датами по порядку следования.
    """
    need = nuzhnye_stroki()
    plan = {}
    total = 0
    for title, po_datam in sorted(need.items()):
        if title not in ids:
            continue
        rows = S.read_sheet_grid(svc, title)
        kp = S.analyze_kp(rows)
        if not kp:
            continue
        est = kp["dates"]
        nehvatka = []
        for key in sorted(po_datam):
            n = po_datam[key] - len(est.get(key, []))
            if n > 0:
                nehvatka.append((key, n))
        if not nehvatka:
            continue
        plan[title] = (kp, nehvatka)
        print("%s:" % title)
        for key, n in nehvatka:
            d = datetime.date(*key)
            print("   +%d строк(и) на %s (%s)" % (n, d.strftime("%d.%m.%Y"), DNI[d.weekday()]))
            total += n

    if not total:
        print("Все нужные строки на месте.")
        return
    print("\nВсего вставить: %d строк." % total)
    if not apply:
        print("Это сухой прогон. Чтобы вставить — добавь --apply.")
        return

    # проход 1: вставка строк, снизу вверх
    requests = []
    for title, (kp, nehvatka) in plan.items():
        est = kp["dates"]
        for key, n in nehvatka:
            ranshe = [k for k in est if k < key]
            if ranshe:
                yakor = max(est[max(ranshe)])
            elif est:
                yakor = min(min(est.values())) - 1
            else:
                yakor = kp["header_row"] + 1
            requests.append((yakor, {"insertDimension": {
                "range": {"sheetId": ids[title], "dimension": "ROWS",
                          "startIndex": yakor, "endIndex": yakor + n},
                "inheritFromBefore": True}}))
    requests.sort(key=lambda x: -x[0])
    svc.spreadsheets().batchUpdate(
        spreadsheetId=S.SPREADSHEET_ID,
        body={"requests": [r for _, r in requests]}).execute()

    # проход 2: даты в пустые строки
    updates = []
    for title, (kp0, nehvatka) in plan.items():
        rows = S.read_sheet_grid(svc, title)
        kp = S.analyze_kp(rows)
        nuzhno = []
        for key, n in nehvatka:
            nuzhno.extend([key] * n)
        nuzhno.sort()
        posledn = None
        # хвост листа: values API не возвращает строки, где нет ни одного
        # значения, а вставленные строки как раз пустые. Идём с запасом.
        do = len(rows) + len(nuzhno) + 2
        for r in range(kp["header_row"] + 1, do):
            if not nuzhno:
                break
            row = rows[r - 1] if r - 1 < len(rows) else []
            cell = row[kp["col_date"]] if kp["col_date"] < len(row) else ""
            key = S.parse_date(cell)
            if key is not None:
                posledn = key
                continue
            if posledn is None:
                continue
            podhod = [k for k in nuzhno if k >= posledn]
            if not podhod:
                continue
            key = podhod[0]
            nuzhno.remove(key)
            d = datetime.date(*key)
            updates.append({
                "range": "%s!%s%d" % (S.a1_quote(title),
                                      S.col_letter(kp["col_date"]), r),
                "values": [[d.strftime("%d.%m.%Y"), DNI[d.weekday()]]]})
    if updates:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=S.SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()
    print("Вставлено: %d строк, дат проставлено: %d." % (total, len(updates)))


def main():
    apply = "--apply" in sys.argv
    if "--dobavit" in sys.argv:
        svc = S.build_service()
        dobavit(svc, sheet_ids(svc), apply)
        return
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
