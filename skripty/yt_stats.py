#!/usr/bin/env python3
"""Карта внимания канала: title/views/likes/comments по всем видео.
Не тянет комментарии, только statistics — дёшево по квоте. Показывает, где
концентрируется внимание аудитории (= косвенный размер рынка под тему/продукт).

  export YOUTUBE_API_KEY=...
  python3 skripty/yt_stats.py [out.json]   # по умолчанию печатает топ-40 по просмотрам

Дамп (out.json) — сырьё, кладём в analitika/kommentarii/ (gitignored). Выводы —
в analitika/ или produkt/. Только stdlib."""
import os, json, urllib.request, urllib.parse, sys

KEY = os.environ["YOUTUBE_API_KEY"]
API = "https://www.googleapis.com/youtube/v3/"

def get(path, params):
    params["key"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        return json.load(r)

# 1) uploads playlist
ch = get("channels", {"part": "contentDetails,statistics", "forHandle": "violamaro"})
it = ch["items"][0]
uploads = it["contentDetails"]["relatedPlaylists"]["uploads"]
print("CHANNEL stats:", it["statistics"], file=sys.stderr)

# 2) walk uploads, collect video ids
vids = []
tok = None
while True:
    p = {"part": "snippet,contentDetails", "playlistId": uploads, "maxResults": 50}
    if tok: p["pageToken"] = tok
    r = get("playlistItems", p)
    for x in r["items"]:
        vids.append(x["contentDetails"]["videoId"])
    tok = r.get("nextPageToken")
    if not tok: break
print("total videos:", len(vids), file=sys.stderr)

# 3) statistics + snippet in batches of 50
rows = []
for i in range(0, len(vids), 50):
    chunk = vids[i:i+50]
    r = get("videos", {"part": "snippet,statistics", "id": ",".join(chunk)})
    for x in r["items"]:
        s = x.get("statistics", {})
        rows.append({
            "id": x["id"],
            "title": x["snippet"]["title"],
            "date": x["snippet"]["publishedAt"][:10],
            "views": int(s.get("viewCount", 0)),
            "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0)),
        })

rows.sort(key=lambda r: r["views"], reverse=True)
with open(sys.argv[1] if len(sys.argv) > 1 else "yt_stats.json", "w") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("saved", len(rows), "rows", file=sys.stderr)
# quick top
for r in rows[:40]:
    print(f'{r["views"]:>9} v {r["comments"]:>6} c  {r["date"]}  {r["title"][:80]}')
