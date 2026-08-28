#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transkript_test.py — самопроверка skripty/transkript.py без ключа и без сети.

Зачем: живой AssemblyAI дёргать на каждой правке нельзя (деньги и ключ),
а сломать запрос легко — параметры у них меняются. Здесь поднимается
поддельный AssemblyAI, который проверяет тело запроса по документации,
и поддельные yt-dlp/ffmpeg. Прогон идёт в копии дерева во временной
папке, korpus/ репозитория не трогается.

Что закреплено:
  · модель передаётся полем speech_models списком (одиночный speech_model
    объявлен устаревшим и на современное имя модели отвечает 400);
  · язык задан явно (иначе автоопределение уводит с русского);
  · файл корпуса получает шапку-источник и таймкоды;
  · таймкоды пересчитываются обратно, если аудио ускорялось;
  · повторный запуск того же ролика не платит второй раз;
  · необязательный параметр, который модель не приняла, снимается
    и запрос повторяется, а не роняет весь разбор.

Запуск:
    python3 skripty/transkript_test.py
Код возврата 0 — всё сошлось.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8791

PROVERKI = []


def proverit(uslovie, chto):
    PROVERKI.append((bool(uslovie), chto))


# ----------------------------------------------------------------------
# Поддельный AssemblyAI: проверяет запрос так же строго, как настоящий
# ----------------------------------------------------------------------

ZAPROSY = []


