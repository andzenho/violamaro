#!/usr/bin/env python3
"""Собирает один файл-контекст для ассистента в обычном Claude (не Claude Code).

Зачем: сотруднику без git нужен весь контекст проекта одним документом —
он грузит его в Проект Claude (Knowledge) или прикладывает в чат.

Запуск из корня репозитория:
    python3 skripty/kontekst_pak.py            # положит viola-kontekst-dlya-assistenta.md в корень
    python3 skripty/kontekst_pak.py путь.md    # или по указанному пути

Файл — производная выжимка, в git не хранится: пересобирать перед каждой передачей,
иначе разойдётся с источниками правды.
"""

import sys
from datetime import date
from pathlib import Path

RAZDELY = [
    ("1. ПРАВИЛА ПРОЕКТА (CLAUDE.md)", "CLAUDE.md", None),
    ("2. ГОЛОС ВИОЛЫ (baza/golos-viola.md) — читать перед любым текстом от её лица",
     "baza/golos-viola.md", None),
    ("3. ПРИНЦИПЫ И КРАСНЫЕ ЛИНИИ (baza/printsipy-viola.md)", "baza/printsipy-viola.md", None),
    ("4. ПРОДУКТ: практикум «Прикладная эмпатия» (клиентская часть)",
     "produkt/praktikum-dlya-empatov.md", "## 10а."),
    ("5. СТРАТЕГИЯ ЗАПУСКА (produkt/strategiya.md)", "produkt/strategiya.md", None),
    ("6. ПРАВИЛА КОНТЕНТА, ВСЕ КАНАЛЫ (kontent/kp/strategiya-kontent-plana.md)",
     "kontent/kp/strategiya-kontent-plana.md", None),
    ("7. АУДИТОРИЯ: мастер-сводка (analitika/ca-master.md)", "analitika/ca-master.md", None),
    ("8. ЯЗЫК АУДИТОРИИ: банк дословных фраз (analitika/ca-voc.md)", "analitika/ca-voc.md", None),
]


def sobrat() -> str:
    kuski = [
        "# КОНТЕКСТ ПРОЕКТА «ВИОЛА МАРО» — пакет для ассистента\n"
        f"Собран {date.today().strftime('%d.%m.%Y')} из репозитория "
        "github.com/andzenho/violamaro (ветка main).\n"
        "Внутри: правила проекта, голос Виолы, продукт, стратегия, аудитория, правила контента.\n"
        "Это выжимка источников правды. При расхождении с чем-либо ещё — верить этому файлу.\n"
    ]
    for zagolovok, put, obrezat_do in RAZDELY:
        tekst = Path(put).read_text(encoding="utf-8")
        if obrezat_do:
            granica = tekst.find(obrezat_do)
            if granica > 0:
                tekst = tekst[:granica]
        kuski.append("\n\n" + "=" * 70 + f"\n{zagolovok}\n" + "=" * 70 + "\n")
        kuski.append(tekst)
    return "".join(kuski)


if __name__ == "__main__":
    cel = Path(sys.argv[1] if len(sys.argv) > 1 else "viola-kontekst-dlya-assistenta.md")
    soderzhimoe = sobrat()
    cel.write_text(soderzhimoe, encoding="utf-8")
    print(f"Готово: {cel} — {len(soderzhimoe)} знаков, ~{len(soderzhimoe.split())} слов")
