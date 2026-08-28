#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transkript.py — видео Виолы (YouTube / Instagram / локальный файл) → готовый
транскрипт в korpus/.

Одна команда вместо ручной цепочки «скачать → убрать картинку → ускорить →
сжать → залить в AssemblyAI».

Что делает:
  1. yt-dlp тянет **только аудиодорожку** (видео не качается вообще);
  2. ffmpeg сводит её в моно 16 кГц Opus ~24 кбит/с (≈10 МБ на час);
  3. файл уходит в AssemblyAI (universal-2, ru), словарь имён и терминов
     подставляется из skripty/slovar-transkripta.json;
  4. ответ раскладывается по абзацам с таймкодами и кладётся в korpus/
     с очередным номером и шапкой-источником;
  5. запускается skripty/razbor.py — что нового относительно базы.

Запуск:
    python3 skripty/transkript.py <ссылка|файл>
    python3 skripty/transkript.py --kanal <ссылка на канал/плейлист> [--limit 5]
    python3 skripty/transkript.py <ссылка> --suho      # только план и цена
    python3 skripty/transkript.py <ссылка> --kommit    # сразу закоммитить

Ключ: переменная окружения ASSEMBLYAI_API_KEY либо файл .assemblyai-key
в корне репозитория (он в .gitignore).

Нужны внешние бинарники: yt-dlp, ffmpeg, ffprobe. Python — только stdlib.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KORPUS_DIR = os.path.join(KOREN, "korpus")
SOSTOYANIE_DIR = os.path.join(KOREN, ".transkript")
INDEX_PATH = os.path.join(SOSTOYANIE_DIR, "index.json")
SYROY_DIR = os.path.join(SOSTOYANIE_DIR, "otvety")
SLOVAR_PATH = os.path.join(KOREN, "skripty", "slovar-transkripta.json")

# Базовый адрес API. Для европейского проекта AssemblyAI задай
# ASSEMBLYAI_API_URL=https://api.eu.assemblyai.com/v2
API = os.environ.get("ASSEMBLYAI_API_URL",
                     "https://api.assemblyai.com/v2").rstrip("/")
CENA_ZA_CHAS = 0.15          # universal-2, доллары за час аудио
CENA_DIARIZATSIYA = 0.02     # надбавка за разметку говорящих

# ----------------------------------------------------------------------
# Настройки звука. Правь здесь.
# ----------------------------------------------------------------------

CHASTOTA = 16000     # Гц; ASR всё равно приводит к 16 кГц, выше — только вес
BITREYT = "24k"      # opus voip: на речи неотличимо от исходника для ASR


# ----------------------------------------------------------------------
# Мелочи
# ----------------------------------------------------------------------

def umer(soobshchenie, kod=1):
    print("ОШИБКА: " + soobshchenie, file=sys.stderr)
    sys.exit(kod)


def shag(tekst):
    print("→ " + tekst, flush=True)


def vremya(sekundy):
    sekundy = int(round(sekundy))
    ch, ost = divmod(sekundy, 3600)
    m, s = divmod(ost, 60)
    if ch:
        return "%d:%02d:%02d" % (ch, m, s)
    return "%02d:%02d" % (m, s)


TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def slug(nazvanie, predel=48):
    s = (nazvanie or "").lower()
    s = "".join(TRANSLIT.get(ch, ch) for ch in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > predel:
        s = s[:predel].rsplit("-", 1)[0] or s[:predel]
    return s or "video"


def sleduyushchiy_nomer():
    maks = 0
    if os.path.isdir(KORPUS_DIR):
        for name in os.listdir(KORPUS_DIR):
            m = re.match(r"^(\d+)-", name)
            if m:
                maks = max(maks, int(m.group(1)))
    return "%02d" % (maks + 1)


def chitat_json(path, po_umolchaniyu):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return po_umolchaniyu


def zapisat_json(path, dannye):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dannye, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


# ----------------------------------------------------------------------
# Ключ и внешние инструменты
# ----------------------------------------------------------------------

def klyuch():
    for imya in ("ASSEMBLYAI_API_KEY", "ASSEMBLY_API_KEY", "ASSEMBLYAI_KEY"):
        v = os.environ.get(imya, "").strip()
        if v:
            return v
    fayl = os.path.join(KOREN, ".assemblyai-key")
    if os.path.isfile(fayl):
        with open(fayl, "r", encoding="utf-8") as f:
            v = f.read().strip()
        if v:
            return v
    umer("нет ключа AssemblyAI. Задай ASSEMBLYAI_API_KEY=... "
         "или положи ключ в файл .assemblyai-key в корне репозитория.")


def nuzhen(binar, kak_stavit):
    put = shutil.which(binar)
    if not put:
        umer("не найден %s. Поставь: %s" % (binar, kak_stavit))
    return put


def zapustit(cmd, **kw):
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as e:
        umer("команда упала (%s): %s" % (e.returncode, " ".join(cmd[:4]) + " …"))


# ----------------------------------------------------------------------
# 1. Скачивание аудио
# ----------------------------------------------------------------------

def argumenty_yt_dlp(args):
    dop = []
    if args.cookies:
        dop += ["--cookies", args.cookies]
    if args.brauzer:
        dop += ["--cookies-from-browser", args.brauzer]
    return dop


def svedeniya(url, args):
    """Метаданные ролика без скачивания."""
    nuzhen("yt-dlp", "brew install yt-dlp  (или pipx install yt-dlp)")
    cmd = ["yt-dlp", "--no-playlist", "--dump-single-json", "--skip-download"]
    cmd += argumenty_yt_dlp(args) + [url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        podskazka = ""
        if "instagram" in url.lower():
            podskazka = ("\nInstagram почти всегда требует куки: "
                         "добавь --brauzer chrome (или --cookies cookies.txt).")
        umer("yt-dlp не смог прочитать ссылку.\n" +
             p.stderr.strip()[-800:] + podskazka)
    return json.loads(p.stdout)


def skachat_audio(url, katalog, args):
    shag("качаю аудиодорожку (видеопоток не трогаем)")
    shablon = os.path.join(katalog, "%(id)s.%(ext)s")
    cmd = ["yt-dlp", "--no-playlist", "-f", "bestaudio/best",
           "-o", shablon, "--no-progress", "--quiet"]
    cmd += argumenty_yt_dlp(args) + [url]
    zapustit(cmd)
    fayly = [os.path.join(katalog, n) for n in os.listdir(katalog)]
    fayly = [f for f in fayly if os.path.isfile(f)]
    if not fayly:
        umer("yt-dlp ничего не скачал.")
    return max(fayly, key=os.path.getsize)


# ----------------------------------------------------------------------
# 2. Подготовка звука
# ----------------------------------------------------------------------

def dlitelnost(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def est_libopus():
    p = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                       capture_output=True, text=True)
    return "libopus" in p.stdout


def tsep_atempo(skorost):
    """atempo умеет 0.5–2.0 на старых сборках — режем на множители."""
    zvenya = []
    ost = skorost
    while ost > 2.0:
        zvenya.append(2.0)
        ost /= 2.0
    while ost < 0.5:
        zvenya.append(0.5)
        ost /= 0.5
    zvenya.append(ost)
    return ",".join("atempo=%.4f" % z for z in zvenya)


def podgotovit_audio(istochnik, katalog, skorost):
    opus = est_libopus()
    vyhod = os.path.join(katalog, "audio." + ("ogg" if opus else "m4a"))
    filtr = []
    if abs(skorost - 1.0) > 1e-6:
        filtr = ["-filter:a", tsep_atempo(skorost)]
    kodek = (["-c:a", "libopus", "-b:a", BITREYT, "-application", "voip"]
             if opus else ["-c:a", "aac", "-b:a", "32k"])
    shag("свожу в моно %d Гц %s%s"
         % (CHASTOTA, "opus " + BITREYT if opus else "aac 32k",
            "" if skorost == 1.0 else ", ускорение ×%.2f" % skorost))
    zapustit(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
              "-i", istochnik, "-vn", "-ac", "1", "-ar", str(CHASTOTA)]
             + filtr + kodek + [vyhod])
    return vyhod


# ----------------------------------------------------------------------
# 3. AssemblyAI
# ----------------------------------------------------------------------

def zapros(metod, put, key, telo=None, fayl=None, popytok=4):
    url = put if put.startswith("http") else API + put
    zaderzhka = 2
    for nomer in range(popytok):
        try:
            zagolovki = {"authorization": key}
            dannye = None
            if fayl is not None:
                zagolovki["content-type"] = "application/octet-stream"
                zagolovki["content-length"] = str(os.path.getsize(fayl))
                dannye = open(fayl, "rb")
            elif telo is not None:
                zagolovki["content-type"] = "application/json"
                dannye = json.dumps(telo).encode("utf-8")
            req = urllib.request.Request(url, data=dannye,
                                         headers=zagolovki, method=metod)
            with urllib.request.urlopen(req, timeout=900) as otvet:
                return json.loads(otvet.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            tekst = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and nomer < popytok - 1:
                time.sleep(zaderzhka)
                zaderzhka *= 2
                continue
            raise RuntimeError("AssemblyAI %s: %s" % (e.code, tekst[:600]))
        except urllib.error.URLError as e:
            if nomer < popytok - 1:
                time.sleep(zaderzhka)
                zaderzhka *= 2
                continue
            raise RuntimeError("сеть: %s" % e)
        finally:
            if fayl is not None and dannye is not None:
                dannye.close()
    raise RuntimeError("не достучались до AssemblyAI")


def slovar():
    """Имена и термины Виолы: подсказка ASR + исправление написания."""
    d = chitat_json(SLOVAR_PATH, {})
    return d.get("podskazka", []), d.get("napisanie", [])


def otpravit(audio, key, args):
    shag("загружаю в AssemblyAI (%.1f МБ)" % (os.path.getsize(audio) / 1e6))
    up = zapros("POST", "/upload", key, fayl=audio)["upload_url"]

    podskazka, napisanie = slovar()
    telo = {
        "audio_url": up,
        "speech_model": args.model,
        "language_code": args.yazyk,
        "punctuate": True,
        "format_text": True,
    }
    if args.govoryashchie is not None:
        telo["speaker_labels"] = True
        if args.govoryashchie > 1:
            telo["speakers_expected"] = args.govoryashchie
    if napisanie:
        telo["custom_spelling"] = napisanie
    if podskazka and not args.bez_slovarya:
        telo["word_boost"] = podskazka[:1000]
        telo["boost_param"] = "high"

    shag("ставлю в очередь: %s, язык %s%s"
         % (args.model, args.yazyk,
            ", говорящие размечаются" if args.govoryashchie is not None else ""))
    try:
        zadacha = zapros("POST", "/transcript", key, telo=telo)
    except RuntimeError as e:
        # часть параметров живёт не на всех моделях — снимаем и пробуем ещё раз
        if "word_boost" in str(e) or "boost_param" in str(e):
            telo.pop("word_boost", None)
            telo.pop("boost_param", None)
            print("   (словарь-подсказка не поддержан этой моделью — снял)")
            zadacha = zapros("POST", "/transcript", key, telo=telo)
        else:
            raise
    return zadacha["id"]


def dozhdatsya(zadacha_id, key):
    nachalo = time.time()
    pauza = 3
    while True:
        z = zapros("GET", "/transcript/" + zadacha_id, key)
        status = z.get("status")
        if status == "completed":
            print("   готово за %s" % vremya(time.time() - nachalo))
            return z
        if status == "error":
            umer("AssemblyAI: " + str(z.get("error")))
        print("   %s… %s" % (status, vremya(time.time() - nachalo)),
              end="\r", flush=True)
        time.sleep(pauza)
        pauza = min(pauza + 1, 10)


def abzatsy(zadacha_id, key, gotovoe):
    """Абзацы с таймкодами; если эндпоинт не отдал — режем сами."""
    try:
        p = zapros("GET", "/transcript/%s/paragraphs" % zadacha_id, key)
        if p.get("paragraphs"):
            return [(a["start"], a["text"]) for a in p["paragraphs"]]
    except RuntimeError:
        pass
    if gotovoe.get("utterances"):
        return [(u["start"], "%s: %s" % (u["speaker"], u["text"]))
                for u in gotovoe["utterances"]]
    return [(0, gotovoe.get("text", ""))]


# ----------------------------------------------------------------------
# 4. Сборка файла корпуса
# ----------------------------------------------------------------------

def metka_po_ssylke(url, yavnaya):
    if yavnaya:
        return yavnaya.strip("[]").upper()
    u = (url or "").lower()
    if "instagram" in u:
        return "ИГ"
    if "youtube" in u or "youtu.be" in u:
        return "ВИД"
    return "ФАЙЛ"


def sobrat_tekst(kuski, meta, skorost):
    shapka = ["Источник: [%s] %s" % (meta["metka"], meta["nazvanie"])]
    if meta.get("url"):
        shapka.append("Ссылка: " + meta["url"])
    if meta.get("data"):
        shapka.append("Опубликовано: " + meta["data"])
    shapka.append("Длительность: %s · расшифровка: AssemblyAI %s (%s)%s"
                  % (vremya(meta["sekund"]), meta["model"], meta["yazyk"],
                     "" if skorost == 1.0 else
                     ", аудио ускорялось ×%.2f, таймкоды пересчитаны" % skorost))
    shapka.append("Прямая речь Виолы, сырая ASR-расшифровка, как есть. "
                  "Метка для базы: [%s]." % meta["metka"])
    stroki = ["\n".join(shapka), "---", ""]
    for start_ms, tekst in kuski:
        tekst = (tekst or "").strip()
        if not tekst:
            continue
        stroki.append("[%s] %s" % (vremya(start_ms * skorost / 1000.0), tekst))
        stroki.append("")
    return "\n".join(stroki).rstrip() + "\n"


# ----------------------------------------------------------------------
# 5. Один ролик целиком
# ----------------------------------------------------------------------

def obrabotat(istochnik, args, key):
    lokalnyy = os.path.isfile(istochnik)
    index = chitat_json(INDEX_PATH, {})

    if lokalnyy:
        info = {"id": "file:" + os.path.basename(istochnik),
                "title": os.path.splitext(os.path.basename(istochnik))[0]}
        url = ""
    else:
        info = svedeniya(istochnik, args)
        url = info.get("webpage_url") or istochnik

    vid_id = str(info.get("id") or istochnik)
    if vid_id in index and not args.zanovo:
        print("· уже расшифровано → %s (перезапуск: --zanovo)"
              % index[vid_id].get("fayl"))
        return None

    nazvanie = (info.get("title") or "").strip() or "без названия"
    data = info.get("upload_date") or ""
    if re.match(r"^\d{8}$", data):
        data = "%s-%s-%s" % (data[:4], data[4:6], data[6:8])

    print()
    print("=" * 60)
    print("  " + nazvanie)
    print("=" * 60)

    nuzhen("ffmpeg", "brew install ffmpeg")
    nuzhen("ffprobe", "brew install ffmpeg")

    katalog = tempfile.mkdtemp(prefix="transkript-")
    try:
        syroy = istochnik if lokalnyy else skachat_audio(istochnik, katalog, args)
        ishodnaya_dlina = dlitelnost(syroy)
        audio = podgotovit_audio(syroy, katalog, args.skorost)
        oplachivaemaya = ishodnaya_dlina / args.skorost
        tsena = oplachivaemaya / 3600.0 * (
            CENA_ZA_CHAS + (CENA_DIARIZATSIYA
                            if args.govoryashchie is not None else 0))
        print("   исходник %s → к оплате %s ≈ $%.3f · файл %.1f МБ"
              % (vremya(ishodnaya_dlina), vremya(oplachivaemaya),
                 tsena, os.path.getsize(audio) / 1e6))

        if args.suho:
            print("   (сухой прогон — в AssemblyAI ничего не ушло)")
            return None

        zadacha_id = otpravit(audio, key, args)
        gotovoe = dozhdatsya(zadacha_id, key)
    finally:
        if not args.derzhat_audio:
            shutil.rmtree(katalog, ignore_errors=True)
        else:
            print("   аудио оставлено в " + katalog)

    kuski = abzatsy(zadacha_id, key, gotovoe)
    meta = {"metka": metka_po_ssylke(url, args.metka), "nazvanie": nazvanie,
            "url": url, "data": data, "sekund": ishodnaya_dlina,
            "model": args.model, "yazyk": args.yazyk}
    tekst = sobrat_tekst(kuski, meta, args.skorost)

    imya = "%s-%s.txt" % (args.nomer or sleduyushchiy_nomer(),
                          args.slug or slug(nazvanie))
    put = os.path.join(KORPUS_DIR, imya)
    os.makedirs(KORPUS_DIR, exist_ok=True)
    with open(put, "w", encoding="utf-8") as f:
        f.write(tekst)

    zapisat_json(os.path.join(SYROY_DIR, zadacha_id + ".json"), gotovoe)
    index[vid_id] = {"fayl": os.path.join("korpus", imya), "url": url,
                     "nazvanie": nazvanie, "data": data,
                     "sekund": round(ishodnaya_dlina), "zadacha": zadacha_id,
                     "model": args.model, "skorost": args.skorost,
                     "kogda": time.strftime("%Y-%m-%d %H:%M")}
    zapisat_json(INDEX_PATH, index)

    slov = len(re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", tekst))
    print("   → korpus/%s · %d слов, %d абзацев" % (imya, slov, len(kuski)))
    return put


# ----------------------------------------------------------------------
# 6. Канал: только новые ролики
# ----------------------------------------------------------------------

def spisok_kanala(url, args):
    nuzhen("yt-dlp", "brew install yt-dlp")
    cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--skip-download"]
    if args.limit:
        cmd += ["--playlist-end", str(args.limit)]
    cmd += argumenty_yt_dlp(args) + [url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 and not p.stdout.strip():
        umer("не удалось прочитать канал.\n" + p.stderr.strip()[-800:])
    out = []
    for stroka in p.stdout.splitlines():
        stroka = stroka.strip()
        if not stroka:
            continue
        try:
            zapis = json.loads(stroka)
        except ValueError:
            continue
        if zapis.get("url") or zapis.get("id"):
            out.append(zapis)
    return out


# ----------------------------------------------------------------------

def razbor(put):
    skript = os.path.join(KOREN, "skripty", "razbor.py")
    if not os.path.isfile(skript):
        return
    print()
    subprocess.run([sys.executable, skript, put])


def kommit(fayly):
    if not fayly:
        return
    otn = [os.path.relpath(f, KOREN) for f in fayly]
    zapustit(["git", "-C", KOREN, "add"] + otn +
             [".transkript"], stdout=subprocess.DEVNULL)
    soobshchenie = ("Корпус: транскрипт " +
                    ", ".join(os.path.basename(f) for f in otn) +
                    " (AssemblyAI, автоматическая расшифровка видео)")
    subprocess.run(["git", "-C", KOREN, "commit", "-m", soobshchenie])


def parser():
    p = argparse.ArgumentParser(
        description="Видео Виолы → транскрипт в korpus/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Примеры:\n"
               "  python3 skripty/transkript.py https://youtu.be/XXXX\n"
               "  python3 skripty/transkript.py https://www.instagram.com/reel/XXXX/ --brauzer chrome\n"
               "  python3 skripty/transkript.py --kanal @violamaro --limit 5\n"
               "  python3 skripty/transkript.py zapis.mp4 --govoryashchie 2\n")
    p.add_argument("istochnik", nargs="?", help="ссылка на видео или путь к файлу")
    p.add_argument("--kanal", help="канал/плейлист: взять только новые ролики")
    p.add_argument("--limit", type=int, default=10,
                   help="сколько последних роликов смотреть в канале (10)")
    p.add_argument("--skorost", type=float, default=1.0,
                   help="ускорить аудио перед отправкой (1.0 — не ускорять; "
                        "таймкоды пересчитываются обратно)")
    p.add_argument("--model", default="universal-2",
                   help="модель AssemblyAI (universal-2 — та, что знает русский)")
    p.add_argument("--yazyk", default="ru", help="код языка (ru)")
    p.add_argument("--govoryashchie", type=int, nargs="?", const=0, default=None,
                   metavar="N", help="разметить говорящих (для созвонов и эфиров); "
                                     "можно указать ожидаемое число")
    p.add_argument("--metka", help="метка источника для шапки: ВИД, ИГ, ЭФИР…")
    p.add_argument("--slug", help="имя файла в korpus/ без номера")
    p.add_argument("--nomer", help="номер файла в korpus/ (иначе следующий)")
    p.add_argument("--cookies", help="файл cookies.txt (нужен для Instagram)")
    p.add_argument("--brauzer", help="взять куки из браузера: chrome, safari, firefox")
    p.add_argument("--suho", action="store_true",
                   help="сухой прогон: скачать, посчитать цену, ничего не отправлять")
    p.add_argument("--zanovo", action="store_true",
                   help="расшифровать заново, даже если ролик уже в индексе")
    p.add_argument("--bez-razbora", action="store_true", dest="bez_razbora",
                   help="не запускать razbor.py")
    p.add_argument("--bez-slovarya", action="store_true", dest="bez_slovarya",
                   help="не подсказывать модели имена и термины Виолы")
    p.add_argument("--derzhat-audio", action="store_true", dest="derzhat_audio",
                   help="не удалять подготовленное аудио")
    p.add_argument("--kommit", action="store_true",
                   help="закоммитить добавленные файлы корпуса")
    return p


def main():
    args = parser().parse_args()
    if not args.istochnik and not args.kanal:
        parser().print_help()
        sys.exit(2)
    if args.skorost <= 0:
        umer("--skorost должна быть больше нуля")
    if args.skorost > 1.5:
        print("! ускорение больше ×1.5 заметно роняет точность на русском, "
              "а экономит центы: час аудио стоит $%.2f." % CENA_ZA_CHAS)

    key = "" if args.suho else klyuch()
    sdelano = []

    if args.kanal:
        index = chitat_json(INDEX_PATH, {})
        roliki = spisok_kanala(args.kanal, args)
        novye = [r for r in roliki
                 if str(r.get("id")) not in index or args.zanovo]
        print("в канале просмотрено %d, новых %d" % (len(roliki), len(novye)))
        # yt-dlp отдаёт канал от свежего к старому — разворачиваем,
        # чтобы номера в korpus/ росли по хронологии, как у остальных файлов
        for r in reversed(novye):
            ssylka = r.get("url") or ("https://www.youtube.com/watch?v=" + r["id"])
            try:
                put = obrabotat(ssylka, args, key)
            except RuntimeError as e:
                print("! пропускаю %s: %s" % (ssylka, e), file=sys.stderr)
                continue
            if put:
                sdelano.append(put)
    else:
        try:
            put = obrabotat(args.istochnik, args, key)
        except RuntimeError as e:
            umer(str(e))
        if put:
            sdelano.append(put)

    if not sdelano:
        return
    if not args.bez_razbora:
        for put in sdelano:
            razbor(put)
    if args.kommit:
        kommit(sdelano)
    else:
        print()
        print("Закоммитить: git add %s .transkript && git commit"
              % " ".join(os.path.relpath(f, KOREN) for f in sdelano))


if __name__ == "__main__":
    main()
