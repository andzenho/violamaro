#!/usr/bin/env python3
"""Сборка промпта для Claude Design.

Бриф (`produkt/lending-promt-dizayn.md`) + клиентская часть продукта
(`produkt/praktikum-dlya-empatov.md`, между метками ✂️) → готовый промпт.

    python3 skripty/lending_promt.py                      # сухой прогон, флагман
    python3 skripty/lending_promt.py --apply              # записать lending-promt-gotovyy.md
    python3 skripty/lending_promt.py --sobytie            # сухой прогон, событие «Неудобные»
    python3 skripty/lending_promt.py --sobytie --apply    # записать neudobnye-promt-gotovyy.md
    python3 skripty/lending_promt.py --stdout             # напечатать в консоль

Источник правды по тексту — praktikum-dlya-empatov.md (флагман) либо
neudobnye-lending.md (событие). Собранный файл перезаписывается, правки
вносить в бриф и в текст, а не в него.
"""

import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent

# Два набора: флагман «Прикладная эмпатия» и событие «Неудобные».
NABORY = {
    "flagman": {
        "brif": "lending-promt-dizayn.md",
        "produkt": "praktikum-dlya-empatov.md",
        "gotovyy": "lending-promt-gotovyy.md",
    },
    "sobytie": {
        "brif": "neudobnye-promt-dizayn.md",
        "produkt": "neudobnye-lending.md",
        "gotovyy": "neudobnye-promt-gotovyy.md",
    },
}

BRIF = PRODUKT = GOTOVYY = None  # проставляются в main() по выбранному набору

NACHALO = "<!-- НАЧАЛО ПРОМПТА -->"
KONETS = "<!-- КОНЕЦ ПРОМПТА -->"
METKA = "{{КЛИЕНТСКАЯ_ЧАСТЬ}}"
REZ_START = "# ✂️ КЛИЕНТСКАЯ ЧАСТЬ"
REZ_KONETS = "# ✂️ КОНЕЦ КЛИЕНТСКОЙ ЧАСТИ"

SHAPKA = (
    "<!-- Собрано скриптом skripty/lending_promt.py. Не править руками: "
    "правки вносить в бриф и в исходный текст. -->\n\n"
)


def vzyat_klientskuyu_chast() -> str:
    text = PRODUKT.read_text(encoding="utf-8")
    if REZ_START not in text or REZ_KONETS not in text:
        oshibka(
            f"в {PRODUKT.name} не нашлись метки ✂️ — клиентскую часть не вырезать.\n"
            f"Ожидались строки:\n  {REZ_START}\n  {REZ_KONETS}"
        )
    telo = text.split(REZ_START, 1)[1].split(REZ_KONETS, 1)[0]
    return telo.strip()


def vzyat_brif() -> str:
    text = BRIF.read_text(encoding="utf-8")
    if NACHALO not in text or KONETS not in text:
        oshibka(f"в {BRIF.name} не нашлись метки {NACHALO} / {KONETS}.")
    telo = text.split(NACHALO, 1)[1].split(KONETS, 1)[0]
    if METKA not in telo:
        oshibka(f"в {BRIF.name} не нашлась метка {METKA} — некуда вставить текст страницы.")
    return telo.strip()


def oshibka(soobshchenie: str) -> None:
    print(f"⛔ {soobshchenie}", file=sys.stderr)
    sys.exit(1)


def sobrat() -> str:
    return SHAPKA + vzyat_brif().replace(METKA, vzyat_klientskuyu_chast()) + "\n"


def vybrat_nabor(flagi: set) -> None:
    """Проставить пути под выбранный набор: --sobytie или флагман по умолчанию."""
    global BRIF, PRODUKT, GOTOVYY
    nabor = NABORY["sobytie" if "--sobytie" in flagi else "flagman"]
    BRIF = KOREN / "produkt" / nabor["brif"]
    PRODUKT = KOREN / "produkt" / nabor["produkt"]
    GOTOVYY = KOREN / "produkt" / nabor["gotovyy"]


def main() -> None:
    flagi = set(sys.argv[1:])
    neizvestnye = flagi - {"--apply", "--stdout", "--sobytie"}
    if neizvestnye:
        oshibka(f"неизвестные ключи: {', '.join(sorted(neizvestnye))}")
    vybrat_nabor(flagi)

    promt = sobrat()
    znakov = len(promt)
    strok = promt.count("\n") + 1

    if "--stdout" in flagi:
        print(promt)
        return

    if "--apply" in flagi:
        GOTOVYY.write_text(promt, encoding="utf-8")
        print(f"✅ записано: {GOTOVYY.relative_to(KOREN)} — {strok} строк, {znakov} знаков")
        return

    print("Сухой прогон, файл не тронут.")
    print(f"  бриф:   {BRIF.relative_to(KOREN)}")
    print(f"  текст:  {PRODUKT.relative_to(KOREN)} (клиентская часть между ✂️)")
    print(f"  выход:  {GOTOVYY.relative_to(KOREN)}")
    print(f"  объём:  {strok} строк, {znakov} знаков")
    klyuch = " --sobytie" if "--sobytie" in flagi else ""
    print(f"Записать: python3 skripty/lending_promt.py{klyuch} --apply")


if __name__ == "__main__":
    main()
