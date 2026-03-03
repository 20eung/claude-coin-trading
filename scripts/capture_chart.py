#!/usr/bin/env python3
"""
Playwright로 Bithumb BTC/KRW 차트 캡처 스크립트

headless Chromium을 사용하여 차트를 캡처한다.
data/charts/ 에 타임스탬프 기반 파일명으로 저장한다.

의존성:
  pip install playwright
  playwright install chromium

출력: JSON (stdout)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path


TRADINGVIEW_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body { margin: 0; background: #fff; }
.chart-container { width: 1920px; height: 1080px; }
</style></head><body>
<div class="chart-container">
  <div class="tradingview-widget-container" style="width:100%;height:100%">
    <div id="tv_chart" style="width:100%;height:100%"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      container_id: "tv_chart",
      autosize: true,
      symbol: "BITHUMB:BTCKRW",
      interval: "60",
      timezone: "Asia/Seoul",
      theme: "light",
      style: "1",
      locale: "kr",
      toolbar_bg: "#f1f3f6",
      enable_publishing: false,
      hide_side_toolbar: false,
      studies: ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
    });
    </script>
  </div>
</div>
</body></html>"""


async def capture_chart():
    from playwright.async_api import async_playwright

    charts_dir = Path(os.getcwd()) / "data" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = str(charts_dir / f"btc_chart_{timestamp}.png")

    # TradingView 위젯 HTML을 임시 파일로 생성
    html_path = charts_dir / "_chart_widget.html"
    html_path.write_text(TRADINGVIEW_HTML, encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        await page.goto(
            f"file://{html_path.resolve()}",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        # TradingView 위젯 로딩 대기
        await page.wait_for_timeout(10000)

        await page.screenshot(path=screenshot_path, full_page=False)
        await browser.close()

    # 임시 HTML 파일 정리
    html_path.unlink(missing_ok=True)

    result = {
        "timestamp": datetime.now().isoformat(),
        "chart_path": screenshot_path,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(capture_chart())
    except Exception as e:
        json.dump({"error": str(e)}, sys.stderr, ensure_ascii=False)
        sys.exit(1)
