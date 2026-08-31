#!/usr/bin/env python3
"""perenos.py — расставить переносы строк в транскрипте по границам предложений.

Зачем. Часть файлов в korpus/ — одна строка на весь файл (02-otvety.txt: 57 тыс.
символов в одной строке). Для человека разницы нет, для инструментов — большая:
grep возвращает «строку с совпадением», то есть весь файл целиком, а чтение
кусками (offset/limit) вообще не работает. Один поиск по такому файлу стоит
столько же, сколько прочитать его весь.

Что делает. Разрезает только сами переносы строк. Ни один символ текста не
меняется, ничего не чистится и не сокращается — правило korpus/ («сырьё, не
редактировать») соблюдено. Перед записью сверяет: текст с схлопнутыми пробелами
до и после обязан совпасть символ в символ, иначе файл не переписывается.

Идемпотентен: строки короче порога не трогает, повторный запуск ничего не меняет.

    python3 skripty/perenos.py korpus/02-otvety.txt        # показать, что будет
    python3 skripty/perenos.py korpus/*.txt --primenit     # переписать файлы
"""

import re
import sys
from pathlib import Path

# Строки короче этого не режем: они уже читаемы и грепаются нормально.
PORAG = 400

# После этих сокращений точка — не конец предложения.
SOKRASHCHENIYA = {
    "т", "тт", "др", "пр", "см", "ср", "им", "гг", "вв", "руб", "коп",
    "тыс", "млн", "млрд", "г", "гг", "в", "вв", "н", "э", "стр", "рис",
    "табл", "пп", "ст", "чч", "мин", "сек", "проф", "доц", "акад",
}

# Конец предложения: . ! ? … (возможно с закрывающей кавычкой/скобкой),
# затем пробел, затем начало следующего — заглавная, кавычка, тире, цифра.
GRANITSA = re.compile(
    r'(?<=[.!?…])(["»)\]]?)\s+(?=[«"(\[—–-]?[А-ЯЁA-Z0-9])'
)


def _ne_rezat(levo: str) -> bool:
    """True, если точка слева — часть сокращения или инициала, а не конец фразы."""
    hvost = levo.rstrip('"»)]')
    if not hvost.endswith((".", "!", "?", "…")):
        return False
    if not hvost.endswith("."):
        return False
    slovo = re.split(r"[\s(«\"]", hvost[:-1])[-1].lower()
    if not slovo:
        return False
    # Инициал («А. С. Пушкин») или известное сокращение.
    if len(slovo) == 1 and slovo.isalpha():
        return True
    return slovo in SOKRASHCHENIYA


def razbit(stroka: str) -> list[str]:
    """Разрезать одну длинную строку на предложения."""
    if len(stroka) <= PORAG:
        return [stroka]
    chasti: list[str] = []
    nachalo = 0
    for m in GRANITSA.finditer(stroka):
        konets = m.end(1)  # включая закрывающую кавычку, без пробела
        if _ne_rezat(stroka[nachalo:konets]):
            continue
        kusok = stroka[nachalo:konets].strip()
        if kusok:
            chasti.append(kusok)
        nachalo = m.end()
    ostatok = stroka[nachalo:].strip()
    if ostatok:
        chasti.append(ostatok)
    return chasti or [stroka]


def obrabotat(tekst: str) -> str:
    novye: list[str] = []
    for stroka in tekst.split("\n"):
        novye.extend(razbit(stroka))
    return "\n".join(novye)


def _sverit(a: str, b: str) -> bool:
    """Тексты совпадают, если различия только в пробельных символах."""
    return re.sub(r"\s+", " ", a).strip() == re.sub(r"\s+", " ", b).strip()


def main(argv: list[str]) -> int:
    primenit = "--primenit" in argv
    puti = [Path(a) for a in argv if not a.startswith("-")]
    if not puti:
        print(__doc__)
        return 1

    vsego_izmeneno = 0
    for put in puti:
        if not put.is_file():
            print(f"нет файла: {put}", file=sys.stderr)
            return 1
        staryy = put.read_text(encoding="utf-8")
        novyy = obrabotat(staryy)

        if not _sverit(staryy, novyy):
            print(f"СТОП {put}: текст разошёлся, файл не тронут", file=sys.stderr)
            return 2

        bylo = staryy.count("\n") + 1
        stalo = novyy.count("\n") + 1
        makso = max((len(s) for s in staryy.split("\n")), default=0)
        maksn = max((len(s) for s in novyy.split("\n")), default=0)

        if novyy == staryy:
            print(f"без изменений  {put}  ({bylo} строк, макс. {makso})")
            continue

        vsego_izmeneno += 1
        print(f"{'переписан ' if primenit else 'изменится '} {put}"
              f"  строк {bylo} → {stalo}, макс. строка {makso} → {maksn}")
        if primenit:
            put.write_text(novyy, encoding="utf-8")

    if vsego_izmeneno and not primenit:
        print("\nСухой прогон. Переписать: добавь --primenit")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
