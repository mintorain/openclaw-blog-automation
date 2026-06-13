# 티스토리 자동 포스팅 (Selenium 골격)

마크다운 글을 읽어 티스토리에 자동 로그인 → 글쓰기 → 발행하는 최소 골격입니다.

## 구조

```
tistory/
├── main.py            # 진입점 (쿠키 우선 → 비밀번호 폴백)
├── save_cookies.py    # 사람이 1회 로그인 → 쿠키 저장 (캡차 회피)
├── config.py          # .env 로딩/검증 (불변 Config)
├── driver_factory.py  # 크롬 드라이버 생성 (탐지 우회 옵션)
├── tistory_bot.py     # 로그인/글쓰기/발행 핵심 로직
├── cookie_store.py    # 쿠키 저장/주입
├── post_reader.py     # posts/*.md -> (제목, 본문)
├── cookies.json       # (생성됨) 저장된 세션 쿠키 — 커밋 금지
├── posts/             # 발행할 .md 글 (첫 줄이 '# 제목')
│   └── done/          # 발행 완료된 글 이동 위치
└── logs/              # 실행 로그
```

## 로그인 방식: 쿠키 재사용 (권장)

네이버만큼은 아니지만 카카오 로그인도 캡차/2단계 인증이 걸릴 수 있습니다.
사람이 **한 번만** 직접 로그인해 쿠키를 저장해 두면, 이후 자동 실행은
비밀번호 없이 그 쿠키로 로그인 상태를 복원합니다.

```bash
# 1) 최초 1회: 브라우저가 뜨면 직접 로그인(캡차 통과) 후 터미널에서 Enter
python save_cookies.py        # -> cookies.json 생성

# 2) 이후 매 실행: 쿠키로 자동 로그인
python main.py
```

- `main.py` 는 **쿠키 로그인 우선 → 실패 시 .env 의 ID/PW 비밀번호 로그인**으로 폴백합니다.
- 쿠키가 만료되면(로그인 안 됨) 다시 `python save_cookies.py` 만 실행하면 됩니다.
- 쿠키 모드만 쓸 거면 `.env` 의 `TISTORY_ID/PW` 는 비워둬도 됩니다.
- ⚠️ `cookies.json` 은 비밀번호급 정보입니다. `.gitignore`에 등록되어 있으니 커밋하지 마세요.

## 실행 방법

```bash
cd tistory
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # 값 채우기 (절대 커밋 금지)
python main.py
```

## ⚠️ 처음 쓸 때 주의

1. **반드시 비공개(`PUBLISH_VISIBILITY=0`)로 먼저 테스트**하세요.
2. `HEADLESS=false`로 두고 브라우저 동작을 눈으로 확인하세요.
3. **셀렉터는 바뀝니다.** 동작이 멈추면 `tistory_bot.py`의 `SELECTORS`만
   개발자도구로 확인해 교체하면 됩니다.
4. **캡차**가 뜨면 자동 로그인이 막힙니다. 그럴 땐 직접 1회 로그인 후
   쿠키 재사용 방식으로 확장하세요(매뉴얼 4장 참고).
5. 약관상 과도한 자동화는 제재 대상입니다. 본인 계정·소량 운영 원칙을 지키세요.

## 다음 확장 지점 (코드 내 TODO)

- `tistory_bot.publish()`: 공개설정/카테고리/태그 선택 로직
- 쿠키 저장/재사용으로 캡차 회피
- OpenAI API로 본문 자동 생성 후 `posts/`에 적재
- 스케줄러(cron/launchd)로 정기 실행
