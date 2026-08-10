# skripty/

Служебные скрипты. По умолчанию — только стандартная библиотека Python 3.

- `proverka.py` — проверка готового текста от лица Виолы перед отправкой.
  `python3 skripty/proverka.py путь/к/тексту.txt`
- `razbor.py` — разбор нового транскрипта: что нового относительно базы.
  `python3 skripty/razbor.py korpus/новый.txt`
- `sheets_sync.py` — синхронизация контент-плана из `kontent/kp/` в Google-таблицу
  «Рабочее пространство» (репозиторий → таблица, только колонки «Тема / идея» и
  «Текст поста»). Установка и настройка — `kontent/kp/README.md`.
  `python3 skripty/sheets_sync.py --list-tabs | (без флага) | --apply`
- `ca_sync.py` — синхронизация анализа ЦА из `analitika/ca-data.json` в Google-таблицу
  «ЦА и продукты» (репозиторий → таблица, лист = вкладка; форматирование и твои
  доп-колонки не трогает). Настройка — `analitika/README.md`.
  `python3 skripty/ca_sync.py --list-tabs | (без флага) | --apply`

`sheets_sync.py` и `ca_sync.py` — **единственные скрипты с внешними зависимостями**
(Google Sheets API нельзя вызвать без библиотеки), ставятся из
`skripty/requirements-sheets.txt`. Оба используют один ключ сервис-аккаунта.
