#!/usr/bin/env python3
"""ves.py — сколько токенов весит файл, папка или набор файлов.

Зачем. Решения «читать целиком или искать грепом» принимаются вслепую, а разброс
огромный: `baza/kanon-empat.md` — 4 тыс. токенов, методичка из `korpus/` — 130 тыс.
Тридцатикратная разница, которую на глаз не видно.

Считает питоном, а не `wc`: в системе без UTF-8-локали `wc -w` и `wc -m` на
кириллице врут (`wc -m` отдаёт байты, счёт слов занижен втрое). Один такой
просчёт уже привёл к неверному выводу — поэтому здесь отдельный скрипт.

Оценка токенов приблизительная: для русского примерно 2,5 символа на токен.
Порядок величины верный, точность до процентов не нужна.

    python3 skripty/ves.py baza/                    # по файлам + итог
    python3 skripty/ves.py baza/ korpus/ produkt/   # несколько путей
    python3 skripty/ves.py . --papki                # только сводка по папкам
"""

import sys
from pathlib import Path

RASSHIRENIYA = {".md", ".txt", ".srt", ".json"}
SIMVOLOV_NA_TOKEN = 2.5
PROPUSK = {".git", "arhiv", "graphify-out", "__pycache__", ".venv"}


def sobrat(put: Path) -> list[tuple[Path, int]]:
    if put.is_file():
        return [(put, len(put.read_text(encoding="utf-8", errors="ignore")))]
    out = []
    for p in sorted(put.rglob("*")):
        if any(ch in PROPUSK for ch in p.parts):
            continue
        if p.is_file() and p.suffix in RASSHIRENIYA:
            out.append((p, len(p.read_text(encoding="utf-8", errors="ignore"))))
    return out


def tokenov(simvolov: int) -> int:
    return int(simvolov / SIMVOLOV_NA_TOKEN)


def main(argv: list[str]) -> int:
    tolko_papki = "--papki" in argv
    puti = [Path(a) for a in argv if not a.startswith("-")] or [Path(".")]

    vse: list[tuple[Path, int]] = []
    for put in puti:
        if not put.exists():
            print(f"нет пути: {put}", file=sys.stderr)
            return 1
        vse.extend(sobrat(put))

    if not vse:
        print("подходящих файлов нет")
        return 0

    if tolko_papki:
        po_papkam: dict[str, tuple[int, int]] = {}
        for p, c in vse:
            klyuch = str(p.parent)
            n, s = po_papkam.get(klyuch, (0, 0))
            po_papkam[klyuch] = (n + 1, s + c)
        for klyuch, (n, s) in sorted(po_papkam.items(), key=lambda kv: -kv[1][1]):
            print(f"{tokenov(s):>9} ток.  {n:>4} файл.  {klyuch}")
    else:
        for p, c in sorted(vse, key=lambda x: -x[1]):
            print(f"{tokenov(c):>9} ток.  {p}")

    itogo = sum(c for _, c in vse)
    print(f"{'-' * 40}\n{tokenov(itogo):>9} ток.  всего в {len(vse)} файлах")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
