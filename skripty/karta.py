#!/usr/bin/env python3
"""karta.py — собрать karta.md: индекс репозитория для ассистента.

Зачем. В Claude Code нет поиска по репозиторию: ассистент видит только то, что
открыл руками. Значит навигация решается индексом, а не поиском. Одна строка на
файл — путь, вес в токенах и суть — стоит пару тысяч токенов на весь
репозиторий и заменяет угадывание, куда лезть.

Откуда берётся описание файла, по порядку:
  1. строка `описание: ...` в первых 15 строках файла (если дописали руками);
  2. первый заголовок `# ...`;
  3. первая непустая строка.
Статус — из строки `статус: ...`, иначе выводится из папки.

Формализма намеренно минимум: два необязательных поля, остальное скрипт достаёт
сам. Раздутая разметка в таких индексах вредит больше, чем помогает.

Свёрнуто, чтобы карта не разрослась: посты контент-плана — одной строкой на
вкладку (навигация по ним — `plan.py`), архив — списком имён без описаний,
скрипты — списком имён (подробности в `skripty/README.md`).

    python3 skripty/karta.py            # пересобрать karta.md
    python3 skripty/karta.py --stdout   # напечатать, ничего не записывая
"""

import re
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent
VYHOD = KOREN / "karta.md"

RASSHIRENIYA = {".md", ".txt", ".srt", ".json", ".html"}
PROPUSK_PAPOK = {".git", "__pycache__", ".venv", "node_modules", "graphify-out"}
PROPUSK_FAYLOV = {"karta.md", "package-lock.json", "_tab.txt"}
SIMVOLOV_NA_TOKEN = 2.5
TYAZHELYY = 10_000  # токенов — дальше только кусками
DATA_V_IMENI = re.compile(r"^\d{4}-\d{2}-\d{2}")

RAZDELY = [
    ("baza", "Источник правды по смыслу: голос и каноны"),
    ("produkt", "Программы, цены, условия"),
    ("analitika", "ЦА, цифры, кастдэвы"),
    ("kontent", "Контент-план и стратегия контента"),
    ("korpus", "Сырьё: транскрипты. ⚠️ Тяжёлое, только кусками"),
    ("docs", "Опубликованное на GitHub Pages"),
]

STATUS_PO_PAPKE = {"arhiv": "архив", "korpus": "сырьё"}


def tokenov(simvolov: int) -> int:
    return int(simvolov / SIMVOLOV_NA_TOKEN)


