/**
 * Сборка .docx из презентации продукта.
 *
 * Текст НЕ хранится здесь. Скрипт читает markdown-источник правды и рендерит
 * его клиентскую часть (между метками «✂️ КЛИЕНТСКАЯ ЧАСТЬ» и «✂️ КОНЕЦ
 * КЛИЕНТСКОЙ ЧАСТИ») плюс служебный блок для команды. Правки текста — только
 * в .md, здесь живёт исключительно оформление.
 *
 *   node skripty/gen_prezentatsiya_docx.js [исходник.md] [выход.docx]
 *
 * По умолчанию: produkt/prezentatsiya-lyubov-i-dengi.md →
 *               produkt/docs/Любовь-и-деньги-презентация.docx
 */
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, convertInchesToTwip, PageBreak
} = require('docx');
const fs = require('fs');
const path = require('path');

const SRC = process.argv[2] || path.join('produkt', 'prezentatsiya-lyubov-i-dengi.md');
const OUT = process.argv[3] || path.join('produkt', 'docs', 'Любовь-и-деньги-презентация.docx');

const ACCENT = "8E3B62";      // приглушённый бордовый
const GOLD   = "B08D57";
const DARK   = "2B2440";
const GREY   = "6B6478";
const LIGHT  = "F4F1F7";

const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

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
  shading: opts.shading,
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

const BULLET_RUNS = (runs) => new Paragraph({
  numbering: { reference: "dash-list", level: 0 },
  spacing: { after: 90, line: 276 },
  children: runs.map(r => new TextRun({
    text: r.t, bold: r.b, italics: r.i, size: 22, color: "1A1A1A", font: "Georgia",
  })),
});

const RULE = () => new Paragraph({
  spacing: { before: 200, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "D8D2E0" } },
  children: [new TextRun({ text: "", size: 2 })],
});

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

// ---------- разбор inline-разметки ----------
// **жирный**, *курсив*, «текст» — в runs. Служебная разметка снимается.
function inline(text) {
  text = text.replace(/`/g, '');
  const out = [];
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push({ t: text.slice(last, m.index) });
    if (m[1] !== undefined) out.push({ t: m[1], b: true });
    else out.push({ t: m[2], i: true });
    last = re.lastIndex;
  }
  if (last < text.length) out.push({ t: text.slice(last) });
  return out.length ? out : [{ t: text }];
}

const strip = (s) => s
  .replace(/<br\s*\/?>/gi, ' ')
  .replace(/<\/?sub>/gi, '')
  .replace(/\*\*/g, '')
  .replace(/(^|[^*])\*([^*]+)\*/g, '$1$2')
  .replace(/`/g, '')
  .trim();

// ---------- чтение источника ----------
const raw = fs.readFileSync(SRC, 'utf8');
const startMark = raw.indexOf('## ✂️ КЛИЕНТСКАЯ ЧАСТЬ');
const endMark = raw.indexOf('## ✂️ КОНЕЦ КЛИЕНТСКОЙ ЧАСТИ');
if (startMark < 0 || endMark < 0) {
  console.error('Не нашёл меток клиентской части в ' + SRC + '. Метки: «## ✂️ КЛИЕНТСКАЯ ЧАСТЬ» и «## ✂️ КОНЕЦ КЛИЕНТСКОЙ ЧАСТИ».');
  process.exit(1);
}
const clientLines = raw.slice(startMark, endMark).split('\n').slice(1);

// ---------- таблица тарифов ----------
const TW = 9360;
const COLS = [3960, 1800, 1800, 1800];

const cell = (children, opts = {}) => new TableCell({
  width: { size: opts.w, type: WidthType.DXA },
  shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: "auto" } : undefined,
  margins: { top: 100, bottom: 100, left: 120, right: 120 },
  verticalAlign: opts.valign,
  columnSpan: opts.span,
  children,
});

// строка вида: | **Имя**<br><sub>подпись</sub> | ✓ | ✓ | ✓ |
function splitRow(line) {
  return line.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
}

