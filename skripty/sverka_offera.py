#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сверка оффера: не разошлись ли копии клиентского текста.

Источник правды — produkt/prezentatsiya-lyubov-i-dengi.md. Остальные файлы
пересказывают его для своих задач и обязаны совпадать по фактам:
цены, названия лекций, состав того, что человек получает, формат.

    python3 skripty/sverka_offera.py

Код возврата 1, если найдены расхождения — можно вешать на хук.
Только стандартная библиотека.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ISTOCHNIK = ROOT / "produkt" / "prezentatsiya-lyubov-i-dengi.md"
KOPII = [
    ROOT / "produkt" / "odnostranichnik-sozvon-lyubov-i-dengi.md",
    ROOT / "produkt" / "programma-lyubov-i-dengi-v1.md",
    ROOT / "produkt" / "karta-smyslov-i-argumentov.md",
]
DOCX = ROOT / "produkt" / "docs" / "Любовь-и-деньги-презентация.docx"


def chitat(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def klient_chast(text):
    """Кусок между метками клиентской части."""
    a = text.find("## ✂️ КЛИЕНТСКАЯ ЧАСТЬ")
    b = text.find("## ✂️ КОНЕЦ КЛИЕНТСКОЙ ЧАСТИ")
    return text[a:b] if a >= 0 and b > a else text


def ceny(text):
    return sorted(set(re.findall(r"\b\d{2}\s?900\b", text)))


def lekcii(text):
    """Номер лекции → её название."""
    out = {}
    for n, name in re.findall(r"\*\*Лекция (\d)\.\s*([^*]+)\*\*", text):
        out[n] = name.strip().rstrip(".")
    # сжатая форма: нумерованный список внутри цитаты («> 1. **Название**»)
    for n, name in re.findall(r"^>\s*(\d)\.\s+\*\*([^*]+)\*\*", text, re.M):
        out.setdefault(n, name.strip().rstrip("."))
    return out


def dostavka(text):
    """Что человек получает — по ключевым словам, а не по формулировке."""
    marks = {
        "аудиоверсия": r"аудиоверси",
        "мастер-класс": r"мастер-класс",
        "рабочая тетрадь": r"рабоч\w+ тетрад",
        "доска желаний": r"доск\w+ желаний",
        "практики голосом": r"практик\w+ голосом",
        "готовые фразы": r"готов\w+ фраз",
        "конституция эмпата": r"конституци\w+ эмпата",
        "сообщество": r"сообществ\w+ эмпатов",
        "доступ навсегда": r"навсегда",
    }
    return {k: bool(re.search(v, text, re.I)) for k, v in marks.items()}


def main():
    if not ISTOCHNIK.exists():
        print("Нет источника правды: %s" % ISTOCHNIK)
        return 2

    src_full = chitat(ISTOCHNIK)
    src = klient_chast(src_full)
    src_ceny, src_lekcii, src_dost = ceny(src), lekcii(src), dostavka(src)

    print("Источник правды: %s" % ISTOCHNIK.relative_to(ROOT))
    print("  цены:   %s" % ", ".join(src_ceny))
    print("  лекций: %d" % len(src_lekcii))
    print()

    problemy = []

    for p in KOPII:
        if not p.exists():
            continue
        txt = chitat(p)
        imya = p.relative_to(ROOT)
        zamechaniya = []

        # цены: в копии не должно быть цен, которых нет в источнике
        chuzhie = [c for c in ceny(txt) if c not in src_ceny]
        if chuzhie:
            zamechaniya.append("цены, которых нет в источнике: %s" % ", ".join(chuzhie))

        # названия лекций
        for n, name in lekcii(txt).items():
            etalon = src_lekcii.get(n)
            if etalon and name.lower() != etalon.lower():
                zamechaniya.append(
                    "лекция %s: «%s» ≠ «%s»" % (n, name, etalon))

        # состав: проверяем только там, где файл сам заявляет полный список
        if "**Что вы получите**" in txt or "## Что вы получите" in txt:
            kop_dost = dostavka(txt)
            net = [k for k, v in src_dost.items() if v and not kop_dost.get(k)]
            if net:
                zamechaniya.append("не упомянуто из состава: %s" % ", ".join(net))

        if zamechaniya:
            problemy.append((imya, zamechaniya))

    # .docx собран из источника или отстал
    if DOCX.exists():
        if DOCX.stat().st_mtime < ISTOCHNIK.stat().st_mtime:
            problemy.append((DOCX.relative_to(ROOT), [
                "собран раньше последней правки источника — пересобрать: "
                "node skripty/gen_prezentatsiya_docx.js"]))
    else:
        problemy.append((DOCX.relative_to(ROOT), ["файла нет — собрать генератором"]))

    if not problemy:
        print("Расхождений нет.")
        return 0

    print("РАСХОЖДЕНИЯ")
    for imya, zs in problemy:
        print("\n  %s" % imya)
        for z in zs:
            print("    · %s" % z)
    print("\nПравим копии под источник, не наоборот.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
