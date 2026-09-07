# news-stock-dashboard

뉴스와 주가를 한 화면에서 확인하는 Streamlit MVP입니다.

## 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run app.py
```

## Docker로 실행

Docker와 Docker Compose가 설치되어 있다면 다음 명령으로 계획 대시보드를 실행합니다.

```bash
docker compose up --build
```

브라우저에서 `http://localhost:8502`를 엽니다. SQLite 데이터는 프로젝트의 `data/` 디렉터리에 저장되어 컨테이너를 다시 만들어도 유지됩니다. 환경 설정이 필요하면 `.env` 파일을 프로젝트 루트에 만들고 실행합니다.

계획 대시보드는 `http://localhost:8502`에서 확인합니다. 기존 뉴스·주식 앱을 실행하려면 다음 명령을 사용합니다.

```bash
docker compose --profile app up --build app
```

뉴스·주식 앱 주소는 `http://localhost:8501`입니다.

```bash
docker compose down
```

Docker 이미지 안에서 테스트를 실행하려면 다음 명령을 사용합니다.

```bash
docker compose --profile test run --rm test
```

## 구현 계획 진행도 확인

`PROJECT_PLAN.md`와 현재 `master` 브랜치의 코드·Git 상태를 비교한 진행도 화면을 실행합니다.

```bash
git fetch origin master
python3 -m streamlit run plan_dashboard.py
```

Docker에서는 다음과 같이 실행합니다.

```bash
docker compose up --build
```

화면에서 전체 진행도, 단계별 진행도, 완료·부분 완료·미구현 목록, 코드 근거, 보완할 점, 최신 `origin/master` 커밋, 로컬 master에 아직 반영되지 않은 원격 커밋, 현재 변경사항을 확인할 수 있습니다. 컨테이너는 저장소를 읽기 전용으로 마운트하므로 원격 동기화는 실행 전에 `git fetch origin master`로 수행합니다.

`plan_dashboard.py`는 고정된 진입점만 유지하며, 실제 분석 결과와 UI/UX는 `plan-master-review` 스킬이 `plan_dashboard_generated.py`에 실행 시 생성합니다. 생성 파일은 Git에 저장하지 않습니다.

왼쪽 입력창에서 미국 티커(예: `AAPL`) 또는 한국 종목 코드를 입력합니다. 외부 API가 실패하면 상태 메시지와 함께 샘플 데이터가 표시됩니다.

기업명은 FinanceDataReader의 시장별 종목 목록에서 가져오며, 가져온 목록은 SQLite에 24시간 동안 캐시합니다. 새로운 종목도 소스코드 수정 없이 검색할 수 있습니다.

외부 주가·뉴스 요청은 기본 10초 timeout과 2회 재시도를 사용합니다. `.env`에서 `DATA_REQUEST_TIMEOUT_SECONDS`, `DATA_REQUEST_MAX_RETRIES`, `DATA_REQUEST_RETRY_DELAY_SECONDS`를 조정할 수 있습니다. 모든 재시도가 실패하면 마지막 성공 데이터가 있으면 이를 표시하고, 없으면 샘플 데이터와 오류 상태를 표시합니다. 수집 시도·성공·실패 상태는 SQLite에 저장되며, 발행 시각이 있는 뉴스는 기본 90일 뒤 자동 삭제됩니다. 보관 기간은 `DATA_RETENTION_DAYS`로 조정할 수 있습니다.

데이터는 참고용이며 투자 추천이 아닙니다. 무료 데이터는 지연될 수 있습니다.

## 데스크톱 창으로 실행

브라우저 대신 별도 앱 창으로 실행하려면 데스크톱 의존성을 설치합니다.

```bash
pip install -e '.[desktop]'
news-stock-radar
```

또는 다음 명령을 사용할 수 있습니다.

```bash
python desktop.py
```

앱을 닫으면 내부 Streamlit 서버도 함께 종료됩니다. 데스크톱 실행 시 SQLite 데이터는 운영체제별 사용자 데이터 폴더에 저장됩니다. 개발 중 프로젝트의 `data/`에 저장하려면 `.env`에 `RADAR_DATA_DIR=./data`를 설정하세요.

데스크톱 창이 열려 있는 동안에는 관심 종목을 `NEWS_REFRESH_MINUTES` 간격으로 순차 수집합니다. 수집은 SQLite에 저장되며, 앱을 닫으면 스케줄러도 종료됩니다. `.env`의 `SCHEDULED_COLLECTION_ENABLED=false`로 자동 수집을 끌 수 있습니다.
