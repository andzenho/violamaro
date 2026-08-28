#!/bin/sh
# Звуковой сигнал в конце ответа Клода. Вызывается Stop-хуком (.claude/settings.json).
#
# Задача: дать понять на слух, что Клод додумал задачу и ждёт тебя, — когда
# терминал свёрнут. Ничего не печатает: хук пишет в контекст сессии, мусор там не нужен.
#
# Аргумент (необязательно): gotovo — ответ готов (по умолчанию), vopros — Клод
# ждёт ответа или разрешения.
#
# Проверить руками: sh skripty/zvuk.sh

signal=${1:-gotovo}

if [ "$signal" = "vopros" ]; then
    mac_zvuk=/System/Library/Sounds/Ping.aiff
    lin_zvuk=/usr/share/sounds/freedesktop/stereo/message.oga
else
    mac_zvuk=/System/Library/Sounds/Glass.aiff
    lin_zvuk=/usr/share/sounds/freedesktop/stereo/complete.oga
fi

# macOS
if command -v afplay >/dev/null 2>&1; then
    afplay "$mac_zvuk" >/dev/null 2>&1 && exit 0
fi

# Linux: PulseAudio/PipeWire, потом ALSA
if command -v paplay >/dev/null 2>&1 && [ -f "$lin_zvuk" ]; then
    paplay "$lin_zvuk" >/dev/null 2>&1 && exit 0
fi
if command -v aplay >/dev/null 2>&1 && [ -f /usr/share/sounds/alsa/Front_Center.wav ]; then
    aplay -q /usr/share/sounds/alsa/Front_Center.wav >/dev/null 2>&1 && exit 0
fi

# Windows из WSL
if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -c '[console]::beep(880,180)' >/dev/null 2>&1 && exit 0
fi

# Ничего не нашлось — звонок терминала (BEL) в /dev/tty, а не в stdout хука
{ printf '\a' > /dev/tty; } 2>/dev/null || printf '\a' >&2
exit 0
