#!/usr/bin/env python3
"""시뮬라티오 랩 블로그 만들기: content/*.md → docs/ (GitHub Pages)

  python3 build.py

- content/NN-slug.md : 글 한 편 (맨 위 --- 사이에 제목·날짜 등, 아래는 본문)
- content/plan.json  : 아직 안 쓴 다음 편 계획
- 게시일(date)이 지난 글만 블로그 첫 화면·RSS에 나온다. 매일 0시(한국 시간) GitHub Actions가 다시 만든다.
- 각 글 페이지 주소 뒤에 #naver 를 붙이면 '네이버 블로그로 옮기기' 버튼(제목·본문·태그 복사)이 나온다.

본문 쓰는 법 (마크다운 일부 + 약속 기호)
  ### 소제목           ---  구분(· · ·)          !! 강조 한 줄
  > 마지막 질문(인용)   ~~ 덧붙임(작은 글씨)    @@ 앞 문장 | 링크 글자 | 주소   (실험 링크 상자)
  ![사진 설명](img/02/a.jpg)   - 목록   1. 번호 목록   **굵게**   [글자](주소)
  {{photo a | 사진 설명(한국어) | ChatGPT에 줄 영어 부탁}}   ← 실사 사진 자리

실사 사진(ChatGPT 등으로 만든 것): content/photos/NN/ 폴더에 넣으면 그 편의 사진 자리에 들어간다.
  - 파일 이름이 자리 이름(a.png, b.jpg …)이면 그 자리로, 아니면 파일 이름 순서대로 빈자리를 채운다
  - 자리보다 많으면 남는 사진은 글 끝(덧붙임 앞)에 이어 붙인다. 비어 있는 자리는 화면에 안 보인다
  - 1600px·JPEG로 줄여 docs/photos/NN/ 에 넣는다(sips 또는 Pillow). 원본은 content/photos/ 에 그대로
"""
import subprocess
import datetime as dt, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(ROOT, 'content'), os.path.join(ROOT, 'docs')
SITE = 'https://heekeunlee.github.io/simulatiolab_blog/'
REPO = 'https://github.com/heekeunlee/simulatiolab_blog'
IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp')
PHOTO_RE = re.compile(r'^\{\{photo\s+(\w+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\}\}$')
BLOG = '시뮬라티오 랩 블로그'
KST = dt.timezone(dt.timedelta(hours=9))
TODAY = dt.datetime.now(KST).date()
WEEK = '월화수목금토일'
PLAN = []


def front(text):
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        meta[k.strip()] = v.strip()
    meta['no'] = int(meta['no'])
    meta['tags'] = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
    return meta, m.group(2).strip()


