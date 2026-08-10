#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
razbor_kommentov.py — разбор комментариев аудитории (сырьё из analitika/kommentarii/)
для анализа ЦА: язык, фигуры вины, ярлыки, сигнал по углам, боли.

ВАЖНО (оговорка из ca-analiz): комментарии = ЯЗЫК и перечень тем, НЕ замер долей.
Комментируют самые вовлечённые; состав задан выбором роликов.

Запуск:
    python3 skripty/razbor_kommentov.py               # все *.jsonl в analitika/kommentarii
    python3 skripty/razbor_kommentov.py файл.jsonl ...

Только стандартная библиотека.
"""
import glob
import json
import os
import re
import sys
from collections import Counter

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(KOREN, "analitika", "kommentarii")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower().replace("ё", "е")).strip()


def words(s):
    return re.findall(r"[а-яa-z]+", norm(s))


# Фигуры, на которых аудитория вешает вину/токсичность.
FIGURY = {
    "мать/мама":      [r"\bмам", r"\bмать", r"\bматер"],
    "отец/папа":      [r"\bпап", r"\bотец", r"\bотц"],
    "муж":            [r"\bмуж\b", r"\bмужа\b", r"\bмужу\b", r"\bмужем\b"],
    "жена":           [r"\bжена\b", r"\bжену\b", r"\bжене\b", r"\bженой\b"],
    "партнёр":        [r"\bпартн"],
    "бывший/ая":      [r"\bбывш"],
    "свекровь":       [r"\bсвекров"],
    "тёща":           [r"\bтеща", r"\bтещ"],
    "сестра":         [r"\bсестр"],
    "брат":           [r"\bбрат"],
    "сын":            [r"\bсын"],
    "дочь":           [r"\bдоч", r"\bдочер"],
    "ребёнок/дети":   [r"\bребен", r"\bдет(и|ей|ям|ьми|ях)\b", r"\bдочк", r"\bсыноч"],
    "начальник/работа": [r"\bначальн", r"\bруковод", r"\bколлег", r"\bна работе"],
    "подруга/друг":   [r"\bподруг", r"\bдруг\b", r"\bдрузья"],
    "невестка/сноха": [r"\bневестк", r"\bснох", r"\bзолов"],
}

YARLYKI = {
    "нарцисс":   [r"нарцис"],
    "абьюзер":   [r"абьюз", r"абъюз"],
    "токсичный": [r"токсич"],
    "психопат":  [r"психопат", r"социопат"],
    "газлайтинг":[r"газлайт"],
    "манипулятор":[r"манипул"],
    "тиран/деспот":[r"тиран", r"деспот", r"самодур"],
}

# Сигнал по углам ЦА (маркеры — из анализа v1.1). Совпадение = хотя бы один маркер.
UGLY = {
    "С1 уйти нельзя":        [r"уйти не могу", r"не могу уйти", r"некуда идти", r"невозможно уйти",
                              r"живем вместе", r"общий ребенок", r"ради детей", r"деться некуда"],
    "С2 назначенный ребёнок":[r"с меня спрашива", r"должна всем", r"должен всем", r"тяну", r"тащу семью",
                              r"золушк", r"черная овца", r"наследств"],
    "С3 выгоревший дающий":  [r"всем помога", r"не могу отказ", r"удобн", r"спасат", r"выгор",
                              r"мать тереза", r"обесточен", r"на себя нет"],
    "С4 мужчина/вина за семью":[r"я отец", r"как отец", r"ушел из семьи", r"алимент", r"платит", r"плачу",
                              r"я мужчина", r"как мужик"],
    "С5 не могу отцепиться":  [r"не могу отпустить", r"все равно думаю", r"слежу за ним", r"смотрю его",
                              r"откат", r"сорвал", r"зависим", r"тянет к нему"],
}

BOLI = {
    "вина":    [r"\bвин(а|у|ы|е|ой)\b", r"винова", r"виню себя", r"чувство вины"],
    "стыд":    [r"\bстыд", r"стыдно"],
    "страх":   [r"\bстрах", r"боюсь", r"страшно"],
    "обида":   [r"\bобид"],
    "тревога": [r"тревог", r"паник"],
    "усталость/выгорание":[r"устал", r"вымота", r"выгор", r"нет сил"],
    "ненависть/злость":[r"ненавиж", r"бесит", r"злюсь", r"ярост"],
    "одиночество":[r"одинок", r"одна", r"никому не нужн"],
    "спасибо/узнавание":[r"спасибо", r"это про меня", r"как про меня", r"прям я", r"в точку", r"актуальн"],
}

STOP = set("""и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее
мне было вот от меня еще нет о из ем ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас
нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам
чтоб без будто чего раз тоже себе под будет ж кто этот того потому этого какой совсем ним здесь этом один почти
мой тем чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой хоть после над больше тот
через эти нас про всего них какая много разве три эту моя впрочем хорошо свою этой перед иногда лучше чуть том
нельзя такой им более всегда конечно всю между это её очень так эх ой да нее также именно просто когда очень
свой люди человек жизнь""".split())


def load(paths):
    comments = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    c = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if c.get("text"):
                    comments.append(c)
    return comments


def count_group(comments, groups):
    """Сколько комментариев содержат хотя бы один маркер группы."""
    res = Counter()
    compiled = {k: [re.compile(p) for p in pats] for k, pats in groups.items()}
    for c in comments:
        t = norm(c["text"])
        for name, pats in compiled.items():
            if any(p.search(t) for p in pats):
                res[name] += 1
    return res


def bar(n, total, width=28):
    fill = int(round(width * n / total)) if total else 0
    return "█" * fill + "·" * (width - fill)


def block(title, counter, total):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)
    for name, n in counter.most_common():
        print("  %-26s %6d  %5.1f%%  %s" % (name, n, 100 * n / total, bar(n, total)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = args if args else sorted(glob.glob(os.path.join(DEFAULT_DIR, "*.jsonl")))
    if not paths:
        sys.exit("Нет файлов .jsonl. Сначала собери комментарии: skripty/yt_comments.py")

    comments = load(paths)
    total = len(comments)
    print("Файлов: %d | комментариев: %d" % (len(paths), total))

    # Топ по лайкам — самые «зашедшие» формулировки аудитории.
    top = sorted(comments, key=lambda c: c.get("likes", 0), reverse=True)[:30]
    print("\n" + "=" * 64)
    print("ТОП-30 ПО ЛАЙКАМ (язык аудитории, самое отзывающееся)")
    print("=" * 64)
    for c in top:
        txt = re.sub(r"\s+", " ", c["text"]).strip()
        print("  [%5d] %s" % (c.get("likes", 0), txt[:150]))

    block("ФИГУРЫ: кого называют (упоминания в комментариях)", count_group(comments, FIGURY), total)
    block("ЯРЛЫКИ", count_group(comments, YARLYKI), total)
    block("СИГНАЛ ПО УГЛАМ ЦА (это вовлечённость, НЕ доли аудитории)", count_group(comments, UGLY), total)
    block("БОЛИ / ЭМОЦИИ", count_group(comments, BOLI), total)

    # Топ биграммы содержательных слов.
    bigrams = Counter()
    for c in comments:
        ws = [w for w in words(c["text"]) if w not in STOP and len(w) > 2]
        for a, b in zip(ws, ws[1:]):
            bigrams[a + " " + b] += 1
    print("\n" + "=" * 64)
    print("ТОП-25 БИГРАММ (частые связки слов)")
    print("=" * 64)
    for bg, n in bigrams.most_common(25):
        print("  %5d  %s" % (n, bg))


if __name__ == "__main__":
    main()
