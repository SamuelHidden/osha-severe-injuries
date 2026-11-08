// Экспорт дашбордов в PDF: A4 альбомный, светлая тема, номера страниц.
//
//     node Report/export_pdf.mjs
//
// Нужны Node.js 22+ (встроенные fetch и WebSocket) и Google Chrome или Chromium;
// путь к браузеру можно задать переменной окружения CHROME. PDF сохраняются в Report/pdf.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'pdf');

const PAGES = [
  ['index', '00_overview', 'Обзор'],
  ['01_body_parts', '01_body_parts', 'Части тела'],
  ['02_sources', '02_sources', 'Источники травмы'],
  ['03_industries', '03_industries', 'Отрасли'],
  ['04_seasons', '04_seasons', 'Сезоны и дни недели'],
  ['05_nature', '05_nature', 'Типы травм'],
];

const CHROME =
  process.env.CHROME ||
  [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ].find(existsSync);
if (!CHROME) throw new Error('Не найден Chrome: укажите путь в переменной CHROME');

// Лист A4 альбомный, поля как в @page (style.css): 10 мм по бокам и сверху, 14 мм снизу под номер страницы.
const MM = 1 / 25.4;
const PAPER = { width: 297 * MM, height: 210 * MM, top: 10 * MM, side: 10 * MM, bottom: 14 * MM };
// Масштаб 0,7: вёрстка шириной ~1496 px — ряд карточек помещается на лист целиком.
// Страница открывается сразу в режиме печати, поэтому графики рисуются под эту же ширину.
const SCALE = 0.7;
const VIEWPORT = Math.round(((PAPER.width - 2 * PAPER.side) * 96) / SCALE);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const footer = (title) => `
  <div style="width:100%; padding:0 10mm; display:flex; justify-content:space-between;
              font:7.5px -apple-system, system-ui, 'Segoe UI', sans-serif; color:#898781;">
    <span>Тяжёлые производственные травмы в США · OSHA, 2015–2025 · ${title}</span>
    <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
  </div>`;

async function main() {
  mkdirSync(OUT, { recursive: true });
  const profile = mkdtempSync(join(tmpdir(), 'report-pdf-'));
  const port = 9300 + Math.floor(Math.random() * 500);
  const chrome = spawn(
    CHROME,
    ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank'],
    { stdio: 'ignore' }
  );

  try {
    let target;
    for (let i = 0; i < 100 && !target; i++) {
      try {
        const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
        target = list.find((t) => t.type === 'page');
      } catch {
        /* браузер ещё запускается */
      }
      if (!target) await sleep(100);
    }
    if (!target) throw new Error('Chrome не ответил на порту отладки');

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.addEventListener('open', resolve);
      ws.addEventListener('error', reject);
    });

    let id = 0;
    const pending = new Map();
    const loaded = [];
    const errors = [];
    ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      } else if (msg.method === 'Page.loadEventFired') {
        loaded.splice(0).forEach((fn) => fn());
      } else if (msg.method === 'Runtime.exceptionThrown') {
        errors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
      }
    });
    const send = (method, params = {}) =>
      new Promise((resolve, reject) => {
        const n = ++id;
        pending.set(n, { resolve, reject });
        ws.send(JSON.stringify({ id: n, method, params }));
      });

    await send('Page.enable');
    await send('Runtime.enable');
    await send('Emulation.setDeviceMetricsOverride', { width: VIEWPORT, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send('Emulation.setEmulatedMedia', { media: 'print', features: [{ name: 'prefers-color-scheme', value: 'light' }] });

    for (const [page, name, title] of PAGES) {
      const done = new Promise((resolve) => loaded.push(resolve));
      await send('Page.navigate', { url: pathToFileURL(join(HERE, `${page}.html`)).href });
      await done;
      await sleep(600); // графики дорисовываются после загрузки

      const { data } = await send('Page.printToPDF', {
        paperWidth: PAPER.width,
        paperHeight: PAPER.height,
        marginTop: PAPER.top,
        marginBottom: PAPER.bottom,
        marginLeft: PAPER.side,
        marginRight: PAPER.side,
        scale: SCALE,
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: '<span></span>',
        footerTemplate: footer(title),
      });
      writeFileSync(join(OUT, `${name}.pdf`), Buffer.from(data, 'base64'));
      console.log(`OK: Report/pdf/${name}.pdf`);
    }

    if (errors.length) console.error('Ошибки JavaScript на страницах:\n' + errors.join('\n'));
    ws.close();
  } finally {
    chrome.kill();
    await sleep(200);
    rmSync(profile, { recursive: true, force: true });
  }
}

await main();
