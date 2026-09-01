# 뉴스·주식 레이더 배포 가이드

`news-stock-dashboard`를 GitHub와 Streamlit Community Cloud에 배포할 때 필요한 요구사항과 제한사항입니다.

## 1. 현재 배포 방식

- 웹 배포: `app.py`를 Streamlit Community Cloud에서 실행
- 로컬 데스크톱 실행: `desktop.py`를 pywebview 창에서 실행

Cloud에는 `desktop.py`가 아니라 `app.py`를 엔트리포인트로 지정합니다.

## 2. 배포에 필요한 파일

```text
news-stock-dashboard/
├── app.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   └── collectors/
│       ├── __init__.py
│       ├── market.py
│       └── news.py
└── .streamlit/       # 선택 사항
    └── config.toml
```

`requirements.txt`는 엔트리포인트와 같은 폴더 또는 저장소 루트에 있어야 합니다. [Streamlit 의존성 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

현재 웹 배포 의존성은 다음과 같습니다.

```text
streamlit>=1.40
yfinance>=0.2.40
feedparser>=6.0
python-dotenv>=1.0
```

`pywebview`와 `pyinstaller`는 데스크톱 실행용이므로 웹 배포 의존성에 포함하지 않습니다.

## 3. GitHub 요구사항

1. GitHub 저장소를 준비합니다.
2. 프로젝트 파일을 저장소에 push합니다.
3. Streamlit Community Cloud에서 GitHub 계정을 연결합니다.
4. 저장소, 브랜치, 앱 파일을 선택합니다.

비공개 저장소는 Streamlit 계정에 읽기 권한이 필요합니다. [GitHub 연결 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account)

## 4. 배포 절차

1. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인합니다.
2. `Create app` 또는 `Deploy`를 선택합니다.
3. 저장소와 브랜치를 선택합니다.
4. 앱 파일에 `app.py`를 지정합니다.
5. `Deploy`를 실행합니다.
6. 빌드 로그에서 의존성 설치와 앱 시작 결과를 확인합니다.
7. 생성된 `streamlit.app` URL로 접속합니다.

Streamlit은 저장소의 파일을 복사한 뒤 원격 서버에서 앱을 실행합니다. [파일 구성 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)

## 5. 환경변수와 비밀값

현재 기본 설정은 다음과 같으며, 별도 설정 없이도 실행됩니다.

```text
DEFAULT_MARKET=US
NEWS_REFRESH_MINUTES=30
```

API 키나 비밀번호가 추가되면 배포 화면의 `Secrets`에 입력합니다. `.env`, API 키, 비밀번호를 GitHub에 commit하지 않습니다.

로컬에서는 `.env`를 사용하고, 배포 환경에서는 Streamlit Secrets 또는 환경변수를 사용합니다.

## 6. 외부 데이터 제약

앱은 다음 외부 서비스를 사용합니다.

- `yfinance`: Yahoo Finance 주가 조회
- `FinanceDataReader`: 시장별 종목 코드·기업명 목록 조회
- Google News RSS: 종목 검색 뉴스 조회

배포 서버가 외부 인터넷에 접속할 수 있어야 합니다. 무료 데이터는 실시간이 아니거나 누락될 수 있습니다.

Yahoo Finance에서 `429 Too Many Requests`가 발생하면 요청 제한에 걸린 것입니다.

- 짧은 시간에 새로고침을 반복하지 않습니다.
- 기본 캐시 시간인 30분 동안 반복 요청하지 않습니다.
- 일정 시간 후 다시 시도합니다.
- 계속 발생하면 다른 주가 API를 검토합니다.

RSS에 뉴스가 없거나 접속에 실패하면 앱은 오류 상태와 샘플 뉴스를 표시합니다. 샘플 데이터는 실제 시장 정보가 아닙니다.

## 7. 데이터 저장 제약

SQLite에는 관심 종목과 수집 뉴스가 저장됩니다. 하지만 Community Cloud의 로컬 파일은 영구 데이터베이스로 보장되지 않습니다.

앱 재시작, 재배포, 환경 교체 시 SQLite 데이터가 사라질 수 있습니다. 영구 저장이 필요하면 PostgreSQL, Supabase, Neon 같은 외부 데이터베이스로 전환해야 합니다.

인증 없이 공개 배포하면 방문자가 같은 저장 공간을 공유할 수 있으므로 개인 정보나 민감한 매매 기록을 저장하지 않습니다.

## 8. 보안 및 운영 원칙

- 투자 추천처럼 표현하지 않습니다.
- API 키와 비밀번호를 소스 코드에 저장하지 않습니다.
- 뉴스 원문 URL과 출처를 보존합니다.
- 실시간 데이터라고 표현하지 않습니다.
- 외부 사이트 이용약관과 API/RSS 호출 제한을 준수합니다.
- 외부 요청 실패 시 오류 상태와 샘플 데이터를 구분합니다.
- 공개 앱에서는 종목 입력과 요청 횟수를 제한하는 것을 권장합니다.

## 9. 배포 전 점검

- [ ] `app.py`, `src/`, `requirements.txt`가 GitHub에 올라갔는가
- [ ] `.env`와 비밀값이 제외되었는가
- [ ] 로컬에서 `streamlit run app.py`가 실행되는가
- [ ] 잘못된 티커가 앱 전체를 중단시키지 않는가
- [ ] 외부 API 실패 상태가 표시되는가
- [ ] 뉴스 원문 링크가 열리는가
- [ ] 배포 후 앱 로그에 import 오류가 없는가
- [ ] SQLite가 영구 저장소가 아님을 인지했는가

## 10. 실행 방식 비교

```text
로컬 웹:       streamlit run app.py → 브라우저
로컬 데스크톱: python desktop.py   → pywebview 창
클라우드:      GitHub → Streamlit Cloud → app.py → 웹 URL
```

웹 배포는 컴퓨터가 꺼져 있어도 접속할 수 있지만 클라우드 절전, 자원, 외부 API 제한의 영향을 받습니다. 데스크톱 실행은 로컬 환경을 사용하지만 컴퓨터가 켜져 있어야 합니다.

## 참고 문서

- [Streamlit Community Cloud 배포](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [앱 의존성 설정](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [파일 구성](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
- [Python 버전 설정](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python)
