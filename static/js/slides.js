(function () {
  const array = window.__ARRAY__;
  const steps = window.__STEPS__;

  let current = 0;

  const arrayRow = document.getElementById('arrayRow');
  const pointerRow = document.getElementById('pointerRow');
  const infoRow = document.getElementById('infoRow');
  const stepMessage = document.getElementById('stepMessage');
  const stepStatus = document.getElementById('stepStatus');
  const stepCounter = document.getElementById('stepCounter');
  const card = document.getElementById('card');
  const ticksEl = document.getElementById('ticks');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const legendEl = document.getElementById('legend');

  const LEGEND_LABELS = {
    compare: 'comparing',
    active: 'current',
    swap: 'swapping',
    pivot: 'pivot / candidate',
    sorted: 'settled',
    eliminated: 'ruled out',
    match: 'answer',
  };

  // progress ticks, built once
  steps.forEach((_, i) => {
    const t = document.createElement('span');
    t.className = 'tick';
    t.dataset.index = i;
    t.addEventListener('click', () => { current = i; render(); });
    ticksEl.appendChild(t);
  });

  // legend: only show the highlight kinds actually used across this run
  const kindsUsed = new Set();
  steps.forEach(s => Object.values(s.highlights || {}).forEach(k => kindsUsed.add(k)));
  legendEl.innerHTML = '';
  Object.keys(LEGEND_LABELS).forEach(kind => {
    if (!kindsUsed.has(kind)) return;
    const item = document.createElement('span');
    item.className = 'legend__item';
    item.innerHTML = `<span class="legend__swatch legend__swatch--${kind}"></span>${LEGEND_LABELS[kind]}`;
    legendEl.appendChild(item);
  });

  function render() {
    const step = steps[current];
    const values = step.array && step.array.length ? step.array : array;
    const highlights = step.highlights || {};

    arrayRow.style.gridTemplateColumns = `repeat(${values.length}, 1fr)`;
    pointerRow.style.gridTemplateColumns = `repeat(${values.length}, 1fr)`;

    // --- array cells ---
    arrayRow.innerHTML = '';
    values.forEach((val, i) => {
      const cell = document.createElement('div');
      const kind = highlights[i] || highlights[String(i)];
      cell.className = 'cell' + (kind ? ` cell--${kind}` : '');
      cell.innerHTML = `
        <span class="cell__index">${i}</span>
        <span class="cell__value">${val}</span>
      `;
      arrayRow.appendChild(cell);
    });

    // --- pointer row ---
    pointerRow.innerHTML = '';
    (step.pointers || []).forEach(p => {
      const el = document.createElement('div');
      el.className = 'pointer';
      el.style.gridColumn = `${p.index + 1} / ${p.index + 2}`;
      el.innerHTML = `<span class="pointer__arrow">▲</span><span class="pointer__label">${p.label}</span>`;
      pointerRow.appendChild(el);
    });

    // --- info badges ---
    infoRow.innerHTML = '';
    const info = step.info || {};
    Object.keys(info).forEach(label => {
      const badge = document.createElement('span');
      badge.className = 'badge';
      badge.innerHTML = `<span class="badge__label">${label}</span><span class="badge__value">${info[label]}</span>`;
      infoRow.appendChild(badge);
    });

    // --- message + status ---
    stepMessage.textContent = step.message;
    stepStatus.textContent = step.status || '';
    stepStatus.style.display = step.status ? 'inline-block' : 'none';
    card.classList.toggle('card--found', !!step.complete);

    // --- counter + ticks ---
    stepCounter.textContent = `STEP ${current + 1} / ${steps.length}`;
    [...ticksEl.children].forEach((t, i) => {
      t.classList.toggle('tick--active', i === current);
      t.classList.toggle('tick--done', i < current);
    });

    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === steps.length - 1;
  }

  prevBtn.addEventListener('click', () => { if (current > 0) { current--; render(); } });
  nextBtn.addEventListener('click', () => { if (current < steps.length - 1) { current++; render(); } });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') nextBtn.click();
    if (e.key === 'ArrowLeft') prevBtn.click();
  });

  render();
})();
