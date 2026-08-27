#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proverka.py — проверка готового текста, написанного от лица Виолы,
перед отправкой ей.

Запуск:
    python3 skripty/proverka.py путь/к/тексту.txt

Только стандартная библиотека.
"""

import os
import re
import sys

# ----------------------------------------------------------------------
# Настройки норм. Правь здесь, если Виола уточнит свои параметры.
# ----------------------------------------------------------------------

# Средняя длина предложения (в словах)
SR_DLINA_NORMA = (11, 12)
SR_DLINA_MIN = 7          # предупреждать, если меньше
SR_DLINA_MAX = 14         # предупреждать, если больше

# Доля коротких предложений (до 5 слов включительно)
KOROTKIE_POROG = 5        # «короткое» = <= 5 слов
KOROTKIE_NORMA = (20, 30)  # проценты
KOROTKIE_MIN = 15         # предупреждать, если меньше, %

# Длинные предложения
DLINNOE_POROG = 30        # больше стольких слов — выводить целиком

# «вот» на 1000 слов
VOT_NORMA = 20
VOT_MIN = 8               # предупреждать, если меньше

# «очень» на 1000 слов
OCHEN_NORMA_MAX = 4       # предупреждать при превышении

# Слова, которые Виола вычищает сама при записи
ZAPRESCHENNYE = [
    "допустим", "кстати", "значит", "прям",
    "слушайте", "смотрите", "послушайте", "короче",
]

# Лимиты Telegram (в знаках)
TG_PODPIS = 1024          # подпись к видео
TG_POST = 4096            # обычный пост

KORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "korpus")


# ----------------------------------------------------------------------
# Разбор текста
# ----------------------------------------------------------------------

def razbit_na_predlozheniya(text):
    """Грубое, но предсказуемое разбиение на предложения по . ! ? … и переводам строк."""
    # переводы строки тоже считаем границей
    chunks = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def slova(fragment):
    """Список слов: последовательности из букв/цифр/дефиса."""
    return re.findall(r"[0-9A-Za-zА-Яа-яЁё]+(?:-[0-9A-Za-zА-Яа-яЁё]+)*", fragment)


def normalizovat(s):
    """Нижний регистр, ё->е, схлопывание пробелов. Для сверки с корпусом."""
    s = s.lower().replace("ё", "е")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def chastota_slova(text_lower_words, target):
    return sum(1 for w in text_lower_words if w == target)


# ----------------------------------------------------------------------
# Отчёт
# ----------------------------------------------------------------------

def hr():
    print("-" * 60)


def predupr(cond, msg):
    """Печатает строку с пометкой, если cond истинно."""
    if cond:
        print("  ⚠ " + msg)


def otchet(text):
    predlozheniya = razbit_na_predlozheniya(text)
    vse_slova = slova(text)
    slova_lower = [w.lower().replace("ё", "е") for w in vse_slova]

    n_znakov = len(text)
    n_slov = len(vse_slova)
    n_predl = len(predlozheniya)

    dliny = [len(slova(p)) for p in predlozheniya]
    sr_dlina = (sum(dliny) / len(dliny)) if dliny else 0

    print()
    print("=" * 60)
    print("ОТЧЁТ ПО ТЕКСТУ")
    print("=" * 60)

    # 1. Объём и средняя длина
    hr()
    print("1. ОБЪЁМ")
    print(f"  Знаков:      {n_znakov}")
    print(f"  Слов:        {n_slov}")
    print(f"  Предложений: {n_predl}")
    print(f"  Средняя длина предложения: {sr_dlina:.1f} слов "
          f"(норма {SR_DLINA_NORMA[0]}-{SR_DLINA_NORMA[1]})")
    predupr(sr_dlina and sr_dlina < SR_DLINA_MIN,
            f"средняя длина меньше {SR_DLINA_MIN} — речь рубленая")
    predupr(sr_dlina > SR_DLINA_MAX,
            f"средняя длина больше {SR_DLINA_MAX} — предложения тяжёлые")

    # 2. Доля коротких предложений
    hr()
    korotkie = [d for d in dliny if 0 < d <= KOROTKIE_POROG]
    dolya_kor = (len(korotkie) / n_predl * 100) if n_predl else 0
    print("2. КОРОТКИЕ ПРЕДЛОЖЕНИЯ (до 5 слов)")
    print(f"  Доля: {dolya_kor:.0f}% "
          f"(норма {KOROTKIE_NORMA[0]}-{KOROTKIE_NORMA[1]}%)")
    predupr(dolya_kor < KOROTKIE_MIN,
            f"коротких меньше {KOROTKIE_MIN}% — не хватает её ритма")

    # 3. Длинные предложения
    hr()
    print(f"3. ДЛИННЫЕ ПРЕДЛОЖЕНИЯ (больше {DLINNOE_POROG} слов) — норма 0")
    dlinnye = [(d, p) for d, p in zip(dliny, predlozheniya) if d > DLINNOE_POROG]
    if not dlinnye:
        print("  Нет.")
    else:
        print(f"  Найдено: {len(dlinnye)}")
        for d, p in dlinnye:
            print(f"  ⚠ [{d} слов] {p}")

    # 4. «вот»
    hr()
    n_vot = chastota_slova(slova_lower, "вот")
    vot_na_1000 = (n_vot / n_slov * 1000) if n_slov else 0
    print("4. СЛОВО «вот»")
    print(f"  Найдено: {n_vot}. На 1000 слов: {vot_na_1000:.1f} "
          f"(норма около {VOT_NORMA})")
    predupr(vot_na_1000 < VOT_MIN,
            f"«вот» меньше {VOT_MIN} на 1000 — недостаёт её интонации")

    # 5. Запрещённые слова
    hr()
    print("5. ЗАПРЕЩЁННЫЕ СЛОВА (она их вычищает сама)")
    nashli = False
    for z in ZAPRESCHENNYE:
        for m in re.finditer(r"(?<![0-9A-Za-zА-Яа-яЁё])" + re.escape(z) +
                             r"(?![0-9A-Za-zА-Яа-яЁё])", text, flags=re.IGNORECASE):
            nashli = True
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            kontekst = re.sub(r"\s+", " ", text[start:end]).strip()
            print(f"  ⚠ «{z}»: …{kontekst}…")
    if not nashli:
        print("  Нет.")

    # 6. «очень»
    hr()
    n_ochen = chastota_slova(slova_lower, "очень")
    ochen_na_1000 = (n_ochen / n_slov * 1000) if n_slov else 0
    print("6. СЛОВО «очень»")
    print(f"  Найдено: {n_ochen}. На 1000 слов: {ochen_na_1000:.1f} "
          f"(норма до {OCHEN_NORMA_MAX})")
    predupr(ochen_na_1000 > OCHEN_NORMA_MAX,
            f"«очень» больше {OCHEN_NORMA_MAX} на 1000 — усилитель приелся")

    # 7. Конструкция «не ..., а ...»
    hr()
    print("7. КОНСТРУКЦИЯ «не ..., а ...» (в продающем тексте запрещена)")
    ne_a = re.findall(r"\bне\s+[^,.;!?]{1,40}?,\s*а\s+[^,.;!?]{1,40}",
                      text, flags=re.IGNORECASE)
    if not ne_a:
        print("  Нет.")
    else:
        print(f"  Найдено: {len(ne_a)}")
        for frag in ne_a:
            frag = re.sub(r"\s+", " ", frag).strip()
            print(f"  ⚠ «{frag}» — запрещено в продающем тексте, "
                  f"допустимо в экспертном контенте от лица Виолы")

    # 8. Лимиты Telegram
    hr()
    print("8. ЛИМИТЫ TELEGRAM")
    print(f"  Знаков в тексте: {n_znakov}")
    znak_podpis = "OK" if n_znakov <= TG_PODPIS else f"ПРЕВЫШЕН на {n_znakov - TG_PODPIS}"
    znak_post = "OK" if n_znakov <= TG_POST else f"ПРЕВЫШЕН на {n_znakov - TG_POST}"
    print(f"  Подпись к видео ({TG_PODPIS}): {znak_podpis}")
    print(f"  Обычный пост   ({TG_POST}): {znak_post}")

    # Сверка с корпусом
    hr()
    sverka_s_korpusom(predlozheniya)

    print("=" * 60)
    print()


# ----------------------------------------------------------------------
# Сверка с корпусом
# ----------------------------------------------------------------------

def zagruzit_korpus():
    """Возвращает единый нормализованный текст всех файлов korpus/."""
    if not os.path.isdir(KORPUS_DIR):
        return None
    kuski = []
    for name in sorted(os.listdir(KORPUS_DIR)):
        path = os.path.join(KORPUS_DIR, name)
        if not os.path.isfile(path):
            continue
        if not name.lower().endswith((".txt", ".md")):
            continue
        if name.lower() == "readme.md":
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                kuski.append(f.read())
        except OSError:
            continue
    if not kuski:
        return None
    return normalizovat("\n".join(kuski))


def sverka_s_korpusom(predlozheniya):
    print("СВЕРКА С КОРПУСОМ (дословность фрагментов)")
    korpus = zagruzit_korpus()
    if korpus is None:
        print("  korpus/ пуст или недоступен — сверка пропущена.")
        return

    shirina = 50
    print(f"  {'фрагмент':<{shirina}} | в корпусе")
    print(f"  {'-' * shirina}-+----------")
    naideno = 0
    for p in predlozheniya:
        norm = normalizovat(p)
        if not norm:
            continue
        est = norm in korpus
        if est:
            naideno += 1
        pokaz = (p[:shirina - 1] + "…") if len(p) > shirina else p
        print(f"  {pokaz:<{shirina}} | {'да' if est else 'нет'}")
    vsego = sum(1 for p in predlozheniya if normalizovat(p))
    if vsego:
        print(f"  Дословно из корпуса: {naideno} из {vsego} "
              f"({naideno / vsego * 100:.0f}%)")


# ----------------------------------------------------------------------

def otbrosit_shapku_kp(text, path=""):
    """Файлы контент-плана начинаются со служебной шапки:

        формат: ...
        тема: ...
        статус: ...
        ---
        <текст поста>

    Шапка — не текст Виолы: она искажает и метрики (длина фраз, доля
    коротких), и лимиты Telegram, и сверку с корпусом. Отбрасываем её.
    Обычные тексты без шапки возвращаем как есть.
    """
    lines = text.split("\n")
    if not lines or not lines[0].lower().startswith(("формат:", "тема:", "статус:")):
        return text
    for i, line in enumerate(lines[:12]):
        if line.strip() == "---":
            ostatok = "\n".join(lines[i + 1:]).strip()
            if ostatok:
                if path:
                    print(f"(шапка контент-плана отброшена, проверяю только текст поста)\n")
                return ostatok
            break
    return text


def main(argv):
    if len(argv) != 2:
        print("Использование: python3 skripty/proverka.py путь/к/тексту.txt")
        return 2
    path = argv[1]
    if not os.path.isfile(path):
        print(f"Файл не найден: {path}")
        return 1
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = otbrosit_shapku_kp(text, path)
    otchet(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
