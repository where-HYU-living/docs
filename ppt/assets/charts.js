// 슬라이드 차트: 인라인 SVG. 강조 막대만 남색, 나머지는 회색. 숫자는 research.md 와 같다.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, attrs, text) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  };
  const tip = (node, t) => { node.appendChild(mk('title', {}, t)); return node; };

  // 가로 막대 (순위)
  function hbar(el, o) {
    const W = o.width, rowH = o.rowH || 54, barH = o.barH || 26, L = o.labelW || 180, R = o.valW || 120;
    const H = o.rows.length * rowH + 40;
    const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': o.aria });
    const x = (v) => L + ((v - (o.min || 0)) / (o.max - (o.min || 0))) * (W - L - R);
    if (o.ref) {
      const rx = x(o.ref.value);
      svg.appendChild(mk('line', { x1: rx, x2: rx, y1: 0, y2: H - 26, class: 'ref' }));
      svg.appendChild(mk('text', { x: rx, y: H - 2, class: 'reflbl', 'text-anchor': 'middle' }, o.ref.label));
    }
    o.rows.forEach((r, i) => {
      const y = i * rowH + (rowH - barH) / 2;
      const hi = r.hi ? ' hi' : '';
      svg.appendChild(mk('text', { x: L - 18, y: y + barH / 2 + 8, class: 'lbl' + hi, 'text-anchor': 'end' }, r.label));
      const w = Math.max(4, x(r.value) - L);
      const bar = mk('rect', { x: L, y, width: w, height: barH, rx: 4, class: 'bar' + hi });
      tip(bar, `${r.label} ${r.text || r.value}`);
      svg.appendChild(bar);
      svg.appendChild(mk('text', { x: L + w + 12, y: y + barH / 2 + 8, class: 'val' + hi }, r.text || r.value));
    });
    svg.appendChild(mk('line', { x1: L, x2: L, y1: 0, y2: o.rows.length * rowH, class: 'axis' }));
    el.appendChild(svg);
  }

  // 세로 막대 분포 (10만 원 구간) + 백분위 표시
  function histo(el, o) {
    const W = o.width, H = o.height, B = 56, T = 70, Lp = 10;
    const n = o.bins.length, gap = 4, bw = (W - Lp) / n;
    const max = Math.max(...o.bins.map((b) => b[1]));
    const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': o.aria });
    const y = (v) => T + (1 - v / max) * (H - T - B);
    const xv = (man) => Lp + ((man - o.bins[0][0]) / 10) * bw; // 만원 → x
    o.bins.forEach(([lo, c], i) => {
      const inMid = lo + 10 > o.p10 && lo < o.p90;
      const r = mk('rect', { x: Lp + i * bw + gap / 2, y: y(c), width: bw - gap, height: H - B - y(c), rx: 4, class: 'bar' + (inMid ? '' : '') });
      r.style.fill = inMid ? '#c3ccd8' : '#e1e6ed';
      tip(r, `${lo}~${lo + 10}만 원: ${c}건`);
      svg.appendChild(r);
      svg.appendChild(mk('text', { x: Lp + i * bw + bw / 2, y: H - B + 30, class: 'tick', 'text-anchor': 'middle' }, lo));
    });
    svg.appendChild(mk('text', { x: W, y: H - 4, class: 'tick', 'text-anchor': 'end' }, '환산 월세(만 원)'));
    svg.appendChild(mk('line', { x1: Lp, x2: W, y1: H - B, y2: H - B, class: 'axis' }));
    for (const m of o.marks) {
      const xx = xv(m.v);
      svg.appendChild(mk('line', { x1: xx, x2: xx, y1: T - 20, y2: H - B, stroke: m.hi ? 'var(--hy)' : 'var(--ink)', 'stroke-width': m.hi ? 3 : 2, 'stroke-dasharray': m.hi ? '' : '6 6' }));
      svg.appendChild(mk('text', { x: xx, y: T - 50, 'text-anchor': 'middle', class: 'reflbl' }, m.label));
      const t = mk('text', { x: xx, y: T - 26, 'text-anchor': 'middle', class: 'val' + (m.hi ? ' hi' : '') }, m.v + '만');
      svg.appendChild(t);
    }
    el.appendChild(svg);
  }

  // 작은 추이 선 (한양대 인근 1월 월세)
  function trend(el, o) {
    const W = o.width, H = o.height, P = 40, T = 50, B = 46;
    const vs = o.points.map((p) => p[1]);
    const lo = o.min, hi = o.max;
    const x = (i) => P + (i / (o.points.length - 1)) * (W - 2 * P);
    const y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
    const svg = mk('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': o.aria });
    svg.appendChild(mk('line', { x1: 0, x2: W, y1: H - B, y2: H - B, class: 'axis' }));
    svg.appendChild(mk('polyline', { points: o.points.map((p, i) => `${x(i)},${y(p[1])}`).join(' '), fill: 'none', stroke: 'var(--hy)', 'stroke-width': 3, 'stroke-linejoin': 'round' }));
    o.points.forEach(([lab, v], i) => {
      const last = i === o.points.length - 1;
      svg.appendChild(tip(mk('circle', { cx: x(i), cy: y(v), r: last ? 9 : 6, fill: last ? 'var(--hy)' : '#fff', stroke: 'var(--hy)', 'stroke-width': 3 }), `${lab} ${v}만 원`));
      svg.appendChild(mk('text', { x: x(i), y: y(v) - 20, 'text-anchor': 'middle', class: 'val' + (last ? ' hi' : '') }, v));
      svg.appendChild(mk('text', { x: x(i), y: H - B + 30, 'text-anchor': 'middle', class: 'tick' }, lab));
    });
    el.appendChild(svg);
  }

  window.drawCharts = function () {
    // 01 문제: 한양대 주변 6개 동, 전용 15~25㎡ 월세 거래 1,315건 (자체 분석)
    const h = document.getElementById('ch-histo');
    if (h && !h.firstChild) histo(h, {
      width: 940, height: 430, aria: '한양대 주변 원룸 환산 월세 분포',
      bins: [[20, 2], [30, 58], [40, 164], [50, 300], [60, 270], [70, 172], [80, 123], [90, 110], [100, 72], [110, 33], [120, 10], [130, 1]],
      p10: 44.2, p90: 98.8,
      marks: [{ v: 44.2, label: '하위 10%' }, { v: 63.8, label: '중앙값', hi: true }, { v: 98.8, label: '상위 10%' }],
    });
    // 02: 다방여지도 2026년 9월, 서울 평균 대비 (서울 평균을 넘는 구만 공개)
    const g = document.getElementById('ch-gu');
    if (g && !g.firstChild) hbar(g, {
      width: 800, rowH: 44, barH: 24, labelW: 100, min: 80, max: 140, valW: 190, aria: '서울 자치구 원룸 월세, 서울 평균 대비',
      ref: { value: 100, label: '서울 평균 71만 원 = 100' },
      rows: [
        { label: '강남구', value: 138, text: '138%' }, { label: '용산구', value: 126, text: '126%' },
        { label: '관악구', value: 123, text: '123%' }, { label: '성동구', value: 117, text: '117% · 82만 원', hi: true },
        { label: '광진구', value: 112, text: '112%' }, { label: '서초구', value: 109, text: '109%' },
        { label: '마포구', value: 108, text: '108%' }, { label: '중구', value: 108, text: '108%' },
        { label: '강서구', value: 106, text: '106%' }, { label: '금천구', value: 106, text: '106%' },
        { label: '동작구', value: 102, text: '102%' },
      ],
    });
    // 02: 다방 서울 주요 10개 대학 인근 원룸 월세, 2026년 1월
    const u = document.getElementById('ch-univ');
    if (u && !u.firstChild) hbar(u, {
      width: 800, rowH: 48, barH: 26, labelW: 120, min: 0, max: 80, aria: '서울 주요 대학가 원룸 월세',
      ref: { value: 62.2, label: '10곳 평균 62.2만' },
      rows: [
        { label: '성균관대', value: 73.8, text: '73.8만' }, { label: '이화여대', value: 71.1, text: '71.1만' },
        { label: '연세대', value: 68.3, text: '68.3만' }, { label: '고려대', value: 66.3, text: '66.3만' },
        { label: '한양대', value: 64.2, text: '64.2만', hi: true }, { label: '경희대', value: 62.2, text: '62.2만' },
        { label: '서강대', value: 59.9, text: '59.9만' }, { label: '한국외대', value: 59.9, text: '59.9만' },
        { label: '서울대', value: 48.9, text: '48.9만' }, { label: '중앙대', value: 46.9, text: '46.9만' },
      ],
    });
    const t = document.getElementById('ch-trend');
    if (t && !t.firstChild) trend(t, {
      width: 560, height: 330, min: 40, max: 70, aria: '한양대 인근 원룸 월세 추이(매년 1월)',
      points: [['2023.1', 49.0], ['2024.1', 55.0], ['2025.1', 57.7], ['2026.1', 64.2]],
    });
  };
})();
