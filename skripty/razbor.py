#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
razbor.py — обработать новый транскрипт Виолы и показать, что в нём есть
нового относительно уже собранной базы.

Запуск:
    python3 skripty/razbor.py korpus/новый.txt

Только стандартная библиотека.
"""

import os
import re
import sys

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KORPUS_DIR = os.path.join(KOREN, "korpus")
BAZA_DIR = os.path.join(KOREN, "baza")
KANON = os.path.join(BAZA_DIR, "kanon-viny.md")
GOLOS = os.path.join(BAZA_DIR, "golos-viola.md")

# ----------------------------------------------------------------------
# Настройки. Правь здесь.
# ----------------------------------------------------------------------

# Маркеры речи для метрик регистра
MARKERY = ["вот", "и вот", "очень", "то есть", "именно",
           "допустим", "кстати", "значит"]

# Темы -> ключевые слова. Если ключевые слова темы есть в транскрипте,
# но темы нет в kanon-viny.md — тема попадает в список «новое».
# Правь этот словарь под задачи.
TEMY = {
    "вина и стыд":        ["стыд", "стыдно"],
    "вина перед детьми":  ["ребёнок", "ребенок", "дети", "мама", "мать"],
    "вина перед родителями": ["родител", "отец", "мать перед"],
    "вина в отношениях":  ["партнёр", "партнер", "муж", "жена", "развод"],
    "гиперответственность": ["ответственност", "должна", "должен"],
    "прощение себя":      ["прости", "прощение", "простить себя"],
    "границы":            ["границ", "отказ", "нет"],
    "самокритика":        ["критик", "ругаю себя", "виню себя"],
    "тело и вина":        ["тело", "телесн", "напряжение"],
    "деньги и вина":      ["деньг", "трата", "позволить себе"],
}

# Маркеры предложений-определений / формулировок техник
FORMULY = ["это всегда", "это когда", "нужно", "я говорю", "называется", "техника"]


# ----------------------------------------------------------------------
# Общие утилиты
# ----------------------------------------------------------------------

def chitat(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def normalizovat(s):
    s = s.lower().replace("ё", "е")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def razbit_na_predlozheniya(text):
    chunks = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def slova(fragment):
    return re.findall(r"[0-9A-Za-zА-Яа-яЁё]+(?:-[0-9A-Za-zА-Яа-яЁё]+)*", fragment)


def metriki(text):
    """Словарь метрик регистра для одного текста."""
    predl = razbit_na_predlozheniya(text)
    vse = slova(text)
    dliny = [len(slova(p)) for p in predl]
    n_slov = len(vse)
    m = {
        "slov": n_slov,
        "predl": len(predl),
        "sr_dlina": (sum(dliny) / len(dliny)) if dliny else 0,
        "dolya_korotkih": (sum(1 for d in dliny if 0 < d <= 5) / len(dliny) * 100)
                          if dliny else 0,
    }
    norm = normalizovat(text)
    for mk in MARKERY:
        cnt = len(re.findall(r"(?<![0-9a-zа-я])" + re.escape(mk) + r"(?![0-9a-zа-я])", norm))
        m["m_" + mk] = (cnt / n_slov * 1000) if n_slov else 0
    return m


# ----------------------------------------------------------------------
# 1. Метрики регистра рядом со средними по корпусу
# ----------------------------------------------------------------------

def sredniy_korpus(iskl_path):
    """Средние метрики по существующему корпусу (кроме разбираемого файла)."""
    if not os.path.isdir(KORPUS_DIR):
        return None
    tex = []
    iskl = os.path.abspath(iskl_path)
    for name in sorted(os.listdir(KORPUS_DIR)):
        path = os.path.join(KORPUS_DIR, name)
        if not os.path.isfile(path) or os.path.abspath(path) == iskl:
            continue
        if not name.lower().endswith((".txt", ".md")) or name.lower() == "readme.md":
            continue
        t = chitat(path)
        if t:
            tex.append(t)
    if not tex:
        return None
    return metriki("\n".join(tex))


def blok_metriki(text, path):
    print("=" * 60)
    print("1. МЕТРИКИ РЕГИСТРА")
    print("=" * 60)
    tek = metriki(text)
    sred = sredniy_korpus(path)

    def stroka(label, key, fmt="{:.1f}"):
        v = fmt.format(tek[key])
        if sred is not None:
            print(f"  {label:<28} {v:>8}   | корпус: {fmt.format(sred[key]):>8}")
        else:
            print(f"  {label:<28} {v:>8}   | корпус: —")

    stroka("Слов", "slov", "{:.0f}")
    stroka("Предложений", "predl", "{:.0f}")
    stroka("Средняя длина, слов", "sr_dlina")
    stroka("Доля коротких (<=5), %", "dolya_korotkih")
    print("  Маркеры (на 1000 слов):")
    for mk in MARKERY:
        stroka("  «" + mk + "»", "m_" + mk)
    if sred is None:
        print("  (корпуса для сравнения нет — залей исходники в korpus/)")
    print("  Ориентир: высокие маркеры и много коротких фраз = сырая речь;")
    print("            низкие маркеры и ровная длина = отредактированная запись.")
    print()


# ----------------------------------------------------------------------
# 2. Темы, которых нет в kanon-viny.md
# ----------------------------------------------------------------------

def blok_temy(text):
    print("=" * 60)
    print("2. ТЕМЫ, КОТОРЫХ НЕТ В baza/kanon-viny.md")
    print("=" * 60)
    kanon = chitat(KANON)
    norm_text = normalizovat(text)
    if kanon is None:
        print("  baza/kanon-viny.md не найден — сравнить не с чем.")
        print()
        return
    norm_kanon = normalizovat(kanon)
    novye = []
    for tema, keys in TEMY.items():
        v_tekste = any(normalizovat(k) in norm_text for k in keys)
        v_kanone = any(normalizovat(k) in norm_kanon for k in keys) or \
            normalizovat(tema) in norm_kanon
        if v_tekste and not v_kanone:
            novye.append(tema)
    if not novye:
        print("  Новых тем по ключевым словам не найдено.")
    else:
        for t in novye:
            print(f"  • {t}")
    print()


# ----------------------------------------------------------------------
# 3. Кандидаты: определения и формулировки техник
# ----------------------------------------------------------------------

def blok_formuly(text):
    print("=" * 60)
    print("3. КАНДИДАТЫ НА ДОБАВЛЕНИЕ (определения / техники)")
    print("=" * 60)
    predl = razbit_na_predlozheniya(text)
    naideno = []
    for p in predl:
        low = normalizovat(p)
        hit = [f for f in FORMULY if f in low]
        if hit:
            naideno.append((p, hit))
    if not naideno:
        print("  Ничего похожего на определения или техники не найдено.")
    else:
        for p, hit in naideno:
            print(f"  • [{', '.join(hit)}] {p}")
    print()


# ----------------------------------------------------------------------
# 4. Образы и метафоры, которых нет в golos-viola.md (раздел 6)
# ----------------------------------------------------------------------

def izvlech_razdel6(golos_text):
    """Пытается вырезать раздел 6 из golos-viola.md. Возвращает нормализованный текст
    раздела либо весь файл, если раздел не выделился."""
    lines = golos_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*#{0,6}\s*6[\.\)]?\s+", ln) or re.match(r"^\s*6[\.\)]\s+\S", ln):
            start = i
            break
    if start is None:
        return normalizovat(golos_text)  # весь файл как запасной вариант
    # ищем следующий заголовок вида 7 ...
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\s*#{0,6}\s*7[\.\)]?\s+", lines[j]) or re.match(r"^\s*7[\.\)]\s+\S", lines[j]):
            end = j
            break
    return normalizovat("\n".join(lines[start:end]))


# Слова-приметы образности: если предложение содержит сравнение или один из этих
# корней, считаем его кандидатом в образы/метафоры.
OBRAZ_MARKERY = ["как будто", "словно", "будто", "как если", "похож",
                 "камен", "клетк", "стен", "груз", "ноша", "яма",
                 "капкан", "маска", "панцирь", "броня", "узел", "тиск"]


def blok_obrazy(text):
    print("=" * 60)
    print("4. ОБРАЗЫ И МЕТАФОРЫ, КОТОРЫХ НЕТ В golos-viola.md (раздел 6)")
    print("=" * 60)
    golos = chitat(GOLOS)
    if golos is None:
        print("  baza/golos-viola.md не найден — сравнить не с чем.")
        print()
        return
    razdel6 = izvlech_razdel6(golos)
    predl = razbit_na_predlozheniya(text)
    novye = []
    for p in predl:
        low = normalizovat(p)
        if any(m in low for m in OBRAZ_MARKERY):
            # ключевое слово образа
            klyuch = next((m for m in OBRAZ_MARKERY if m in low), "")
            if klyuch and klyuch not in razdel6:
                novye.append(p)
    if not novye:
        print("  Новых образов не найдено (или все уже есть в разделе 6).")
    else:
        for p in novye:
            print(f"  • {p}")
    print()


# ----------------------------------------------------------------------

def main(argv):
    if len(argv) != 2:
        print("Использование: python3 skripty/razbor.py korpus/новый.txt")
        return 2
    path = argv[1]
    text = chitat(path)
    if text is None:
        print(f"Файл не найден: {path}")
        return 1

    print()
    print(f"РАЗБОР ТРАНСКРИПТА: {path}")
    print()
    blok_metriki(text, path)
    blok_temy(text)
    blok_formuly(text)
    blok_obrazy(text)
    print("Ничего в базу не записано. Добавления — только после подтверждения.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
