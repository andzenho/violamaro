#!/usr/bin/env node
/*
 * sait.js — открыть сайт реальным браузером (Chromium) и вытащить сырьё:
 *   - читаемый текст в порядке чтения (как видит человек);
 *   - карту структуры (заголовки h1–h4, кнопки/CTA, формы, найденные цены);
 *   - список ссылок с якорным текстом;
 *   - (опционально) полностраничный скриншот.
 *
 * Зачем не WebFetch: WebFetch не рендерит JS и не видит порядок/оформление.
 * Здесь настоящий Chromium — Tilda/Taplink/SPA открываются как у человека.
 *
 * Среда: рассчитан на облако Claude Code (Chromium предустановлен в /opt/pw-browsers).
 * В отличие от /transkript, сайты из облака грузятся нормально — гонять локально не нужно.
 * Перед первым запуском в свежей сессии: bash skripty/sait_setup.sh
 *
 * Использование:
 *   node skripty/sait.js <url> [--out FILE.md] [--shot FILE.png] [--no-shot] [--full]
 *     --out    куда сохранить markdown (иначе печатает в stdout)
 *     --shot   путь для скриншота (по умолчанию рядом с --out или во временную папку)
 *     --no-shot  не делать скриншот
 *     --full   скриншот всей страницы целиком (по умолчанию — первый экран 1366x900)
 */

const fs = require('fs');
const path = require('path');

function findChromium() {
  const base = '/opt/pw-browsers';
  if (fs.existsSync(base)) {
    const dirs = fs.readdirSync(base)
      .filter(d => d.startsWith('chromium-') && !d.includes('headless'))
      .sort();
    for (const d of dirs.reverse()) {
      const p = path.join(base, d, 'chrome-linux', 'chrome');
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined; // пусть playwright ищет сам (локальная машина)
}

function parseArgs(argv) {
  const a = { url: null, out: null, shot: null, noShot: false, full: false };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === '--out') a.out = argv[++i];
    else if (v === '--shot') a.shot = argv[++i];
    else if (v === '--no-shot') a.noShot = true;
    else if (v === '--full') a.full = true;
    else if (!a.url && !v.startsWith('--')) a.url = v;
  }
  return a;
}

