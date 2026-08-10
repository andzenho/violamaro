# skripty/

Служебные скрипты. По умолчанию — только стандартная библиотека Python 3.

- `proverka.py` — проверка готового текста от лица Виолы перед отправкой.
  `python3 skripty/proverka.py путь/к/тексту.txt`
- `razbor.py` — разбор нового транскрипта: что нового относительно базы.
  `python3 skripty/razbor.py korpus/новый.txt`
- `sheets_sync.py` — синхронизация контент-плана из `kontent/kp/` в Google-таблицу
  (репозиторий → таблица, только колонки «Тема / идея» и «Текст поста»).
  **Единственный скрипт с внешними зависимостями** (Google Sheets API нельзя
  вызвать без библиотеки). Установка и настройка — `kontent/kp/README.md`.
  `python3 skripty/sheets_sync.py --list-tabs | (без флага) | --apply`
