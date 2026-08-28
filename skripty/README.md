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

- `bot_probe.py` — кому бот может написать первым: прогоняет список Telegram ID
  через Bot API (`sendChatAction`, без видимых сообщений) и по каждому даёт
  вердикт — reachable / no_access (нет разрешения писать) / blocked. Нужен для
  аудита людей из мини-аппа, которые в чат бота не писали. Только stdlib; токен —
  `TG_BOT_TOKEN`. Вход — файл с ID по строке или CSV с колонкой `userId`.
  `TG_BOT_TOKEN=... python3 skripty/bot_probe.py ids.txt [--out otchet.csv]`

- `sait.js` — открыть сайт **реальным браузером** (Chromium) и вытащить сырьё:
  читаемый текст в порядке чтения, структуру (заголовки h1–h4, кнопки/CTA, формы,
  цены), ссылки и скриншот. В отличие от WebFetch рендерит JS и видит оформление —
  Tilda/Taplink/SPA открываются как у человека. Единственный скрипт на **Node**
  (не Python). Команда — `/sait`.
  - Настройка окружения (разово в свежей сессии): `bash skripty/sait_setup.sh` —
    ставит `playwright-core` (Chromium уже в образе облака), в облаке импортирует
    CA прокси в NSS.
  - `node skripty/sait.js <url> --out analitika/saity/NN-slug.md [--full]`
  - Облачный инструмент: сайты из облака грузятся нормально. Закрытые за логином
    соцсети и капча-стены не обходит — это браузер, а не антибот-скрейпер.

`sheets_sync.py` и `ca_sync.py` — **единственные Python-скрипты с внешними
зависимостями** (Google Sheets API нельзя вызвать без библиотеки), ставятся из
`skripty/requirements-sheets.txt`. Оба используют один ключ сервис-аккаунта.