function slugify(s) {
  return (s || 'sait').toLowerCase()
    .replace(/https?:\/\//, '').replace(/[^a-z0-9а-я]+/gi, '-')
    .replace(/^-+|-+$/g, '').slice(0, 60) || 'sait';
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.url) {
    console.error('Укажи URL: node skripty/sait.js <url> [--out FILE.md] [--shot FILE.png]');
    process.exit(2);
  }
  let url = args.url;
  if (!/^https?:\/\//i.test(url)) url = 'https://' + url;

  let chromium;
  try { ({ chromium } = require('playwright-core')); }
  catch (e) {
    console.error('Нет playwright-core. Сначала: bash skripty/sait_setup.sh');
    process.exit(3);
  }

  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy || null;
  const launchArgs = ['--no-sandbox', '--disable-dev-shm-usage'];
  if (proxy) {
    // В облаке трафик идёт через MITM-прокси. Chromium 141 по умолчанию шлёт
    // пост-квантовый ключ (большой ClientHello TLS1.3), который прокси сбрасывает
    // (ERR_CONNECTION_RESET). Форсируем TLS1.2 и отключаем h2/QUIC — рукопожатие
    // становится маленьким и проходит. CA прокси должен быть в NSS (см. sait_setup.sh).
    launchArgs.push('--disable-quic', '--disable-http2', '--ssl-version-max=tls1.2');
  }

  const browser = await chromium.launch({
    executablePath: findChromium(),
    proxy: proxy ? { server: proxy } : undefined,
    args: launchArgs,
  });
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: 'ru-RU' });
  const page = await ctx.newPage();

  const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  // дать догрузиться динамике
  await page.waitForTimeout(4000);
  try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}

  const status = resp ? resp.status() : 0;
  const finalUrl = page.url();

  const data = await page.evaluate(() => {
    const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const meta = (n) => document.querySelector(`meta[name="${n}"]`)?.content
      || document.querySelector(`meta[property="${n}"]`)?.content || null;

    // Заголовки в порядке появления
    const headings = [...document.querySelectorAll('h1,h2,h3,h4')]
      .map(h => ({ level: +h.tagName[1], text: clean(h.innerText) }))
      .filter(h => h.text);

    // Кнопки / CTA
    const ctaSel = 'button, a.btn, a.button, [role="button"], input[type="submit"], .tn-atom__button';
    const ctas = [...new Set([...document.querySelectorAll(ctaSel)]
      .map(b => clean(b.innerText || b.value)).filter(Boolean))].slice(0, 40);

    // Формы (поля ввода → намёк на анкету/подписку)
    const forms = [...document.querySelectorAll('form')].map(f => {
      const fields = [...f.querySelectorAll('input,textarea,select')]
        .map(i => i.getAttribute('placeholder') || i.getAttribute('name') || i.type)
        .filter(Boolean);
      return { fields: [...new Set(fields)].slice(0, 15) };
    }).filter(f => f.fields.length);

    // Ссылки
    const links = [...new Set([...document.querySelectorAll('a[href]')]
      .map(a => `${clean(a.innerText).slice(0, 80)} → ${a.href}`)
      .filter(x => !x.startsWith(' →')))].slice(0, 120);

    // Цены: числа рядом с валютой
    const bodyText = document.body.innerText || '';
    const prices = [...new Set((bodyText.match(/[\d][\d\s.,]*\s*(?:₽|руб|р\.|rub|\$|€|eur|usd)/gi) || [])
      .map(s => s.replace(/\s+/g, ' ').trim()))].slice(0, 30);

    return {
      title: document.title,
      ogTitle: meta('og:title'),
      description: meta('description') || meta('og:description'),
      canonical: document.querySelector('link[rel="canonical"]')?.href || null,
      headings, ctas, forms, links, prices,
      fullText: bodyText,
    };
  });

  // Скриншот
  let shotPath = null;
  if (!args.noShot) {
    shotPath = args.shot
      || (args.out ? args.out.replace(/\.md$/i, '') + '.png' : path.join(require('os').tmpdir(), slugify(data.title || finalUrl) + '.png'));
    await page.screenshot({ path: shotPath, fullPage: !!args.full });
  }
  await browser.close();

  // Сборка markdown
  const L = [];
  L.push(`# ${data.title || finalUrl}`, '');
  L.push(`- URL: ${finalUrl}`);
  L.push(`- HTTP: ${status}`);
  if (data.canonical) L.push(`- canonical: ${data.canonical}`);
  if (shotPath) L.push(`- Скриншот: ${shotPath}`);
  L.push('');
  if (data.description) { L.push('## Meta-описание', '', data.description, ''); }

  L.push('## Структура (заголовки)', '');
  if (data.headings.length) for (const h of data.headings) L.push(`${'  '.repeat(h.level - 1)}- h${h.level}: ${h.text}`);
  else L.push('_нет заголовков h1–h4_');
  L.push('');

  if (data.ctas.length) { L.push('## Кнопки / CTA', ''); for (const c of data.ctas) L.push(`- ${c}`); L.push(''); }
  if (data.prices.length) { L.push('## Найденные цены', ''); for (const p of data.prices) L.push(`- ${p}`); L.push(''); }
  if (data.forms.length) {
    L.push('## Формы', '');
    data.forms.forEach((f, i) => L.push(`- Форма ${i + 1}: ${f.fields.join(', ')}`));
    L.push('');
  }

  L.push('## Полный текст (в порядке чтения)', '', data.fullText.trim(), '');

  if (data.links.length) { L.push('## Ссылки', ''); for (const ln of data.links) L.push(`- ${ln}`); L.push(''); }

  const md = L.join('\n');
  if (args.out) {
    fs.mkdirSync(path.dirname(args.out), { recursive: true });
    fs.writeFileSync(args.out, md);
    console.error(`Сохранено: ${args.out}`);
    if (shotPath) console.error(`Скриншот: ${shotPath}`);
  } else {
    process.stdout.write(md);
    if (shotPath) console.error(`\nСкриншот: ${shotPath}`);
  }
}

main().catch(e => { console.error('ОШИБКА:', e.message.split('\n')[0]); process.exit(1); });