class API(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _otvet(self, obj, kod=200):
        b = json.dumps(obj).encode()
        self.send_response(kod)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if self.headers.get("authorization") != "TEST-KEY":
            return self._otvet({"error": "нет ключа"}, 401)
        telo = self.rfile.read(int(self.headers.get("content-length", 0)))
        if self.path.endswith("/upload"):
            return self._otvet({"upload_url": "https://cdn/uploaded"})
        if self.path.endswith("/transcript"):
            t = json.loads(telo)
            ZAPROSY.append(t)
            # так ведёт себя настоящий API
            if "speech_model" in t:
                return self._otvet(
                    {"error": "speech_model is deprecated, use speech_models"}, 400)
            if "word_boost" in t and len(ZAPROSY) == 1:
                return self._otvet(
                    {"error": "word_boost is not supported for this model"}, 400)
            return self._otvet({"id": "TR1", "status": "queued"})
        self._otvet({"error": "нет такого пути"}, 404)

    def do_GET(self):
        if self.path.endswith("/paragraphs"):
            return self._otvet({"paragraphs": [
                {"start": 0, "text": "Первый абзац про эмпатов."},
                {"start": 60000, "text": "Второй абзац, техника называется опора."}]})
        self._otvet({"status": "completed", "id": "TR1", "text": "текст"})


# ----------------------------------------------------------------------
# Поддельные бинарники
# ----------------------------------------------------------------------

YT_DLP = '''#!/usr/bin/env python3
import json, sys, os, re
a = sys.argv[1:]
url = a[-1]
m = re.search(r"(?:v=|/)([A-Za-z0-9_-]{4,})/?$", url)
vid = m.group(1) if m else "ABC123"
if "--dump-single-json" in a:
    print(json.dumps({"id": vid, "title": "Пробуждение эмпата",
                      "upload_date": "20260820", "duration": 120,
                      "webpage_url": url})); sys.exit(0)
o = a[a.index("-o") + 1]
open(os.path.join(os.path.dirname(o), vid + ".webm"), "wb").write(b"x" * 5000)
'''

FFMPEG = '''#!/usr/bin/env python3
import sys
a = sys.argv[1:]
if "-encoders" in a:
    print("A..... libopus  Opus"); sys.exit(0)
open("SLED", "a").write(" ".join(a) + "\\n")
open(a[-1], "wb").write(b"y" * 300000)
'''

FFPROBE = '''#!/bin/sh
echo 120.0
'''


def sobrat_okruzhenie(koren):
    """Копия дерева: скрипт считает корнем папку над собой."""
    os.makedirs(os.path.join(koren, "skripty"))
    os.makedirs(os.path.join(koren, "korpus"))
    for f in ("transkript.py", "slovar-transkripta.json"):
        shutil.copy(os.path.join(KOREN, "skripty", f),
                    os.path.join(koren, "skripty", f))
    binar = os.path.join(koren, "bin")
    os.makedirs(binar)
    for imya, telo in (("yt-dlp", YT_DLP), ("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
        put = os.path.join(binar, imya)
        with open(put, "w", encoding="utf-8") as f:
            f.write(telo.replace("SLED", os.path.join(koren, "ffmpeg.log")))
        os.chmod(put, 0o755)
    return binar


def pusk(koren, binar, *args):
    sreda = dict(os.environ)
    # заглушки идут первыми, дальше — каталог с python3 (без него в
    # заглушках не сработает #!/usr/bin/env python3)
    sreda["PATH"] = binar + os.pathsep + os.path.dirname(sys.executable)
    sreda["ASSEMBLYAI_API_KEY"] = "TEST-KEY"
    sreda["ASSEMBLYAI_API_URL"] = "http://127.0.0.1:%d" % PORT
    return subprocess.run(
        [sys.executable, os.path.join(koren, "skripty", "transkript.py")] + list(args),
        capture_output=True, text=True, env=sreda)


# ----------------------------------------------------------------------

def main():
    server = HTTPServer(("127.0.0.1", PORT), API)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    vrem = tempfile.mkdtemp(prefix="transkript-test-")
    koren = os.path.join(vrem, "repo")
    binar = sobrat_okruzhenie(koren)
    korpus = os.path.join(koren, "korpus")
    ssylka = "https://www.youtube.com/watch?v=ABC123"

    # --- 1. Обычный прогон
    p = pusk(koren, binar, ssylka, "--bez-razbora")
    proverit(p.returncode == 0, "обычный прогон завершается без ошибки")
    if p.returncode != 0:
        print(p.stdout + p.stderr)

    fayly = [f for f in os.listdir(korpus) if f.endswith(".txt")]
    proverit(len(fayly) == 1, "в korpus/ появился ровно один файл")
    tekst = ""
    if fayly:
        with open(os.path.join(korpus, fayly[0]), encoding="utf-8") as f:
            tekst = f.read()

    proverit(tekst.startswith("Источник: [ВИД]"), "у файла есть шапка-источник")
    proverit(ssylka in tekst, "в шапке стоит ссылка на ролик")
    proverit("[00:00]" in tekst and "[01:00]" in tekst, "абзацы идут с таймкодами")

    # --- 2. Тело запроса: контракт AssemblyAI
    proverit(ZAPROSY, "запрос до AssemblyAI дошёл")
    if ZAPROSY:
        posledniy = ZAPROSY[-1]
        proverit("speech_models" in posledniy,
                 "модель передаётся полем speech_models")
        proverit(isinstance(posledniy.get("speech_models"), list),
                 "speech_models — список")
        proverit("speech_model" not in posledniy,
                 "устаревший speech_model не отправляется")
        proverit(posledniy.get("language_code") == "ru",
                 "язык задан явно (ru)")
        proverit("word_boost" not in posledniy,
                 "отвергнутый word_boost снят, а не отправлен снова")
        proverit(len(ZAPROSY) == 2,
                 "после отказа по word_boost запрос повторён один раз")

    # --- 3. Повторный запуск не платит второй раз
    do = len(ZAPROSY)
    p = pusk(koren, binar, ssylka, "--bez-razbora")
    proverit(len(ZAPROSY) == do, "повторный запуск не шлёт новый запрос")
    proverit("уже расшифровано" in p.stdout, "повторный запуск говорит, почему пропустил")

    # --- 4. Ускорение: таймкоды пересчитываются обратно
    p = pusk(koren, binar, "https://www.youtube.com/watch?v=XYZ789",
             "--skorost", "2", "--bez-razbora")
    novye = [f for f in os.listdir(korpus) if f.endswith(".txt")
             and f not in fayly]
    proverit(len(novye) == 1, "второй ролик лёг отдельным файлом")
    if novye:
        with open(os.path.join(korpus, novye[0]), encoding="utf-8") as f:
            t2 = f.read()
        proverit("[02:00]" in t2,
                 "при ускорении ×2 таймкод 01:00 пересчитан в 02:00")
        proverit("ускорялось ×2" in t2, "шапка предупреждает об ускорении")
    with open(os.path.join(koren, "ffmpeg.log"), encoding="utf-8") as f:
        log = f.read()
    proverit("atempo" in log, "ускорение действительно ушло в ffmpeg")
    proverit(re.search(r"-ac 1 .*-ar 16000", log), "звук сводится в моно 16 кГц")

    # --- 5. Номера в корпусе растут
    nomera = sorted(int(f.split("-")[0]) for f in os.listdir(korpus)
                    if re.match(r"^\d+-", f))
    proverit(nomera == [1, 2], "номера файлов идут по порядку: %s" % nomera)

    shutil.rmtree(vrem, ignore_errors=True)

    # --- итог
    print()
    upalo = 0
    for ok, chto in PROVERKI:
        print(("  ok   " if ok else "  ПЛОХО") + "  " + chto)
        upalo += 0 if ok else 1
    print()
    if upalo:
        print("не сошлось: %d из %d" % (upalo, len(PROVERKI)))
        return 1
    print("всё сошлось: %d проверок" % len(PROVERKI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
