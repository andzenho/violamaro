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

var HEADERS = [
  'Дата', 'ID в Телеграме', 'Имя',
  'Ранг', 'Процент',
  'Дар', 'Прилипание', 'История', 'Тело', 'Адресат', 'Гигиена', 'Люди', 'Фон', 'Контроль',
  'Где съедает', 'Что менять первым', 'Что уже делали', 'Давно смотрит',
  'Ответы (1–24)',
  'Секунд', 'Быстро', 'Одна кнопка'
];

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
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

function doGet() {
  return json_({ ok: true, note: 'Приёмник теста эмпата жив' });
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
