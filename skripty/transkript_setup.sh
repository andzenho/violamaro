#!/usr/bin/env bash
# Разовая настройка окружения для skripty/transkript.py (локальная машина).
# Идемпотентно: можно запускать сколько угодно раз.
#
#   1) ставит yt-dlp, JS-движок deno (нужен YouTube) и ffmpeg
#      (необязателен — только ужимает заливку и нужен для --skorost);
#   2) принимает ключ AssemblyAI и кладёт его в .assemblyai-key (в .gitignore);
#   3) прогоняет самопроверку.
#
# Ключ можно передать аргументом или переменной ASSEMBLYAI_API_KEY:
#   sh skripty/transkript_setup.sh <ключ>

set -u
KOREN="$(cd "$(dirname "$0")/.." && pwd)"
cd "$KOREN"
SBOY=0

echo "== инструменты =="
STAVIT=""
for BIN in ffmpeg yt-dlp; do
  if command -v "$BIN" >/dev/null 2>&1; then
    echo "$BIN — есть"
  else
    STAVIT="$STAVIT $BIN"
  fi
done

# YouTube без JS-движка отдаёт неполные метаданные и часть форматов.
# yt-dlp по умолчанию ищет только deno; node и bun скрипт подставит сам.
if command -v deno >/dev/null 2>&1 || command -v node >/dev/null 2>&1 \
   || command -v bun >/dev/null 2>&1; then
  echo "JS-движок — есть"
else
  STAVIT="$STAVIT deno"
fi

if [ -n "$STAVIT" ]; then
  if command -v brew >/dev/null 2>&1; then
    echo "ставлю:$STAVIT"
    # shellcheck disable=SC2086
    brew install $STAVIT || SBOY=1
  else
    echo "НЕ ХВАТАЕТ:$STAVIT"
    echo "  Homebrew не найден. Поставь его — https://brew.sh — и запусти скрипт заново."
    echo "  Либо поставь пакеты сам любым способом."
    SBOY=1
  fi
fi

echo
echo "== ключ AssemblyAI =="
KLYUCH="${1:-${ASSEMBLYAI_API_KEY:-}}"
if [ -s .assemblyai-key ] && [ -z "$KLYUCH" ]; then
  echo ".assemblyai-key уже на месте"
elif [ -n "$KLYUCH" ]; then
  printf '%s' "$KLYUCH" > .assemblyai-key
  chmod 600 .assemblyai-key
  echo "ключ записан в .assemblyai-key (файл в .gitignore, в репозиторий не уедет)"
else
  echo "ключа нет. Возьми его на https://www.assemblyai.com/app/api-keys и запусти:"
  echo "  sh skripty/transkript_setup.sh <ключ>"
  SBOY=1
fi

echo
echo "== самопроверка =="
if command -v ffmpeg >/dev/null 2>&1; then
  PROBA="$(mktemp -d)/proba.m4a"
  ffmpeg -y -hide_banner -loglevel error -f lavfi -i "sine=frequency=220:duration=8" \
         -c:a aac "$PROBA" 2>/dev/null
  python3 skripty/transkript.py "$PROBA" --suho --bez-razbora || SBOY=1
  rm -rf "$(dirname "$PROBA")"
else
  echo "пропущена — нет ffmpeg (не блокирует: файлы уйдут как есть)"
fi

echo
if [ "$SBOY" -eq 0 ]; then
  echo "Готово. Дальше просто скажи Клоду: /transkript <ссылка на видео>"
else
  echo "Настройка не завершена — смотри строки выше."
  exit 1
fi
