#!/usr/bin/env python3
"""Проверка, кому бот может написать первым, — по каждому Telegram ID.

Зачем: люди приходят в мини-апп по прямой ссылке и в чат бота не пишут.
Рассылка до такого человека доходит, только если Telegram хранит для него
разрешение «этому боту можно писать первым». Снаружи это разрешение не видно
ни в ChatPlace, ни в самом Telegram — узнать можно только спросив Bot API
по каждому ID. Этим скрипт и занимается.

Как спрашиваем: метод sendChatAction («бот печатает…»). Он проходит те же
проверки, что и настоящее сообщение, но ничего не отправляет — у достижимых
людей на секунду мелькнёт «печатает…» вверху чата, и всё.

Вердикты:
  reachable   — рассылка дойдёт;
  no_access   — разрешения нет: снял галочку «Разрешить боту писать» при
                первом открытии, или его клиент разрешение не передал;
  blocked     — разрешение было, но человек бота заблокировал/остановил;
  bad_id      — это не Telegram ID (опечатка, пустая строка);
  error       — другое: смотреть текст ответа в отчёте.

Запуск:
  TG_BOT_TOKEN=123:abc python3 skripty/bot_probe.py ids.txt
  python3 skripty/bot_probe.py --token 123:abc vygruzka.csv --out otchet.csv

Вход: файл с ID — по одному в строке, либо CSV с колонкой userId
(как в выгрузке Google-таблицы теста; колонка находится по заголовку).
Токен бота: переменная TG_BOT_TOKEN или флаг --token.
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.telegram.org/bot{token}/{method}"


def read_ids(path):
    """Файл: CSV с колонкой userId или просто ID по строке. Порядок сохраняем."""
    ids, seen = [], set()

    def add(raw):
        raw = raw.strip().strip('"')
        if not raw or raw in seen:
            return
        seen.add(raw)
        ids.append(raw)

    with open(path, encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        if "," in first or ";" in first:
            delim = ";" if first.count(";") > first.count(",") else ","
            rows = list(csv.reader(f, delimiter=delim))
            header = [c.strip().lower() for c in rows[0]] if rows else []
            col = next((i for i, c in enumerate(header) if c in ("userid", "user_id", "id", "tg_id")), None)
            if col is None:
                sys.exit("В CSV не нашлась колонка userId (или user_id / id / tg_id). "
                         "Либо дайте файл с ID по одному в строке.")
            for row in rows[1:]:
                if len(row) > col:
                    add(row[col])
        else:
            for line in f:
                add(line)
    return ids


def call(token, method, payload):
    """Один вызов Bot API. Возвращает (ok, описание_ошибки, retry_after)."""
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            return bool(data.get("ok")), "", 0
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode())
        except Exception:
            return False, "HTTP %s" % e.code, 0
        desc = data.get("description", "HTTP %s" % e.code)
        retry = data.get("parameters", {}).get("retry_after", 0)
        return False, desc, retry
    except urllib.error.URLError as e:
        return False, "сеть: %s" % e.reason, 0


def verdict(ok, desc):
    d = desc.lower()
    if ok:
        return "reachable"
    if "blocked" in d or "deactivated" in d:
        return "blocked"
    if "chat not found" in d or "initiate" in d or "forbidden" in d:
        return "no_access"
    return "error"


def main():
    ap = argparse.ArgumentParser(description="Кому бот может написать первым")
    ap.add_argument("ids_file", help="файл с Telegram ID (по строке) или CSV с колонкой userId")
    ap.add_argument("--token", default=os.environ.get("TG_BOT_TOKEN"), help="токен бота (или TG_BOT_TOKEN)")
    ap.add_argument("--out", help="куда писать отчёт CSV (по умолчанию <вход>-probe.csv)")
    args = ap.parse_args()

    if not args.token:
        sys.exit("Нет токена: задайте TG_BOT_TOKEN или --token. Токен — в BotFather.")

    ids = read_ids(args.ids_file)
    if not ids:
        sys.exit("В файле не нашлось ни одного ID.")

    ok, desc, _ = call(args.token, "getMe", {})
    if not ok:
        sys.exit("Токен не работает: %s" % desc)

    out_path = args.out or os.path.splitext(args.ids_file)[0] + "-probe.csv"
    counts = {}
    rows = []

    for n, uid in enumerate(ids, 1):
        if not uid.lstrip("-").isdigit():
            v, desc = "bad_id", "не число"
        else:
            while True:
                ok, desc, retry = call(args.token, "sendChatAction",
                                       {"chat_id": int(uid), "action": "typing"})
                if retry:
                    time.sleep(retry + 1)
                    continue
                break
            v = verdict(ok, desc)
        counts[v] = counts.get(v, 0) + 1
        rows.append((uid, v, desc))
        print("%4d/%d  %-12s %-10s %s" % (n, len(ids), uid, v, desc))
        time.sleep(0.1)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["userId", "verdict", "telegram_answer"])
        w.writerows(rows)

    print("\nИтог по %d ID:" % len(ids))
    for v in ("reachable", "no_access", "blocked", "bad_id", "error"):
        if v in counts:
            print("  %-10s %d" % (v, counts[v]))
    print("Отчёт: %s" % out_path)


if __name__ == "__main__":
    main()
