#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg_comments.py — разбор HTML-экспорта чата/канала из Telegram Desktop
(«Export chat history» → формат HTML). Достаёт сообщения из messages*.html
и раскладывает их на две части:

  • речь Виолы (посты и её ответы в комментариях) — это НЕ аудитория;
  • комментарии аудитории — сырьё для анализа ЦА (язык, боли, роли, фразы).

Комментарии аудитории кладутся в analitika/kommentarii/ (НЕ в korpus/ —
это не речь Виолы). Реплики самой Виолы сохраняются отдельным файлом:
они её голос, но это переписка, а не подготовленный материал, поэтому в
korpus/ автоматически не тащим — при необходимости переносит человек.

Формат выгрузки на весь экспорт:
  • <prefix>.jsonl — по сообщению аудитории на строку:
    author, text, date, reactions (сумма), reply (флаг ответа), id.
  • <prefix>.txt   — только тексты аудитории, для быстрого анализа.
  • <prefix>.viola.txt — реплики Виолы (её голос в переписке).

Запуск:
  python3 skripty/tg_comments.py /путь/к/папке_экспорта
  python3 skripty/tg_comments.py /путь/к/экспорту --prefix tg-violamaro1
  python3 skripty/tg_comments.py /путь --out analitika/kommentarii

Кого считать Виолой — список имён в --viola (через запятую). По умолчанию
берутся частые варианты написания её имени в экспортах канала.

Только стандартная библиотека.
"""
import argparse
import glob
import html
import json
import os
import re
import sys

# По умолчанию — имя канала/аккаунта Виолы в разных написаниях (в экспортах
# латинская «a» иногда подменяет кириллическую). «… Chat» — служебный автор.
DEFAULT_VIOLA = [
    "Виолa Маро", "Виола Маро", "Виолa Маро Chat", "Виола Маро Chat",
    "Практическая Эмпатия 3.0",  # промо-аккаунт её продукта, не аудитория
]


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def field(block, cls):
    m = re.search(r'<div class="%s[^"]*">(.*?)</div>' % re.escape(cls), block, re.S)
    return clean(m.group(1)) if m else None


def text_of(block):
    m = re.search(
        r'<div class="text">(.*?)</div>\s*'
        r'(?:<span class="reactions"|<div class="signature'
        r'|<div class="media|<div class="reply|</div>)',
        block, re.S)
    if not m:
        m = re.search(r'<div class="text">(.*?)</div>', block, re.S)
    return clean(m.group(1)) if m else None


def reactions_sum(block):
    return sum(int(x) for x in re.findall(r'<span class="count">\s*(\d+)\s*</span>', block))


def parse_dir(src):
    files = sorted(glob.glob(os.path.join(src, "messages*.html")),
                   key=lambda p: (len(p), p))
    if not files:
        sys.exit("Не нашёл messages*.html в: %s" % src)
    msgs = []
    last_author = None
    for f in files:
        txt = open(f, encoding="utf-8").read()
        parts = re.split(
            r'(?=<div class="message (?:default|service)[^"]*" id="message-?\d+">)',
            txt)
        for p in parts:
            mh = re.match(
                r'<div class="message (default|service)([^"]*)" id="message(-?\d+)">',
                p)
            if not mh:
                continue
            if mh.group(1) == "service":
                last_author = None
                continue
            joined = "joined" in mh.group(2)
            author = field(p, "from_name") or (last_author if joined else None)
            if author:
                last_author = author
            dm = re.search(r'<div class="pull_right date details" title="([^"]+)"', p)
            msgs.append({
                "id": mh.group(3),
                "author": author or "Unknown",
                "text": text_of(p) or "",
                "date": dm.group(1) if dm else None,
                "reply": "In reply to" in p,
                "reactions": reactions_sum(p),
            })
    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="папка HTML-экспорта Telegram (с messages*.html)")
    ap.add_argument("--out", default="analitika/kommentarii")
    ap.add_argument("--prefix", default="tg-violamaro1")
    ap.add_argument("--viola", default=",".join(DEFAULT_VIOLA),
                    help="имена, считать речью Виолы (через запятую)")
    a = ap.parse_args()
    viola_names = {x.strip() for x in a.viola.split(",") if x.strip()}

    msgs = parse_dir(a.src)
    users = [m for m in msgs if m["author"] not in viola_names and m["text"].strip()]
    viola = [m for m in msgs if m["author"] in viola_names and m["text"].strip()]

    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, a.prefix)
    with open(base + ".jsonl", "w", encoding="utf-8") as fh:
        for m in users:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    with open(base + ".txt", "w", encoding="utf-8") as fh:
        for m in users:
            fh.write(m["text"].replace("\n", " ").strip() + "\n")
    with open(base + ".viola.txt", "w", encoding="utf-8") as fh:
        for m in viola:
            fh.write(m["text"].replace("\n", " ").strip() + "\n")

    print("Сообщений всего:      ", len(msgs))
    print("Комментариев аудитории:", len(users))
    print("Реплик Виолы:          ", len(viola))
    print("Записано:", base + ".jsonl / .txt / .viola.txt")


if __name__ == "__main__":
    main()
