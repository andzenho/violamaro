# skripty/

Служебные скрипты. По умолчанию — только стандартная библиотека Python 3.

- `proverka.py` — проверка готового текста от лица Виолы перед отправкой.
  `python3 skripty/proverka.py путь/к/тексту.txt`
- `razbor.py` — разбор нового транскрипта: что нового относительно базы.
  `python3 skripty/razbor.py korpus/новый.txt`
- `transkript.py` — видео Виолы (YouTube / Instagram / локальный файл) →
  готовый транскрипт в `korpus/`. Одна команда вместо ручной цепочки
  «скачать → убрать картинку → ускорить → сжать → залить в AssemblyAI»:
  `yt-dlp` тянет **только аудиодорожку** (видеопоток не качается вообще),
  `ffmpeg` сводит её в моно 16 кГц Opus 24 кбит/с (≈10 МБ на час),
  файл уходит в AssemblyAI (`universal-2`, `ru`), ответ раскладывается по
  абзацам с таймкодами, ложится в `korpus/NN-slug.txt` с шапкой-источником,
  дальше сам запускается `razbor.py`. Только stdlib; нужны бинарники
  `yt-dlp`, `ffmpeg` и JS-движок для YouTube (`deno`, либо уже стоящий
  `node` — скрипт подставит его сам); ключ — `ASSEMBLYAI_API_KEY` или файл `.assemblyai-key`
  в корне (оба в `.gitignore`). Имена и термины Виолы подсказываются модели
  из `slovar-transkripta.json`. Обработанные ролики помнятся в
  `.transkript/index.json` — повторно не платим. Вызывается и командой
  `/transkript`.
  Разовая настройка: `sh skripty/transkript_setup.sh <ключ AssemblyAI>` —
  ставит недостающее через brew, кладёт ключ в `.assemblyai-key`, прогоняет
  самопроверку. Идемпотентно.
  `python3 skripty/transkript.py <ссылка|файл> [--suho] [--kommit]`
  `python3 skripty/transkript.py --kanal <канал> --limit 5` — только новые ролики
  Instagram почти всегда просит куки, YouTube — периодически («Sign in to confirm
  you're not a bot»): `--brauzer chrome` или `--cookies cookies.txt`. Скрипт
  распознаёт эту ошибку и говорит, что делать.
  Созвоны и эфиры на два голоса: `--govoryashchie 2`.
  **Ускорение аудио (`--skorost`) по умолчанию выключено намеренно:** час
  расшифровки стоит $0.15, ×2 экономит 7 центов и роняет точность на русском.
  Экономия времени берётся не отсюда, а с того, что видеопоток не качается,
  а звук ужимается до опуса.
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

- `sait.js` — открыть сайт настоящим Chromium и снять сырьё: текст в порядке
  чтения, структуру (заголовки, CTA, формы, цены), ссылки, скриншот. Нужен там,
  где `WebFetch` бесполезен: Tilda, Taplink, любой SPA. Node, не Python; разовая
  настройка — `sh skripty/sait_setup.sh`. Вызывается и командой `/sait`.
  `node skripty/sait.js <адрес>`

`sheets_sync.py` и `ca_sync.py` — **единственные скрипты с внешними зависимостями**
(Google Sheets API нельзя вызвать без библиотеки), ставятся из
`skripty/requirements-sheets.txt`. Оба используют один ключ сервис-аккаунта.
