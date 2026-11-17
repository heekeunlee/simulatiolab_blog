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

## 네이버 블로그
공개된 글 페이지 주소 뒤에 `#naver`를 붙이면 제목·본문(사진 포함)·태그 복사 버튼이 나온다. 네이버에 올린 뒤 주소를 글 파일의 `naver_url`에 적으면 대시보드 상태가 바뀐다. 나중에 자동 연동은 `rss.xml`을 쓴다.

글 속 숫자는 [simulatiolab.com](https://simulatiolab.com)의 시뮬레이션 모델을 실제로 돌린 값이다. 글 정리에 AI(Claude)의 도움을 받았다.
