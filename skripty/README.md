# skripty/

Служебные скрипты. По умолчанию — только стандартная библиотека Python 3.

- `proverka.py` — проверка готового текста от лица Виолы перед отправкой.
  `python3 skripty/proverka.py путь/к/тексту.txt`
- `razbor.py` — разбор нового транскрипта: что нового относительно базы.
  `python3 skripty/razbor.py korpus/новый.txt`
- `yt_comments.py` — выгрузка комментариев из-под видео/Shorts через YouTube Data
  API v3 (работает из облака, не скрейпинг). Только stdlib; нужен ключ
  `YOUTUBE_API_KEY`. Сырьё кладётся в `analitika/kommentarii/`.
  `python3 skripty/yt_comments.py <ссылка> | --channel <канал>`
- `razbor_kommentov.py` — разбор собранных комментариев для анализа ЦА: топ по
  лайкам, фигуры вины, ярлыки, сигнал по углам С1–С5, боли, биграммы. Только stdlib.
  `python3 skripty/razbor_kommentov.py analitika/kommentarii/<...>/*.jsonl`
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
