# -*- coding: utf-8 -*-
"""
tossmarketing/portfolio.html → A4 PDF (토스 마케팅 제출용)
- 페이지 분리/축소/인쇄 보정은 portfolio.html 의 @media print 에 내장 (단일 소스).
- 접힌 분석(.moredetail/.abcard.extra/.ps.psx)은 @media print 에서 전부 펼쳐져 PDF에 누락되지 않음.
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "portfolio.html").as_uri()
OUT = "/Users/jiuk/마케팅 개발/포트폴리오/토스 파이널/윤지욱_포트폴리오_토스마케팅.pdf"

FORCE_SHOW = """
  document.documentElement.classList.remove('js-motion');
  document.documentElement.classList.add('loaded');
  document.querySelectorAll('.reveal,.hero-anim,.grow-x,.grow-y').forEach(function(e){ e.classList.add('in'); });
  // 접힘 토글도 열린 상태로(이중 안전장치 — @media print 가 주담당)
  document.querySelectorAll('.moredetail').forEach(function(e){ e.classList.add('show'); });
  document.querySelectorAll('.abgrid').forEach(function(e){ e.classList.add('show-all'); });
  document.querySelectorAll('.psolve').forEach(function(e){ e.classList.add('show-all'); });
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600}, device_scale_factor=2)
        page.goto(SRC, wait_until="networkidle", timeout=120000)
        page.evaluate(FORCE_SHOW)
        page.evaluate("document.fonts && document.fonts.ready")
        try:
            page.wait_for_function("document.fonts.status === 'loaded'", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(1800)
        page.emulate_media(media="print")
        page.pdf(path=OUT, print_background=True, prefer_css_page_size=True)
        browser.close()
    print("PDF OK ->", OUT)

if __name__ == "__main__":
    main()
