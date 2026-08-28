#!/usr/bin/env bash
# Разовая настройка окружения для skripty/sait.js (облако Claude Code).
# Идемпотентно: можно запускать сколько угодно раз.
#
#   1) ставит playwright-core (сам Chromium уже предустановлен в образе);
#   2) в облаке с MITM-прокси — импортирует CA прокси в NSS-хранилище,
#      иначе Chromium не доверяет сертификату и рвёт соединение.
#
# На локальной машине (без прокси) шаг с CA пропускается.

set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "== playwright-core =="
if [ ! -d node_modules/playwright-core ]; then
  npm install playwright-core >/dev/null 2>&1 && echo "playwright-core установлен" || { echo "не удалось поставить playwright-core"; exit 1; }
else
  echo "уже есть"
fi

# CA прокси нужен только когда трафик идёт через MITM-прокси (облако)
CA="${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}"
if [ -n "${HTTPS_PROXY:-}${https_proxy:-}" ] && [ -f "$CA" ]; then
  echo "== доверие CA прокси (NSS) =="
  if ! command -v certutil >/dev/null 2>&1; then
    apt-get update >/dev/null 2>&1
    apt-get install -y libnss3-tools >/dev/null 2>&1 || { echo "не удалось поставить certutil"; exit 1; }
  fi
  NSSDB="$HOME/.pki/nssdb"
  mkdir -p "$NSSDB"
  [ -f "$NSSDB/cert9.db" ] || certutil -d "sql:$NSSDB" -N --empty-password >/dev/null 2>&1
  # уже импортировали?
  if certutil -d "sql:$NSSDB" -L 2>/dev/null | grep -q "ccr-proxy-0"; then
    echo "CA уже в хранилище"
  else
    TMP="$(mktemp -d)"
    ( cd "$TMP" && csplit -z -f cert- -b '%03d.pem' "$CA" '/-----BEGIN CERTIFICATE-----/' '{*}' >/dev/null 2>&1 )
    n=0
    for f in "$TMP"/cert-*.pem; do
      [ -f "$f" ] || continue
      certutil -d "sql:$NSSDB" -A -t "C,," -n "ccr-proxy-$n" -i "$f" >/dev/null 2>&1 && n=$((n+1))
    done
    rm -rf "$TMP"
    echo "импортировано сертификатов: $n"
  fi
else
  echo "== прокси не обнаружен — шаг CA пропущен (локальная машина) =="
fi

echo "Готово. Пример: node skripty/sait.js https://example.com --out korpus/01-example.md"
