#!/usr/bin/env python3
"""Сборка промпта для Claude Design.

Бриф (`produkt/lending-promt-dizayn.md`) + клиентская часть продукта
(`produkt/praktikum-dlya-empatov.md`, между метками ✂️) → готовый промпт.

    python3 skripty/lending_promt.py            # сухой прогон: что получится
    python3 skripty/lending_promt.py --apply    # записать produkt/lending-promt-gotovyy.md
    python3 skripty/lending_promt.py --stdout   # напечатать в консоль

Источник правды по тексту — praktikum-dlya-empatov.md. Собранный файл
перезаписывается, правки вносить в бриф и в продукт, а не в него.
"""

import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
BRIF = KOREN / "produkt" / "lending-promt-dizayn.md"
PRODUKT = KOREN / "produkt" / "praktikum-dlya-empatov.md"
GOTOVYY = KOREN / "produkt" / "lending-promt-gotovyy.md"

NACHALO = "<!-- НАЧАЛО ПРОМПТА -->"
KONETS = "<!-- КОНЕЦ ПРОМПТА -->"
METKA = "{{КЛИЕНТСКАЯ_ЧАСТЬ}}"
REZ_START = "# ✂️ КЛИЕНТСКАЯ ЧАСТЬ"
REZ_KONETS = "# ✂️ КОНЕЦ КЛИЕНТСКОЙ ЧАСТИ"

SHAPKA = (
    "<!-- Собрано скриптом skripty/lending_promt.py. Не править руками: "
    "бриф — produkt/lending-promt-dizayn.md, текст — produkt/praktikum-dlya-empatov.md. -->\n\n"
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


def main() -> None:
    flagi = set(sys.argv[1:])
    neizvestnye = flagi - {"--apply", "--stdout"}
    if neizvestnye:
        oshibka(f"неизвестные ключи: {', '.join(sorted(neizvestnye))}")

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
    print("Записать: python3 skripty/lending_promt.py --apply")


if __name__ == "__main__":
    main()
