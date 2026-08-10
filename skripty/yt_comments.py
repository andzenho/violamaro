#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt_comments.py — выгрузка комментариев с YouTube через официальный
YouTube Data API v3 (не скрейпинг страницы, поэтому работает и из облака).

Комментарии — сырьё аудитории для анализа ЦА (язык, боли, роли, фразы).
Складываются в analitika/kommentarii/ (НЕ в korpus/ — это не речь Виолы).

Ключ API: переменная окружения YOUTUBE_API_KEY.
  Как получить: Google Cloud → тот же проект → включить «YouTube Data API v3»
  → «Создать учётные данные» → API-ключ. Квота 10 000 ед/день (хватает с запасом:
  один запрос commentThreads = 1 ед. и до 100 комментариев).

Запуск:
  # все комментарии одного видео или Shorts:
  python3 skripty/yt_comments.py "https://www.youtube.com/watch?v=XXXX"
  python3 skripty/yt_comments.py "https://youtube.com/shorts/XXXX"
  python3 skripty/yt_comments.py XXXX            # просто ID

  # все видео канала (перечислит загрузки и пройдётся по ним):
  python3 skripty/yt_comments.py --channel "https://www.youtube.com/@handle"
  python3 skripty/yt_comments.py --channel @handle [--max-videos 50]

Флаги:
  --order time|relevance   порядок комментов (по умолчанию time)
  --out DIR                куда класть (по умолчанию analitika/kommentarii)
  --no-replies             не тянуть ответы на комментарии

Только стандартная библиотека.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3"
KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DEFAULT = os.path.join(KOREN, "analitika", "kommentarii")


def api_key():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not k:
        sys.exit(
            "Нет ключа. Задай переменную окружения YOUTUBE_API_KEY.\n"
            "Google Cloud → включить «YouTube Data API v3» → создать API-ключ."
        )
    return k


def get(path, params):
    """GET к API, с обработкой ошибок и простыми ретраями."""
    params = dict(params)
    params["key"] = api_key()
    url = "%s/%s?%s" % (API, path, urllib.parse.urlencode(params))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            reason = ""
            try:
                reason = json.loads(body)["error"]["errors"][0].get("reason", "")
            except Exception:
                pass
            if e.code == 403 and reason in ("commentsDisabled",):
                return {"_error": "commentsDisabled"}
            if e.code in (403, 400) and reason in ("quotaExceeded", "keyInvalid",
                                                   "accessNotConfigured"):
                sys.exit("API отказал (%s): %s" % (reason, body[:300]))
            if e.code >= 500 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            sys.exit("HTTP %s %s: %s" % (e.code, reason, body[:300]))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            sys.exit("Сеть: %s" % e)
    return {}


# ----------------------------------------------------------------------
# Разбор ссылок
# ----------------------------------------------------------------------

def video_id(s):
    s = s.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = re.search(r"(?:v=|/shorts/|youtu\.be/|/embed/|/live/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else None


def channel_uploads_playlist(spec):
    """Из ссылки/handle канала получить ID плейлиста «загрузки»."""
    spec = spec.strip()
    params = None
    m = re.search(r"/channel/(UC[A-Za-z0-9_-]+)", spec)
    if m:
        params = {"part": "contentDetails,snippet", "id": m.group(1)}
    elif spec.startswith("UC") and re.fullmatch(r"UC[A-Za-z0-9_-]+", spec):
        params = {"part": "contentDetails,snippet", "id": spec}
    else:
        m = re.search(r"@([A-Za-z0-9._-]+)", spec)
        handle = m.group(1) if m else spec.lstrip("@")
        params = {"part": "contentDetails,snippet", "forHandle": handle}
    data = get("channels", params)
    items = data.get("items") or []
    if not items:
        sys.exit("Канал не найден: %s" % spec)
    ch = items[0]
    title = ch["snippet"]["title"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    return uploads, title


def playlist_video_ids(playlist_id, limit):
    ids = []
    token = None
    while True:
        data = get("playlistItems", {
            "part": "contentDetails", "playlistId": playlist_id,
            "maxResults": 50, **({"pageToken": token} if token else {}),
        })
        for it in data.get("items", []):
            ids.append(it["contentDetails"]["videoId"])
            if limit and len(ids) >= limit:
                return ids
        token = data.get("nextPageToken")
        if not token:
            return ids


# ----------------------------------------------------------------------
# Комментарии
# ----------------------------------------------------------------------

def flatten_comment(sn, is_reply=False):
    return {
        "author": sn.get("authorDisplayName", ""),
        "text": sn.get("textOriginal") or sn.get("textDisplay") or "",
        "likes": sn.get("likeCount", 0),
        "published": sn.get("publishedAt", ""),
        "reply": is_reply,
    }


def fetch_comments(vid, order, replies):
    out = []
    token = None
    while True:
        data = get("commentThreads", {
            "part": "snippet,replies", "videoId": vid, "maxResults": 100,
            "order": order, "textFormat": "plainText",
            **({"pageToken": token} if token else {}),
        })
        if data.get("_error") == "commentsDisabled":
            return None
        for th in data.get("items", []):
            top = th["snippet"]["topLevelComment"]["snippet"]
            out.append(flatten_comment(top))
            if replies:
                for rep in (th.get("replies", {}).get("comments") or []):
                    out.append(flatten_comment(rep["snippet"], is_reply=True))
        token = data.get("nextPageToken")
        if not token:
            return out


def save(vid, comments, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    jl = os.path.join(out_dir, "%s.jsonl" % vid)
    tx = os.path.join(out_dir, "%s.txt" % vid)
    with open(jl, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(tx, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(c["text"].replace("\n", " ").strip() + "\n")
    return jl, tx


def do_video(vid, order, replies, out_dir):
    comments = fetch_comments(vid, order, replies)
    if comments is None:
        print("  [%s] комментарии отключены — пропускаю." % vid)
        return 0
    jl, tx = save(vid, comments, out_dir)
    tops = sum(1 for c in comments if not c["reply"])
    print("  [%s] комментариев: %d (верхнего уровня %d) → %s" % (vid, len(comments), tops, tx))
    return len(comments)


def main():
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        return
    order = "time"
    if "--order" in args:
        order = args[args.index("--order") + 1]
    out_dir = OUT_DEFAULT
    if "--out" in args:
        out_dir = args[args.index("--out") + 1]
    replies = "--no-replies" not in args
    max_videos = None
    if "--max-videos" in args:
        max_videos = int(args[args.index("--max-videos") + 1])

    if "--channel" in args:
        spec = args[args.index("--channel") + 1]
        uploads, title = channel_uploads_playlist(spec)
        vids = playlist_video_ids(uploads, max_videos)
        print("Канал «%s»: видео к разбору: %d" % (title, len(vids)))
        total = 0
        for vid in vids:
            total += do_video(vid, order, replies, out_dir)
        print("Итого комментариев: %d. Папка: %s" % (total, out_dir))
        return

    # одиночные видео (можно несколько ссылок подряд)
    positional = [a for a in args if not a.startswith("--")
                  and args[args.index(a) - 1] not in ("--order", "--out", "--max-videos")]
    if not positional:
        sys.exit("Дай ссылку на видео/Shorts или --channel <канал>.")
    total = 0
    for a in positional:
        vid = video_id(a)
        if not vid:
            print("  не распознал ID: %s" % a)
            continue
        total += do_video(vid, order, replies, out_dir)
    print("Итого комментариев: %d. Папка: %s" % (total, out_dir))


if __name__ == "__main__":
    main()
