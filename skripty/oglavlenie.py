#!/usr/bin/env python3
"""oglavlenie.py — вставить/обновить оглавление с номерами строк в тяжёлом файле.

Зачем. Файл на 30 тыс. токенов целиком не читают — читают кусками через
`Read` с `offset`/`limit`. Но чтобы взять нужный кусок, надо знать, на какой он
строке. Оглавление с номерами строк превращает «прочитать §16а» из поиска
вслепую в одно точное чтение.

Блок ставится в шапку файла между маркерами и при повторном запуске
переписывается — номера строк остаются верными после правок.

    python3 skripty/oglavlenie.py produkt/praktikum-vnutrennie-zametki.md
    python3 skripty/oglavlenie.py <файл> --uroven 3   # включить и ### тоже
    python3 skripty/oglavlenie.py --vse               # все файлы тяжелее 10 тыс. ток.
"""

import re
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
NACHALO = "<!-- оглавление: собрано skripty/oglavlenie.py, руками не править -->"
KONEC = "<!-- /оглавление -->"
SIMVOLOV_NA_TOKEN = 2.5
TYAZHELYY = 10_000


def sobrat_oglavlenie(stroki: list[str], uroven: int) -> list[str]:
    """Заголовки без блока оглавления, с номерами строк в итоговом файле."""
    punkty = []
    for i, s in enumerate(stroki, 1):
        m = re.match(r"^(#{2,%d}) +(.+)$" % uroven, s)
        if m:
            otstup = "  " * (len(m.group(1)) - 2)
            punkty.append((i, otstup, m.group(2).strip()))
    return punkty


def bez_bloka(tekst: str) -> str:
    if NACHALO in tekst and KONEC in tekst:
        do = tekst.split(NACHALO)[0]
        posle = tekst.split(KONEC, 1)[1].lstrip("\n")
        return do.rstrip("\n") + "\n\n" + posle
    return tekst


def tochka_vstavki(stroki: list[str]) -> int:
    """После вводной части: перед первым '---' или первым '## '."""
    for i, s in enumerate(stroki):
        if i > 0 and (s.strip() == "---" or s.startswith("## ")):
            return i
    return min(len(stroki), 1)


def obrabotat(put: Path, uroven: int) -> bool:
    chistyy = bez_bloka(put.read_text(encoding="utf-8"))
    stroki = chistyy.splitlines()
    vstavka = tochka_vstavki(stroki)  # индекс, перед которым встанет блок

    punkty = sobrat_oglavlenie(stroki, uroven)
    if not punkty:
        print(f"{put}: заголовков не найдено, пропуск")
        return False

    # Длина блока известна заранее: 4 строки шапки + пункты + 3 строки хвоста.
    dlina_bloka = len(punkty) + 7

    blok = [NACHALO, "", "## Оглавление (строки)", ""]
    for nomer, otstup, zagolovok in punkty:
        # Заголовок с 1-based строкой nomer стоит по индексу nomer-1.
        sdvig = dlina_bloka if nomer - 1 >= vstavka else 0
        blok.append(f"{otstup}- {zagolovok} — строка {nomer + sdvig}")
    blok += ["", KONEC, ""]
    assert len(blok) == dlina_bloka, (len(blok), dlina_bloka)

    novye = stroki[:vstavka] + blok + stroki[vstavka:]
    put.write_text("\n".join(novye).rstrip("\n") + "\n", encoding="utf-8")
    print(f"{put}: оглавление на {len(punkty)} пунктов")
    return True


def tyazhelye() -> list[Path]:
    out = []
    for p in sorted(KOREN.rglob("*.md")):
        if any(ch in {".git", "arhiv", "node_modules"} for ch in p.parts):
            continue
        if len(p.read_text(encoding="utf-8", errors="ignore")) / SIMVOLOV_NA_TOKEN > TYAZHELYY:
            out.append(p)
    return out


def main(argv: list[str]) -> int:
    uroven = 2
    if "--uroven" in argv:
        uroven = int(argv[argv.index("--uroven") + 1])
    if "--vse" in argv:
        puti = tyazhelye()
    else:
        puti = [Path(a) for a in argv if not a.startswith("-") and not a.isdigit()]
    if not puti:
        print(__doc__)
        return 1
    for p in puti:
        if not p.is_file():
            print(f"нет файла: {p}", file=sys.stderr)
            return 1
        obrabotat(p, uroven)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
