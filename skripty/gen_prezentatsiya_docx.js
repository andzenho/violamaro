const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, convertInchesToTwip
} = require('docx');
const fs = require('fs');

const ACCENT = "8E3B62";      // приглушённый бордовый
const GOLD   = "B08D57";
const DARK   = "2B2440";
const GREY   = "6B6478";
const LIGHT  = "F4F1F7";

const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE };

// ---------- helpers ----------
const P = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: 276 },
  alignment: opts.align,
  indent: opts.indent,
  border: opts.border,
  shading: opts.shading,
  children: [new TextRun({
    text,
    bold: opts.bold,
    italics: opts.italics,
    size: opts.size ?? 22,
    color: opts.color ?? "1A1A1A",
    font: "Georgia",
    allCaps: opts.caps,
  })],
});

const RUNS = (runs, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: 276 },
  alignment: opts.align,
  indent: opts.indent,
  children: runs.map(r => new TextRun({
    text: r.t, bold: r.b, italics: r.i, size: r.size ?? 22,
    color: r.c ?? "1A1A1A", font: "Georgia",
  })),
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 },
  children: [new TextRun({ text, bold: true, size: 34, color: DARK, font: "Georgia" })],
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 300, after: 140 },
  children: [new TextRun({ text, bold: true, size: 26, color: ACCENT, font: "Georgia" })],
});

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 80 },
  children: [new TextRun({ text, bold: true, size: 23, color: DARK, font: "Georgia" })],
});

const BULLET = (text) => new Paragraph({
  numbering: { reference: "dash-list", level: 0 },
  spacing: { after: 90, line: 276 },
  children: [new TextRun({ text, size: 22, color: "1A1A1A", font: "Georgia" })],
});

const BULLET2 = (lead, rest) => new Paragraph({
  numbering: { reference: "dash-list", level: 0 },
  spacing: { after: 90, line: 276 },
  children: [
    new TextRun({ text: lead, bold: true, size: 22, color: "1A1A1A", font: "Georgia" }),
    new TextRun({ text: rest, size: 22, color: "1A1A1A", font: "Georgia" }),
  ],
});

const RULE = () => new Paragraph({
  spacing: { before: 200, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "D8D2E0" } },
  children: [new TextRun({ text: "", size: 2 })],
});

// ---------- numbering ----------
const numbering = {
  config: [{
    reference: "dash-list",
    levels: [{
      level: 0, format: LevelFormat.BULLET, text: "—", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.22) } },
               run: { color: ACCENT } },
    }],
  }],
};

// ---------- таблица тарифов ----------
const TW = 9360;               // ширина таблицы (DXA) для полей 1"
const COLS = [3960, 1800, 1800, 1800];

const cell = (children, opts = {}) => new TableCell({
  width: { size: opts.w, type: WidthType.DXA },
  shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: "auto" } : undefined,
  margins: { top: 100, bottom: 100, left: 120, right: 120 },
  verticalAlign: opts.valign,
  columnSpan: opts.span,
  children,
});

