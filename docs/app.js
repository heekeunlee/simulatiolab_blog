// 시뮬라티오 랩 블로그: 목록·대시보드 그리기, 네이버 옮기기 버튼
(function () {
  const W = '월화수목금토일';
  const today = () => { const d = new Date(Date.now() + 9 * 3600e3); return d.toISOString().slice(0, 10); };   // 한국 날짜
  const day = (s) => { const d = new Date(s + 'T00:00:00+09:00'); return `${d.getMonth() + 1}/${d.getDate()}(${W[(d.getDay() + 6) % 7]})`; };
  const dleft = (s) => Math.round((new Date(s + 'T00:00:00+09:00') - new Date(today() + 'T00:00:00+09:00')) / 864e5);
  const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const T = today();

  // 글 페이지: #naver 이면 옮기기 상자 보이기, 예약 글의 '다음 글' 링크 숨기기
  ['naver', 'photos'].forEach((id) => { const nv = document.getElementById(id); if (!nv) return;
    if (location.hash === '#' + id) { nv.hidden = false; setTimeout(() => nv.scrollIntoView({ behavior: 'smooth' }), 300); }
    const msg = nv.querySelector('.msg');
    nv.querySelectorAll('[data-copy]').forEach((b) => b.addEventListener('click', async () => {
      const el = document.getElementById(b.dataset.copy); let ok = false;
      try {
        if (el.tagName === 'TEXTAREA' || el.id === 'nt') { await navigator.clipboard.writeText(el.value || el.textContent.trim()); ok = true; }
        else { await navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([el.innerHTML], { type: 'text/html' }), 'text/plain': new Blob([el.innerText], { type: 'text/plain' }) })]); ok = true; }
      } catch (e) {
        const r = document.createRange(); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); try { ok = document.execCommand('copy'); } catch (e2) {} s.removeAllRanges();
      }
      msg.textContent = ok ? b.textContent.replace(/^[①②③]\s*/, '') + ' 복사됨 ✓' : '복사가 막혔어요. 직접 선택해 ⌘C';
      setTimeout(() => (msg.textContent = ''), 2500);
    }));
  });
  document.querySelectorAll('.pn a.nx').forEach((a) => { if (a.dataset.date > T && !location.hash) a.style.visibility = 'hidden'; });

  const L = document.getElementById('list'), D = document.getElementById('dash');
  if (!L && !D) return;
  fetch('posts.json?t=' + Date.now()).then((r) => r.json()).then((data) => {
    const posts = data.posts.slice().sort((a, b) => b.date.localeCompare(a.date));
    if (L) home(posts, data); else dash(data);
  });

  function home(posts, data) {
    const pub = posts.filter((p) => p.date <= T), cat = new URLSearchParams(location.search).get('c');
    const cats = {}; pub.forEach((p) => (cats[p.category] = (cats[p.category] || 0) + 1));
    document.getElementById('cats').innerHTML = `<a href="./" class="${cat ? '' : 'on'}"><span>전체 글</span><span>${pub.length}</span></a>` +
      Object.entries(cats).map(([c, n]) => `<a href="?c=${encodeURIComponent(c)}" class="${c === cat ? 'on' : ''}"><span>${esc(c)}</span><span>${n}</span></a>`).join('');
    const shown = pub.filter((p) => !cat || p.category === cat);
    const nxt = posts.filter((p) => p.date > T).sort((a, b) => a.date.localeCompare(b.date))[0] || data.plan.find((p) => p.date > T);
    L.innerHTML = (nxt ? `<div class="next">📅 다음 글 <b>${day(nxt.date)}</b> 공개 예정 · ${esc(nxt.title)}</div>` : '') +
      (shown.length ? shown.map((p) => `<a class="card" href="p/${p.slug}/"><div><div class="d">${esc(p.category)} · ${day(p.date)}</div><h3>${esc(p.title)}</h3><p>${esc(p.excerpt)}…</p><div class="d">#${p.tags.slice(0, 4).map(esc).join(' #')}</div></div><img src="${p.cover}" alt="" loading="lazy"></a>`).join('')
        : '<div class="empty">아직 공개된 글이 없어요.</div>');
  }

  function dash(data) {
    const rows = data.posts.map((p) => ({ ...p, kind: 'post' })).concat(data.plan.map((p) => ({ ...p, kind: 'plan' }))).sort((a, b) => a.date.localeCompare(b.date));
    const pubN = data.posts.filter((p) => p.date <= T).length, navN = data.posts.filter((p) => p.naver_url).length;
    const waitN = data.posts.filter((p) => p.date <= T && !p.naver_url).length, next = rows.find((r) => r.date > T);
    document.getElementById('kpis').innerHTML = [
      ['공개된 글', pubN + '편'], ['네이버 게시', navN + '편'], ['네이버 대기', waitN + '편'],
      ['예약·계획', rows.filter((r) => r.date > T).length + '편'], ['다음 공개', next ? `${day(next.date)} · D-${dleft(next.date)}` : '—'],
    ].map(([a, b]) => `<div class="kpi"><span>${a}</span><b>${b}</b></div>`).join('');
    D.innerHTML = rows.map((r) => {
      let st;
      if (r.kind === 'plan') st = '<span class="st plan">계획 · 글 쓰기 전</span>';
      else if (r.naver_url) st = '<span class="st nav">네이버 게시</span>';
      else if (r.date > T) st = `<span class="st res">예약 · D-${dleft(r.date)}</span>`;
      else st = dleft(r.date) < -2 ? '<span class="st late">공개 · 네이버 늦음</span>' : '<span class="st pub">공개 · 네이버 대기</span>';
      const acts = r.kind === 'post'
        ? `<a href="p/${r.slug}/">보기</a><a href="p/${r.slug}/#photos">사진 ${r.photos_filled}/${r.photos_total}</a><a href="p/${r.slug}/#naver">네이버 옮기기</a>${r.naver_url ? `<a href="${esc(r.naver_url)}" target="_blank" rel="noopener">네이버 글</a>` : ''}`
        : `<span style="color:#999">${esc(r.note || '')}</span>`;
      return `<tr class="${r.date === T ? 'today' : ''}"><td class="n">${r.no}편</td><td class="dt">${day(r.date)}</td><td>${esc(r.title)}${r.kind === 'post' ? `<div style="color:#999;font-size:12px">${r.chars.toLocaleString()}자 · ${esc(r.category)}</div>` : ''}</td><td>${st}</td>
        <td><a href="https://simulatiolab.com/${r.experiment}" target="_blank" rel="noopener">${esc(r.experiment)}</a>${r.video ? ` · <a href="${esc(r.video)}" target="_blank" rel="noopener">영상</a>` : ''}</td><td class="acts">${acts}</td></tr>`;
    }).join('');
    document.getElementById('built').textContent = `마지막으로 만든 시각 ${data.built} (매일 0시 자동)`;
  }
})();
