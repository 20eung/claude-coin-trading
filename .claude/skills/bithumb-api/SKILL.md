---
name: bithumb-api
description: Bithumb 거래소 REST API 래퍼. 시세 조회, 계좌 잔고, 주문 실행, 주문 관리, 입출금 조회 등 Bithumb API의 전체 기능을 Python 스크립트로 제공한다. JWT 인증을 자동 처리한다.
version: 1.0.0
tags:
  - Bithumb
  - 거래소
  - API
  - 자동매매
---

# bithumb-api 스킬

Bithumb 거래소 API를 래핑한 스킬이다.

## 공식 문서

- API 레퍼런스: https://apidocs.bithumb.com/reference
- 인증 방식: JWT (JSON Web Token)
- Base URL: `https://api.bithumb.com`

## 환경 변수

```bash
BITHUMB_ACCESS_KEY=...
BITHUMB_SECRET_KEY=...
```

## 인증 방식

Bithumb API는 JWT 토큰 기반 인증을 사용한다. Access Key와 Secret Key로 JWT를 생성하여 `Authorization: Bearer {token}` 헤더에 포함한다.

```python
import hashlib, os, time, uuid, jwt, requests, urllib.parse

BASE = "https://api.bithumb.com"

def make_auth_header(query_params: dict | None = None) -> dict:
    payload = {
        "access_key": os.environ["BITHUMB_ACCESS_KEY"],
        "nonce": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
    }
    if query_params:
        qs = urllib.parse.urlencode(query_params)
        payload["query_hash"] = hashlib.sha512(qs.encode()).hexdigest()
        payload["query_hash_alg"] = "SHA512"
    token = jwt.encode(payload, os.environ["BITHUMB_SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
```

- 쿼리 파라미터가 있는 요청(주문 등)은 쿼리스트링을 SHA-512로 해싱하여 페이로드에 포함해야 한다.

## 레퍼런스 스크립트

| 스크립트 | 설명 |
|----------|------|
| `scripts/collect_market_data.py` | 현재가, OHLCV, 호가, 체결 + 기술지표(RSI, SMA, MACD, 볼린저) 수집 |
| `scripts/execute_trade.py` | 시장가 매수/매도 주문 실행 (DRY_RUN, EMERGENCY_STOP 안전장치 내장) |
| `scripts/get_portfolio.py` | 계좌 잔고 조회 + 보유 자산 평가 |

---

## Quotation API (시세 조회 - 인증 불필요)

### 마켓 코드

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/market/all` | 거래 가능한 마켓 목록 |

```python
r = requests.get(f"{BASE}/v1/market/all")
# [{"market":"KRW-BTC","korean_name":"비트코인","english_name":"Bitcoin",...}, ...]
```

### 캔들 (OHLCV)

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/candles/minutes/{unit}` | `market`, `count`(최대 200), unit: 1,3,5,10,15,30,60,240 | 분봉 |
| `GET /v1/candles/days` | `market`, `count`(최대 200), `convertingPriceUnit` | 일봉 |
| `GET /v1/candles/weeks` | `market`, `count`(최대 200) | 주봉 |
| `GET /v1/candles/months` | `market`, `count`(최대 200) | 월봉 |

```python
# 일봉 30일
r = requests.get(f"{BASE}/v1/candles/days", params={"market": "KRW-BTC", "count": 30})

# 4시간봉 42개
r = requests.get(f"{BASE}/v1/candles/minutes/240", params={"market": "KRW-BTC", "count": 42})

# 주봉 12주
r = requests.get(f"{BASE}/v1/candles/weeks", params={"market": "KRW-BTC", "count": 12})
```

**캔들 응답 필드:**
`market`, `candle_date_time_utc`, `candle_date_time_kst`, `opening_price`, `high_price`, `low_price`, `trade_price`, `timestamp`, `candle_acc_trade_price`, `candle_acc_trade_volume`

### 현재가 (Ticker)

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/ticker` | `markets` (쉼표 구분) | 종목별 현재가 |

```python
# 단일 종목
r = requests.get(f"{BASE}/v1/ticker", params={"markets": "KRW-BTC"})