function buildTariffTable(lines) {
  const rows = [];
  const headFills = [DARK, DARK, "3D3357", ACCENT];
  const cells = lines.map(splitRow);
  // 0 — шапка тарифов, 1 — разделитель, 2 — цены
  const names = cells[0].slice(1).map(c => c.split(/<br\s*\/?>/i));
  const prices = cells[2].slice(1).map(strip);
  rows.push(new TableRow({
    tableHeader: true,
    children: [
      cell([P("", { size: 18 })], { w: COLS[0], fill: DARK }),
      ...names.map((n, i) => cell([
        P(strip(n[0] || ''), { bold: true, size: 24, color: "FFFFFF", align: AlignmentType.CENTER, after: 20 }),
        P(strip(n[1] || ''), { italics: true, size: 17, color: i === 2 ? "EFD9E4" : "CFC8DC", align: AlignmentType.CENTER, after: 60 }),
        P(prices[i] || '', { bold: true, size: 26, color: "FFFFFF", align: AlignmentType.CENTER, after: 0 }),
      ], { w: COLS[i + 1], fill: headFills[i + 1] })),
    ],
  }));

  for (const c of cells.slice(3)) {
    const label = c[0];
    const marks = c.slice(1);
    const isGroup = marks.every(m => m === '');
    if (isGroup) {
      rows.push(new TableRow({
        children: [cell([P(strip(label), { bold: true, size: 17, color: ACCENT, caps: true, after: 0 })],
          { w: TW, fill: LIGHT, span: 4 })],
      }));
      continue;
    }
    const parts = label.split(/<br\s*\/?>/i);
    const name = strip(parts[0]);
    const sub = parts[1] ? strip(parts[1]) : '';
    const isTick = marks.every(m => m === '✓' || m === '—');
    rows.push(new TableRow({
      children: [
        cell([
          P(name, { bold: true, size: 21, after: sub ? 40 : 0 }),
          ...(sub ? [P(sub, { size: 17, color: GREY, after: 0 })] : []),
        ], { w: COLS[0] }),
        ...marks.map((m, i) => {
          const v = strip(m);
          const on = v === '✓';
          return cell([P(v, {
            align: AlignmentType.CENTER,
            bold: isTick ? on : /\d/.test(v) || v.includes('['),
            size: isTick ? (on ? 24 : 22) : 20,
            color: isTick ? (on ? ACCENT : "B9B3C4") : (/\d|\[/.test(v) ? ACCENT : "1A1A1A"),
            after: 0,
          })], { w: COLS[i + 1], valign: "center" });
        }),
      ],
    }));
  }
  return new Table({
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
    rows,
  });
}

// ---------- рендер клиентской части ----------
const body = [];
let titleDone = false;
let tableBuf = null;

const flushTable = () => {
  if (tableBuf && tableBuf.length > 3) body.push(buildTariffTable(tableBuf));
  tableBuf = null;
};

for (let i = 0; i < clientLines.length; i++) {
  const line = clientLines[i];
  const t = line.trim();

  if (t.startsWith('|')) { (tableBuf = tableBuf || []).push(t); continue; }
  flushTable();

  if (!t) continue;
  if (t === '---') { body.push(RULE()); continue; }

  // главный заголовок продукта
  if (t.startsWith('# ')) {
    body.push(new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: strip(t.slice(2)), bold: true, size: 56, color: DARK, font: "Georgia" })],
    }));
    titleDone = true;
    continue;
  }
  if (t.startsWith('## ')) {
    const h = strip(t.slice(3));
    body.push(/^Программа|^Тарифы/.test(h) ? H1(h) : H2(h));
    continue;
  }
  if (t.startsWith('### ')) { body.push(H3(strip(t.slice(4)))); continue; }

  // цитата Виолы
  if (t.startsWith('> ')) {
    const q = t.slice(2).trim();
    const isAttr = /^\*[^*]+\*$/.test(q);
    body.push(P(strip(q), isAttr
      ? { italics: true, size: 20, color: GREY, after: 200 }
      : { bold: true, size: 24, color: DARK, shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" }, after: 40 }));
    continue;
  }

  // маркированный список: «— текст» или «— **лид.** текст»
  if (/^—\s/.test(t)) {
    body.push(BULLET_RUNS(inline(t.replace(/^—\s*/, ''))));
    continue;
  }

  // надзаголовочная плашка (до титула)
  if (!titleDone && /^\*\*[^*]+\*\*$/.test(t)) {
    body.push(P(strip(t), { bold: true, size: 19, color: ACCENT, caps: true, after: 100 }));
    continue;
  }

  // строки лекции: *Осваиваете:* … / *В отношениях:* …
  const lect = t.match(/^\*([^*:]+):\*\s*(.+)$/);
  if (lect) {
    const lead = lect[1] + ': ';
    const color = lect[1] === 'Осваиваете' ? ACCENT : DARK;
    body.push(RUNS([{ t: lead, b: true, c: color }, ...inline(lect[2])], { after: 60 }));
    continue;
  }

  // заголовок лекции
  if (/^\*\*Лекция \d+\./.test(t)) { body.push(H3(strip(t))); continue; }

  // целиком курсивная строка — сноска
  if (/^\*[^*]+\*$/.test(t)) { body.push(P(strip(t), { italics: true, color: GREY, after: 100 })); continue; }

  // целиком жирная строка — акцент
  if (/^\*\*[^*]+\*\*$/.test(t)) {
    const isPromise = !titleDone || body.length < 6;
    body.push(P(strip(t), isPromise
      ? { bold: true, size: 26, color: DARK, after: 100 }
      : { bold: true, shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" }, after: 160 }));
    continue;
  }

  body.push(RUNS(inline(t)));
}
flushTable();

// ---------- служебный блок ----------
const internal = [];
const internalStart = raw.indexOf('### На визирование Виоле');
if (internalStart > 0) {
  const tail = raw.slice(internalStart).split('\n');
  internal.push(new Paragraph({ children: [new PageBreak()] }));
  internal.push(H1('Для команды: что осталось закрыть'));
  internal.push(P('Этот раздел клиенту не показываем.', { italics: true, color: GREY, after: 160 }));
  for (const line of tail) {
    const t = line.trim();
    if (!t || t === '---') continue;
    if (t.startsWith('### ')) { internal.push(H3(strip(t.slice(4)))); continue; }
    if (/^\d+[а-я]?\.\s/.test(t) || /^[-–]\s/.test(t)) {
      internal.push(BULLET_RUNS(inline(t.replace(/^\d+[а-я]?\.\s*/, '').replace(/^[-–]\s*/, ''))));
      continue;
    }
    if (t.startsWith('*') && t.endsWith('*')) continue;
    internal.push(RUNS(inline(t)));
  }
}

// ---------- документ ----------
const doc = new Document({
  numbering,
  styles: { default: { document: { run: { font: "Georgia", size: 22 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },            // A4
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 },
      },
    },
    children: [
      P("ПРЕЗЕНТАЦИЯ ПРОДУКТА · ЧЕРНОВИК ПОД КАСТДЕВ · СОБРАНО ИЗ " + path.basename(SRC).toUpperCase(),
        { size: 17, color: GOLD, caps: true, after: 240 }),
      ...body,
      ...internal,
    ],
  }],
});

fs.mkdirSync(path.dirname(OUT), { recursive: true });
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log('собрано: ' + OUT + ' (из ' + SRC + ')');
});
