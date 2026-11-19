# 시뮬라티오 랩 블로그

일상의 "왜 그럴까"를 시뮬레이션으로 돌려 보는 Lab장의 글. 2~3일에 한 편.

- 블로그: https://heekeunlee.github.io/simulatiolab_blog/
- 대시보드(일정·상태·네이버 옮기기): https://heekeunlee.github.io/simulatiolab_blog/dashboard.html
- RSS(공개된 글만): https://heekeunlee.github.io/simulatiolab_blog/rss.xml
- 실험실: https://simulatiolab.com · 유튜브: https://www.youtube.com/@simulatiolab

## 구조
- `content/NN-slug.md` 글 한 편(위쪽 `---` 사이에 제목·공개일 등). 쓰는 법은 `build.py` 맨 위 설명
- `content/plan.json` 아직 안 쓴 다음 편 계획
- `content/img/NN/` 그림
- `web/` 화면(목록·대시보드·스타일·스크립트)
- `python3 build.py` → `docs/`(GitHub Pages가 보여 주는 곳). 공개일이 된 글만 목록·RSS에 나옴
- `.github/workflows/daily.yml` 매일 0시(한국 시간)와 글을 고칠 때마다 자동으로 다시 만듦

## 실사 사진 (ChatGPT 등)
글 속 `{{photo a | 설명 | 영어 부탁}}` 자리마다 사진이 들어간다. 글 페이지 주소#photos 에서 ChatGPT 부탁 문구를 복사하고, 만든 사진을 `content/photos/NN/`에 올리면(깃허브 웹에서 끌어다 놓기 → Commit changes) 자동으로 1600px JPEG로 줄여 글·네이버 옮기기 본문·RSS에 들어간다. 파일 이름이 a.png, b.png … 이면 그 자리로, 아니면 이름 순서대로 빈자리를 채운다. 사진 설명에는 'AI 생성 이미지'가 붙는다.

## 네이버 블로그
공개된 글 페이지 주소 뒤에 `#naver`를 붙이면 제목·본문(사진 포함)·태그 복사 버튼이 나온다. 네이버에 올린 뒤 주소를 글 파일의 `naver_url`에 적으면 대시보드 상태가 바뀐다. 나중에 자동 연동은 `rss.xml`을 쓴다.

글 속 숫자는 [simulatiolab.com](https://simulatiolab.com)의 시뮬레이션 모델을 실제로 돌린 값이다. 글 정리에 AI(Claude)의 도움을 받았다.

## 실험·영상 링크와 QR (2026-11-18)
- 글마다 맨 위 한 줄 링크(실험·쇼츠·롱폼·채널 구독)와 글 끝 "영상과 실험으로 더 보기" QR 상자가 자동으로 붙는다. 네이버 옮기기 본문에도 QR 모음 그림 한 장과 주소가 들어간다.
- 주소는 `links.json`(사이트·채널·롱폼). 롱폼이 늘면 여기만 고친다.
- QR 그림은 **이 컴퓨터에서** 만든다(서버엔 한글 글꼴이 없음): `python3 -m venv .venv && .venv/bin/pip install segno pillow` 한 번, 그 뒤 새 글을 쓸 때마다 `.venv/bin/python qr.py` → `content/img/qr/`

## 실험 뒤의 생각 (네이버 전용 인문학 에세이, 2026-11-19)
- `content/essays/GUIDE.md` 쓰는 기준 · `topics.json` 12편 주제 · `NN-slug.md` 원고(status 대기/발행, planned 네이버 예약 시각)
- 작성 대기실: https://heekeunlee.github.io/simulatiolab_blog/essays/ (네이버가 원본이라 noindex, 글 목록·RSS에 안 나옴)
- 글마다 /essays/slug/ 에 네이버 옮기기(제목·본문·태그 복사) 상자
