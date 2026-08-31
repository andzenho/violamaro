#!/usr/bin/env python3
"""karta_korpusa.py — оглавление большого файла корпуса, чтобы читать его кусками.

Зачем. Методички в korpus/ — по 80–130 тыс. токенов каждая. Открыть такую
целиком ради одного абзаца дороже, чем вся остальная работа над постом.
Но внутри есть разметка страниц (`----- PAGE N -----`), а первая содержательная
строка страницы почти всегда её заголовок. Из этого собирается оглавление
с номерами строк — дальше читаем нужный кусок через offset/limit.

Ничего не пишет на диск и ничего не меняет: печатает и выходит.

    python3 skripty/karta_korpusa.py korpus/06-metodichka-empatiya-modul2-pole.txt
    python3 skripty/karta_korpusa.py korpus/*.txt --iskat поле
"""

import re
import sys
from pathlib import Path

MARKER = re.compile(r"^-+\s*PAGE\s+(\d+)\s*-+$")
SLUZHEBNOE = ("Виола Маро", "©", "www.", "ПРАКТИЧЕСКАЯ ЭМПАТИЯ", "Практическая Эмпатия")


def zagolovok(stroki: list[str], s: int) -> str:
    """Первая содержательная строка после маркера страницы."""
    for j in range(s, min(s + 6, len(stroki))):
        c = stroki[j].strip()
        if c and not c.startswith(SLUZHEBNOE):
            return c
    return ""


def karta(put: Path) -> list[tuple[str, int, str]]:
    stroki = put.read_text(encoding="utf-8").split("\n")
    out = []
    for i, l in enumerate(stroki, 1):
        m = MARKER.match(l.strip())
        if m:
            out.append((m.group(1), i, zagolovok(stroki, i)))
    return out


def main(argv: list[str]) -> int:
    iskat = None
    if "--iskat" in argv:
        k = argv.index("--iskat")
        iskat = argv[k + 1].lower() if k + 1 < len(argv) else None
        argv = argv[:k] + argv[k + 2:]
    puti = [Path(a) for a in argv if not a.startswith("-")]
    if not puti:
        print(__doc__)
        return 1

    for put in puti:
        if not put.is_file():
            print(f"нет файла: {put}", file=sys.stderr)
            return 1
        stranitsy = karta(put)
        vsego = put.read_text(encoding="utf-8").count("\n") + 1
        if not stranitsy:
            print(f"\n{put} — разметки страниц нет, {vsego} строк. "
                  f"Ищи grep -n, читай найденный диапазон.")
            continue
        print(f"\n{put} — {len(stranitsy)} страниц, {vsego} строк")
        pokazano = 0
        for nomer, stroka, zag in stranitsy:
            if iskat and iskat not in zag.lower():
                continue
            pokazano += 1
            print(f"  стр.{nomer:>4}  строка {stroka:>5}  {zag[:76]}")
        if iskat and not pokazano:
            print(f"  по «{iskat}» в заголовках страниц ничего нет — пробуй grep -n")
    print("\nЧитать кусок: Read <файл> offset=<строка> limit=50")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
