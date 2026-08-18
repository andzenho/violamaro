/**
 * Приёмник результатов теста «Есть у вас способности эмпата?» в Google-таблицу.
 *
 * Сервер не нужен: это скрипт внутри самой таблицы, Google сам держит адрес,
 * по которому страница теста присылает результат.
 *
 * ── Установка (пять минут, один раз) ────────────────────────────────────────
 * 1. Создать таблицу, назвать лист «Тест эмпата».
 * 2. В таблице: Расширения → Apps Script. Вставить весь этот файл, сохранить.
 * 3. Развернуть → Новое развёртывание → тип «Веб-приложение».
 *      Запуск от имени: я
 *      Доступ: все, включая анонимных
 *    Google выдаст адрес вида https://script.google.com/macros/s/…/exec
 * 4. Этот адрес вписать в produkt/test-empat.html, в CONFIG.sheetUrl.
 * 5. Первую строку заголовков скрипт создаст сам при первом прохождении.
 *
 * Повторное развёртывание после правок: Развернуть → Управление развёртываниями
 * → карандаш → новая версия. Адрес при этом не меняется.
 */

var SHEET_NAME = 'Тест эмпата';

/* Имя листа для заявок. Должно совпадать с названием вкладки в таблице буква
   в букву: если лист переименовать, скрипт его не найдёт и молча заведёт новый
   пустой лист со старым именем — заявки уйдут туда. Переименовали вкладку —
   поправьте эту строку и переразверните скрипт. */
var LEAD_SHEET = 'Предзапись с теста';

var HEADERS = [
  'Дата', 'ID в Телеграме', 'Имя',
  'Ранг', 'Процент',
  'Дар', 'Прилипание', 'История', 'Тело', 'Адресат', 'Гигиена', 'Люди', 'Фон', 'Контроль',
  'Где съедает', 'Что менять первым', 'Что уже делали', 'Давно смотрит',
  'Ответы (1–24)',
  'Секунд', 'Быстро', 'Одна кнопка'
];

var LEAD_HEADERS = [
  'Дата', 'Имя', 'Телеграм', 'ID в Телеграме',
  'Тип', 'Процент', 'Что менять первым', 'Где съедает', 'Готовность',
  /* Акцепт — теми же полями, что и на сайте оплаты, чтобы сводить в одну картину. */
  'Согласие на ПД', 'Реклама', 'Время акцепта', 'Ред. согласия'
];

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    return route_(d);
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/**
 * Страница присылает данные обычным GET с параметром payload.
 * Так надёжнее: POST на веб-приложение Apps Script упирается в редирект,
 * который у анонимных запросов отдаёт «Page Not Found».
 */
function doGet(e) {
  try {
    var raw = e && e.parameter && e.parameter.payload;
    if (!raw) return json_({ ok: true, note: 'Приёмник теста эмпата жив' });
    return route_(JSON.parse(raw));
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function route_(d) {
  try {
    if (d.type === 'lead') { return saveLead_(d); }

    var sheet = getSheet_();
    var s = d.scales || {};

    sheet.appendRow([
      new Date(),
      d.userId || '',
      d.userName || '',
      rankName_(d.rank),
      d.percent || '',
      s.A, s.P, s.I, s.B, s.C, s.G, s.L, s.F, s.K,
      pick_(d.forks, 'bol'), pick_(d.forks, 'zapros'),
      pick_(d.forks, 'opyt'), pick_(d.forks, 'davno'),
      (d.answers || []).join(','),
      d.seconds || '', d.fast ? 'да' : '', d.monotone ? 'да' : ''
    ]);

    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

/** Запись в первый поток — отдельным листом, чтобы не мешать сырьё теста и контакты. */
function saveLead_(d) {
  var sheet = getSheet2_(LEAD_SHEET, LEAD_HEADERS);
  sheet.appendRow([
    new Date(),
    d.name || '',
    d.contact || '',
    d.userId || '',
    rankName_(d.rank),
    d.percent || '',
    pick_(d.forks, 'zapros'),
    pick_(d.forks, 'bol'),
    /* d.talk — из заявок, отправленных до 17.08: там это поле называлось иначе,
       а в буфере браузера такие записи могут лежать до сих пор. */
    d.ready || d.talk || '',
    d.accept_pd || '',
    d.accept_ads || '',
    d.consent_ts || '',
    d.doc_version_consent || ''
  ]);
  /* Возвращаем имя листа: по ответу видно, куда именно легла заявка,
     и проверка больше не сводится к угадыванию по содержимому таблицы. */
  return json_({ ok: true, sheet: sheet.getName() });
}

function getSheet2_(name, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name) || ss.insertSheet(name);

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
    return sheet;
  }

  /* Лист уже с данными, а колонок стало больше — подписываем только пустые
     ячейки шапки. Названия, поставленные руками, не трогаем: если колонку
     переименовали в таблице, это решение человека, а не сбой.
     Строки с данными не трогаем никогда. */
  if (sheet.getMaxColumns() < headers.length) {
    sheet.insertColumnsAfter(sheet.getMaxColumns(), headers.length - sheet.getMaxColumns());
  }
  var have = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  var fixed = [];
  var need = false;
  for (var i = 0; i < headers.length; i++) {
    var cur = String(have[i] == null ? '' : have[i]).trim();
    fixed.push(cur ? have[i] : headers[i]);
    if (!cur) need = true;
  }
  if (need) {
    sheet.getRange(1, 1, 1, headers.length).setValues([fixed]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function rankName_(key) {
  var names = {
    donor: 'Эмпат-донор',
    filter: 'Эмпат без фильтра',
    sleeping: 'Спящий эмпат',
    awake: 'Проснувшийся эмпат',
    reader: 'Считывающий',
    caring: 'Сочувствующий',
    other: 'Другая настройка'
  };
  return names[key] || key || '';
}

function pick_(obj, key) {
  return (obj && obj[key]) ? obj[key] : '';
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
