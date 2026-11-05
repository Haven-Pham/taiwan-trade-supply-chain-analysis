/* Renders the dashboard from data.json. All sentences containing numbers are built from the data,
   so they stay correct when the monthly refresh adds new figures. */
(() => {
  'use strict';

  const I18N = {
    en: {
      skip: 'Skip to content', eyebrow: 'Supply chain analytics · official open data',
      title: "Taiwan's export boom through a supply chain lens",
      kpiTitle: 'Key figures', yearLabel: 'Partner year', flowLabel: 'Trade flow', tableView: 'View data as a table', period: 'Period', item: 'Item',
      s1: 'What is growing?', c1: 'Exports by product group, same months each year', c2: 'Export sub-groups, rolling 12 months',
      s2: 'Where is it going?', c3: 'Share of trade by market, rolling 12 months', c4: 'Ten largest trade partners',
      s3: 'Volume or price?', c5: 'Export indices, 12-month average, 2021 = 100', c6: 'Export quantity by product, 2021 = 100',
      s4: 'Do the ports see it?', c7: 'Trade value and containers, 2021 = 100', c8: 'Share of container throughput by port',
      airNote: 'Trade value includes air freight, while TEU counts sea containers only. A shift to air freight would explain part of the gap, but the only open monthly airport cargo file ends in 2022, so this remains untested.',
      s5: 'How exposed is the boom? Try a scenario', t5: 'Choose a trade lane and a size of fall to see the first-order effect on total exports.',
      laneLabel: 'Trade lane', outUsd: 'of exports lost over the period', outPct: 'of total exports', outShare: 'lane share of total exports', laneChart: 'Effect of the same fall on each lane',
      scenarioNote: 'An exposure measure, not a forecast. It assumes no diversion to other markets and no change elsewhere in trade.',
      s6: 'Method and limits',
      m1: 'Comparisons use the same calendar months in every year, so a partial year compares fairly.',
      m2: 'Shares use the published total as the denominator, so unallocated values do not inflate them.',
      m3: 'Quantity indices measure volume change. They are not tonnes. Value per TEU shows how value separated from containers, and does not describe what is inside a container.',
      m5: 'Official categories cannot isolate servers, chips or specific supply chains. Recent figures may be revised.',
      by: 'Pham Hong Hieu (Haven)', code: 'Code and full analysis', portfolio: 'Portfolio',
      exports: 'Exports', imports: 'Imports', machinery: 'Machinery & electrical', rest: 'All other products',
      value: 'Value', quantity: 'Quantity', price: 'Unit value', machQuantity: 'Machinery qty',
      tradeValue: 'Trade value', teu: 'TEU', share: '% of total', index: 'Index', all: 'All markets', usdM: 'US$ million',
      goods: { 'ICT & audio-visual products': 'ICT & AV', 'Electronic components': 'Components', Machinery: 'Machinery' },
      shortMarket: { usa: 'US', china_hk: 'China & HK' },
      theme: ['Dark mode', 'Light mode'],
      lane: 'machinery & electrical',
      kExports: 'Exports', kShare: 'Machinery share of exports', kUs: 'United States share of exports',
      kLane: 'US machinery as share of all exports', kTeu: 'Container throughput (TEU)', kDensity: 'Trade value per TEU',
      since: base => `${base}`, yoy: 'vs a year earlier',
      lede: (d, k) => `Exports rose ${fmt(k.exports_yoy)}% in ${period(d)}. Machinery and electrical equipment is ${fmt(k.machinery_share)}% of them, and containers handled ${move(k.teu_change)} against the same months of ${d.baseYear}.`,
      periodNote: d => `Data through ${monthName(d.asOf)}. Figures compare ${period(d)} with the same months of earlier years. Refreshed automatically when new official data appear.`,
      shockLabel: v => `Fall in the lane's value: ${v}%`,
      t1: (d, k) => `Machinery and electrical equipment is ${fmt(k.machinery_share)}% of exports, up from ${fmt(k.machinery_share_base)}% in ${d.baseYear}. It accounts for ${fmt(k.machinery_growth_contribution, 0)}% of the export increase since then, while all other exports ${move(k.rest_change)}. Imports show the same shift: the group went from ${fmt(k.import_machinery_share_base)}% to ${fmt(k.import_machinery_share)}% of imports.`,
      t2: (d, k) => `The United States went from ${fmt(k.us_share_base)}% to ${fmt(k.us_share)}% of exports, while China & Hong Kong went from ${fmt(k.china_hk_share_base)}% to ${fmt(k.china_hk_share)}%.${d.crossover ? ` On a rolling 12-month basis the US has led since ${monthName(d.crossover)}.` : ''} Machinery and electrical equipment is ${fmt(k.us_basket_machinery)}% of what the US buys, so the largest customer changed but product dependence grew.`,
      t3: (d, k) => `Since ${d.baseYear}, export quantity has multiplied by ${fmt(k.quantity_multiple, 2)} and unit value by ${fmt(k.price_multiple, 2)}. ${d.quantityBelow} of ${d.quantity.length} indexed product groups remain below their ${d.baseYear} quantity.`,
      t4: (d, k) => `Trade value multiplied by ${fmt(k.trade_multiple, 2)} since ${d.baseYear} while containers ${move(k.teu_change)}. Trade value per TEU went from $${compact(k.usd_per_teu_base)} to $${compact(k.usd_per_teu)}.`,
      countryNote: (d, x) => `Shares of the published total. ${x}% of ${d.year} imports have no listed country in the source, so import shares are lower bounds.`,
      m4: d => `The notebook analyses a fixed snapshot for reproducibility; this dashboard shows the latest month (${monthName(d.asOf)}).`,
      sources: 'Sources: Ministry of Finance trade statistics and Taiwan International Ports Corporation, via data.gov.tw (Open Government Data License, version 1.0).',
    },
    zh: {
      skip: '跳至主要內容', eyebrow: '供應鏈分析 · 政府開放資料',
      title: '從供應鏈角度看臺灣出口榮景',
      kpiTitle: '重點數據', yearLabel: '貿易夥伴年份', flowLabel: '貿易方向', tableView: '以表格檢視資料', period: '期間', item: '項目',
      s1: '成長來自哪裡？', c1: '依貨品類別之出口值（各年同期）', c2: '出口細項（近 12 個月合計）',
      s2: '貨品銷往何處？', c3: '各市場占貿易比重（近 12 個月合計）', c4: '前十大貿易夥伴',
      s3: '是量增還是價漲？', c5: '出口指數，12 個月平均（2021 年 = 100）', c6: '各類貨品出口數量指數（2021 年 = 100）',
      s4: '港口感受到了嗎？', c7: '貿易值與貨櫃量（2021 年 = 100）', c8: '各港貨櫃裝卸量占比',
      airNote: '貿易值包含空運，TEU 僅計算海運貨櫃。轉向空運可能解釋部分落差，但目前開放的機場月貨運量資料僅至 2022 年，因此這仍是尚未驗證的假設。',
      s5: '這波榮景的曝險有多大？試算情境', t5: '選擇一條貿易路線與跌幅，查看對總出口的一階影響。',
      laneLabel: '貿易路線', outUsd: '期間損失之出口值', outPct: '占總出口', outShare: '該路線占總出口比重', laneChart: '相同跌幅對各路線的影響',
      scenarioNote: '此為曝險衡量，並非預測。假設貨品不轉銷其他市場，其他貿易亦維持不變。',
      s6: '方法與限制',
      m1: '各年比較皆採相同月份，使未滿一年的資料仍可公平比較。',
      m2: '比重以官方公布總額為分母，避免未分配金額造成高估。',
      m3: '數量指數衡量數量變化，並非噸數。每 TEU 貿易值呈現貿易值與貨櫃量的脫鉤程度，並非貨櫃內貨物的價值。',
      m5: '官方分類無法單獨區分伺服器、晶片或特定供應鏈。近期數據可能修正。',
      by: '范鴻孝 Pham Hong Hieu (Haven)', code: '程式碼與完整分析', portfolio: '作品集',
      exports: '出口', imports: '進口', machinery: '機械及電機設備', rest: '其他貨品',
      value: '價值', quantity: '數量', price: '單位價值', machQuantity: '機電數量',
      tradeValue: '貿易值', teu: 'TEU', share: '占總額 %', index: '指數', all: '所有市場', usdM: '百萬美元',
      goods: { 'ICT & audio-visual products': '資通與視聽', 'Electronic components': '電子零組件', Machinery: '機械' },
      shortMarket: { usa: '美國', china_hk: '中國大陸及香港' },
      theme: ['深色模式', '淺色模式'],
      lane: '機械及電機設備',
      kExports: '出口值（億美元）', kShare: '機械及電機設備占出口比重', kUs: '美國占出口比重',
      kLane: '對美機械及電機設備占總出口', kTeu: '貨櫃裝卸量（TEU）', kDensity: '每 TEU 貿易值',
      since: base => `${base} 年`, yoy: '較去年同期',
      lede: (d, k) => `${period(d)}出口成長 ${fmt(k.exports_yoy)}%，其中機械及電機設備占 ${fmt(k.machinery_share)}%；貨櫃裝卸量與 ${d.baseYear} 年同期相比${move(k.teu_change)}。`,
      periodNote: d => `資料截至 ${monthName(d.asOf)}。數據為${period(d)}與歷年同期之比較，官方資料更新後自動更新。`,
      shockLabel: v => `該路線出口值下跌：${v}%`,
      t1: (d, k) => `機械及電機設備占出口 ${fmt(k.machinery_share)}%，${d.baseYear} 年為 ${fmt(k.machinery_share_base)}%，並貢獻此後出口增額的 ${fmt(k.machinery_growth_contribution, 0)}%；其他貨品出口則${move(k.rest_change)}。進口亦呈現相同轉變：該類貨品占進口比重由 ${fmt(k.import_machinery_share_base)}% 升至 ${fmt(k.import_machinery_share)}%。`,
      t2: (d, k) => `美國占出口比重由 ${fmt(k.us_share_base)}% 變為 ${fmt(k.us_share)}%，中國大陸及香港則由 ${fmt(k.china_hk_share_base)}% 變為 ${fmt(k.china_hk_share)}%。${d.crossover ? `以近 12 個月合計計算，美國自 ${monthName(d.crossover)} 起居首。` : ''}美國購買的貨品中有 ${fmt(k.us_basket_machinery)}% 屬機械及電機設備，因此最大客戶雖已改變，貨品依賴度卻更高。`,
      t3: (d, k) => `${d.baseYear} 年以來，出口數量增為 ${fmt(k.quantity_multiple, 2)} 倍，單位價值增為 ${fmt(k.price_multiple, 2)} 倍。${d.quantity.length} 個有指數的貨品類別中，有 ${d.quantityBelow} 個的數量仍低於 ${d.baseYear} 年水準。`,
      t4: (d, k) => `${d.baseYear} 年以來貿易值增為 ${fmt(k.trade_multiple, 2)} 倍，貨櫃量則${move(k.teu_change)}。每 TEU 貿易值由 ${compact(k.usd_per_teu_base)} 美元變為 ${compact(k.usd_per_teu)} 美元。`,
      countryNote: (d, x) => `比重以官方公布總額計算。${d.year} 年有 ${x}% 的進口值在資料中未列明國家，因此進口比重為下限。`,
      m4: d => `Notebook 為確保可重現性採固定時點資料；本儀表板顯示最新月份（${monthName(d.asOf)}）。`,
      sources: '資料來源：財政部進出口貿易統計、臺灣港務股份有限公司，經政府資料開放平臺取得（政府資料開放授權條款第 1 版）。',
    },
  };

  /* Categorical slots run in a fixed, validated order; dark mode has its own steps.
     Checked with the palette validator on this page's two card surfaces. */
  const SERIES = {
    light: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300'],
    dark: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300'],
  };
  const MARKET_ORDER = ['usa', 'china_hk', 'asean', 'japan', 'korea', 'germany'];

  let DATA, lang = 'en', flow = 'x';
  const $ = id => document.getElementById(id);
  const t = key => I18N[lang][key];
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const slot = i => SERIES[document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'][i];
  const narrow = () => matchMedia('(max-width: 520px)').matches;

  const fmt = (v, digits = 1) => Number(v).toLocaleString(lang === 'zh' ? 'zh-TW' : 'en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
  const sign = v => `${v > 0 ? '+' : ''}${fmt(v)}`;
  const move = v => (lang === 'zh' ? `${v < 0 ? '下降' : '上升'} ${fmt(Math.abs(v))}%` : `${v < 0 ? 'fell' : 'rose'} ${fmt(Math.abs(v))}%`);
  const compact = v => Number(Math.round(v / 100) * 100).toLocaleString('en-US');
  const money = millions => (lang === 'zh' ? `${fmt(millions / 100, 0)} 億美元` : `$${fmt(millions / 1e3)}B`);
  const escapeHtml = text => String(text).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function monthName(ym) {
    const [y, m] = ym.split('-').map(Number);
    if (lang === 'zh') return `${y} 年 ${m} 月`;
    return new Date(Date.UTC(y, m - 1, 1)).toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  }
  function period(d) {
    if (lang === 'zh') return `${d.year} 年 1 至 ${d.lastMonth} 月`;
    const end = new Date(Date.UTC(d.year, d.lastMonth - 1, 1)).toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' });
    return `Jan-${end} ${d.year}`;
  }
  const sectionName = name => (lang === 'zh' ? (DATA.sectionZh[name] || name) : name);

  function layout(extra = {}) {
    const ink = css('--ink'), soft = css('--soft'), line = css('--line');
    const base = {
      margin: { l: 58, r: 14, t: 34, b: 40 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: css('--font') || 'sans-serif', size: 12, color: soft },
      hovermode: 'x unified', hoverlabel: { font: { color: '#16202E' }, bgcolor: '#FFFFFF' },
      legend: { orientation: 'h', x: 0, y: 1.02, xanchor: 'left', yanchor: 'bottom', traceorder: 'normal', font: { color: ink } },
      xaxis: { gridcolor: 'rgba(0,0,0,0)', linecolor: line, zeroline: false, automargin: true },
      yaxis: { gridcolor: line, gridwidth: 1, linecolor: 'rgba(0,0,0,0)', zeroline: false, automargin: true },
    };
    return { ...base, ...extra, xaxis: { ...base.xaxis, ...(extra.xaxis || {}) }, yaxis: { ...base.yaxis, ...(extra.yaxis || {}) } };
  }
  const CONFIG = { responsive: true, displaylogo: false, displayModeBar: false };

  /* Every chart gets a table twin, so no value depends on hover or on colour alone. */
  function tableHtml(traces) {
    const horizontal = traces[0].orientation === 'h';
    const keys = horizontal ? traces[0].y : traces[0].x;
    const cell = v => (typeof v === 'number' ? v.toLocaleString(lang === 'zh' ? 'zh-TW' : 'en-US', { maximumFractionDigits: 2 }) : (v === null || v === undefined ? '' : v));
    const head = [horizontal ? t('item') : t('period'), ...traces.map(tr => tr.name || t('value'))];
    const rows = keys.map((key, i) => [key, ...traces.map(tr => (horizontal ? tr.x[i] : tr.y[i]))]);
    const ordered = [...rows].reverse();
    return `<table><thead><tr>${head.map(h => `<th scope="col">${escapeHtml(h)}</th>`).join('')}</tr></thead><tbody>${
      ordered.map(r => `<tr><th scope="row">${escapeHtml(r[0])}</th>${r.slice(1).map(v => `<td>${escapeHtml(cell(v))}</td>`).join('')}</tr>`).join('')
    }</tbody></table>`;
  }
  function draw(id, traces, extra, label) {
    const node = $(id);
    node.setAttribute('aria-label', label);
    Plotly.react(node, traces, layout(extra), CONFIG);
    let details = node.nextElementSibling;
    if (!details || !details.classList.contains('table-view')) {
      details = document.createElement('details');
      details.className = 'table-view';
      details.innerHTML = '<summary></summary><div class="table-scroll" tabindex="0" role="region"></div>';
      node.after(details);
    }
    details.querySelector('summary').textContent = t('tableView');
    const box = details.querySelector('.table-scroll');
    box.setAttribute('aria-label', label);
    box.innerHTML = tableHtml(traces);
  }

  /* Series names at the line ends, nudged apart so that close series do not collide. */
  function endLabels(items, range) {
    const gap = (range[1] - range[0]) * 0.075;
    const sorted = [...items].sort((a, b) => a.y - b.y);
    sorted.forEach((item, i) => { item.shown = i && item.y - sorted[i - 1].shown < gap ? sorted[i - 1].shown + gap : item.y; });
    return sorted.map(item => ({ x: item.x, y: item.shown, text: item.text, xanchor: 'left', xshift: 6, showarrow: false, font: { color: css('--ink'), size: 11 } }));
  }
  const yRange = traces => {
    const values = traces.flatMap(tr => tr.y.filter(v => v !== null));
    return [Math.min(...values), Math.max(...values)];
  };
  const lineMargin = () => ({ l: 50, r: narrow() ? 74 : 92, t: 34, b: 40 });
  const spanX = traces => ({ range: [traces[0].x[0], traces[0].x[traces[0].x.length - 1]] });
  const line = (x, y, name, color) => ({ type: 'scatter', mode: 'lines', x, y, name, line: { color, width: 2 } });
  const last = arr => arr[arr.length - 1];

  function renderKpis() {
    const k = DATA.kpis, b = t('since')(DATA.baseYear);
    const cards = [
      [t('kExports'), lang === 'zh' ? fmt(k.exports / 100, 0) : money(k.exports), `${t('yoy')} ${sign(k.exports_yoy)}%`],
      [t('kShare'), `${fmt(k.machinery_share)}%`, `${b}: ${fmt(k.machinery_share_base)}%`],
      [t('kUs'), `${fmt(k.us_share)}%`, `${b}: ${fmt(k.us_share_base)}%`],
      [t('kLane'), `${fmt(k.us_machinery_share)}%`, `${b}: ${fmt(k.us_machinery_share_base)}%`],
      [t('kTeu'), lang === 'zh' ? `${fmt(k.teu / 1e4, 0)} 萬` : `${fmt(k.teu / 1e6, 2)}M`, `${b}: ${sign(k.teu_change)}%`],
      [t('kDensity'), `$${compact(k.usd_per_teu)}`, `${b}: $${compact(k.usd_per_teu_base)}`],
    ];
    $('kpis').innerHTML = cards.map(([label, value, sub]) => `<div class="kpi"><span class="label">${label}</span><span class="value">${value}</span><span class="sub">${sub}</span></div>`).join('');
  }

  function renderGrowth() {
    const d = DATA.byYear.exports, surface = css('--surface');
    const bar = (y, name, color) => ({ type: 'bar', x: DATA.years, y, name, marker: { color, line: { color: surface, width: 2 } } });
    draw('chart-growth', [bar(d.machinery, t('machinery'), slot(0)), bar(d.rest, t('rest'), css('--muted'))],
      { barmode: 'stack', bargap: 0.3, barcornerradius: 4, yaxis: { title: t('usdM'), tickformat: ',d' }, xaxis: { dtick: 2 } }, t('c1'));
  }
  function renderGoods() {
    const g = DATA.goods, names = t('goods'), keys = Object.keys(names);
    const traces = keys.map((c, i) => line(g.months, g[c], names[c], slot(i)));
    const range = yRange(traces);
    draw('chart-goods', traces, { margin: { ...lineMargin(), l: 58 }, xaxis: spanX(traces), yaxis: { title: t('usdM'), tickformat: ',d' },
      annotations: endLabels(traces.map(tr => ({ x: last(tr.x), y: last(tr.y), text: tr.name })), range) }, t('c2'));
  }
  function renderMarkets() {
    const traces = MARKET_ORDER.map((key, i) => line(DATA.shareMonths, DATA.markets[flow][key].share, DATA.marketNames[key][lang], slot(i)));
    const short = t('shortMarket');
    const labelled = MARKET_ORDER.map((key, i) => ({ key, tr: traces[i] })).filter(({ key }) => short[key]);
    draw('chart-markets', traces, { margin: { l: 44, r: lang === 'zh' ? 108 : (narrow() ? 74 : 92), t: 60, b: 40 }, xaxis: spanX(traces), yaxis: { title: t('share') },
      annotations: endLabels(labelled.map(({ key, tr }) => ({ x: last(tr.x), y: last(tr.y), text: short[key] })), yRange(traces)) }, t('c3'));
  }
  function renderCountries() {
    const direction = flow === 'x' ? 'exports' : 'imports';
    const rows = DATA.countries[direction][$('country-year').value].slice(0, 10).reverse();
    draw('chart-countries', [{ type: 'bar', orientation: 'h', y: rows.map(r => r[lang]), x: rows.map(r => r.share), name: t('share'), marker: { color: slot(0) },
      text: rows.map(r => `${fmt(r.share)}%`), textposition: 'outside', textfont: { color: css('--ink') }, cliponaxis: false, hovertemplate: '%{y}: %{x:.1f}%<extra></extra>' }],
    { hovermode: 'closest', bargap: 0.35, barcornerradius: 4, showlegend: false, margin: { l: 12, r: 48, t: 8, b: 40 }, xaxis: { title: t('share') }, yaxis: { gridcolor: 'rgba(0,0,0,0)' } }, t('c4'));
    $('country-note').textContent = t('countryNote')(DATA, fmt(DATA.countries.imports_unallocated_pct));
  }
  function renderIndex() {
    const i = DATA.indices;
    const series = [['export_value', t('value')], ['export_quantity', t('quantity')], ['export_unit_value', t('price')], ['machinery_quantity', t('machQuantity')]];
    const traces = series.map(([key, name], n) => line(i.months, i[key], name, slot(n)));
    draw('chart-index', traces, { margin: lineMargin(), xaxis: spanX(traces), yaxis: { title: t('index') },
      annotations: endLabels(traces.map(tr => ({ x: last(tr.x), y: last(tr.y), text: tr.name })), yRange(traces)) }, t('c5'));
  }
  function renderQuantity() {
    const rows = [...DATA.quantity].reverse();
    draw('chart-quantity', [{ type: 'bar', orientation: 'h', y: rows.map(r => sectionName(r.name)), x: rows.map(r => r.value), name: t('index'),
      marker: { color: rows.map(r => (r.value > 100 ? slot(0) : css('--muted'))) }, hovertemplate: '%{y}: %{x:.1f}<extra></extra>' }],
    { hovermode: 'closest', bargap: 0.3, barcornerradius: 3, showlegend: false, margin: { l: 12, r: 14, t: 8, b: 40 }, xaxis: { title: t('index') }, yaxis: { tickfont: { size: 11 }, gridcolor: 'rgba(0,0,0,0)' },
      shapes: [{ type: 'line', x0: 100, x1: 100, yref: 'paper', y0: 0, y1: 1, line: { color: css('--soft'), width: 1 } }] }, t('c6'));
  }
  function renderPorts() {
    const p = DATA.ports, at = p.years.indexOf(DATA.baseYear);
    const indexed = values => values.map(v => +(v / values[at] * 100).toFixed(1));
    const teu = [line(p.years, indexed(p.trade), t('tradeValue'), slot(0)), line(p.years, indexed(p.teu), t('teu'), slot(1))];
    draw('chart-teu', teu, { margin: lineMargin(), yaxis: { title: t('index') }, xaxis: { ...spanX(teu), dtick: 2 },
      annotations: endLabels(teu.map(tr => ({ x: last(tr.x), y: last(tr.y), text: tr.name })), yRange(teu)) }, t('c7'));

    const surface = css('--surface');
    const ports = Object.keys(p.share);
    let base = 0;
    const annotations = ports.map(port => {
      const value = last(p.share[port]);
      const mid = base + value / 2;
      base += value;
      return { x: last(p.shareYears), y: mid, text: p.names[port][lang], xanchor: 'left', xshift: 6, showarrow: false, font: { color: css('--ink'), size: 11 } };
    });
    draw('chart-ports', ports.map((port, i) => ({ type: 'scatter', mode: 'lines', stackgroup: 'one', x: p.shareYears, y: p.share[port], name: p.names[port][lang],
      line: { width: 2, color: surface }, fillcolor: slot(i) })),
    { margin: lineMargin(), xaxis: { range: [p.shareYears[0], last(p.shareYears)] }, yaxis: { title: t('share'), range: [0, 100], gridcolor: 'rgba(0,0,0,0)' }, annotations }, t('c8'));
  }

  function lanes() {
    const total = DATA.kpis.exports;
    const rows = MARKET_ORDER.map(key => ({ key, name: `${DATA.marketNames[key][lang]}: ${t('lane')}`, value: DATA.markets.x[key].machinery_ytd }));
    rows.push({ key: 'all', name: `${t('all')}: ${t('lane')}`, value: DATA.sections.exports.find(s => s.name === DATA.machinery).value });
    return rows.sort((a, b) => b.value - a.value).map(r => ({ ...r, share: r.value / total * 100 }));
  }
  function renderLaneOptions() {
    const select = $('lane'), current = select.value || 'usa';
    select.innerHTML = lanes().map(r => `<option value="${r.key}">${escapeHtml(r.name)}</option>`).join('');
    select.value = current;
  }
  function renderScenario() {
    const shock = Number($('shock').value), rows = lanes(), lane = rows.find(r => r.key === $('lane').value) || rows[0];
    $('shock-label').textContent = t('shockLabel')(shock);
    $('shock').setAttribute('aria-valuetext', `${shock}%`);
    $('out-usd').textContent = money(lane.value * shock / 100);
    $('out-pct').textContent = `${fmt(lane.share * shock / 100)}%`;
    $('out-share').textContent = `${fmt(lane.share)}%`;
    const display = rows.filter(r => r.key !== 'all').reverse();
    draw('chart-lanes', [{ type: 'bar', orientation: 'h', y: display.map(r => DATA.marketNames[r.key][lang]), x: display.map(r => +(r.share * shock / 100).toFixed(2)), name: t('outPct'),
      marker: { color: display.map(r => (r.key === lane.key ? slot(0) : css('--muted'))) }, text: display.map(r => `${fmt(r.share * shock / 100)}%`), textposition: 'outside', textfont: { color: css('--ink') }, cliponaxis: false,
      hovertemplate: '%{y}: %{x:.2f}%<extra></extra>' }],
    { hovermode: 'closest', bargap: 0.35, barcornerradius: 4, showlegend: false, margin: { l: 12, r: 48, t: 8, b: 42 }, xaxis: { title: t('outPct') }, yaxis: { gridcolor: 'rgba(0,0,0,0)' } }, t('laneChart'));
  }

  function renderSegments() {
    const box = document.querySelector('[data-group="flow"]');
    box.setAttribute('aria-label', t('flowLabel'));
    box.innerHTML = [['x', t('exports')], ['m', t('imports')]].map(([value, label]) => `<button type="button" data-value="${value}" aria-pressed="${value === flow}">${label}</button>`).join('');
  }

  function renderText() {
    document.documentElement.lang = lang === 'zh' ? 'zh-Hant' : 'en';
    document.title = t('title');
    document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
    document.querySelectorAll('[data-lang]').forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.lang === lang)));
    const k = DATA.kpis;
    $('lede').textContent = t('lede')(DATA, k);
    $('period-note').textContent = t('periodNote')(DATA);
    ['t1', 't2', 't3', 't4'].forEach(id => { $(id).textContent = t(id)(DATA, k); });
    $('m4').textContent = t('m4')(DATA);
    $('sources').textContent = t('sources');
    const dark = document.documentElement.dataset.theme === 'dark';
    $('theme').textContent = t('theme')[dark ? 1 : 0];
    $('theme').setAttribute('aria-pressed', String(dark));
  }

  function renderAll() {
    renderText(); renderSegments(); renderKpis(); renderGrowth(); renderGoods(); renderMarkets(); renderCountries();
    renderIndex(); renderQuantity(); renderPorts(); renderLaneOptions(); renderScenario();
  }

  function bind() {
    document.querySelectorAll('[data-lang]').forEach(btn => btn.addEventListener('click', () => {
      lang = btn.dataset.lang;
      try { localStorage.setItem('tw-lang', lang); } catch { /* preference is optional */ }
      renderAll();
    }));
    $('theme').addEventListener('click', () => {
      const root = document.documentElement;
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('tw-theme', root.dataset.theme); } catch { /* preference is optional */ }
      renderAll();
    });
    document.querySelector('[data-group="flow"]').addEventListener('click', event => {
      const button = event.target.closest('button');
      if (!button) return;
      flow = button.dataset.value;
      renderSegments(); renderMarkets(); renderCountries();
    });
    $('country-year').addEventListener('change', renderCountries);
    $('lane').addEventListener('change', renderScenario);
    $('shock').addEventListener('input', renderScenario);
  }

  async function start() {
    const stored = key => { try { return localStorage.getItem(key); } catch { return null; } };
    const urlLang = new URLSearchParams(location.search).get('lang');
    lang = urlLang === 'zh' || urlLang === 'en' ? urlLang : (stored('tw-lang') || (navigator.language.startsWith('zh') ? 'zh' : 'en'));
    const urlTheme = new URLSearchParams(location.search).get('theme');
    document.documentElement.dataset.theme = urlTheme || stored('tw-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const response = await fetch('data.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    DATA = await response.json();
    $('country-year').innerHTML = [...DATA.years].reverse().map(y => `<option value="${y}">${y}</option>`).join('');
    bind();
    renderAll();
  }
  start().catch(error => {
    $('main').insertAdjacentHTML('afterbegin', `<p class="takeaway" role="alert">The data could not be loaded (${escapeHtml(error.message)}). Please reload the page.</p>`);
  });
})();
