# Карта репозитория

<!-- Собирается скриптом: python3 skripty/karta.py
     Руками не править — правки затрутся. Чтобы задать файлу описание
     или статус, добавь в САМ файл строку «описание: …» / «статус: …». -->

Путь, вес в токенах, суть одной строкой. Читается вместо угадывания, куда лезть.

⚠️ — тяжелее 10 000 токенов: целиком не открывать, только `grep -n` + `Read` с `offset`/`limit`.
Правила по разделам подгружаются сами из `.claude/rules/*.md`.

## Корень
| Файл | Ток. | Суть |
|---|---:|---|
| `CLAUDE.md` | 2 360 | Проект «Виола Маро» |
| `README.md` | 1 195 | Виола Маро — рабочий репозиторий |

## `baza/` — 10 файл., 49 031 ток.
*Источник правды по смыслу: голос и каноны*

| Файл | Ток. | Суть |
|---|---:|---|
| `README.md` | 270 | baza/ — база знаний (источник правды) |
| `golos-viola.md` | 8 455 | Голос Виолы |
| `kanon-empat.md` | 5 374 | Канон Виолы. Тема эмпата (пробуждение и сила) |
| `kanon-empatiya-metod.md` | 8 026 | Канон эмпатии. Методология курса «Практическая эмпатия 3.0» |
| `kanon-lyubov-i-dengi.md` | 5 144 | Канон Виолы. Тема «Любовь и деньги» (наполненность / изобилие) |
| `kanon-viny.md` | 8 176 | Канон Виолы. Тема вины |
| `printsipy-viola.md` | 3 124 | Принципы Виолы. Сквозное |
| `reestr-istochnikov.md` | 4 127 | База знаний Виолы. Карта и реестр источников |
| `tehniki-viola.md` | 3 502 | Техники Виолы. Сквозной каталог |
| `zhurnal-resheniy.md` | 2 833 | Журнал решений |

## `produkt/` — 31 файл., 210 744 ток.
*Программы, цены, условия*

| Файл | Ток. | Суть |
|---|---:|---|
| `README.md` | 2 542 | produkt/ |
| `dengi-dlya-empata-razbor.md` | 2 358 | Деньги как средство самореализации и благополучия для эмпата — разбор |
| `efir-2-voprosy.md` | 3 075 | Эфир 2 (22.08) — вопросы для Виолы |
| `efir-lyubov-i-dengi-razbor.md` | 3 002 | Эфир «Любовь и деньги» — разбор (скелет флагмана) |
| `fakty-viola.md` | 2 466 | Факты и решения от Виолы (рабочий чат, 08.2026) |
| `karta-smyslov-i-argumentov.md` | 6 113 | Карта смыслов ЦА → аргументы к покупке. И симуляция продаж |
| `lending-palitra.html` | 8 883 | — |
| `lending-promt-dizayn.md` | 6 904 | Промпт для Claude Design — лендинг «Практическая эмпатия 4.0» |
| `lending-promt-gotovyy.md` | 12 670 ⚠️ | ТЕКСТ СТРАНИЦЫ — ДОСЛОВНО |
| `lending-strategiya-dizayna.md` | 8 074 | Лендинг «Практическая эмпатия 4.0» — стратегия дизайна |
| `marafon-po-sferam.md` | 12 484 ⚠️ | Календарь запуска и пять эфиров |
| `neudobnye-lending.md` | 13 311 ⚠️ | Текст лендинга «Неудобные» |
| `neudobnye-promt-dizayn.md` | 10 196 ⚠️ | Промпт для Claude Design — лендинг «Неудобные» |
| `neudobnye-promt-gotovyy.md` | 11 570 ⚠️ | ТЕКСТ СТРАНИЦЫ — ДОСЛОВНО |
| `neudobnye-razbor.md` | 4 278 | «Неудобные» — разбор комментария Виолы (29.08.2026) |
| `neudobnye.md` | 13 851 ⚠️ | Событие «Неудобные» — источник правды |
| `praktikum-dlya-empatov.md` | 6 516 | Практикум для эмпатов — источник правды по продукту |
| `praktikum-vnutrennie-zametki.md` | 30 703 ⚠️ | Практикум «Прикладная эмпатия» — внутренние заметки |
| `produkty-viola-staryye.md` | 2 051 | Старые продукты Виолы — разбор для контекста |
| `programma-otnosheniya-razbor.md` | 3 543 | Внутрянка Виолы по отношениям — разбор и сведение с нашей программой |
| `skript-prodazh-kontekst.md` | 9 849 | Скрипт продаж: контекст и фреймворки под сборку |
| `skript-prodazh-sozvon.md` | 5 636 | Скрипт созвона |
| `strategiya.md` | 2 637 | Стратегия запуска «Виола Маро» |
| `test-empat-chatplace.md` | 2 500 | Сборка теста в ChatPlace — карта для конструктора |
| `test-empat-chistovik.md` | 4 636 | Тест «Есть у вас способности эмпата?» — чистовик под сборку |
| `test-empat-lite.md` | 2 735 | Тест эмпата — облегчённая версия под быструю сборку |
| `test-empat.md` | 8 989 | *[**черновик под сборку в боте**. Строки голосом Виолы — на её визирование.]* Тест «Есть у вас способности эмпата?» — конструкция, вопросы, ответы |
| `transformatsii.md` | 2 778 | Канон трансформаций «Виола» |
| `transformatsiya-za-dengi.md` | 3 011 | Трансформация за деньги: какую метаморфозу продавать для максимальной в… |
| `vebinar-empaty-dengi-razbor.md` | 1 835 | Вебинар «Эмпаты и деньги» — разбор под продукт |
| `voronka.md` | 1 548 | Воронка «Виола»: тема, глубина, фрейм |

