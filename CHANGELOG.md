# Changelog

이 문서는 프로젝트의 주요 변경 사항을 기록합니다.

## [1.0.0] - 2026-03-03

### 거래소 마이그레이션: Upbit → Bithumb

거래소 API를 Upbit에서 Bithumb으로 전면 전환하였습니다.

#### 변경된 스크립트

- **collect_market_data.py** — Base URL `api.upbit.com` → `api.bithumb.com`, 환경변수 `UPBIT_*` → `BITHUMB_*`
- **execute_trade.py** — 주문 API를 v2(`/v2/orders`)로 변경, 파라미터 `ord_type` → `order_type`
- **get_portfolio.py** — Bithumb 계좌에 KRW 마켓이 없는 코인(에어드롭 등)이 존재하여 `/v1/market/all`로 유효 마켓 필터링 로직 추가
- **capture_chart.py** — 빗썸/TradingView가 headless 브라우저를 차단하여, 로컬 HTML에 TradingView 위젯을 임베드하는 방식으로 변경 (RSI + MACD 지표 포함)
- **notify_telegram.py** — 예시 메시지의 Upbit 참조를 Bithumb으로 변경

#### 변경된 설정 파일

- **.env.example** — `UPBIT_ACCESS_KEY/SECRET_KEY` → `BITHUMB_ACCESS_KEY/SECRET_KEY`
- **setup.sh** — API 발급 안내 문구를 빗썸으로 변경

#### 변경된 문서

- **CLAUDE.md** — 전체 Upbit 참조를 Bithumb으로 변경 (데이터 소스, 스킬 테이블, API 문서 링크)
- **README.md** — 아키텍처 다이어그램, 교육 커리큘럼, 프로젝트 구조, 기술 스택 업데이트. 출처 및 참고 자료 섹션 추가

#### 변경된 스킬 가이드

- **bithumb-api** (신규) — Bithumb REST API 스킬 문서 작성 (Quotation API v1, Exchange API v2, JWT 인증)
- **upbit-api** (삭제) — 기존 Upbit API 스킬 제거
- **crypto-trader** — 거래소 참조, 환경변수, 태그를 Bithumb으로 변경
- **chart-capture** — 차트 URL과 설명을 Bithumb으로 변경
- **trade-notifier** — 예시 에러 메시지 변경

### 테스트 결과

| 스크립트 | 상태 | 비고 |
|---------|------|------|
| collect_market_data.py | 통과 | BTC 98,748,000 KRW, RSI 41.43 |
| get_portfolio.py | 통과 | BTC 0.188개, 총 평가 ~18.6M KRW |
| execute_trade.py | 통과 | DRY_RUN=true 정상 |
| capture_chart.py | 통과 | TradingView 위젯 차트 캡처 성공 |
| run_analysis.sh | 통과 | 전체 파이프라인 데이터 수집 + 프롬프트 생성 |

## [0.1.0] - 2026-02-26

### 초기 릴리즈

- Claude Code 기반 암호화폐 자동매매 시스템 초기 구현
- Upbit API 연동 (시세 조회, 포트폴리오, 매매 실행)
- Fear & Greed Index, Tavily 뉴스, Playwright 차트 캡처
- Supabase DB 스키마, 텔레그램 알림
- cron 자동화 파이프라인 (run_analysis.sh, cron_run.sh, setup_cron.sh)
- 6개 Claude 스킬 문서
- 안전장치: DRY_RUN, EMERGENCY_STOP, MAX_TRADE_AMOUNT
