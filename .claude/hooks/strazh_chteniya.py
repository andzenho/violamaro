#!/usr/bin/env python3
"""strazh_chteniya.py — PreToolUse-хук: не дать прочитать тяжёлый файл целиком.

Зачем. В `korpus/` лежат методички по 60–110 тыс. токенов. Один `Read` без
`limit` съедает половину сессии, и дальше ассистент работает хуже: чем длиннее
контекст, тем ниже точность (это измеримый эффект, не суеверие). Правило
«читать кусками» жило в CLAUDE.md как просьба, а просьбы соблюдаются не всегда.

Что делает:
  • `Read` файла тяжелее ПОРОГА без `limit` — запрещает и объясняет, как надо;
  • `Read` чего-либо из `arhiv/` — пропускает, но напоминает, что это архив.

Escape hatch: запрет висит только на инструменте `Read`. Если файл правда нужен
целиком — `sed -n '1,400p' <файл>` через Bash работает и хуком не трогается.

Никогда не блокирует ничего, кроме описанного случая: любая ошибка внутри —
это выход 0 и молчание, работа продолжается.
"""

import json
import os
import sys

POROG_TOKENOV = 10_000
SIMVOLOV_NA_TOKEN = 2.5
POROG_SIMVOLOV = int(POROG_TOKENOV * SIMVOLOV_NA_TOKEN)

# Файлы, которые по правилам проекта читаются целиком, каким бы ни был вес.
ISKLYUCHENIYA = {
    "baza/golos-viola.md",   # правило воронки текста: читается целиком
    "karta.md",
    "CLAUDE.md",
}


def otvet(reshenie: str, prichina: str = "", kontekst: str = "") -> None:
    blok = {"hookEventName": "PreToolUse"}
    if reshenie:
        blok["permissionDecision"] = reshenie
        blok["permissionDecisionReason"] = prichina
    if kontekst:
        blok["additionalContext"] = kontekst
    print(json.dumps({"hookSpecificOutput": blok}, ensure_ascii=False))


def main() -> int:
    try:
        dannye = json.load(sys.stdin)
    except Exception:
        return 0

    if dannye.get("tool_name") != "Read":
        return 0

    vhod = dannye.get("tool_input") or {}
    put = vhod.get("file_path") or ""
    if not put or not os.path.isfile(put):
        return 0

    koren = dannye.get("cwd") or os.getcwd()
    try:
        otnositelnyy = os.path.relpath(put, koren)
    except ValueError:
        otnositelnyy = put

    if otnositelnyy.startswith("arhiv" + os.sep):
        otvet(
            "",
            kontekst=(
                "⚠️ Это `arhiv/` — устаревшее и противоречащее текущему курсу. "
                "Цены, названия и портреты ЦА оттуда недействительны. "
                "Ничего отсюда не переносить в тексты: правда — в `baza/` и `produkt/`."
            ),
        )
        return 0

    if vhod.get("limit"):
        return 0

    if otnositelnyy.replace(os.sep, "/") in ISKLYUCHENIYA:
        return 0

    try:
        # Считаем СИМВОЛЫ, а не байты: в UTF-8 кириллица занимает два байта,
        # и по размеру файла вес завышается вдвое.
        simvolov = len(
            open(put, encoding="utf-8", errors="ignore").read()
        )
    except OSError:
        return 0
    if simvolov <= POROG_SIMVOLOV:
        return 0

    priblizitelno = int(simvolov / SIMVOLOV_NA_TOKEN)
    otvet(
        "deny",
        prichina=(
            f"Файл тяжёлый — примерно {priblizitelno:,} токенов".replace(",", " ")
            + f" (порог {POROG_TOKENOV:,} ток.).".replace(",", " ")
            + " Целиком не читаем: длинный контекст снижает точность работы дальше."
            " Порядок: `grep -n '<что ищем>' " + otnositelnyy + "`,"
            " затем Read с offset/limit вокруг найденных строк."
            " Оглавление с номерами строк — `python3 skripty/oglavlenie.py <файл>`."
            " Если файл правда нужен целиком — `sed -n '1,400p' " + otnositelnyy
            + "` через Bash, хук это не трогает."
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
