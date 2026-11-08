/*
 * Мини-библиотека графиков для дашбордов отчёта: HTML/SVG без внешних зависимостей,
 * чтобы страницы открывались двойным щелчком и без интернета.
 *
 * Report.hbar      — горизонтальные столбцы (один или несколько рядов на строку)
 * Report.donut     — кольцевая диаграмма с легендой и числом в центре
 * Report.lineChart — линии по годам с перекрестием и подсказкой
 * Report.sparkline — маленький тренд для KPI
 * Report.card      — карточка с переключателем «График / Таблица»
 */
(function () {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';

  // ---------- Форматирование ----------

  const nfInt = new Intl.NumberFormat('ru-RU');
  const nfFixed = {};
  const fmt = {
    int: (n) => nfInt.format(n),
    num: (x, d = 1) =>
      (nfFixed[d] ??= new Intl.NumberFormat('ru-RU', { minimumFractionDigits: d, maximumFractionDigits: d })).format(x),
    pct: (x, d = 1) => fmt.num(x, d) + '%',
    plural(n, [one, few, many]) {
      const a = Math.abs(n) % 100;
      const b = a % 10;
      if (a > 10 && a < 20) return many;
      if (b === 1) return one;
      if (b > 1 && b < 5) return few;
      return many;
    },
  };
  const casesWord = (n) => fmt.plural(n, ['случай', 'случая', 'случаев']);

  // ---------- DOM ----------

  function assign(el, attrs) {
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') el.setAttribute('class', v);
      else if (k === 'text') el.textContent = v;
      else if (k === 'style') {
        for (const [p, val] of Object.entries(v)) {
          if (p.startsWith('--')) el.style.setProperty(p, val);
          else el.style[p] = val;
        }
      } else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    return el;
  }

  function append(el, children) {
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      el.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return el;
  }

  const h = (tag, attrs, ...children) => append(assign(document.createElement(tag), attrs), children);
  const s = (tag, attrs, ...children) => append(assign(document.createElementNS(SVG_NS, tag), attrs), children);

  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  function luminance(hex) {
    const m = hex.replace('#', '').match(/.{2}/g);
    if (!m) return 0.5;
    const [r, g, b] = m.map((x) => {
      const c = parseInt(x, 16) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /** Цвет подписи внутри заливки: белый или чернила — что контрастнее. */
  function inkOn(hex) {
    const L = luminance(hex);
    const vsWhite = 1.05 / (L + 0.05);
    const vsInk = (L + 0.05) / (luminance('#0b0b0b') + 0.05);
    return vsWhite >= vsInk ? '#ffffff' : '#0b0b0b';
  }

  // ---------- Подсказка ----------

  let tipEl = null;

  function showTip(nodes, x, y) {
    if (!tipEl) {
      tipEl = h('div', { class: 'tooltip', role: 'tooltip', hidden: true });
      document.body.append(tipEl);
    }
    tipEl.replaceChildren(...nodes);
    tipEl.hidden = false;
    const r = tipEl.getBoundingClientRect();
    const pad = 14;
    let left = x + pad;
    let top = y + pad;
    if (left + r.width > innerWidth - 8) left = x - r.width - pad;
    if (top + r.height > innerHeight - 8) top = y - r.height - pad;
    tipEl.style.left = Math.max(8, left) + 'px';
    tipEl.style.top = Math.max(8, top) + 'px';
  }

  function showTipAt(el, nodes) {
    const r = el.getBoundingClientRect();
    showTip(nodes, r.left + Math.min(r.width * 0.6, 360), r.top + r.height - 6);
  }

  const hideTip = () => tipEl && (tipEl.hidden = true);

  const tt = {
    title: (t) => h('div', { class: 'tt-title', text: t }),
    sub: (t) => h('div', { class: 'tt-sub', text: t }),
    kv: (k, v) => h('div', { class: 'tt-kv' }, h('span', { text: k }), h('span', { text: v })),
    series: (color, value, name, kind = 'line') =>
      h(
        'div',
        { class: 'tt-row' },
        h('span', { class: kind === 'line' ? 'key-line' : 'key-rect', style: { background: color } }),
        h('span', { class: 'tt-value', text: value }),
        h('span', { class: 'tt-name', text: name })
      ),
  };

  // ---------- Перерисовка при изменении размера и темы ----------

  const themeListeners = new Set();
  const onThemeChange = (fn) => themeListeners.add(fn);

  function watchWidth(el, fn) {
    let last = el.clientWidth;
    let raf = 0;
    new ResizeObserver(() => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const w = el.clientWidth;
        if (w > 0 && Math.abs(w - last) >= 1) {
          last = w;
          fn();
        }
      });
    }).observe(el);
  }

  // ---------- Легенда ----------

  /** items: [{key, label, color}], kind: 'rect' | 'line' */
  function legend(items, { kind = 'rect', onFocus } = {}) {
    const ul = h('ul', { class: 'legend' + (onFocus ? ' interactive' : '') });
    for (const it of items) {
      const li = h(
        'li',
        { 'data-key': it.key, tabindex: onFocus ? 0 : null },
        h('span', { class: kind === 'line' ? 'key-line' : 'key-rect', style: { background: it.color } }),
        h('span', { text: it.label })
      );
      if (onFocus) {
        li.addEventListener('pointerenter', () => onFocus(it.key));
        li.addEventListener('pointerleave', () => onFocus(null));
        li.addEventListener('focus', () => onFocus(it.key));
        li.addEventListener('blur', () => onFocus(null));
      }
      ul.append(li);
    }
    ul.setFocus = (key) => {
      ul.classList.toggle('has-focus', key != null);
      for (const li of ul.children) li.classList.toggle('is-focus', li.dataset.key === key);
    };
    return ul;
  }

  // ---------- Горизонтальные столбцы ----------

  /**
   * rows:   [{label, rank?, group?, values: [{value, color, text, extra?}]}]
   * tip:    row => Node[] — содержимое подсказки
   * reserve — место справа под подпись значения (CSS-длина)
   */
  function hbar(el, { rows, max, tip, rank = true, thin = false, reserve = '8rem', onEnter, onLeave }) {
    const top = max ?? Math.max(...rows.flatMap((r) => r.values.map((v) => v.value)));
    const root = h('div', { class: ['hbar', rank ? '' : 'no-rank', thin ? 'thin' : ''].join(' ').trim(), role: 'list' });

    for (const r of rows) {
      const track = h('div', { class: 'hbar-track' });
      for (const v of r.values) {
        const frac = Math.max(0, v.value / top);
        track.append(
          h(
            'div',
            { class: 'hbar-line' },
            h('div', {
              class: 'hbar-bar',
              style: { width: `calc((100% - ${reserve}) * ${frac.toFixed(4)})`, background: v.color },
            }),
            h('span', { class: 'hbar-value' }, v.text, v.extra ? h('span', { class: 'muted', text: ' · ' + v.extra }) : null)
          )
        );
      }
      const aria = r.label + ': ' + r.values.map((v) => (v.name ? v.name + ' ' : '') + v.text + (v.extra ? ', ' + v.extra : '')).join('; ');
      const row = h(
        'div',
        { class: 'hbar-row', role: 'listitem', tabindex: 0, 'data-group': r.group, 'aria-label': aria },
        rank ? h('span', { class: 'hbar-rank', text: r.rank }) : null,
        h('span', { class: 'hbar-label', text: r.label }),
        track
      );
      if (tip) {
        row.addEventListener('pointermove', (e) => showTip(tip(r), e.clientX, e.clientY));
        row.addEventListener('focus', () => showTipAt(row, tip(r)));
      }
      row.addEventListener('pointerenter', () => onEnter?.(r));
      row.addEventListener('focus', () => onEnter?.(r));
      row.addEventListener('pointerleave', () => (hideTip(), onLeave?.(r)));
      row.addEventListener('blur', () => (hideTip(), onLeave?.(r)));
      root.append(row);
    }

    el.replaceChildren(root);
    return {
      setFocus(group) {
        if (group == null) delete root.dataset.focus;
        else root.dataset.focus = group;
        for (const row of root.children) row.classList.toggle('is-focus', group != null && row.dataset.group === group);
      },
    };
  }

  // ---------- Кольцевая диаграмма ----------

  function arcPath(cx, cy, R, r, a0, a1) {
    const large = a1 - a0 > Math.PI ? 1 : 0;
    const pt = (rad, a) => `${(cx + rad * Math.cos(a)).toFixed(2)},${(cy + rad * Math.sin(a)).toFixed(2)}`;
    return `M${pt(R, a0)} A${R},${R} 0 ${large} 1 ${pt(R, a1)} L${pt(r, a1)} A${r},${r} 0 ${large} 0 ${pt(r, a0)} Z`;
  }

  /**
   * items: [{key, label, sub?, value, pct, colorVar}]
   * center: {value, label} — что показано в центре без наведения
   * onFocus(key|null) — наведение на сегмент или строку легенды
   */
  function donut(el, { items, center, onFocus, labelMin = 6 }) {
    const width = el.clientWidth || 320;
    const size = Math.round(Math.min(260, Math.max(190, width)));
    const R = size / 2 - 2;
    const r0 = R * 0.62;
    const cx = size / 2;
    const cy = size / 2;
    const total = items.reduce((a, it) => a + it.value, 0);

    const svg = s('svg', {
      class: 'donut-svg',
      width: size,
      height: size,
      viewBox: `0 0 ${size} ${size}`,
      role: 'img',
      'aria-label': items.map((it) => `${it.label} ${fmt.pct(it.pct)}`).join(', '),
    });
    const segs = s('g');
    const labels = s('g');
    svg.append(segs, labels);

    let a = -Math.PI / 2;
    for (const it of items) {
      const a1 = a + (it.value / total) * Math.PI * 2;
      segs.append(
        s('path', {
          d: arcPath(cx, cy, R, r0, a, a1),
          'data-key': it.key,
          style: { fill: `var(${it.colorVar})`, stroke: 'var(--surface)', strokeWidth: '2px', strokeLinejoin: 'round' },
          onpointerenter: () => setFocus(it.key),
          onpointerleave: () => setFocus(null),
        })
      );
      if (it.pct >= labelMin) {
        const mid = (a + a1) / 2;
        const rm = (R + r0) / 2;
        labels.append(
          s('text', {
            class: 'donut-seg-label',
            x: (cx + rm * Math.cos(mid)).toFixed(1),
            y: (cy + rm * Math.sin(mid)).toFixed(1),
            'text-anchor': 'middle',
            'dominant-baseline': 'central',
            style: { fill: inkOn(cssVar(it.colorVar)) },
            text: fmt.pct(it.pct),
          })
        );
      }
      a = a1;
    }

    const cValue = s('text', { class: 'donut-center-value', x: cx, y: cy - 6, 'text-anchor': 'middle' });
    const cLabel = s('text', { class: 'donut-center-label', x: cx, y: cy + 16, 'text-anchor': 'middle' });
    const cSub = s('text', { class: 'donut-center-label', x: cx, y: cy + 33, 'text-anchor': 'middle', style: { fill: 'var(--muted)' } });
    svg.append(cValue, cLabel, cSub);

    const list = h('ul', { class: 'donut-legend' });
    for (const it of items) {
      const li = h(
        'li',
        { tabindex: 0, 'data-key': it.key, 'aria-label': `${it.label}: ${fmt.pct(it.pct)}, ${fmt.int(it.value)} ${casesWord(it.value)}` },
        h('span', { class: 'key-rect', style: { background: `var(${it.colorVar})` } }),
        h('span', { text: it.label }),
        h('span', { class: 'pct', text: fmt.pct(it.pct) }),
        h('span', { class: 'cases', text: fmt.int(it.value) })
      );
      li.addEventListener('pointerenter', () => setFocus(it.key));
      li.addEventListener('pointerleave', () => setFocus(null));
      li.addEventListener('focus', () => setFocus(it.key));
      li.addEventListener('blur', () => setFocus(null));
      list.append(li);
    }

    function setCenter(it) {
      cValue.textContent = it ? fmt.pct(it.pct) : center.value;
      cLabel.textContent = it ? it.label : center.label;
      cSub.textContent = it ? `${fmt.int(it.value)} ${casesWord(it.value)}` : center.sub || '';
    }

    function setFocus(key, { silent = false } = {}) {
      svg.classList.toggle('has-focus', key != null);
      list.classList.toggle('has-focus', key != null);
      for (const p of segs.children) p.classList.toggle('is-focus', p.dataset.key === key);
      for (const li of list.children) li.classList.toggle('is-focus', li.dataset.key === key);
      setCenter(items.find((it) => it.key === key));
      if (!silent) onFocus?.(key);
    }

    setCenter(null);
    el.replaceChildren(h('div', { class: 'donut-wrap' }, svg, list));
    return { setFocus };
  }

  // ---------- Линейный график ----------

  function niceStep(max, desired) {
    const candidates = [];
    for (let e = Math.floor(Math.log10(max / 20)); e <= Math.ceil(Math.log10(max)); e++) {
      for (const m of [1, 2, 5]) candidates.push(m * 10 ** e);
    }
    let best = candidates[0];
    let bestDiff = Infinity;
    for (const st of candidates) {
      const diff = Math.abs(Math.ceil(max / st) - desired);
      if (diff < bestDiff) (best = st), (bestDiff = diff);
    }
    return best;
  }

  /**
   * x:      [2015, 2016, ...]
   * series: [{key, name, color, values}]
   * xLabel: x => подпись оси; xTitle: x => заголовок подсказки
   */
  function lineChart(el, { x, series, height = 320, yFormat, xLabel = String, xTitle = String, valueFormat }) {
    const W = Math.max(280, el.clientWidth || 600);
    const H = height;
    const m = { top: 10, right: 54, bottom: 28, left: 42 };
    const iw = W - m.left - m.right;
    const ih = H - m.top - m.bottom;
    const n = x.length;

    const maxV = Math.max(...series.flatMap((sr) => sr.values));
    const step = niceStep(maxV, Math.max(4, Math.round(ih / 42)));
    const yMax = Math.ceil(maxV / step) * step;
    const xs = (i) => m.left + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
    const ys = (v) => m.top + ih - (v / yMax) * ih;

    const wrap = h('div', { class: 'line-chart' });
    const leg = legend(
      series.map((sr) => ({ key: sr.key, label: sr.name, color: sr.color })),
      { kind: 'line', onFocus: (k) => setFocus(k) }
    );

    const svg = s('svg', {
      viewBox: `0 0 ${W} ${H}`,
      height: H,
      role: 'img',
      'aria-label': series
        .map((sr) => `${sr.name}: ${valueFormat(sr.values[0])} в ${x[0]}, ${valueFormat(sr.values[n - 1])} в ${x[n - 1]}`)
        .join('; '),
    });

    // Сетка и ось Y
    const grid = s('g');
    for (let v = 0; v <= yMax + 1e-9; v += step) {
      const y = ys(v);
      grid.append(
        s('line', { x1: m.left, x2: m.left + iw, y1: y, y2: y, style: { stroke: v === 0 ? 'var(--axis)' : 'var(--grid)', strokeWidth: '1px' } }),
        s('text', { class: 'tick', x: m.left - 8, y, 'text-anchor': 'end', 'dominant-baseline': 'central', text: yFormat(v) })
      );
    }
    // Ось X
    const every = iw / Math.max(1, n - 1) < 40 ? 2 : 1;
    for (let i = 0; i < n; i++) {
      if ((n - 1 - i) % every) continue;
      grid.append(s('text', { class: 'tick', x: xs(i), y: m.top + ih + 18, 'text-anchor': 'middle', text: xLabel(x[i]) }));
    }
    svg.append(grid);

    // Линии
    const lines = s('g');
    for (const sr of series) {
      const d = sr.values.map((v, i) => `${i ? 'L' : 'M'}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join('');
      lines.append(
        s(
          'g',
          { class: 'series', 'data-key': sr.key },
          s('path', { d, style: { fill: 'none', stroke: sr.color, strokeWidth: '2px', strokeLinejoin: 'round', strokeLinecap: 'round' } }),
          s('circle', { cx: xs(n - 1), cy: ys(sr.values[n - 1]), r: 4, style: { fill: sr.color, stroke: 'var(--surface)', strokeWidth: '2px' } })
        )
      );
    }
    svg.append(lines);

    // Подписи значений на правом конце, без наложений
    const gap = 15;
    const ends = series
      .map((sr) => ({ sr, y0: ys(sr.values[n - 1]), y: ys(sr.values[n - 1]) }))
      .sort((p, q) => p.y0 - q.y0);
    for (let k = 1; k < ends.length; k++) ends[k].y = Math.max(ends[k].y, ends[k - 1].y + gap);
    let limit = m.top + ih + 4;
    for (let k = ends.length - 1; k >= 0; k--) {
      ends[k].y = Math.min(ends[k].y, limit);
      limit = ends[k].y - gap;
    }
    const endLabels = s('g');
    const lx = xs(n - 1) + 12;
    for (const e of ends) {
      const g = s('g', { class: 'series', 'data-key': e.sr.key });
      if (Math.abs(e.y - e.y0) > 2) {
        g.append(s('path', { d: `M${xs(n - 1) + 6},${e.y0} L${lx - 3},${e.y}`, style: { stroke: 'var(--axis)', strokeWidth: '1px', fill: 'none' } }));
      }
      g.append(s('text', { class: 'end-label', x: lx, y: e.y, 'dominant-baseline': 'central', text: valueFormat(e.sr.values[n - 1]) }));
      endLabels.append(g);
    }
    svg.append(endLabels);

    // Перекрестие и подсказка
    const cross = s('line', { y1: m.top, y2: m.top + ih, style: { stroke: 'var(--muted)', strokeWidth: '1px', visibility: 'hidden' } });
    const dots = s('g', { style: { visibility: 'hidden' } });
    const dotEls = series.map((sr) => {
      const c = s('circle', { r: 4.5, style: { fill: sr.color, stroke: 'var(--surface)', strokeWidth: '2px' } });
      dots.append(c);
      return c;
    });
    const overlay = s('rect', {
      x: m.left - 12,
      y: m.top,
      width: iw + 24,
      height: ih,
      tabindex: 0,
      'aria-label': 'Значения по годам: стрелки влево и вправо',
      style: { fill: 'transparent', cursor: 'crosshair', outline: 'none' },
    });
    svg.append(cross, dots, overlay);

    let idx = -1;
    function showAt(i, clientX, clientY) {
      idx = Math.max(0, Math.min(n - 1, i));
      const cx = xs(idx);
      cross.setAttribute('x1', cx);
      cross.setAttribute('x2', cx);
      cross.style.visibility = 'visible';
      dots.style.visibility = 'visible';
      series.forEach((sr, k) => {
        dotEls[k].setAttribute('cx', cx);
        dotEls[k].setAttribute('cy', ys(sr.values[idx]));
      });
      const rows = series
        .map((sr) => ({ sr, v: sr.values[idx] }))
        .sort((p, q) => q.v - p.v)
        .map(({ sr, v }) => tt.series(sr.color, valueFormat(v), sr.name));
      if (clientX == null) {
        const r = svg.getBoundingClientRect();
        const scale = r.width / W;
        clientX = r.left + cx * scale;
        clientY = r.top + m.top * scale;
      }
      showTip([tt.title(xTitle(x[idx])), ...rows], clientX, clientY);
    }
    function hide() {
      cross.style.visibility = 'hidden';
      dots.style.visibility = 'hidden';
      hideTip();
    }
    const indexFromEvent = (e) => {
      const r = svg.getBoundingClientRect();
      const px = ((e.clientX - r.left) / r.width) * W;
      return Math.round(((px - m.left) / iw) * (n - 1));
    };
    overlay.addEventListener('pointermove', (e) => showAt(indexFromEvent(e), e.clientX, e.clientY));
    overlay.addEventListener('pointerdown', (e) => showAt(indexFromEvent(e), e.clientX, e.clientY));
    overlay.addEventListener('pointerleave', hide);
    overlay.addEventListener('focus', () => showAt(n - 1));
    overlay.addEventListener('blur', hide);
    overlay.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        e.preventDefault();
        showAt(idx + (e.key === 'ArrowRight' ? 1 : -1));
      }
    });

    function setFocus(key) {
      wrap.classList.toggle('has-focus', key != null);
      for (const g of svg.querySelectorAll('.series')) g.classList.toggle('is-focus', g.dataset.key === key);
      leg.setFocus(key);
    }

    wrap.append(leg, svg);
    el.replaceChildren(wrap);
    return { setFocus };
  }

  // ---------- Спарклайн ----------

  function sparkline(el, { values, color = 'var(--accent)' }) {
    const W = Math.max(60, el.clientWidth || 200);
    const H = el.clientHeight || 36;
    const p = 5;
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    const xs = (i) => p + (i / (values.length - 1)) * (W - 2 * p);
    const ys = (v) => H - p - ((v - lo) / (hi - lo || 1)) * (H - 2 * p);
    const d = values.map((v, i) => `${i ? 'L' : 'M'}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join('');
    const last = values.length - 1;
    el.replaceChildren(
      s(
        'svg',
        { viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' },
        s('path', { d, style: { fill: 'none', stroke: 'var(--muted)', strokeWidth: '1.5px', strokeLinejoin: 'round', strokeLinecap: 'round' } }),
        s('circle', { cx: xs(0), cy: ys(values[0]), r: 2.5, style: { fill: 'var(--muted)' } }),
        s('circle', { cx: xs(last), cy: ys(values[last]), r: 4, style: { fill: color, stroke: 'var(--surface)', strokeWidth: '2px' } })
      )
    );
  }

  // ---------- Цветовые шкалы (интерполяция в OKLab) ----------

  const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
  const hexToRgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.replace('#', '').slice(i, i + 2), 16) / 255);
  const toLinear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const fromLinear = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);

  function toOklab(hex) {
    const [r, g, b] = hexToRgb(hex).map(toLinear);
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const q = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [
      0.2104542553 * l + 0.793617785 * m - 0.0040720468 * q,
      1.9779984951 * l - 2.428592205 * m + 0.4505937099 * q,
      0.0259040371 * l + 0.7827717662 * m - 0.808675766 * q,
    ];
  }

  function fromOklab([L, A, B]) {
    const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3;
    const m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3;
    const q = (L - 0.0894841775 * A - 1.291485548 * B) ** 3;
    const rgb = [
      4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * q,
      -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * q,
      -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * q,
    ];
    return '#' + rgb.map((c) => Math.round(clamp(fromLinear(c)) * 255).toString(16).padStart(2, '0')).join('');
  }

  function mixColor(a, b, t) {
    const A = toOklab(a);
    const B = toOklab(b);
    return fromOklab(A.map((v, i) => v + (B[i] - v) * t));
  }

  /** Последовательная шкала: светлое — мало, тёмное — много (в тёмной теме наоборот). */
  function sequentialScale(min, max) {
    const lo = cssVar('--seq-lo');
    const hi = cssVar('--seq-hi');
    return (v) => mixColor(lo, hi, clamp((v - min) / (max - min || 1)));
  }

  /** Расходящаяся шкала: t от −limit до +limit, серая середина. */
  function divergingScale(limit) {
    const neg = cssVar('--div-neg');
    const mid = cssVar('--div-mid');
    const pos = cssVar('--div-pos');
    return (t) => {
      const u = clamp(t / limit, -1, 1);
      return u < 0 ? mixColor(mid, neg, -u) : mixColor(mid, pos, u);
    };
  }

  /** Легенда шкалы: градиент и подписи в долях ширины (0…1). */
  function scaleLegend(color, { from, to, ticks, title }) {
    const stops = Array.from({ length: 11 }, (_, i) => color(from + ((to - from) * i) / 10));
    return h(
      'div',
      { class: 'scale-legend' },
      title ? h('span', { class: 'scale-title', text: title }) : null,
      h(
        'div',
        { class: 'scale-body' },
        h('div', { class: 'scale-bar', style: { background: `linear-gradient(90deg, ${stops.join(', ')})` } }),
        h('div', { class: 'scale-ticks' }, ticks.map((t) => h('span', { style: { left: `${t.at * 100}%` }, text: t.label })))
      )
    );
  }

  // ---------- Тепловая карта ----------

  /**
   * rows: [{label}], cols: [{label}]
   * cell(i, j) → {value, text, color, strong?} | null (нет данных)
   * tip(i, j) → Node[]
   */
  function heatmap(el, { rows, cols, cell, tip, label = 'minmax(7.5rem, 13rem)', minCell = 40 }) {
    const grid = h('div', {
      class: 'heat',
      role: 'table',
      style: { gridTemplateColumns: `${label} repeat(${cols.length}, minmax(${minCell}px, 1fr))` },
    });
    const colHeads = cols.map((c) => h('div', { class: 'heat-col', role: 'columnheader', text: c.label }));
    const rowHeads = rows.map((r) => h('div', { class: 'heat-row', role: 'rowheader', text: r.label }));
    grid.append(h('div', { class: 'heat-corner' }), ...colHeads);

    const hover = (i, j) => {
      rowHeads.forEach((e, k) => e.classList.toggle('is-hover', k === i));
      colHeads.forEach((e, k) => e.classList.toggle('is-hover', k === j));
    };

    rows.forEach((r, i) => {
      const line = h('div', { class: 'heat-line', role: 'row' }, rowHeads[i]);
      cols.forEach((c, j) => {
        const v = cell(i, j);
        const td = h(
          'div',
          {
            class: 'heat-cell' + (v ? '' : ' empty') + (v?.strong ? ' strong' : ''),
            role: 'cell',
            tabindex: v ? 0 : null,
            'aria-label': `${r.label}, ${c.label}: ${v ? v.text : 'нет данных'}`,
            style: v ? { background: v.color, color: inkOn(v.color) } : null,
          },
          v ? v.text : '—'
        );
        if (v && tip) {
          td.addEventListener('pointermove', (e) => (hover(i, j), showTip(tip(i, j), e.clientX, e.clientY)));
          td.addEventListener('focus', () => (hover(i, j), showTipAt(td, tip(i, j))));
        }
        const out = () => (hover(-1, -1), hideTip());
        td.addEventListener('pointerleave', out);
        td.addEventListener('blur', out);
        line.append(td);
      });
      grid.append(line);
    });

    el.replaceChildren(h('div', { class: 'heat-scroll' }, grid));
  }

  // ---------- Вертикальные столбцы ----------

  function niceMax(max, desired = 5) {
    const step = niceStep(max, desired);
    return { max: Math.ceil(max / step) * step, step };
  }

  function columnPath(x, y0, w, y1, r) {
    const rr = Math.min(r, w / 2, Math.max(0, y0 - y1));
    return `M${x},${y0} V${y1 + rr} Q${x},${y1} ${x + rr},${y1} H${x + w - rr} Q${x + w},${y1} ${x + w},${y1 + rr} V${y0} Z`;
  }

  /**
   * items:  [{label, value, color, lo?, hi?, text?}] — lo/hi рисуют доверительный интервал
   * groups: [{label, from, to}] — подписи групп под осью (например, сезоны)
   * ref:    {value, label} — опорная линия (среднее)
   */
  function columns(el, { items, height = 260, yFormat, tip, groups, ref, labelEvery }) {
    const W = Math.max(280, el.clientWidth || 600);
    const m = { top: 20, right: 10, bottom: groups ? 50 : 28, left: 40 };
    const iw = W - m.left - m.right;
    const ih = height - m.top - m.bottom;
    const n = items.length;
    const top = Math.max(...items.map((it) => it.hi ?? it.value), ref?.value ?? 0);
    const { max: yMax, step } = niceMax(top * 1.08, Math.max(3, Math.round(ih / 45)));
    const band = iw / n;
    const bw = Math.min(24, band * 0.62);
    const xc = (i) => m.left + band * (i + 0.5);
    const ys = (v) => m.top + ih - (v / yMax) * ih;
    const showValues = band >= (labelEvery ?? 34);

    const svg = s('svg', {
      viewBox: `0 0 ${W} ${height}`,
      height,
      role: 'img',
      'aria-label': items.map((it) => `${it.label}: ${it.text ?? yFormat(it.value)}`).join(', '),
    });

    for (let v = 0; v <= yMax + 1e-9; v += step) {
      svg.append(
        s('line', { x1: m.left, x2: m.left + iw, y1: ys(v), y2: ys(v), style: { stroke: v === 0 ? 'var(--axis)' : 'var(--grid)', strokeWidth: '1px' } }),
        s('text', { class: 'tick', x: m.left - 8, y: ys(v), 'text-anchor': 'end', 'dominant-baseline': 'central', text: yFormat(v) })
      );
    }

    if (ref) {
      svg.append(
        s('line', { x1: m.left, x2: m.left + iw, y1: ys(ref.value), y2: ys(ref.value), style: { stroke: 'var(--ink-2)', strokeWidth: '1px', opacity: 0.55 } }),
        ref.label ? s('text', { class: 'ref-label', x: m.left + iw, y: ys(ref.value) - 5, 'text-anchor': 'end', text: ref.label }) : null
      );
    }

    const marks = s('g');
    items.forEach((it, i) => {
      const g = s('g', { class: 'col', tabindex: 0, 'aria-label': `${it.label}: ${it.text ?? yFormat(it.value)}` });
      g.append(
        s('rect', { x: m.left + band * i, y: m.top, width: band, height: ih, style: { fill: 'transparent' } }),
        s('path', { d: columnPath(xc(i) - bw / 2, ys(0), bw, ys(it.value), 4), style: { fill: it.color } })
      );
      if (it.lo != null && it.hi != null) {
        const cap = Math.min(8, bw * 0.5);
        g.append(
          s('path', {
            d: `M${xc(i)},${ys(it.lo)} V${ys(it.hi)} M${xc(i) - cap / 2},${ys(it.lo)} H${xc(i) + cap / 2} M${xc(i) - cap / 2},${ys(it.hi)} H${xc(i) + cap / 2}`,
            style: { stroke: 'var(--ink-2)', strokeWidth: '1px', fill: 'none' },
          })
        );
      }
      if (showValues) {
        g.append(s('text', { class: 'col-value', x: xc(i), y: ys(it.hi ?? it.value) - 6, 'text-anchor': 'middle', text: it.text ?? yFormat(it.value) }));
      }
      const xText = band < 30 && it.short ? it.short : it.label;
      g.append(s('text', { class: 'tick', x: xc(i), y: m.top + ih + 17, 'text-anchor': 'middle', text: xText }));
      if (tip) {
        g.addEventListener('pointermove', (e) => showTip(tip(it, i), e.clientX, e.clientY));
        g.addEventListener('focus', () => showTipAt(g, tip(it, i)));
        g.addEventListener('pointerleave', hideTip);
        g.addEventListener('blur', hideTip);
      }
      marks.append(g);
    });
    svg.append(marks);

    for (const gr of groups || []) {
      const x0 = m.left + band * gr.from + 4;
      const x1 = m.left + band * (gr.to + 1) - 4;
      const y = m.top + ih + 30;
      svg.append(
        s('path', { d: `M${x0},${y - 4} V${y} H${x1} V${y - 4}`, style: { stroke: 'var(--axis)', strokeWidth: '1px', fill: 'none' } }),
        s('text', { class: 'group-label', x: (x0 + x1) / 2, y: y + 14, 'text-anchor': 'middle', text: gr.label })
      );
    }

    el.replaceChildren(h('div', { class: 'col-chart' }, svg));
  }

  // ---------- Расходящиеся столбцы с доверительным интервалом ----------

  /**
   * rows: [{label, value, low, high, color, text}] — изменение в % с 95% ДИ
   * ref:  {value, label} — опорная линия (например, все отрасли вместе)
   */
  function divbar(el, { rows, ref, tip, ticks = [] }) {
    const lo = Math.min(0, ...rows.map((r) => r.low));
    const hi = Math.max(0, ...rows.map((r) => r.high));
    const pad = (hi - lo) * 0.17;
    const d0 = lo - pad;
    const d1 = hi + pad;
    const pos = (v) => (100 * (v - d0)) / (d1 - d0);

    const root = h('div', { class: 'hbar no-rank div-bars', role: 'list' });
    for (const r of rows) {
      const left = Math.min(pos(0), pos(r.value));
      const width = Math.abs(pos(r.value) - pos(0));
      const label =
        r.value >= 0
          ? { left: `calc(${pos(r.high)}% + 6px)` }
          : { right: `calc(${100 - pos(r.low)}% + 6px)` };
      const track = h(
        'div',
        { class: 'div-track' },
        h('span', { class: 'div-zero', style: { left: `${pos(0)}%` } }),
        ref ? h('span', { class: 'div-ref', style: { left: `${pos(ref.value)}%` } }) : null,
        h('span', {
          class: 'div-bar',
          style: { left: `${left}%`, width: `${width}%`, background: r.color, borderRadius: r.value >= 0 ? '0 4px 4px 0' : '4px 0 0 4px' },
        }),
        h('span', { class: 'div-ci', style: { left: `${pos(r.low)}%`, width: `${pos(r.high) - pos(r.low)}%` } }),
        h('span', { class: 'div-value', style: label, text: r.text })
      );
      const row = h(
        'div',
        { class: 'hbar-row', role: 'listitem', tabindex: 0, 'aria-label': `${r.label}: ${r.text}` },
        h('span', { class: 'hbar-label', text: r.label }),
        track
      );
      if (tip) {
        row.addEventListener('pointermove', (e) => showTip(tip(r), e.clientX, e.clientY));
        row.addEventListener('focus', () => showTipAt(row, tip(r)));
      }
      row.addEventListener('pointerleave', hideTip);
      row.addEventListener('blur', hideTip);
      root.append(row);
    }
    const axis = h(
      'div',
      { class: 'hbar-row div-axis-row', 'aria-hidden': 'true' },
      h('span'),
      h(
        'div',
        { class: 'div-axis' },
        ticks.filter((t) => t >= d0 && t <= d1).map((t) => h('span', { style: { left: `${pos(t)}%` }, text: (t > 0 ? '+' : t < 0 ? '−' : '') + Math.abs(t) + '%' })),
        ref ? h('span', { class: 'div-ref-label', style: { left: `${pos(ref.value)}%` }, text: ref.label }) : null
      )
    );
    root.append(axis);
    el.replaceChildren(root);
  }

  // ---------- Табличный вид ----------

  /** columns: [{label, value: row => string, num?, sub?: row => string}] */
  function table({ columns, rows, caption }) {
    return h(
      'table',
      { class: 'data-table' },
      caption ? h('caption', { class: 'sr-only', text: caption }) : null,
      h('thead', null, h('tr', null, columns.map((c) => h('th', { class: c.num ? 'num' : null, scope: 'col', text: c.label })))),
      h(
        'tbody',
        null,
        rows.map((r) =>
          h(
            'tr',
            null,
            columns.map((c) =>
              h(
                'td',
                { class: c.num ? 'num' : null },
                h('div', { text: c.value(r) }),
                c.sub ? h('div', { class: 'en', text: c.sub(r) }) : null
              )
            )
          )
        )
      )
    );
  }

  /**
   * Карточка: .chart — график, .table-wrap — таблица, .seg — переключатель.
   * Кнопки .seg с data-view: 'table' — таблица, любое другое значение — режим графика.
   * render(chartEl, view) рисует график и возвращает его API; responsive — перерисовывать при изменении ширины/темы.
   */
  function card(id, { render, table: tableSpec, responsive = false }) {
    const root = document.getElementById(id);
    const chartEl = root.querySelector('.chart');
    const tableEl = root.querySelector('.table-wrap');
    const seg = root.querySelector('.seg');
    const handle = { api: null };
    const first = seg?.querySelector('button[aria-pressed="true"]')?.dataset.view;
    let view = first && first !== 'table' ? first : 'chart';
    const draw = () => (handle.api = render(chartEl, view));
    draw();
    if (responsive) {
      watchWidth(chartEl, draw);
      onThemeChange(draw);
    }
    seg?.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-view]');
      if (!btn) return;
      for (const b of seg.querySelectorAll('button')) b.setAttribute('aria-pressed', String(b === btn));
      const showTable = btn.dataset.view === 'table';
      if (showTable && !tableEl.firstChild) tableEl.append(table(tableSpec));
      chartEl.hidden = showTable;
      tableEl.hidden = !showTable;
      if (!showTable) {
        view = btn.dataset.view;
        draw();
      }
    });
    return handle;
  }

  // ---------- Тема ----------

  const ICONS = {
    dark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    light: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  };

  function initTheme() {
    const root = document.documentElement;
    const mq = matchMedia('(prefers-color-scheme: dark)');
    const effective = () => root.dataset.theme || (mq.matches ? 'dark' : 'light');
    const btn = document.querySelector('.theme-btn');
    const paint = () => {
      if (!btn) return;
      const next = effective() === 'dark' ? 'light' : 'dark';
      btn.innerHTML = ICONS[next];
      btn.setAttribute('aria-label', next === 'dark' ? 'Тёмная тема' : 'Светлая тема');
      btn.title = btn.getAttribute('aria-label');
    };
    const emit = () => themeListeners.forEach((fn) => fn());
    btn?.addEventListener('click', () => {
      const next = effective() === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try {
        localStorage.setItem('report-theme', next);
      } catch (_) {
        /* хранилище недоступно — тема действует до перезагрузки */
      }
      paint();
      emit();
    });
    mq.addEventListener('change', () => {
      paint();
      if (!root.dataset.theme) emit();
    });
    paint();

    // Печать и PDF — всегда в светлой теме; после печати возвращаем выбранную
    let beforePrint;
    addEventListener('beforeprint', () => {
      beforePrint = root.dataset.theme;
      if (beforePrint === 'light') return;
      root.dataset.theme = 'light';
      emit();
    });
    addEventListener('afterprint', () => {
      if (beforePrint === 'light') return;
      if (beforePrint) root.dataset.theme = beforePrint;
      else delete root.dataset.theme;
      emit();
    });
  }

  document.addEventListener('DOMContentLoaded', initTheme);

  // ---------- Мелочи для страниц ----------

  /** Число со знаком и типографским минусом: +8,6 / −7,0. */
  fmt.signed = (x, d = 1) => (x > 0 ? '+' : x < 0 ? '−' : '') + fmt.num(Math.abs(x), d);
  fmt.months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  fmt.monthsShort = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
  fmt.monthsIn = ['январе', 'феврале', 'марте', 'апреле', 'мае', 'июне', 'июле', 'августе', 'сентябре', 'октябре', 'ноябре', 'декабре'];

  /** Текст выводов: **так** — жирным. */
  const rich = (text) => text.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? h('strong', { text: part }) : part));

  /** KPI-плитка: подпись, значение (+ единица), пояснение. */
  const kpi = ({ label, value, unit, note }) =>
    h(
      'div',
      { class: 'card kpi' },
      h('span', { class: 'kpi-label', text: label }),
      h('span', { class: 'kpi-value' }, value, unit ? h('small', { text: unit }) : null),
      h('span', { class: 'kpi-note', text: note })
    );

  window.Report = {
    fmt, casesWord, h, tt, legend, hbar, donut, lineChart, sparkline, table, card, onThemeChange, hideTip,
    columns, heatmap, divbar, scaleLegend, sequentialScale, divergingScale, inkOn, rich, kpi,
  };
})();
