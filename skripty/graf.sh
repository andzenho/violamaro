#!/bin/sh
# graf.sh — обёртка над graphify (граф знаний по репозиторию).
#
# Зачем обёртка: у graphify десяток флагов, и половина ответов зависит от того,
# что именно попало в граф. Что индексируется — задано в .graphifyignore
# (arhiv/, skripty/, docs/ выключены). Здесь зашит бэкенд и путь к графу,
# чтобы никто не собирал граф «по-своему».
#
# ГРАНИЦА ПРИМЕНЕНИЯ. Граф — навигация и аудит, не источник правды.
# Он не заменяет чтение baza/golos-viola.md целиком перед текстом от лица
# Виолы (CLAUDE.md, «Правило воронки текста») и не переносит метки [Д]/[П]/[В].
# Всё, что взято из графа, перед попаданием в текст проверяется по файлу-источнику.
#
# Использование:
#   sh skripty/graf.sh sborka            — собрать граф с нуля (долго, платно)
#   sh skripty/graf.sh obnovit           — дособрать по изменившимся файлам
#   sh skripty/graf.sh vopros "…"        — вопрос к графу
#   sh skripty/graf.sh svyaz "A" "B"     — как связаны два понятия
#   sh skripty/graf.sh uzel "X"          — разбор одного узла
#   sh skripty/graf.sh uzly              — самые связанные узлы (о чём проект на самом деле)
#   sh skripty/graf.sh otchet            — открыть GRAPH_REPORT.md
#   sh skripty/graf.sh status            — есть ли граф, когда собран, что изменилось после

set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/graphify-out"
GRAPH="$OUT/graph.json"

# Бэкенд извлечения. claude-cli ходит в локальный `claude` по подписке —
# отдельный API-ключ не нужен. Если задан GEMINI_API_KEY, graphify возьмёт
# Gemini: он дешевле и быстрее на объёме korpus/.
if [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${GOOGLE_API_KEY:-}" ]; then
  BACKEND=gemini
else
  BACKEND=claude-cli
fi

need_graphify() {
  if ! command -v graphify >/dev/null 2>&1; then
    echo "graphify не установлен. Поставить: pip install graphifyy" >&2
    exit 1
  fi
}

need_graph() {
  if [ ! -f "$GRAPH" ]; then
    echo "Графа нет. Собрать: sh skripty/graf.sh sborka" >&2
    exit 1
  fi
}

cmd=${1:-status}
[ $# -gt 0 ] && shift

case "$cmd" in
  sborka)
    need_graphify
    echo "Сборка графа, бэкенд: $BACKEND. Это надолго — 130+ файлов, ~220 тыс. слов."
    graphify extract "$ROOT" --backend "$BACKEND" --out "$ROOT" "$@"
    ;;
  obnovit)
    need_graphify
    graphify extract "$ROOT" --backend "$BACKEND" --out "$ROOT" "$@"
    ;;
  vopros)
    need_graphify; need_graph
    [ $# -ge 1 ] || { echo 'Нужен вопрос: sh skripty/graf.sh vopros "…"' >&2; exit 1; }
    q=$1; shift
    graphify query "$q" --graph "$GRAPH" "$@"
    ;;
  svyaz)
    need_graphify; need_graph
    [ $# -ge 2 ] || { echo 'Нужны два узла: sh skripty/graf.sh svyaz "A" "B"' >&2; exit 1; }
    graphify path "$1" "$2" --graph "$GRAPH"
    ;;
  uzel)
    need_graphify; need_graph
    [ $# -ge 1 ] || { echo 'Нужен узел: sh skripty/graf.sh uzel "X"' >&2; exit 1; }
    graphify explain "$1" --graph "$GRAPH"
    ;;
  uzly)
    need_graphify; need_graph
    graphify god-nodes --graph "$GRAPH" --top "${1:-20}"
    ;;
  otchet)
    need_graph
    cat "$OUT/GRAPH_REPORT.md"
    ;;
  status)
    if [ ! -f "$GRAPH" ]; then
      echo "Графа нет. Собрать: sh skripty/graf.sh sborka"
      exit 0
    fi
    echo "Граф: $GRAPH"
    # date -r и find -printf по-разному устроены в GNU и BSD, а работаем и с мака,
    # и из облака. Дату берём питоном — он в проекте есть везде.
    echo "Собран: $(python3 -c "import os,sys,time;print(time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(sys.argv[1]))))" "$GRAPH")"
    echo "Изменилось после сборки:"
    find "$ROOT" -name '*.md' -newer "$GRAPH" \
      -not -path "$ROOT/.git/*" -not -path "$OUT/*" -not -path "$ROOT/arhiv/*" \
      2>/dev/null | sed "s|^$ROOT/|  |" | head -30
    ;;
  *)
    sed -n '2,25p' "$0"
    exit 1
    ;;
esac