# 복수 종목
r = requests.get(f"{BASE}/v1/ticker", params={"markets": "KRW-BTC,KRW-ETH,KRW-XRP"})
```

**Ticker 응답 필드:**
`market`, `trade_price`, `opening_price`, `high_price`, `low_price`, `prev_closing_price`, `change`(RISE/EVEN/FALL), `change_price`, `change_rate`, `signed_change_price`, `signed_change_rate`, `trade_volume`, `acc_trade_price`, `acc_trade_price_24h`, `acc_trade_volume`, `acc_trade_volume_24h`, `highest_52_week_price`, `lowest_52_week_price`, `timestamp`

### 호가 (Orderbook)

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/orderbook` | `markets` (쉼표 구분) | 매수/매도 호가 및 잔량 |

```python
r = requests.get(f"{BASE}/v1/orderbook", params={"markets": "KRW-BTC"})
# orderbook_units: [{ask_price, bid_price, ask_size, bid_size}, ...]
```

### 최근 체결 (Trades)

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/trades/ticks` | `market`, `count`(최대 500), `cursor`, `daysAgo`(최대 7) | 최근 체결 내역 |

```python
r = requests.get(f"{BASE}/v1/trades/ticks", params={"market": "KRW-BTC", "count": 100})
```

---

## Exchange API - 자산 (인증 필요)

### 계좌 잔고 조회

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/accounts` | 전체 계좌 잔고 |

```python
headers = make_auth_header()
r = requests.get(f"{BASE}/v1/accounts", headers=headers)
# [{"currency":"KRW","balance":"500000.0","locked":"0.0","avg_buy_price":"0",...}, ...]
```

**응답 필드:** `currency`, `balance`, `locked`, `avg_buy_price`, `avg_buy_price_modified`, `unit_currency`

---

## Exchange API - 주문 (인증 필요, v2)

> Bithumb 주문 API는 **v2** 엔드포인트를 사용한다. 파라미터명이 `ord_type` 대신 `order_type`이며, 응답에 `uuid` 대신 `order_id`를 반환한다.

### 주문 가능 정보 조회

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/orders/chance` | `market` (필수) | 마켓별 주문 가능 정보 |

```python
params = {"market": "KRW-BTC"}
headers = make_auth_header(params)
r = requests.get(f"{BASE}/v1/orders/chance", params=params, headers=headers)
```

**응답 필드:**

| 필드 | 설명 |
|------|------|
| `bid_fee` | 매수 수수료율 |
| `ask_fee` | 매도 수수료율 |
| `maker_bid_fee` | 메이커 매수 수수료율 |
| `maker_ask_fee` | 메이커 매도 수수료율 |
| `market.id` | 마켓 ID |
| `market.bid_types` | 매수 주문 가능 유형 배열 |
| `market.ask_types` | 매도 주문 가능 유형 배열 |
| `market.bid.min_total` | 최소 매수 주문 금액 |
| `market.max_total` | 최대 주문 금액 |
| `market.state` | 마켓 상태 (active 등) |
| `bid_account.balance` | 매수 통화 잔고 |
| `ask_account.balance` | 매도 자산 잔고 |

### 주문 생성 (v2)

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /v2/orders` | 매수/매도 주문 |

```python
# 시장가 매수: KRW 금액 지정
params = {"market": "KRW-BTC", "side": "bid", "order_type": "price", "price": "100000"}

# 시장가 매도: 수량 지정
params = {"market": "KRW-BTC", "side": "ask", "order_type": "market", "volume": "0.001"}

# 지정가 매수: 가격 + 수량
params = {"market": "KRW-BTC", "side": "bid", "order_type": "limit", "price": "50000000", "volume": "0.001"}

headers = make_auth_header(params)
r = requests.post(f"{BASE}/v2/orders", json=params, headers=headers)
```

**주문 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `market` | str | O | 마켓 코드 (예: `KRW-BTC`) |
| `side` | str | O | `bid`: 매수, `ask`: 매도 |
| `order_type` | str | O | 주문 유형 (아래 표 참조) |
| `price` | str | △ | 주문 가격 또는 총액 |
| `volume` | str | △ | 주문 수량 |