## `analitika/` — 23 файл., 146 190 ток.
*ЦА, цифры, кастдэвы*

| Файл | Ток. | Суть |
|---|---:|---|
| `README.md` | 3 216 | analitika/ |
| `anketa-pokupateli-empatia.md` | 3 490 | Анкета + интервью: покупатели курсов Виолы (эмпатия) |
| `anketa-predzapisi-lyubov-dengi.md` | 1 276 | Запись в первый поток «Любовь и деньги» |
| `ca-audit.md` | 1 221 | Аудит ЦА: что собрали, чего не хватает (перед тратами на продукт) |
| `ca-chaty-empatia.md` | 10 197 ⚠️ | Чаты потоков «Практическая эмпатия» — разбор |
| `ca-data.json` | 7 763 | — |
| `ca-empatia.md` | 3 679 | ЦА продукта «Практическая эмпатия» — разбор чата потока (платящая аудит… |
| `ca-itog.md` | 11 287 ⚠️ | Итоговый анализ ЦА: где деньги |
| `ca-klyuchi.md` | 2 464 | ЦА продукта «Ключи» (Интенсив) — разбор чата потока |
| `ca-master.md` | 13 873 ⚠️ | ЦА под продажу «Прикладной эмпатии» — мастер-сводка |
| `ca-portret.md` | 4 962 | Кто наш покупатель. Объяснение для команды |
| `ca-voc.md` | 9 068 | Voice-of-customer: банк дословных фраз аудитории |
| `karta-smyslov.md` | 12 626 ⚠️ | Карта смыслов: боли, желания, страхи → чем закрываем |
| `kastdev-03-empat-3potok.md` | 7 694 | Кастдев №3 — покупательница «Практической эмпатии», 3-й поток |
| `kastdev-sozvony.md` | 10 349 ⚠️ | Кастдев: созвоны с покупателями — разбор |
| `kastdev/01-transkript-empat-60-rf.txt` | 8 758 | Speaker A: Средняя обывательница Российской Федерации, это нельзя сказа… |
| `kastdev/02-transkript-empat-600evro.txt` | 7 330 | Speaker A: Последнее время как бы чаще. |
| `kastdev/03-transkript-empat-3potok.txt` | 9 965 | Кастдев №3 — покупательница «Практической эмпатии», 3-й поток |
| `kastdev/04-transkript-muzhchina-ne-kupil.txt` | 3 052 | Speaker A: всё равно это сделать.— |
| `kommentarii-razbor.md` | 7 054 | Разбор комментариев — партия 1 |
| `kommentarii/README.md` | 453 | analitika/kommentarii/ |
| `temy-i-triggery.md` | 2 998 | Темы и триггеры: что заходит нашей ЦА |
| `tg-kommentarii-razbor.md` | 3 415 | Разбор комментариев Telegram — канал `violamaro1` |

## `kontent/` — 76 файл., 53 959 ток.
*Контент-план и стратегия контента*

| Файл | Ток. | Суть |
|---|---:|---|
| `README.md` | 75 | kontent/ |
| `framework-progreva-neudobnye.md` | 4 296 | Фреймворк прогрева «Неудобных», 01–10.09 |
| `kp/README.md` | 1 638 | kontent/kp/ — контент-план для Google-таблицы |
| `kp/_dlya_vstavki.txt` | 1 702 | ============================================================ |
| `kp/strategiya-kontent-plana.md` | 10 090 ⚠️ | *[рабочий документ, обновляем при решениях продюсера.]* Стратегия контента — все каналы |
| `promt-dlya-agenta-violy.md` | 1 389 | Промпт для агента |

Посты контент-плана (навигация — `python3 skripty/plan.py`):

| Вкладка | Постов | Ток. | Имя вкладки в таблице |
|---|---:|---:|---|
| `kp/bot-rassylki/` | 7 | 2 103 | КП Бот рассылки |
| `kp/instagram/` | 1 | 2 517 | КП Инстаграм |
| `kp/kabinet-predzapisi/` | 9 | 7 260 | КП Кабинет предзаписи |
| `kp/staryy-kanal-chat/` | 4 | 1 819 | КП Старый канал + чат |
| `kp/storis-insta-tiktok/` | 3 | 1 113 | КП Сторис Инста+ТикТок |
| `kp/tg-osnova/` | 36 | 13 948 | КП Телеграм Основа |
| `kp/youtube/` | 10 | 6 009 | КП Ютуб |

## `korpus/` — 15 файл., 297 312 ток.
*Сырьё: транскрипты. ⚠️ Тяжёлое, только кусками*

| Файл | Ток. | Суть |
|---|---:|---|
| `01-lidmagnit.txt` | 8 367 | *[сырьё]* Добрый день, дорогие мои. |
| `02-otvety.txt` | 12 672 ⚠️ | *[сырьё]* Илья, добрый день. |
| `03-samoobman-empatov.txt` | 1 206 | *[сырьё]* Самая большая проблема людей с добрым сердцем, с правильными, хорошими… |
| `04-probuzhdenie-empata.txt` | 574 | *[сырьё]* И, как правило, триггером пробуждения для эмпата является глубокое пред… |
| `05-metodichka-empatiya-modul1-lichnost.txt` | 66 242 ⚠️ | *[сырьё]* Виола Маро |
| `06-metodichka-empatiya-modul2-pole.txt` | 70 485 ⚠️ | *[сырьё]* Виола Маро |
| `07-metodichka-empatiya-modul3-razvitie.txt` | 43 984 ⚠️ | *[сырьё]* Виола Маро |
| `08-efir-lyubov-i-dengi.txt` | 35 354 ⚠️ | *[сырьё]* Эфир «Любовь и деньги» — бонусная лекция курса «Практическая эмпатия» |
| `09-vebinar-empaty-dengi.txt` | 11 113 ⚠️ | *[сырьё]* Источник: [ВЕБ] Третий бесплатный вебинар серии «Практическая эмпатия»… |
| `10-30-priznakov-empata.md` | 3 244 | *[сырьё]* 30 признаков эмпата — документ Виолы |
| `11-sozvon-viola-11.08.srt` | 34 525 ⚠️ | *[сырьё]* 1 |
| `12-programma-otnosheniya-viola.txt` | 2 495 | *[сырьё]* ИСТОЧНИК: внутреннее содержание курса, часть про отношения. |
| `13-9-printsipov-effektivnosti-empatov.md` | 1 686 | *[сырьё]* 9 принципов эффективности для эмпатов (материал Виолы, из старых матери… |
| `14-zayavka-flagman-03.09.md` | 4 721 | *[сырьё]* Прикладная эмпатия — 6-недельный практикум Виолы Маро |
| `README.md` | 644 | *[сырьё]* korpus/ — сырьё |

## `docs/` — 5 файл., 128 980 ток.
*Опубликованное на GitHub Pages*

| Файл | Ток. | Суть |
|---|---:|---|
| `README.md` | 980 | docs/ — то, что опубликовано |
| `dizayn-testov.md` | 1 913 | Дизайн тестов и квестов — стандарт |
| `index.html` | 25 493 ⚠️ | — |
| `koleso/index.html` | 99 879 ⚠️ | — |
| `neudobnye/index.html` | 715 | — |

## `skripty/` — служебные скрипты
*Что делает каждый и как запускать — `skripty/README.md`.*

`bot_probe.py`, `ca_sync.py`, `karta.py`, `karta_korpusa.py`, `kontrast.py`, `kp_export.py`, `lending_promt.py`, `oglavlenie.py`, `perenos.py`, `plan.py`, `proverka.py`, `razbor.py`, `razbor_kommentov.py`, `sheets_chistka.py`, `sheets_sync.py`, `tg_comments.py`, `ves.py`, `yt_comments.py`, `yt_stats.py`

## `.claude/` — настройки ассистента
Правила по папкам (грузятся сами): `analitika.md`, `arhiv.md`, `baza.md`, `docs.md`, `kontent.md`, `korpus.md`, `produkt.md`
Команды: `/den`, `/dyrki`, `/post`, `/proverka`, `/sait`, `/strateg`, `/transkript`

## `arhiv/` — 23 файл., 94 179 ток.
*⚠️ Устаревшее и противоречащее курсу. Открывать только по прямой просьбе.*

- `README.md`
- `lyubov-i-dengi/blok-do-posle-prorabotka.md`
- `lyubov-i-dengi/flagman-sborka-jtbd.md`
- `lyubov-i-dengi/gipoteza-produkt-vokrug-lichnosti.md`
- `lyubov-i-dengi/odnostranichnik-sozvon-lyubov-i-dengi.md`
- `lyubov-i-dengi/peresborka-v2-vokrug-vnimaniya.md`
- `lyubov-i-dengi/prezentatsiya-lyubov-i-dengi.md`
- `lyubov-i-dengi/programma-lyubov-i-dengi-v1.md`
- `lyubov-i-dengi/sozvon-11.08-razbor-dlya-komandy.md`
- `lyubov-i-dengi/sozvon-viola-11.08-itogi.md`
- `ofery-promezhutochnye/ofer-flagman-empat.md`
- `ofery-promezhutochnye/ofer-lyubov-i-dengi-sborka.md`
- `praktikum-snyatye-zametki.md`
- `tehnicheskoe/perenos-v-claude-code.md`
- `tehnicheskoe/sozvon-11.08-agenda.md`
- `vina-staryy-flagman/anketa-pervye-dannye.md`
- `vina-staryy-flagman/anketa-predzapisi.md`
- `vina-staryy-flagman/ca-analiz-v1.1.md`
- `vina-staryy-flagman/ca-framework.md`
- `vina-staryy-flagman/ca-lidmagnit.md`
- `vina-staryy-flagman/ca-ya-vybirayu-sebya.md`
- `vina-staryy-flagman/ofer-ya-vybirayu-sebya.md`
- `vina-staryy-flagman/vozrazheniya-i-prodazhi.md`

---
**Всего 203 файлов, ~994 512 токенов.** Весь репозиторий в один контекст не влезает и не должен.
