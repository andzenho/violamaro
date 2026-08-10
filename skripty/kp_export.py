#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kp_export.py — собрать контент-план из kontent/kp/ в вид, удобный для
РУЧНОЙ вставки в Google-таблицу. Без Google-аккаунта и без зависимостей.

Для каждой вкладки и каждой даты печатает два блока: «Тема / идея» и
«Текст поста» — их копируешь в соответствующие ячейки таблицы.

Запуск:
    python3 skripty/kp_export.py

Результат печатается в терминал и сохраняется в
kontent/kp/_dlya_vstavki.txt (открой, копируй оттуда).

Только стандартная библиотека.
"""

import os
import sys

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOREN, "skripty"))

# Разбор источника переиспользуем из sheets_sync (там только stdlib на верхнем
# уровне; google-библиотеки грузятся лениво и здесь не нужны).
from sheets_sync import load_all_sources  # noqa: E402

OUT_PATH = os.path.join(KOREN, "kontent", "kp", "_dlya_vstavki.txt")

LINE = "─" * 60


def format_date(key):
    y, mo, d = key
    return "%02d.%02d.%04d" % (d, mo, y)


def build_report():
    sources = load_all_sources()
    out = []
    if not sources:
        return "В kontent/kp/ нет вкладок (папок с _tab.txt). Нечего выгружать.\n"

    for tab_title in sorted(sources):
        posts_by_date = sources[tab_title]
        out.append("=" * 60)
        out.append("ВКЛАДКА: %s" % tab_title)
        out.append("=" * 60)
        out.append("")

        for date_key in sorted(posts_by_date):
            posts = posts_by_date[date_key]
            ds = format_date(date_key)
            for i, post in enumerate(posts, 1):
                metka = ds if len(posts) == 1 else "%s  (пост %d из %d)" % (ds, i, len(posts))
                out.append(LINE)
                out.append("ДАТА: %s" % metka)
                out.append(LINE)
                out.append("① В ячейку «Тема / идея»:")
                out.append(post["тема"] or "(пусто)")
                out.append("")
                out.append("② В ячейку «Текст поста»:")
                out.append(post["текст"] if post["текст"] else "(текста пока нет)")
                out.append("")
                out.append("")
    return "\n".join(out)


def main():
    report = build_report()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("\nСохранено в: %s" % OUT_PATH)
    print("Открой этот файл и копируй значения в таблицу по датам.")


if __name__ == "__main__":
    main()
