#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Что реально вышло в Telegram-канале — и сверка с контент-планом.

Читает публичное веб-зеркало канала (https://t.me/s/<канал>). Ни бота, ни токенов,
ни постоянно работающего процесса не нужно: обычный HTTP-запрос.

Ограничение: работает только с публичными каналами. Для закрытых
(Кабинет предзаписи, старый канал) — по-прежнему HTML-экспорт, skripty/tg_comments.py.

Использование:
    python3 skripty/tg_kanal.py                 # сверка КП с каналом, сухой прогон
    python3 skripty/tg_kanal.py --apply         # проставить статус и ссылку в файлы КП
    python3 skripty/tg_kanal.py --list          # просто показать последние посты
    python3 skripty/tg_kanal.py --limit 200     # заглянуть глубже (по 20 постов за запрос)
    python3 skripty/tg_kanal.py --kp "КП Ютуб"  # сверить другую папку КП
"""

import argparse
import html
import os
import re
import sys
import urllib.request

KANAL = "violamaro1"
KP_PAPKA = "КП Телеграм Основа"
KORNI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skachat(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; violamaro-kp/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def ochistit(kusok):
    """HTML одного поста → плоский текст."""
    kusok = re.sub(r"<br\s*/?>", "\n", kusok)
    kusok = re.sub(r"</p>|</div>", "\n", kusok)
    kusok = re.sub(r"<[^>]+>", "", kusok)
    kusok = html.unescape(kusok)
    return re.sub(r"\n{3,}", "\n\n", kusok).strip()


def razobrat(stranica, kanal):
    """HTML ленты → список постов, старые первыми."""
    posty = []
    for blok in stranica.split('class="tgme_widget_message_wrap')[1:]:
        m = re.search(r'data-post="%s/(\d+)"' % re.escape(kanal), blok)
        if not m:
            continue
        nomer = int(m.group(1))
        d = re.search(r'<time datetime="([^"]+)"', blok)
        t = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>\s*(?:<div class="tgme_widget_message_footer|<div class="tgme_widget_message_bubble_tail|$)',
            blok, re.S)
        v = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', blok)
        sluzhebnoe = bool(re.search(
            r"^(Виол\w* Маро )?(pinned|Live stream|Channel (photo|name|created)|joined)",
            ochistit(t.group(1)) if t else "")) or 'class="service_message"' in blok
        posty.append({
            "sluzhebnoe": sluzhebnoe,
            "id": nomer,
            "data": (d.group(1) if d else "")[:10],
            "vremya": (d.group(1) if d else "")[11:16],
            "text": ochistit(t.group(1)) if t else "",
            "media": "tgme_widget_message_photo" in blok or "tgme_widget_message_video" in blok,
            "prosmotry": v.group(1) if v else "",
            "ssylka": "https://t.me/%s/%d" % (kanal, nomer),
        })
    posty.sort(key=lambda p: p["id"])
    return posty


def sobrat(kanal, limit):
    """Листает ленту вверх, пока не наберётся limit постов."""
    vse = {}
    before = None
    while len(vse) < limit:
        url = "https://t.me/s/%s" % kanal + ("?before=%d" % before if before else "")
        try:
            posty = razobrat(skachat(url), kanal)
        except Exception as e:
            print("Не удалось прочитать %s: %s" % (url, e), file=sys.stderr)
            break
        novye = [p for p in posty if p["id"] not in vse]
        if not novye:
            break
        for p in novye:
            vse[p["id"]] = p
        before = min(p["id"] for p in posty)
        if before <= 1:
            break
    return sorted(vse.values(), key=lambda p: p["id"])


def klyuch(text, dlina=70):
    """Нормализованный отпечаток текста для сопоставления."""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^а-яёa-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()[:dlina]


def chitat_kp(papka):
    """Файлы КП → список записей с шапкой и текстом."""
    put = os.path.join(KORNI, "kontent", "kp", papka)
    if not os.path.isdir(put):
        print("Нет папки %s" % put, file=sys.stderr)
        return []
    zapisi = []
    for imya in sorted(os.listdir(put)):
        if not imya.endswith(".md") or imya.startswith("_") or imya == "README.md":
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", imya)
        if not m:
            continue
        syroy = open(os.path.join(put, imya), encoding="utf-8").read()
        chasti = syroy.split("\n---\n", 1)
        shapka = chasti[0]
        text = chasti[1].strip() if len(chasti) > 1 else ""
        st = re.search(r"^статус:\s*(.+)$", shapka, re.M)
        ss = re.search(r"^ссылка:\s*(.+)$", shapka, re.M)
        zapisi.append({
            "fayl": imya,
            "put": os.path.join(put, imya),
            "data": m.group(1),
            "status": st.group(1).strip() if st else "",
            "ssylka": ss.group(1).strip() if ss else "",
            "text": text,
        })
    return zapisi


def pokazat_spisok(posty):
    print("\nПОСЛЕДНИЕ ПОСТЫ В КАНАЛЕ (%d)\n" % len(posty) + "-" * 78)
    for p in reversed(posty):
        if p["sluzhebnoe"]:
            continue
        pervaya = (p["text"].split("\n")[0] or "[без текста]")[:58]
        znachok = "🖼" if p["media"] else "  "
        print("%s %s %s  %s  %-58s  %s" % (
            znachok, p["data"], p["vremya"], p["ssylka"].split("/")[-1].rjust(5), pervaya, p["prosmotry"]))


def svesti(posty, zapisi, papka, primenit):
    po_klyuchu = {}
    for p in posty:
        if p["sluzhebnoe"]:
            continue
        k = klyuch(p["text"])
        if k:
            po_klyuchu.setdefault(k, p)

    nashli, propali, lishnie = [], [], []
    sopostavlennye = set()
    for z in zapisi:
        if not z["text"]:
            continue
        k = klyuch(z["text"])
        p = po_klyuchu.get(k)
        if p is None:
            for kk, pp in po_klyuchu.items():
                if k and (kk.startswith(k[:40]) or k.startswith(kk[:40])):
                    p = pp
                    break
        if p:
            sopostavlennye.add(p["id"])
            nashli.append((z, p))
        elif z["status"] in ("написан", "опубликован"):
            propali.append(z)

    daty_kp = set(z["data"] for z in zapisi)
    for p in posty:
        if p["id"] not in sopostavlennye and p["text"] and not p["sluzhebnoe"] and p["data"] in daty_kp:
            lishnie.append(p)

    print("\nСВЕРКА «%s» С КАНАЛОМ\n" % papka + "=" * 78)

    ne_tot_status = [(z, p) for z, p in nashli if z["status"] != "опубликован"]
    net_ssylki = [(z, p) for z, p in nashli if z["status"] == "опубликован" and z["ssylka"] != p["ssylka"]]
    nuzhna_pravka = ne_tot_status + net_ssylki

    if ne_tot_status:
        print("\n⚠ ВЫШЛИ, НО СТАТУС В КП ДРУГОЙ (%d) — это и есть настоящие расхождения:" % len(ne_tot_status))
        for z, p in ne_tot_status:
            print("   %s   «%s» → опубликован   %s" % (z["fayl"], z["status"] or "нет", p["ssylka"]))
            if z["data"] != p["data"]:
                print("      ⚠ дата в КП %s, в канале %s" % (z["data"], p["data"]))

    if net_ssylki:
        print("\n·  Статус верный, не хватает только ссылки (%d):" % len(net_ssylki))
        for z, p in net_ssylki:
            print("   %s   %s" % (z["fayl"], p["ssylka"]))

    sovpali = len(nashli) - len(nuzhna_pravka)
    if sovpali:
        print("\n✅ ОТМЕЧЕНЫ ВЕРНО И СО ССЫЛКОЙ: %d" % sovpali)

    if propali:
        print("\n⚠ ЧИСЛЯТСЯ ГОТОВЫМИ, НО В КАНАЛЕ НЕ НАЙДЕНЫ (%d):" % len(propali))
        for z in propali:
            print("   %s   статус «%s»" % (z["fayl"], z["status"]))
        print("   (могли выйти раньше глубины просмотра — попробуйте --limit больше)")

    if lishnie:
        print("\n⚠ ЕСТЬ В КАНАЛЕ, НЕТ В КП (%d):" % len(lishnie))
        for p in lishnie:
            print("   %s %s  %s  %s" % (p["data"], p["vremya"], p["ssylka"], (p["text"].split("\n")[0])[:50]))

    if not primenit:
        if nuzhna_pravka:
            print("\nСухой прогон. Записать статусы и ссылки: --apply")
        return

    for z, p in nuzhna_pravka:
        syroy = open(z["put"], encoding="utf-8").read()
        chasti = syroy.split("\n---\n", 1)
        shapka, ostatok = chasti[0], ("\n---\n" + chasti[1] if len(chasti) > 1 else "")
        if re.search(r"^статус:", shapka, re.M):
            shapka = re.sub(r"^статус:.*$", "статус: опубликован", shapka, count=1, flags=re.M)
        else:
            shapka += "\nстатус: опубликован"
        if re.search(r"^ссылка:", shapka, re.M):
            shapka = re.sub(r"^ссылка:.*$", "ссылка: " + p["ssylka"], shapka, count=1, flags=re.M)
        else:
            shapka += "\nссылка: " + p["ssylka"]
        open(z["put"], "w", encoding="utf-8").write(shapka + ostatok)
        print("   записано: %s" % z["fayl"])
    print("\nГотово: обновлено файлов — %d" % len(nuzhna_pravka))


def main():
    ap = argparse.ArgumentParser(description="Что вышло в TG-канале и как это бьётся с контент-планом")
    ap.add_argument("--channel", default=KANAL, help="публичный канал без @ (по умолчанию %s)" % KANAL)
    ap.add_argument("--kp", default=KP_PAPKA, help="папка контент-плана для сверки")
    ap.add_argument("--limit", type=int, default=40, help="сколько постов забрать (по 20 за запрос)")
    ap.add_argument("--list", action="store_true", help="только показать посты, без сверки")
    ap.add_argument("--apply", action="store_true", help="записать статусы и ссылки в файлы КП")
    a = ap.parse_args()

    posty = sobrat(a.channel, a.limit)
    if not posty:
        print("Ничего не прочитано. Канал закрытый или недоступен.", file=sys.stderr)
        return 1
    pokazat_spisok(posty)
    if not a.list:
        svesti(posty, chitat_kp(a.kp), a.kp, a.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