const tHead = () => new TableRow({
  tableHeader: true,
  children: [
    cell([P("", { size: 18 })], { w: COLS[0], fill: DARK }),
    cell([
      P("Базовый", { bold: true, size: 24, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("Программа и сообщество", { italics: true, size: 17, color: "CFC8DC", align: AlignmentType.CENTER, after: 60 }),
      P("19 900 ₽", { bold: true, size: 26, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("месяц", { size: 17, color: "CFC8DC", align: AlignmentType.CENTER, after: 0 }),
    ], { w: COLS[1], fill: DARK }),
    cell([
      P("Полный", { bold: true, size: 24, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("Виола отвечает вам голосом", { italics: true, size: 17, color: "CFC8DC", align: AlignmentType.CENTER, after: 60 }),
      P("29 900 ₽", { bold: true, size: 26, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("месяц", { size: 17, color: "CFC8DC", align: AlignmentType.CENTER, after: 0 }),
    ], { w: COLS[2], fill: "3D3357" }),
    cell([
      P("Личный", { bold: true, size: 24, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("Виола разбирает вас лично", { italics: true, size: 17, color: "EFD9E4", align: AlignmentType.CENTER, after: 60 }),
      P("39 900 ₽", { bold: true, size: 26, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
      P("месяц", { size: 17, color: "EFD9E4", align: AlignmentType.CENTER, after: 0 }),
    ], { w: COLS[3], fill: ACCENT }),
  ],
});

const groupRow = (label) => new TableRow({
  children: [cell([P(label, { bold: true, size: 17, color: ACCENT, caps: true, after: 0 })],
    { w: TW, fill: LIGHT, span: 4 })],
});

const featRow = (name, sub, marks) => new TableRow({
  children: [
    cell([
      P(name, { bold: true, size: 21, after: sub ? 40 : 0 }),
      ...(sub ? [P(sub, { size: 17, color: GREY, after: 0 })] : []),
    ], { w: COLS[0] }),
    ...marks.map((m, i) => cell(
      [P(m ? "✓" : "—", {
        align: AlignmentType.CENTER, bold: m, size: m ? 24 : 22,
        color: m ? ACCENT : "B9B3C4", after: 0,
      })],
      { w: COLS[i + 1], valign: "center" }
    )),
  ],
});

const infoRow = (name, vals, strong) => new TableRow({
  children: [
    cell([P(name, { bold: true, size: 21, after: 0 })], { w: COLS[0] }),
    ...vals.map((v, i) => cell(
      [P(v, { align: AlignmentType.CENTER, size: 20, bold: strong, color: strong ? ACCENT : "1A1A1A", after: 0 })],
      { w: COLS[i + 1], valign: "center" }
    )),
  ],
});

const tariffTable = new Table({
  columnWidths: COLS,
  width: { size: TW, type: WidthType.DXA },
  borders: {
    top:   { style: BorderStyle.SINGLE, size: 2, color: "D8D2E0" },
    bottom:{ style: BorderStyle.SINGLE, size: 2, color: "D8D2E0" },
    left:  { style: BorderStyle.SINGLE, size: 2, color: "D8D2E0" },
    right: { style: BorderStyle.SINGLE, size: 2, color: "D8D2E0" },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "E6E2EC" },
    insideVertical:   { style: BorderStyle.SINGLE, size: 2, color: "E6E2EC" },
  },
  rows: [
    tHead(),
    groupRow("Есть везде — метод целиком, ничего не урезано"),
    featRow("6 лекций Виолы", "Две в неделю. Каждая даёт и в отношения, и в деньги. Открыть когда удобно, в своём часовом поясе", [1,1,1]),
    featRow("Аудиоверсия каждой лекции", "Слушать в дороге и на прогулке, возвращаться сколько нужно", [1,1,1]),
    featRow("Живой мастер-класс с Виолой", "Четвёртая неделя. Виола отвечает на вопросы потока в эфире", [1,1,1]),
    featRow("Рабочая тетрадь", "Задание к каждой лекции, практика на каждый день", [1,1,1]),
    featRow("Доска желаний по состоянию души", "Авторская механика Виолы: вытащить то, чего вы хотите на самом деле", [1,1,1]),
    featRow("Практики голосом Виолы", "Заземлиться, вернуть ресурс, услышать свою интуицию телом", [1,1,1]),
    featRow("Готовые фразы", "Как сказать «нет» и как попросить за себя", [1,1,1]),
    featRow("Записи и материалы, доступ навсегда", "Вернуться можно через год, когда снова накроет", [1,1,1]),
    featRow("Сообщество эмпатов со всего мира", "Закрытый чат потока: Германия, Италия, США, Россия. Наконец свои люди", [1,1,1]),
    groupRow("Со второго тарифа — Виола отвечает лично вам"),
    featRow("Виола отвечает вам голосом", "Ваш вопрос — её ответ голосовым сообщением. Весь поток. То самое, за чем к ней и идут", [0,1,1]),
    featRow("Ваш вопрос на мастер-классе", "Присылаете вопрос заранее, Виола разбирает его в эфире лично", [0,1,1]),
    groupRow("Только в личном — Виола разбирает вашу ситуацию"),
    featRow("Разбор на старте", "Вы описываете свою ситуацию, Виола голосом разбирает: куда именно у вас уходят силы и с чего начинать", [0,0,1]),
    featRow("Разбор вашей доски желаний", "В финале. Виола голосом смотрит, чего вы хотите на самом деле, и называет ваш следующий шаг", [0,0,1]),
    infoRow("Длительность", ["месяц", "месяц", "месяц"], false),
    infoRow("Мест в потоке", ["без ограничений", "без ограничений", "[N]"], true),
  ],
});

// ---------- неделя программы ----------
const week = (title, learn, gives) => [
  H3(title),
  RUNS([{ t: "Осваиваете: ", b: true, c: ACCENT }, { t: learn }], { after: 60 }),
  RUNS([{ t: "Даёт: ", b: true, c: ACCENT }, { t: gives }], { after: 180 }),
];

const lect = (title, learn, love, money) => [
  H3(title),
  RUNS([{ t: "Осваиваете: ", b: true, c: ACCENT }, { t: learn }], { after: 60 }),
  RUNS([{ t: "В отношениях: ", b: true, c: DARK }, { t: love }], { after: 60 }),
  RUNS([{ t: "В деньгах: ", b: true, c: DARK }, { t: money }], { after: 180 }),
];

// ---------- документ ----------
const doc = new Document({
  numbering,
  styles: {
    default: { document: { run: { font: "Georgia", size: 22 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },            // A4
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 },
      },
    },
    children: [
      // ===== ТИТУЛ =====
      P("ПРЕЗЕНТАЦИЯ ПРОДУКТА · ЧЕРНОВИК ПОД КАСТДЕВ · 12.08.2026",
        { size: 17, color: GOLD, caps: true, after: 240 }),
      P("ПЕРВЫЙ ПОТОК · 4-НЕДЕЛЬНЫЙ АВТОРСКИЙ ОНЛАЙН-ИНТЕНСИВ ВИОЛЫ МАРО ДЛЯ ЭМПАТОВ",
        { bold: true, size: 19, color: ACCENT, caps: true, after: 100 }),
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({ text: "Любовь и деньги", bold: true, size: 56, color: DARK, font: "Georgia" })],
      }),

      P("Овладейте своей врождённой суперспособностью эмпата. И начните получать то, что годами отдавали другим.",
        { bold: true, size: 26, color: DARK, after: 100 }),
      P("Любимое дело и деньги. Отношения без потери себя. Жизнь для себя.",
        { italics: true, size: 23, color: ACCENT, after: 200 }),
      RULE(),

      // ===== МЕХАНИЗМ =====
      H2("У вас есть радар, которого нет у других"),
      P("Вы чувствуете сильнее других. Видите людей насквозь, слышите, когда человек говорит одно, а внутри у него другое, замечаете то, чего другие не видят вовсе. Так умеют немногие. Это у вас с рождения."),
      P("Вот только инструкции к нему вам никто не выдал. И работает ваш дар на всех вокруг. Отсюда и усталость, и пустота к вечеру. А вместе с силами уходят и деньги."),
      P("Пора развернуть его на себя.", { bold: true, size: 25, color: ACCENT, after: 160 }),
      P("«Моя задача научить вас пользоваться вашей суперсилой эмпата. Чтобы она наконец работала на вас: на ваш покой, ваши отношения, ваше дело и ваши деньги».",
        { bold: true, size: 24, color: DARK, shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" }, after: 40 }),
      P("Виола Маро", { italics: true, size: 20, color: GREY, after: 200 }),
      // ===== ОКНО =====
      H2("Представьте: та же сила, но теперь вы умеете ею управлять"),
      P("Вот что меняется.", { after: 100 }),
      BULLET2("Силы остаются вам.", " Выслушали человека, а вечер по-прежнему ваш."),
      BULLET2("Радар работает на вас.", " Видите верный шаг, нужного человека, свою дверь."),
      BULLET2("Дело по душе приносит деньги.", " И вы спокойно их берёте."),
      BULLET2("«У меня есть Я».", " Своя сила, своя опора."),
      BULLET2("Живёте свою жизнь, а не чужую.", " Тепла хватает и близким, и себе."),

      H2("Любовь и деньги — это одна точка"),
      P("И любовь, и деньги растут из одного состояния. Из наполненности."),
      P("Когда наполненность разворачивается внутрь, это любовь. Сначала к себе, а потом и отношения, в которых вам хорошо. Когда наружу, это благополучие: возможности, дело, деньги."),
      P("Изобилие тут не про роскошь. Это простая человеческая свобода: делать что хотите, когда хотите и с кем хотите. Свобода быть собой.",
        { shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" }, after: 120, italics: true }),
      P("Вот почему мы не делим курс на «про отношения» и «про деньги». Точка входа одна.", { after: 200 }),

      // ===== ПРОГРАММА =====
      H1("Программа: месяц, шесть лекций и живой мастер-класс"),
      P("Шесть лекций Виолы выходят два раза в неделю: одна в середине недели, одна на выходных. Лекцию можно открыть когда удобно, из любой точки мира и в своём часовом поясе. К каждой лекции есть аудиоверсия: можно слушать в дороге и на прогулке."),
      P("Четвёртая неделя — живой мастер-класс с Виолой. Она отвечает на ваши вопросы в эфире."),
      P("Это программа про практику и действия. К каждой лекции вы осваиваете свой радар и сразу пробуете его в жизни. Никакой теории ради теории. Рабочая тетрадь и техники на каждый день."),
      P("Каждая лекция даёт сразу в обе стороны: в отношения и в деньги. Мы не откладываем обещанное на финал.",
        { bold: true, shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" }, after: 200 }),

      ...lect("Лекция 1. Куда уходит ваша сила",
        "ловить момент, когда ваш радар включается на чужое. По телу, за секунду до того, как вас затянет.",
        "видите, кто именно вас обесточивает. Перестаёте тащить на себе чужие настроения.",
        "видите, где вы годами работаете за спасибо."),
      ...lect("Лекция 2. Вернуть себе энергию",
        "считывать себя так же точно, как вы читаете других. И ставить границы, не выключая свою чувствительность.",
        "близость без выгорания. Держите дистанцию с теми, кто вытягивает, и не отдаляетесь от близких.",
        "силы остаются на своё дело, а не уходят к вечеру в ноль."),
      ...lect("Лекция 3. Разрешить себе получать",
        "отвечать на то, что вы и так чувствуете. Вы всегда знали, когда вами пользуются. Теперь вы это называете и говорите «нет».",
        "спокойно принимаете заботу, помощь и тепло.",
        "берёте деньги без чувства вины. Перестаёте работать за спасибо."),
      ...lect("Лекция 4. Услышать, чего хотите вы",
        "разворачивать радар внутрь. Ваша интуиция годами работала на других, теперь она отвечает на ваши вопросы. Собираете доску желаний по состоянию души.",
        "понимаете, какие отношения вам нужны на самом деле.",
        "понимаете, какое дело ваше."),
      ...lect("Лекция 5. Проявляться без страха",
        "ловить момент, когда вы сжимаетесь и прячете себя. И выходить из него.",
        "вас видно. Рядом появляются люди, которым нужны именно вы.",
        "появляется отдача. Ваш труд замечают и оплачивают."),
      ...lect("Лекция 6. Своя жизнь: и любовь, и деньги",
        "удерживать состояние наполненности и возвращаться в него, когда откатывает. Привычки изобилия на каждый день.",
        "рядом остаются свои люди, и вам с ними хорошо.",
        "занимаетесь тем, что по душе, и это приносит деньги."),

      // ===== ЧТО ПОЛУЧИТЕ =====
      H2("Что вы получите"),
      BULLET("Шесть лекций Виолы, доступ навсегда."),
      BULLET("Аудиоверсию каждой лекции: слушать в дороге и на прогулке."),
      BULLET("Живой мастер-класс с Виолой: она отвечает на вопросы в эфире."),
      BULLET("Рабочую тетрадь и практику на каждый день."),
      BULLET("Доску желаний по состоянию души: вытащить то, чего вы хотите на самом деле."),
      BULLET("Практики голосом Виолы: заземлиться, вернуть ресурс, услышать свою интуицию телом."),
      BULLET("Готовые фразы: как сказать «нет» и как попросить за себя."),
      BULLET("Сообщество эмпатов со всего мира: Германия, Италия, США, Россия. Наконец свои люди."),
      BULLET("Записи и материалы, доступ навсегда."),
      BULLET("Техники, которые остаются с вами на всю жизнь."),
      P("А главное, вы научитесь пользоваться своим радаром: направлять его на себя, на свой покой, свои отношения, своё дело и свои деньги.",
        { bold: true, before: 120, after: 200 }),

      // ===== ТАРИФЫ =====
      new Paragraph({ children: [new (require('docx').PageBreak)()] }),
      H1("Тарифы"),
      P("Первый поток · старт [дата]", { italics: true, color: GREY, after: 60 }),
      P("6 лекций Виолы · живой мастер-класс · месяц интенсива · доступ к материалам навсегда",
        { bold: true, size: 21, color: DARK, after: 200 }),
      tariffTable,
      P("Это цена первого потока. Дальше программа будет стоить дороже.",
        { italics: true, color: GREY, before: 160, after: 100 }),
      RUNS([{ t: "Оплата. ", b: true }, { t: "Рассрочка для РФ и СНГ, оплата из-за рубежа. Для тех, кому нужно, готовим сертификат и подтверждение оплаты." }],
        { after: 100 }),
      P("Программа не заменяет очную психотерапию.", { italics: true, size: 19, color: GREY, after: 200 }),

      // ===== ДЛЯ КОГО =====
      H2("Это для вас, если"),
      P("вы эмпат: чувствуете людей глубже других и от этого устаёте; всю жизнь заботитесь о других, а до себя руки не доходят; хотите, чтобы чувствительность приносила радость.", { after: 100 }),
      RUNS([{ t: "Это не для вас, если ", b: true }, { t: "ищете быструю схему заработка или как переделать другого человека. Здесь про вас." }], { after: 160 }),

      H2("Кто ведёт"),
      P("Виола Маро, психолог, психотерапевт. Живёт в Италии. Её курсы проходят по кругу и возвращаются, у выпускников три живых чата.", { after: 160 }),

      H2("Как попасть"),
      P("Первый поток стартует [дата]. Мест в группе немного.", { after: 60 }),
      P("Хотите, забронирую вам место?", { bold: true, size: 24, color: ACCENT, after: 240 }),

      // ===== СЛУЖЕБНОЕ =====
      new Paragraph({ children: [new (require('docx').PageBreak)()] }),
      H1("Для команды: что осталось закрыть"),
      P("Этот раздел клиенту не показываем.", { italics: true, color: GREY, after: 160 }),

      H3("Ждём от Виолы"),
      BULLET("Одно число: сколько персональных разборов голосом она делает за поток. Это и есть лимит мест в «Личном». Придуманный лимит не публикуем."),
BULLET("Сообщить ей, что индивидуальные встречи один на один в тарифы не идут: час её времени не тиражируется и упирает потолок продаж в её календарь. Вместо встречи — два разбора голосом, её формат из «Эмпатии»."),
      BULLET("Формат голосовых ответов в «Полном»: без ограничений или один вопрос в неделю. От этого зависит, ставить ли лимит мест и туда."),
      BULLET("Мастер-класс: дата, длительность, берём ли вопросы заранее письменно."),
      BULLET("Шесть лекций или восемь: собрано как 6 лекций по две в неделю за три недели плюс мастер-класс на четвёртой."),
      BULLET("Согласование цен 19 900 / 29 900 / 39 900 и самой трёхтарифной сетки."),
      BULLET("Месяц против её же «90 дней» с вебинара: месяц — это интенсив-вход, а глубина следующим продуктом?"),
      BULLET("Визирование строк её голоса, особенно денежных и заголовка (красная линия «без обещаний результата»)."),
      BULLET("Разбивка восьми встреч по шести шагам и дни недели: середина недели и выходные — какие именно."),
      BULLET("Дата старта первого потока."),

      H3("Что замеряем на кастдеве"),
      BULLET("Какой тариф выбирают глазами и почему."),
      BULLET("Цена: «легко / нормально / дорого» и где порог."),
      BULLET("Что цепляет сильнее: спокойствие с деньгами или своё дело."),
      BULLET("Какая неделя программы звучит нужнее всего."),

      H3("Логика тарифной сетки"),
      BULLET("Тарифы различаются только доступом к Виоле. Все материалы одинаковы везде: делить по объёму материалов значит выдать дешёвому тарифу урезанную версию."),
      BULLET("В базовом тарифе метод целиком, результат достижим без доплат."),
      BULLET("Средний тариф стоит ближе к нижнему, поэтому собирает основную массу."),
      BULLET("Ограничение мест только там, где оно вытекает из физики её времени: групповые зумы в ёмкость не упираются, поэтому лимит стоит только в «Личном»."),
      BULLET("Шаг между тарифами меньше воспринимаемой прибавки: оба шага по 10 000 рублей, а прибавка — её голос, который в разовой консультации стоит около 200 евро."),
      BULLET("Старт заметно ниже потолка платёжеспособности: за «Практическую эмпатию» эта аудитория платила 600–1200 евро. Цена дальше только растёт."),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[2] || "out.docx", buf);
  console.log("written");
});