def probel(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def pole(stroki: list[str], imya: str) -> str:
    for s in stroki[:15]:
        if s.strip().lower().startswith(imya + ":"):
            return s.split(":", 1)[1].strip()
    return ""


def opisanie(put: Path, tekst: str) -> tuple[str, str]:
    if put.suffix not in {".md", ".txt", ".srt"}:
        return "", ""
    stroki = tekst.splitlines()
    opis = pole(stroki, "описание")
    stat = pole(stroki, "статус")
    if not opis:
        for s in stroki:
            if s.startswith("# "):
                opis = s[2:].strip()
                break
    if not opis:
        for s in stroki:
            s = s.strip()
            if s and not s.startswith(("---", "#", "<!--", "|")):
                opis = s
                break
    opis = " ".join(opis.split())
    if len(opis) > 72:
        opis = opis[:71].rstrip(" ,.;:—-") + "…"
    return opis, stat


def vse_fayly() -> list[tuple[Path, int, str, str]]:
    out = []
    for p in sorted(KOREN.rglob("*")):
        otn = p.relative_to(KOREN)
        if any(ch in PROPUSK_PAPOK for ch in otn.parts):
            continue
        if not p.is_file() or p.suffix not in RASSHIRENIYA:
            continue
        if p.name in PROPUSK_FAYLOV:
            continue
        tekst = p.read_text(encoding="utf-8", errors="ignore")
        opis, stat = opisanie(p, tekst)
        koren = otn.parts[0] if len(otn.parts) > 1 else "."
        out.append((otn, tokenov(len(tekst)), opis, stat or STATUS_PO_PAPKE.get(koren, "")))
    return out


def tablica(fayly, obrezat_do: str | None = None) -> list[str]:
    out = ["| Файл | Ток. | Суть |", "|---|---:|---|"]
    for otn, t, opis, stat in sorted(fayly, key=lambda x: str(x[0])):
        imya = str(otn)
        if obrezat_do and imya.startswith(obrezat_do):
            imya = imya[len(obrezat_do):]
        metka = " ⚠️" if t > TYAZHELYY else ""
        sut = opis or "—"
        if stat:
            sut = f"*[{stat}]* {sut}"
        out.append(f"| `{imya}` | {probel(t)}{metka} | {sut} |")
    out.append("")
    return out


def sobrat_kartu() -> str:
    fayly = vse_fayly()
    vsego_t = sum(t for _, t, _, _ in fayly)
    po_razdelam: dict[str, list] = {}
    for f in fayly:
        koren = f[0].parts[0] if len(f[0].parts) > 1 else "."
        po_razdelam.setdefault(koren, []).append(f)

    out = [
        "# Карта репозитория",
        "",
        "<!-- Собирается скриптом: python3 skripty/karta.py",
        "     Руками не править — правки затрутся. Чтобы задать файлу описание",
        "     или статус, добавь в САМ файл строку «описание: …» / «статус: …». -->",
        "",
        "Путь, вес в токенах, суть одной строкой. Читается вместо угадывания, куда лезть.",
        "",
        f"⚠️ — тяжелее {probel(TYAZHELYY)} токенов: целиком не открывать, "
        "только `grep -n` + `Read` с `offset`/`limit`.",
        "Правила по разделам подгружаются сами из `.claude/rules/*.md`.",
        "",
    ]

    # Корень
    koren_f = po_razdelam.get(".", [])
    if koren_f:
        out.append("## Корень")
        out += tablica(koren_f)

    # Обычные разделы
    for klyuch, podpis in RAZDELY:
        gr = po_razdelam.get(klyuch, [])
        if not gr:
            continue
        summa = sum(t for _, t, _, _ in gr)
        out.append(f"## `{klyuch}/` — {len(gr)} файл., {probel(summa)} ток.")
        out.append(f"*{podpis}*")
        out.append("")
        if klyuch == "kontent":
            # посты сворачиваем в строку на вкладку
            prostye = [f for f in gr if not DATA_V_IMENI.match(f[0].name)]
            out += tablica(prostye, obrezat_do="kontent/")
            vkladki: dict[str, list] = {}
            for f in gr:
                if DATA_V_IMENI.match(f[0].name):
                    vkladki.setdefault(f[0].parts[2], []).append(f)
            if vkladki:
                out.append("Посты контент-плана (навигация — `python3 skripty/plan.py`):")
                out.append("")
                out.append("| Вкладка | Постов | Ток. | Имя вкладки в таблице |")
                out.append("|---|---:|---:|---|")
                for papka in sorted(vkladki):
                    posty = vkladki[papka]
                    tab = KOREN / "kontent" / "kp" / papka / "_tab.txt"
                    imya_tab = tab.read_text(encoding="utf-8").strip().splitlines()[0] if tab.is_file() else "—"
                    out.append(
                        f"| `kp/{papka}/` | {len(posty)} | "
                        f"{probel(sum(t for _, t, _, _ in posty))} | {imya_tab} |"
                    )
                out.append("")
        else:
            out += tablica(gr, obrezat_do=f"{klyuch}/")

    # Скрипты — только имена
    skripty = sorted(p.name for p in (KOREN / "skripty").glob("*.py"))
    if skripty:
        out.append("## `skripty/` — служебные скрипты")
        out.append("*Что делает каждый и как запускать — `skripty/README.md`.*")
        out.append("")
        out.append(", ".join(f"`{s}`" for s in skripty))
        out.append("")

    # Правила и команды
    pravila = sorted(p.name for p in (KOREN / ".claude" / "rules").glob("*.md"))
    komandy = sorted(p.stem for p in (KOREN / ".claude" / "commands").glob("*.md"))
    if pravila or komandy:
        out.append("## `.claude/` — настройки ассистента")
        if pravila:
            out.append(f"Правила по папкам (грузятся сами): {', '.join('`' + s + '`' for s in pravila)}")
        if komandy:
            out.append(f"Команды: {', '.join('`/' + s + '`' for s in komandy)}")
        out.append("")

    # Архив — только имена
    arhiv = po_razdelam.get("arhiv", [])
    if arhiv:
        summa = sum(t for _, t, _, _ in arhiv)
        out.append(f"## `arhiv/` — {len(arhiv)} файл., {probel(summa)} ток.")
        out.append("*⚠️ Устаревшее и противоречащее курсу. Открывать только по прямой просьбе.*")
        out.append("")
        for otn, _, _, _ in sorted(arhiv, key=lambda x: str(x[0])):
            out.append(f"- `{'/'.join(otn.parts[1:])}`")
        out.append("")

    out.append("---")
    out.append(
        f"**Всего {len(fayly)} файлов, ~{probel(vsego_t)} токенов.** "
        "Весь репозиторий в один контекст не влезает и не должен."
    )
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    tekst = sobrat_kartu()
    if "--stdout" in argv:
        print(tekst)
        return 0
    VYHOD.write_text(tekst, encoding="utf-8")
    print(f"karta.md пересобрана: {tokenov(len(tekst))} ток.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