def inline(s, absolute=False):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[(.+?)\]\((https?://[^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


SENT_RE = re.compile(r'(?<=[.?!…])(\*\*)?(["”’\')]*)\s+')
def mobile_lines(s, limit=26, minpart=7, grouped=False):
    """네이버(휴대폰)용: 문장마다 줄 바꾸고, 긴 문장은 쉼표에서 한 번 더 끊는다(B안)"""
    keep = []
    s = re.sub(r'\[(.+?)\]\((https?://[^)]+)\)', lambda m: keep.append(m.group(0)) or f'\x00{len(keep)-1}\x00', s)
    sents = [x for x in SENT_RE.sub(lambda m: (m.group(1) or '') + m.group(2) + '\n', s).split('\n') if x.strip()]
    vis = lambda t: len(re.sub(r'\*\*|\x00\d+\x00', '', t))
    lines = []
    for t in sents:
        parts = [t]
        while vis(parts[-1]) > limit:
            cur = parts[-1]
            cuts = [m.end() for m in re.finditer(r', ', cur) if vis(cur[:m.end()]) >= minpart and vis(cur[m.end():]) >= minpart]
            if not cuts: break
            half = vis(cur) / 2
            c = min(cuts, key=lambda i: abs(vis(cur[:i]) - half))
            parts[-1:] = [cur[:c].rstrip(), cur[c:]]
        lines += [(k, x) for k, x in enumerate(parts)]
    out, bold = [], False
    for k, t in lines:
        if bold: t = '**' + t
        bold = t.count('**') % 2 == 1
        if bold: t += '**'
        t = re.sub(r'\x00(\d+)\x00', lambda m: keep[int(m.group(1))], t)
        t = t.replace('****', '')
        if grouped and k == 0: out.append([t])
        elif grouped: out[-1].append(t)
        else: out.append(t)
    return out


EMPTY = '<p><br></p>'
def nb_para(s):
    """C안: 문장마다 빈 줄. 쉼표에서 끊은 줄은 같은 덩어리"""
    return EMPTY.join('<p>' + '<br>'.join(inline(x) for x in g) + '</p>' for g in mobile_lines(s, grouped=True))


def blocks(body):
    out, cur = [], []
    for line in body.splitlines():
        if line.strip() == '':
            if cur: out.append(cur); cur = []
        else:
            cur.append(line)
    if cur: out.append(cur)
    return out


def render(body, naver=False, base='', photos=None, extra=()):
    """naver=True: 네이버 스마트에디터에 붙여 넣기 좋은 인라인 서식 HTML"""
    h, photos = [], photos or {}
    def fig(src, cap):
        if naver: return f'<p style="text-align:center"><img src="{SITE}{src}" alt="{html.escape(cap)}"><br><span style="font-size:13px;color:#888">{html.escape(cap)}</span></p>'
        return f'<figure class="photo"><img src="{base}{src}" alt="{html.escape(cap)}" loading="lazy"><figcaption>{html.escape(cap)}</figcaption></figure>'
    for b in blocks(body):
        first = b[0]
        m = PHOTO_RE.match(first)
        if m:
            slot, desc, _ = m.groups()
            if slot in photos: h.append(fig(photos[slot], f'{desc} · AI 생성 이미지'))
            continue
        if first.startswith('~~ ') and extra:
            for src in extra: h.append(fig(src, 'AI 생성 이미지'))
            extra = ()
        if first.startswith('### '):
            t = inline(first[4:])
            h.append(f'<p><b><span style="font-size:19px;color:#7a5c3e">{t}</span></b></p>' if naver else f'<h3>{t}</h3>')
        elif first.strip() == '---':
            h.append('<p style="text-align:center;color:#8b847a">· · ·</p>' if naver else '<p class="orn">· · ·</p>')
        elif first.startswith('!! '):
            t = inline(first[3:])
            h.append(f'<p><b><span style="font-size:19px">{t}</span></b></p>' if naver else f'<p class="pull">{t}</p>')
        elif first.startswith('> '):
            t = inline(' '.join(x[2:] for x in b))
            h.append(f'<p style="text-align:center"><b><span style="font-size:19px">"{t}"</span></b></p>' if naver else f'<blockquote>{t}</blockquote>')
        elif first.startswith('%% '):
            title = inline(first[3:]); items = [inline(x[2:]) for x in b[1:] if x.startswith('- ')]
            if naver:
                h.append(f'<p><b><span style="font-size:17px;color:#1f9d63">💡 {title}</span></b></p>' + ''.join(f'<p>✔ {it}</p>' for it in items))
            else:
                h.append(f'<aside class="insight"><div class="ih">💡 {title}</div><ul>' + ''.join(f'<li>{it}</li>' for it in items) + '</ul></aside>')
        elif first.startswith('~~ '):
            t = inline(' '.join(b)[3:])
            h.append(f'<p><span style="font-size:13px;color:#888">{t}</span></p>' if naver else f'<p class="note">{t}</p>')
        elif first.startswith('@@ '):
            lead, txt, url = [x.strip() for x in first[3:].split('|')]
            if naver:
                h.append(f'<p>{inline(lead)}<br>→ <a href="{url}">{inline(txt)}</a></p>')
            else:
                h.append(f'<p class="link">{inline(lead)}<br>→ <a href="{url}" target="_blank" rel="noopener">{inline(txt)}</a></p>')
        elif re.match(r'!\[.*\]\(.*\)$', first):
            alt, src = re.match(r'!\[(.*)\]\((.*)\)', first).groups()
            if naver:
                h.append(f'<p style="text-align:center"><img src="{SITE}{src}" alt="{html.escape(alt)}"><br><span style="font-size:13px;color:#888">{inline(alt)}</span></p>')
            else:
                h.append(f'<figure><img src="{base}{src}" alt="{html.escape(alt)}" loading="lazy"><figcaption>{inline(alt)}</figcaption></figure>')
        elif all(x.startswith('- ') for x in b):
            items = ''.join(f'<li>{inline(x[2:])}</li>' for x in b)
            h.append(f'<ul>{items}</ul>')
        elif all(re.match(r'\d+\. ', x) for x in b):
            items = ''.join(f'<li>{inline(re.sub(r"^\d+\. ", "", x))}</li>' for x in b)
            h.append(f'<ol>{items}</ol>')
        else:
            if naver == 'nb':
                h.append(EMPTY.join(nb_para(x) for x in b))
            else:
                h.append('<p>' + '<br>'.join(inline(x) for x in b) + '</p>')
    return ('\n' + EMPTY * 2 + '\n' if naver == 'nb' else '\n').join(h)


def plain(body):
    t = re.sub(r'!\[.*?\]\(.*?\)', '', body)
    t = re.sub(r'^\{\{photo.*?\}\}$', '', t, flags=re.M)
    t = re.sub(r'^(###|!!|>|~~|@@|%%|-|\d+\.)\s*', '', t, flags=re.M)
    t = re.sub(r'\*\*|\[|\]\(.*?\)', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def shrink(src, dst):
    """사진을 긴 변 1600px JPEG로 (없으면 그대로 복사)"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        from PIL import Image
        im = Image.open(src).convert('RGB'); im.thumbnail((1600, 1600)); im.save(dst, 'JPEG', quality=84, optimize=True); return dst
    except Exception:
        pass
    if shutil.which('sips'):
        r = subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '84', '-Z', '1600', src, '--out', dst], capture_output=True)
        if r.returncode == 0: return dst
    dst = os.path.splitext(dst)[0] + os.path.splitext(src)[1].lower(); shutil.copy(src, dst); return dst


def photos_for(meta, body):
    """사진 자리 목록과 실제 파일 연결: {slot: 'photos/NN/a.jpg'}, 남는 사진 목록"""
    slots = [PHOTO_RE.match(b[0]).groups() for b in blocks(body) if PHOTO_RE.match(b[0])]
    nn = f"{meta['no']:02d}"
    folder = os.path.join(SRC, 'photos', nn)
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT)) if os.path.isdir(folder) else []
    named = {os.path.splitext(f)[0].lower(): f for f in files}
    used, mapping = set(), {}
    for slot, _, _ in slots:
        if slot.lower() in named: mapping[slot] = named[slot.lower()]; used.add(named[slot.lower()])
    rest = [f for f in files if f not in used]
    for slot, _, _ in slots:
        if slot not in mapping and rest: mapping[slot] = rest.pop(0)
    out, extra = {}, []
    for slot, f in mapping.items():
        out[slot] = os.path.relpath(shrink(os.path.join(folder, f), os.path.join(OUT, 'photos', nn, slot + '.jpg')), OUT)
    for i, f in enumerate(rest):
        extra.append(os.path.relpath(shrink(os.path.join(folder, f), os.path.join(OUT, 'photos', nn, f'extra{i + 1}.jpg')), OUT))
    return slots, out, extra


def daystr(d):
    d = dt.date.fromisoformat(d)
    return f'{d.year}. {d.month}. {d.day}. ({WEEK[d.weekday()]})'


HEAD = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{image}"><meta property="og:type" content="{ogtype}">
<link rel="alternate" type="application/rss+xml" title="{blog}" href="{base}rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Nanum+Gothic:wght@400;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{base}style.css?v={ver}"></head><body>
<header class="top"><a class="brand" href="{base}"><span class="logo">S</span>{blog}</a><nav><a href="{base}">글 목록</a><a href="https://simulatiolab.com" target="_blank" rel="noopener">실험실</a><a href="https://www.youtube.com/@simulatiolab" target="_blank" rel="noopener">유튜브</a><a href="{base}dashboard.html">대시보드</a></nav></header>
'''
FOOT = '''<footer class="foot">시뮬라티오 랩 · Lab장 · <a href="https://simulatiolab.com" target="_blank" rel="noopener">simulatiolab.com</a> · <a href="{base}rss.xml">RSS</a></footer>
<script src="{base}app.js?v={ver}"></script></body></html>'''


LINKS = json.load(open(os.path.join(ROOT, 'links.json'), encoding='utf-8'))


def more_items(meta):
    """QR 상자 칸: (아이콘, 라벨, 작은 글, 주소, QR 파일). qr.py와 같은 순서"""
    L, nn = LINKS, f"{meta['no']:02d}"
    exp, video, lf = meta.get('experiment'), meta.get('video') or '', L['longform']
    it = []
    if exp: it.append(('🧪', '직접 돌려 보기', f'simulatiolab.com/{exp}', f'https://simulatiolab.com/{exp}', f'{nn}-exp.png'))
    if video and lf['id'] not in video:
        it.append(('▶', '쇼츠 영상', '30초 요약', video, f'{nn}-video.png'))
        it.append(('🎬', '롱폼 영상', lf['short'], lf['url'], 'longform.png'))
    elif video:
        it.append(('🎬', '이 이야기 영상', '8분 롱폼', lf['url'], 'longform.png'))
        it.append(('🧪', '실험실 전체', 'simulatiolab.com', L['site'], 'site.png'))
    it.append(('📺', '채널 구독', '@simulatiolab', L['channel_sub'], 'channel.png'))
    return it


def quick(meta, naver=False):
    """글 맨 위 한 줄 링크"""
    it = more_items(meta)
    if naver:
        return '<p><span style="font-size:13px;color:#8b847a">' + ' · '.join(f'{i} <a href="{u}">{l}</a>' for i, l, _, u, _ in it) + '</span></p>'
    return '<div class="quick">' + ''.join(f'<a href="{u}" target="_blank" rel="noopener">{i} {l}</a>' for i, l, _, u, _ in it) + '</div>'


def more_box(meta, base='', naver=False):
    """글 끝 QR 상자: 실험·쇼츠·롱폼·채널"""
    it, nn = more_items(meta), f"{meta['no']:02d}"
    if naver:
        lines = ''.join(f'<p>{i} {l}: <a href="{u}">{u.replace("https://", "")}</a></p>' for i, l, _, u, _ in it)
        return (f'<p><br></p><p style="text-align:center"><b><span style="font-size:17px;color:#7a5c3e">이 이야기, 영상과 실험으로 더 보기</span></b></p>'
                f'<p style="text-align:center"><img src="{SITE}img/qr/{nn}-card.jpg" alt="실험·영상·채널 QR 코드"></p>{lines}')
    cards = ''.join(f'<a class="q" href="{u}" target="_blank" rel="noopener"><img src="{base}img/qr/{f}" alt="{l} QR" loading="lazy"><b>{i} {l}</b><span>{html.escape(sm)}</span></a>' for i, l, sm, u, f in it)
    return f'<section class="more"><h2>이 이야기, 영상과 실험으로 더 보기</h2><div class="qrs">{cards}</div><p>휴대폰 카메라로 QR을 비추면 바로 열려요 · 실험 80여 개는 <a href="{LINKS["site"]}" target="_blank" rel="noopener">simulatiolab.com</a></p></section>'


def teaser(meta, nxt, naver=False):
    """다음 편 예고: front matter의 teaser + 다음 편 제목·공개일"""
    if not meta.get('teaser') or not nxt: return ''
    when = daystr(nxt['date'])
    if naver:
        return (f'<p><br></p><p style="text-align:center;color:#8b847a">· · ·</p><p><b><span style="font-size:17px;color:#7a5c3e">📮 다음 편 예고 · {when}</span></b></p>'
                f'<p><b>{html.escape(nxt["title"])}</b></p>{nb_para(meta["teaser"])}<p><span style="color:#8b847a">이웃 추가해 두시면 새 글이 올라올 때 알려 드려요.</span></p>')
    link = f'../{nxt["slug"]}/' if nxt.get('slug') else ''
    head = f'<a href="{link}" class="tz" data-date="{nxt["date"]}">{html.escape(nxt["title"])}</a>' if link else html.escape(nxt['title'])
    return f'<aside class="teaser"><div class="th">📮 다음 편 예고 · <span>{when}</span></div><div class="tt">{head}</div><p>{inline(meta["teaser"])}</p></aside>'


def photo_box(meta):
    """글 페이지 #photos: ChatGPT에 줄 부탁 문구와 올릴 곳"""
    nn = f"{meta['no']:02d}"
    if not meta['slots']: return ''
    rows = ''
    for slot, desc, prompt in meta['slots']:
        ok = slot in meta['photos']
        rows += f'<li><b>{slot}</b> {"✅" if ok else "⬜"} {html.escape(desc)}<div class="pr">{html.escape(prompt)}</div></li>'
    req = (f"아래 블로그 글에 넣을 실사 사진 {len(meta['slots'])}장을 만들어 줘. 각각 따로, 가로 3:2, 사진처럼 자연스럽게. "
           "실존 인물·알아볼 수 있는 얼굴·상표·로고·읽을 수 있는 글자는 넣지 마.\n\n글 제목: " + meta['title'] + "\n\n" +
           "\n\n".join(f"[{slot}] {desc}\n{prompt}" for slot, desc, prompt in meta['slots']))
    return f'''<section id="photos" class="naver photos" hidden>
<h2>📸 실사 사진 만들기 ({meta['photos_filled']}/{len(meta['slots'])})</h2>
<p>① 아래 "ChatGPT 부탁 복사"를 눌러 ChatGPT에 붙여 넣기 → ② 만든 사진을 내려받기 → ③ "사진 올리러 가기"에서 끌어다 놓고 <b>Commit changes</b> → 1~2분 뒤 글에 자동으로 들어가요. 파일 이름을 a.png, b.png로 바꾸면 그 자리로, 그냥 두면 만든 순서대로 빈자리를 채워요.</p>
<div class="nbtn"><button data-copy="pq">ChatGPT 부탁 복사</button><a class="up" href="{REPO}/upload/main/content/photos/{nn}" target="_blank" rel="noopener">사진 올리러 가기 →</a><span class="msg"></span></div>
<ol class="slots">{rows}</ol><textarea id="pq" class="cp">{html.escape(req)}</textarea></section>'''


def tagbox(tags):
    """네이버 태그: 한꺼번에(#태그 #태그) + 하나씩 누르는 칩(누르면 복사 → 태그 칸 ⌘V → 엔터)"""
    chips = ''.join(f'<button class="tg" data-tag="{html.escape(t)}">#{html.escape(t)}</button>' for t in tags)
    return (f'<textarea id="ng" class="cp">{" ".join("#" + t for t in tags)}</textarea>'
            f'<div class="tags1"><p>③ 태그가 한 덩어리로 들어가면: 아래를 <b>하나씩 눌러 복사 → 태그 칸 ⌘V → 엔터</b> (누른 건 흐려져요)</p>{chips}</div>')


def essays(ver):
    """content/essays: '실험 뒤의 생각' 작성 대기실(네이버가 원본 → noindex). /essays/ 안내·목록, /essays/<slug>/ 네이버 옮기기"""
    E = os.path.join(SRC, 'essays')
    if not os.path.isdir(E): return 0
    NOIDX = '<meta name="robots" content="noindex,nofollow"></head>'
    def page(title, base, inner):
        h = HEAD.format(title=html.escape(title) + ' | 실험 뒤의 생각', desc='실험 뒤의 생각 · 작성 대기', image=SITE + 'img/qr/01-card.jpg', ogtype='article', blog=BLOG, base=base, ver=ver)
        return h.replace('</head>', NOIDX, 1) + inner + FOOT.format(base=base, ver=ver)
    topics = json.load(open(os.path.join(E, 'topics.json'), encoding='utf-8'))
    done = {}
    for fn in sorted(os.listdir(E)):
        if not re.match(r'\d+-.*\.md$', fn): continue
        meta, body = front(open(os.path.join(E, fn), encoding='utf-8').read())
        done[meta['no']] = meta
        d = os.path.join(OUT, 'essays', meta['slug']); os.makedirs(d, exist_ok=True)
        tail = f'<p style="text-align:right;color:#8b847a">— Lab장 (시뮬라티오 랩)</p>' + EMPTY + f'<p><span style="color:#8b847a">이 생각이 시작된 실험, 직접 돌려 보기 →</span> <a href="{meta["link"]}">{meta["link"].replace("https://", "")}</a></p>'
        nb = render(body, naver='nb') + EMPTY * 2 + tail
        inner = f'''<main class="post"><div class="sched">📝 {html.escape(meta.get('status', '대기'))} · 네이버 예약 {html.escape(meta.get('planned', ''))}</div>
<div class="cat">실험 뒤의 생각 · {meta['no']}편 · 짝 실험 글 <a href="../../p/{meta['pair']}/">{meta['pair']}</a></div>
<h1>{html.escape(meta['title'])}</h1>
<section id="naver" class="naver">
<h2>네이버 블로그로 옮기기</h2>
<p>① 제목 → 제목 칸 ⌘V · ② 본문 → 본문 ⌘V · ③ 태그 → 발행 창 태그 칸 · ④ 카테고리 <b>실험 뒤의 생각</b> · 주제 <b>일상·생각</b> · ⑤ 소제목은 굵게+마루부리, 큰 문장(!!)은 가운데 정렬 · ⑥ 발행 뒤 status를 '발행'으로</p>
<div class="nbtn"><button data-copy="nt">① 제목 복사</button><button data-copy="nb">② 본문 복사</button><button data-copy="ng">③ 태그 한꺼번에 복사</button><span class="msg"></span></div>
<div id="nt" class="cp">{html.escape(meta['title'])}</div><div id="nb" class="cp">{nb}</div>{tagbox(meta['tags'])}
</section>
<article id="body">{render(body, base='../../')}</article><p class="sign">— Lab장</p></main>'''
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page(meta['title'], '../../', inner))
    _, guide = '', open(os.path.join(E, 'GUIDE.md'), encoding='utf-8').read()
    rows = ''.join(f'<li><b>{t["no"]}.</b> ' + (f'<a href="{done[t["no"]]["slug"]}/">{html.escape(t["title"])}</a> <span class="ok">✍️ {html.escape(done[t["no"]].get("status", "대기"))}</span>' if t['no'] in done else f'{html.escape(t["title"])} <span class="todo">· 아직</span>') + f'<br><small>짝 실험 글 <a href="../p/{t["pair"]}/">{t["pair"]}</a> · {html.escape(t["idea"])}</small></li>' for t in topics)
    inner = f'''<main class="post"><div class="cat">네이버 블로그 카테고리 · 작성 대기실</div><h1>실험 뒤의 생각</h1><p class="sub">인문학적 메시지 · 일상 속 인사이트 · 작은 글, 큰 울림</p>
<article id="body">{render(guide, base='../')}<h3>글 목록 ({len(done)}/{len(topics)})</h3><ol class="essays" style="list-style:none;padding:0">{rows}</ol></article></main>'''
    os.makedirs(os.path.join(OUT, 'essays'), exist_ok=True)
    open(os.path.join(OUT, 'essays', 'index.html'), 'w', encoding='utf-8').write(page('작성 대기실', '../', inner))
    return len(done)


def main():
    ver = dt.datetime.now(KST).strftime('%Y%m%d%H%M')
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(SRC, 'img'), os.path.join(OUT, 'img'))
    for f in ('style.css', 'app.js', 'index.html', 'dashboard.html'):
        shutil.copy(os.path.join(ROOT, 'web', f), os.path.join(OUT, f))
    global PLAN
    PLAN = json.load(open(os.path.join(SRC, 'plan.json'), encoding='utf-8'))
    posts = []
    for fn in sorted(os.listdir(SRC)):
        if not re.match(r'\d+-.*\.md$', fn): continue
        meta, body = front(open(os.path.join(SRC, fn), encoding='utf-8').read())
        meta['excerpt'] = plain(body)[:150]
        meta['chars'] = len(plain(body))
        meta['published'] = dt.date.fromisoformat(meta['date']) <= TODAY
        meta['slots'], meta['photos'], meta['extra'] = photos_for(meta, body)
        meta['photos_total'], meta['photos_filled'] = len(meta['slots']), len(meta['photos']) + len(meta['extra'])
        posts.append((meta, body))
    posts.sort(key=lambda x: x[0]['no'])
    for i, (meta, body) in enumerate(posts):
        d = os.path.join(OUT, 'p', meta['slug']); os.makedirs(d)
        base = '../../'
        prev_ = posts[i - 1][0] if i > 0 else None
        next_ = posts[i + 1][0] if i + 1 < len(posts) else None
        nav = '<nav class="pn">' + (f'<a href="../{prev_["slug"]}/">← {html.escape(prev_["title"])}</a>' if prev_ else '<span></span>') + \
              (f'<a data-date="{next_["date"]}" class="nx" href="../{next_["slug"]}/">{html.escape(next_["title"])} →</a>' if next_ else '<span></span>') + '</nav>'
        exp = meta.get('experiment')
        cta = f'<div class="cta"><a class="btn" href="https://simulatiolab.com/{exp}" target="_blank" rel="noopener">🧪 이 실험 직접 돌려 보기</a>' + \
              (f'<a class="btn ghost" href="{meta["video"]}" target="_blank" rel="noopener">▶ 영상으로 보기</a>' if meta.get('video') else '') + '</div>'
        tags = ' '.join(f'<span>#{html.escape(t)}</span>' for t in meta['tags'])
        sched = '' if meta['published'] else f'<div class="sched">⏰ 예약 글 · {daystr(meta["date"])} 공개 예정</div>'
        PH = dict(photos=meta['photos'], extra=meta['extra'])
        nxt_meta = next_ or next((x for x in PLAN if x['no'] == meta['no'] + 1), None)
        naverhtml = quick(meta, naver=True) + render(body, naver='nb', **PH) + '<p style="text-align:right;color:#8b847a">— 시뮬라티오 랩, Lab장</p>' + more_box(meta, naver=True) + teaser(meta, nxt_meta, naver=True)
        page = HEAD.format(title=html.escape(meta['title']) + ' | ' + BLOG, desc=html.escape(meta['excerpt']), image=SITE + meta['cover'], ogtype='article', blog=BLOG, base=base, ver=ver) + f'''
<main class="post">{sched}
<div class="cat">{html.escape(meta['category'])} · {meta['no']}편</div>
<h1>{html.escape(meta['title'])}</h1><p class="sub">{html.escape(meta.get('subtitle', ''))}</p>
<div class="meta"><span class="who"><span class="logo s">S</span>Lab장</span><span>{daystr(meta['date'])}</span></div>
{quick(meta)}
<article id="body">{render(body, base=base, **PH)}</article>
<p class="sign">— 시뮬라티오 랩, Lab장</p>
{more_box(meta, base=base)}{teaser(meta, nxt_meta)}<div class="tags">{tags}</div>{nav}
<section id="naver" class="naver" hidden>
<h2>네이버 블로그로 옮기기</h2>
<p>① 제목 → 제목 칸 ⌘V · ② 본문 → 본문 ⌘V (사진도 함께 붙어요. 안 붙으면 사진만 따로 올리기) · ③ 태그 → 발행 창 태그 칸 · ④ 카테고리 <b>돌려 보는 실험실</b> · 주제 <b>교육·학문</b> · ⑤ 발행 뒤 네이버 주소를 content/{meta['no']:02d}-{meta['slug']}.md 의 naver_url에 적기</p>
<div class="nbtn"><button data-copy="nt">① 제목 복사</button><button data-copy="nb">② 본문 복사</button><button data-copy="ng">③ 태그 한꺼번에 복사</button><span class="msg"></span></div>
<div id="nt" class="cp">{html.escape(meta['title'])}</div><div id="nb" class="cp">{naverhtml}</div>{tagbox(meta['tags'])}
</section>{photo_box(meta)}</main>''' + FOOT.format(base=base, ver=ver)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
    plan = json.load(open(os.path.join(SRC, 'plan.json'), encoding='utf-8'))
    data = {'built': dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M'), 'today': TODAY.isoformat(),
            'posts': [{k: m[k] for k in ('no', 'slug', 'title', 'subtitle', 'date', 'category', 'tags', 'cover', 'experiment', 'video', 'naver_url', 'excerpt', 'chars', 'published', 'photos_total', 'photos_filled')} for m, _ in posts],
            'plan': plan}
    json.dump(data, open(os.path.join(OUT, 'posts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # RSS: 공개된 글만 (나중에 네이버 등과 연동할 때 사용)
    items = ''
    for m, body in sorted(posts, key=lambda x: x[0]['date'], reverse=True):
        if not m['published']: continue
        pub = dt.datetime.fromisoformat(m['date'] + 'T09:00:00+09:00').strftime('%a, %d %b %Y %H:%M:%S +0900')
        items += f'''<item><title>{html.escape(m['title'])}</title><link>{SITE}p/{m['slug']}/</link><guid>{SITE}p/{m['slug']}/</guid><pubDate>{pub}</pubDate><category>{html.escape(m['category'])}</category><description><![CDATA[{render(body, naver=True, photos=m['photos'], extra=m['extra'])}]]></description></item>\n'''
    rss = f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{BLOG}</title><link>{SITE}</link><description>작은 규칙, 큰 세상 — 시뮬레이션으로 돌려 보는 '왜 그럴까'</description><language>ko</language>\n{items}</channel></rss>'''
    open(os.path.join(OUT, 'rss.xml'), 'w', encoding='utf-8').write(rss)
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    ne = essays(ver)
    print(f'에세이 {ne}편 · ', end='')
    print(f'{len(posts)}편 (공개 {sum(m["published"] for m, _ in posts)}) · 계획 {len(plan)}편 · {TODAY}')


if __name__ == '__main__':
    main()
