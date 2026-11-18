"""QR 코드 만들기 (로컬에서 실행: .venv/bin/python qr.py)

GitHub Actions 서버에는 한글 글꼴이 없어서, QR 그림은 이 컴퓨터에서 만들어 content/img/qr/ 에 넣어 둔다.
새 글을 쓰면 한 번 돌리기. 이미 있는 파일은 주소가 바뀌었을 때만 다시 만든다.

만드는 것
- 공통: site.png(실험실), channel.png(채널 구독), longform.png(롱폼), home.jpg(목록 옆 QR 카드)
- 글마다: NN-exp.png(이 실험), NN-video.png(이 영상), NN-card.jpg(네이버용 QR 4개 모음 그림)
"""
import json, os, re
import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'content')
OUT = os.path.join(SRC, 'img', 'qr')
LINKS = json.load(open(os.path.join(ROOT, 'links.json'), encoding='utf-8'))
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
F = lambda s, i=6: ImageFont.truetype(FONT, s, index=i)
INK, MUT, ACC, BG = '#2b2824', '#8b847a', '#7a5c3e', '#fffefb'
os.makedirs(OUT, exist_ok=True)
STAMP = os.path.join(OUT, 'urls.json')
stamp = json.load(open(STAMP)) if os.path.exists(STAMP) else {}


def qr(url, name):
    p = os.path.join(OUT, name)
    if stamp.get(name) == url and os.path.exists(p): return p
    segno.make(url, error='m').save(p, scale=10, border=2, dark=INK, light='#ffffff')
    stamp[name] = url
    return p


def card(items, name, title):
    """QR 여러 개를 한 장에: items = [(라벨, 작은 글, qr 경로)]"""
    n = len(items); cw = 300; W = cw * n + 60; H = 520
    im = Image.new('RGB', (W, H), BG); g = ImageDraw.Draw(im)
    g.rounded_rectangle((8, 8, W - 8, H - 8), radius=24, outline='#e6e1d8', width=3)
    g.text((W / 2, 52), title, font=F(34), fill=ACC, anchor='mm')
    for i, (lab, small, path) in enumerate(items):
        cx = 30 + cw * (i + .5)
        q = Image.open(path).convert('RGB').resize((230, 230), Image.NEAREST)
        im.paste(q, (int(cx - 115), 100))
        g.text((cx, 370), lab.split(' ', 1)[1] if lab[0] in '🧪📺🎬▶' else lab, font=F(28), fill=INK, anchor='mm')
        g.text((cx, 410), small, font=F(22, 2), fill=MUT, anchor='mm')
    g.text((W / 2, H - 50), '휴대폰 카메라로 비추면 바로 열려요', font=F(22, 2), fill=MUT, anchor='mm')
    im.save(os.path.join(OUT, name), quality=92)


def main():
    L = LINKS
    site, chan, lf = qr(L['site'], 'site.png'), qr(L['channel_sub'], 'channel.png'), qr(L['longform']['url'], 'longform.png')
    card([('🧪 실험실', 'simulatiolab.com', site), ('📺 채널 구독', '@simulatiolab', chan), ('🎬 롱폼 영상', L['longform']['short'], lf)],
         'home.jpg', '시뮬라티오 랩 더 보기')
    for fn in sorted(os.listdir(SRC)):
        m = re.match(r'(\d+)-.*\.md$', fn)
        if not m: continue
        nn = m.group(1); text = open(os.path.join(SRC, fn), encoding='utf-8').read()
        meta = dict(re.findall(r'^(\w+):[ \t]*(.*)$', text.split('---')[1], re.M))
        exp, video = meta.get('experiment', '').strip(), meta.get('video', '').strip()
        items = []
        if exp: items.append(('🧪 직접 돌려 보기', f'simulatiolab.com/{exp}', qr(f"https://simulatiolab.com/{exp}", f'{nn}-exp.png')))
        if video and video != L['longform']['url'] and L['longform']['id'] not in video:
            items.append(('▶ 쇼츠 영상', '30초 요약', qr(video, f'{nn}-video.png')))
            items.append(('🎬 롱폼 영상', L['longform']['short'], lf))
        elif video:
            items.append(('🎬 이 이야기 영상', '8분 롱폼', lf))
            items.append(('🧪 실험실 전체', 'simulatiolab.com', site))
        items.append(('📺 채널 구독', '@simulatiolab', chan))
        card(items, f'{nn}-card.jpg', '이 이야기, 영상과 실험으로 더 보기')
    json.dump(stamp, open(STAMP, 'w'), ensure_ascii=False, indent=1)
    print('QR 완료 →', OUT)


if __name__ == '__main__':
    main()
