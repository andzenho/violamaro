#!/usr/bin/env python3
"""plan.py — что по контент-плану горит прямо сейчас.

Отвечает на единственный вопрос продюсера: «что делать сегодня». Читает
`kontent/kp/`, разбирает даты, темы и статусы и делит всё на три кучи:
просрочено, сегодня, ближайшие дни. Ничего не пишет и не меняет.

Только стандартная библиотека, работает мгновенно и без модели — поэтому
с него начинается любая сессия по контенту, не тратя ни токена на разведку.

    python3 skripty/plan.py              # просрочено + сегодня + 7 дней вперёд
    python3 skripty/plan.py --dney 14    # другое окно вперёд
    python3 skripty/plan.py --vse        # вообще всё, включая опубликованное
"""

import datetime as dt
import re
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
KP = KOREN / "kontent" / "kp"
DATA_V_IMENI = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")

# Статусы по возрастанию готовности. «опубликовано» — известная опечатка
# в одном файле, приводим к общему виду при чтении, чтобы отчёт не двоился.
GOTOVNOST = {"идея": 0, "план": 1, "написан": 2, "опубликован": 3}
SINONIMY = {"опубликовано": "опубликован"}


def pole(tekst: str, imya: str) -> str:
    m = re.search(rf"^{imya}:\s*(.+)$", tekst, re.MULTILINE)
    return m.group(1).strip() if m else ""


def sobrat() -> list[dict]:
    posty = []
    if not KP.is_dir():
        return posty
    for papka in sorted(KP.iterdir()):
        if not papka.is_dir():
            continue
        tab = papka / "_tab.txt"
        vkladka = tab.read_text(encoding="utf-8").strip().split("\n")[0] if tab.is_file() else papka.name
        for f in sorted(papka.glob("*.md")):
            m = DATA_V_IMENI.match(f.name)
            if not m:
                continue
            t = f.read_text(encoding="utf-8")
            st = pole(t, "статус").lower()
            posty.append({
                "data": dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))),
                "vkladka": vkladka,
                "put": f,
                "format": pole(t, "формат") or "—",
                "tema": pole(t, "тема") or "(темы нет)",
                "status": SINONIMY.get(st, st) or "(статуса нет)",
                "ssylka": bool(pole(t, "ссылка")),
            })
    return posty


def pechat(zagolovok: str, gruppa: list[dict], predel: int = 0) -> None:
    """Печатает группу. predel=0 — без ограничения; иначе первые N и счётчик."""
    if not gruppa:
        return
    ryady = sorted(gruppa, key=lambda x: (x["data"], x["vkladka"]))
    print(f"\n{zagolovok}  ({len(ryady)})")
    vidno = ryady[:predel] if predel else ryady
    for p in vidno:
        tema = p["tema"]
        if len(tema) > 70:
            tema = tema[:69] + "…"
        put = str(p["put"]).replace(str(KOREN) + "/", "")
        print(f"  {p['data']:%d.%m} {p['status']:<11} {tema}")
        print(f"        {put}")
    if predel and len(ryady) > predel:
        print(f"  …и ещё {len(ryady) - predel}. Весь список: --vse")


def main(argv: list[str]) -> int:
    dney = 7
    if "--dney" in argv:
        i = argv.index("--dney")
        if i + 1 < len(argv):
            dney = int(argv[i + 1])
    vse = "--vse" in argv

    segodnya = dt.date.today()
    posty = sobrat()
    if not posty:
        print("В kontent/kp/ постов не найдено.")
        return 0

    nedodelano = [p for p in posty if GOTOVNOST.get(p["status"], 0) < 3]
    prosrocheno = [p for p in nedodelano if p["data"] < segodnya]
    na_segodnya = [p for p in nedodelano if p["data"] == segodnya]
    vperedi = [p for p in nedodelano
               if segodnya < p["data"] <= segodnya + dt.timedelta(days=dney)]

    print(f"Сегодня {segodnya:%d.%m.%Y}. В плане {len(posty)} постов, "
          f"недоделанных {len(nedodelano)}.")

    pechat("ПРОСРОЧЕНО — дата прошла, пост не опубликован:", prosrocheno, 0 if vse else 6)
    pechat("СЕГОДНЯ:", na_segodnya)
    pechat(f"БЛИЖАЙШИЕ {dney} ДНЕЙ:", vperedi, 0 if vse else 8)

    if vse:
        pechat("ОПУБЛИКОВАНО:", [p for p in posty if GOTOVNOST.get(p["status"], 0) == 3])

    bez_ssylki = [p for p in posty if p["status"] == "опубликован" and not p["ssylka"]]
    if bez_ssylki:
        hvost = ":" if vse else " (список: --vse)"
        print(f"\n⚠️  Опубликовано без поля «ссылка:» — {len(bez_ssylki)} шт., "
              f"уточнить у продюсера и дописать{hvost}")
        if vse:
            for p in bez_ssylki:
                print(f"  {p['data']:%d.%m}  {str(p['put']).replace(str(KOREN) + '/', '')}")

    if not (prosrocheno or na_segodnya or vperedi):
        print("\nНа ближайшие дни всё закрыто.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