**주문 유형별 필수 파라미터:**

| order_type | 설명 | 매수(bid) 필수 | 매도(ask) 필수 |
|------------|------|---------------|---------------|
| `limit` | 지정가 | price + volume | price + volume |
| `price` | 시장가 매수 | price (총액) | 사용 불가 |
| `market` | 시장가 매도 | 사용 불가 | volume (수량) |

**주문 응답 필드:**
`order_id`, `side`, `order_type`, `price`, `market`, `created_at`

### 개별 주문 조회

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/order` | `uuid` 또는 `identifier` | 단일 주문 상세 조회 |

### 주문 목록 조회

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `GET /v1/orders` | `market`, `state`, `page`, `limit`, `order_by` | 주문 목록 조회 |

### 주문 취소

| 엔드포인트 | 파라미터 | 설명 |
|-----------|----------|------|
| `DELETE /v2/orders` | `uuid` 또는 `identifier` | 주문 취소 |

---

## Exchange API - 출금 (인증 필요)

### 출금 관련 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/withdraws/chance` | 출금 가능 정보 |
| `GET /v1/withdraws` | 출금 이력 목록 |
| `GET /v1/withdraw` | 개별 출금 조회 |
| `POST /v1/withdraws` | 암호화폐 출금 |
| `POST /v1/withdraws/krw` | KRW 출금 |

---

## Exchange API - 입금 (인증 필요)

### 입금 관련 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/deposits` | 입금 이력 목록 |
| `GET /v1/deposit` | 개별 입금 조회 |
| `GET /v1/deposits/address` | 입금 주소 목록 |
| `POST /v1/deposits/address` | 입금 주소 요청 |

---

## Exchange API - 서비스 상태 (인증 필요)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /v1/status/deposit-withdrawal` | 입출금 서비스 상태 |
| `GET /v1/api-keys` | API 키 목록 |

---

## 실전 활용 레시피

### 매수 전 잔고 확인 → 주문 가능 금액 체크 → 주문

```python
# 1. 주문 가능 정보 확인
params = {"market": "KRW-BTC"}
headers = make_auth_header(params)
chance = requests.get(f"{BASE}/v1/orders/chance", params=params, headers=headers).json()

available_krw = float(chance["bid_account"]["balance"])
fee_rate = float(chance["bid_fee"])
min_total = float(chance["market"]["bid"]["min_total"])

# 2. 주문 금액 결정
order_amount = min(available_krw * 0.1, float(os.environ.get("MAX_TRADE_AMOUNT", 100000)))
if order_amount < min_total:
    print(f"최소 주문 금액({min_total}원) 미달", file=sys.stderr)
    sys.exit(1)

# 3. 시장가 매수 (v2 API)
params = {"market": "KRW-BTC", "side": "bid", "order_type": "price", "price": str(int(order_amount))}
headers = make_auth_header(params)
result = requests.post(f"{BASE}/v2/orders", json=params, headers=headers).json()
print(f"주문 접수: {result['order_id']}")
```

---

## Rate Limit

| API 그룹 | 초당 요청 수 | 비고 |
|----------|------------|------|
| Exchange API (주문/계좌) | 10회 | 계정 단위 |
| Quotation API (시세) | 30회 | IP 단위 |

- 429 응답 시 1초 대기 후 재시도
- `Remaining-Req` 헤더에 남은 요청 수가 포함됨

## 주의 사항

- API 키 발급 시 **서버 공인 IP를 화이트리스트에 등록**해야 한다.
- 자산 조회 및 주문 권한은 API 키 발급 시 별도 체크 필요.
- 처음에는 반드시 `DRY_RUN=true`로 테스트.
- POST 요청의 body는 JSON 형식이지만, JWT query_hash 계산 시에는 URL-encoded 쿼리스트링으로 해싱해야 한다.
- 주문 API는 v2를 사용하며, 자체매매 방지(self-trade prevention) 기능이 내장되어 있다.
